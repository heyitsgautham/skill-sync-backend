"""
Resume Service - Reusable resume upload and processing functions
"""

import os
import shutil
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Resume
from app.services.parser_service import ResumeParser
from app.services.rag_engine import rag_engine
from app.services.resume_intelligence_service import ResumeIntelligenceService
from app.services.s3_service import s3_service


class ResumeService:
    """Service for handling resume uploads and processing"""
    
    @staticmethod
    async def upload_and_process_resume(
        file: UploadFile,
        student_id: int,
        db: Session,
        is_tailored: bool = False,
        internship_id: Optional[int] = None,
        base_resume_id: Optional[int] = None,
        deactivate_others: bool = True
    ) -> Resume:
        """
        Upload and process a resume (base or tailored)
        
        Args:
            file: The uploaded file
            student_id: ID of the student
            db: Database session
            is_tailored: Whether this is a tailored resume for a specific internship
            internship_id: ID of internship if tailored resume
            base_resume_id: ID of the base resume this was tailored from
            deactivate_others: Whether to deactivate other resumes (default True for base resumes)
            
        Returns:
            Resume object
        """
        import logging
        logger = logging.getLogger(__name__)
        
        resume_type = "tailored" if is_tailored else "base"
        logger.info(f"📄 Starting {resume_type} resume upload for student {student_id}")
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Create upload directory
        upload_dir = "app/public/resumes"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        if is_tailored and internship_id:
            file_path = os.path.join(upload_dir, f"{student_id}_tailored_{internship_id}_{file.filename}")
        else:
            file_path = os.path.join(upload_dir, f"{student_id}_{file.filename}")
        
        try:
            # Save file locally (temporary for parsing)
            logger.info(f"💾 Saving file to {file_path}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Upload to S3 if enabled
            s3_key = None
            if s3_service.is_enabled():
                logger.info(f"☁️ Uploading to S3...")
                s3_key = s3_service.upload_resume(
                    file_path=file_path,
                    student_id=student_id,
                    file_name=file.filename,
                    is_tailored=is_tailored,
                    internship_id=internship_id
                )
                if s3_key:
                    logger.info(f"✅ Uploaded to S3: {s3_key}")
                else:
                    logger.warning(f"⚠️ S3 upload failed, will use local storage only")
            else:
                logger.info(f"ℹ️ S3 not enabled, using local storage only")
            
            # Parse resume - first extract raw text
            logger.info(f"🔍 Parsing resume (basic extraction)...")
            basic_data = ResumeParser.parse_resume(file_path)
            resume_text = basic_data.get('parsed_content', '')
            logger.info(f"✅ Extracted raw text ({len(resume_text)} chars)")
            
            # Use Gemini for intelligent extraction
            logger.info(f"🧠 Performing intelligent extraction with Gemini...")
            intelligence_service = ResumeIntelligenceService()
            structured_data = intelligence_service.extract_structured_data(resume_text)
            logger.info(f"✅ Structured data extracted - {len(structured_data.get('all_skills', []))} skills found")
            
            # Combine data
            parsed_data = {
                **basic_data,
                **structured_data,
                'parsed_content': resume_text
            }
            
            # Deactivate old active resumes if this is a base resume
            if deactivate_others and not is_tailored:
                db.query(Resume).filter(
                    Resume.student_id == student_id,
                    Resume.is_active == 1,
                    Resume.is_tailored == 0
                ).update({"is_active": 0})
            
            # Generate embedding directly (for faster matching)
            logger.info(f"🔢 Generating embedding vector...")
            embedding = None
            extracted_skills = structured_data.get('all_skills', basic_data.get('extracted_skills', []))
            if resume_text and extracted_skills:
                embedding_text = f"{resume_text}\n\nSkills: {', '.join(extracted_skills)}"
                embedding = rag_engine.generate_embedding(embedding_text)
                logger.info(f"✅ Generated embedding: dimension {len(embedding) if embedding else 0}")
            
            # Create new resume record
            logger.info(f"💾 Creating resume record in database...")
            new_resume = Resume(
                student_id=student_id,
                file_path=file_path,
                s3_key=s3_key,  # Store S3 key for cloud access
                file_name=file.filename,
                parsed_content=resume_text,
                parsed_data=structured_data,  # Store structured Gemini data
                extracted_skills=extracted_skills,
                # Note: embedding is stored in ChromaDB, not PostgreSQL
                is_active=1 if not is_tailored else 0,  # Tailored resumes are not "active" by default
                is_tailored=1 if is_tailored else 0,
                tailored_for_internship_id=internship_id,
                base_resume_id=base_resume_id
            )
            
            db.add(new_resume)
            db.flush()  # Flush to get ID without committing
            logger.info(f"✅ Resume record prepared with ID: {new_resume.id}")
            
            # Store in vector DB (ChromaDB) for semantic search
            logger.info(f"📚 Storing in vector database (ChromaDB)...")
            
            # Build metadata (ChromaDB doesn't accept None values)
            metadata = {
                "student_id": student_id,
                "file_name": file.filename,
                "is_tailored": is_tailored
            }
            # Only add internship_id if this is a tailored resume
            if is_tailored and internship_id is not None:
                metadata["internship_id"] = internship_id
            
            embedding_id = rag_engine.store_resume_embedding(
                resume_id=str(new_resume.id),
                content=resume_text,
                skills=extracted_skills,
                metadata=metadata
            )
            logger.info(f"✅ Stored in ChromaDB with ID: {embedding_id}")
            
            # Update resume with embedding ID
            new_resume.embedding_id = embedding_id
            
            # Commit everything together (atomic operation)
            db.commit()
            db.refresh(new_resume)
            logger.info(f"✅ All changes committed to database")
            
            logger.info(f"🎉 {resume_type.capitalize()} resume processing complete!")
            return new_resume
            
        except Exception as e:
            # Cleanup on error
            if os.path.exists(file_path):
                os.remove(file_path)
            db.rollback()
            raise Exception(f"Error processing resume: {str(e)}")
    
    @staticmethod
    def get_resume_text(student_id: int, db: Session) -> str:
        """Get the full text of a student's active resume"""
        resume = db.query(Resume).filter(
            Resume.student_id == student_id,
            Resume.is_active == 1
        ).first()
        
        if not resume:
            return ""
        
        return resume.parsed_content or ""
