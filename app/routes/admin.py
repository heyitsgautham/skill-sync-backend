"""
Admin API Routes
Endpoints for administrative operations
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models import User, UserRole
from app.utils.security import get_current_user
from app.services.embedding_recompute_service import EmbeddingRecomputeService

router = APIRouter(prefix="/admin", tags=["Admin"])


class RecomputeResponse(BaseModel):
    """Response model for recompute embeddings endpoint"""
    message: str
    resumes: Dict
    internships: Dict
    matches: Dict = None
    
    class Config:
        from_attributes = True


@router.post("/recompute-embeddings", response_model=RecomputeResponse)
def recompute_all_embeddings_and_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recompute all embeddings and recalculate matches (Admin only)
    
    This endpoint:
    1. Recomputes embeddings for all resumes (base + tailored)
    2. Recomputes embeddings for all active internships
    3. Recalculates all student-internship matches
    
    Uses intelligent caching based on content hashing:
    - Only recomputes if content has changed
    - Shows progress of cached vs newly computed
    
    Returns detailed progress information.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Verify user is admin
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can recompute embeddings"
        )
    
    try:
        logger.info(f"🔄 Admin {current_user.email} initiated embedding recomputation")
        
        # Step 1: Recompute embeddings
        logger.info("📊 Step 1/2: Recomputing embeddings...")
        embedding_results = EmbeddingRecomputeService.recompute_all_embeddings(db)
        
        logger.info(f"✅ Resumes: {embedding_results['resumes']['cached']} cached, "
                   f"{embedding_results['resumes']['recomputed']} recomputed, "
                   f"{embedding_results['resumes']['failed']} failed")
        
        logger.info(f"✅ Internships: {embedding_results['internships']['cached']} cached, "
                   f"{embedding_results['internships']['recomputed']} recomputed, "
                   f"{embedding_results['internships']['failed']} failed")
        
        # Step 2: Recalculate matches
        logger.info("🔗 Step 2/2: Recalculating student-internship matches...")
        match_results = EmbeddingRecomputeService.recalculate_all_matches(db)
        
        logger.info(f"✅ Matches: {match_results['successful']} calculated, "
                   f"{match_results['failed']} failed")
        
        logger.info("🎉 Embedding recomputation completed successfully!")
        
        # Prepare summary
        resume_summary = f"{embedding_results['resumes']['cached']} cached, " \
                        f"{embedding_results['resumes']['recomputed']} recomputed"
        
        internship_summary = f"{embedding_results['internships']['cached']} cached, " \
                            f"{embedding_results['internships']['recomputed']} recomputed"
        
        return RecomputeResponse(
            message="Successfully recomputed embeddings and matches",
            resumes={
                'total': embedding_results['resumes']['total'],
                'cached': embedding_results['resumes']['cached'],
                'recomputed': embedding_results['resumes']['recomputed'],
                'failed': embedding_results['resumes']['failed'],
                'summary': resume_summary
            },
            internships={
                'total': embedding_results['internships']['total'],
                'cached': embedding_results['internships']['cached'],
                'recomputed': embedding_results['internships']['recomputed'],
                'failed': embedding_results['internships']['failed'],
                'summary': internship_summary
            },
            matches={
                'total': match_results['total_matches'],
                'successful': match_results['successful'],
                'failed': match_results['failed']
            }
        )
        
    except Exception as e:
        logger.error(f"  Error recomputing embeddings: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recomputing embeddings: {str(e)}"
        )


@router.post("/clear-chromadb")
def clear_chromadb_embeddings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear all student resume embeddings from ChromaDB (Admin only)
    
    This will:
    1. Delete all resume embeddings from ChromaDB
    2. Clear student-internship match data from database
    3. Clear embedding_id from resumes table
    
    ⚠️ WARNING: This is a destructive operation!
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Verify user is admin
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can clear ChromaDB"
        )
    
    try:
        from app.models import Resume, StudentInternshipMatch
        from app.services.rag_engine import rag_engine
        
        logger.info(f"🗑️  Admin {current_user.email} initiated ChromaDB cleanup")
        
        # Step 1: Clear ALL embeddings from ChromaDB at once (NEW BULK METHOD)
        chromadb_cleared_count = rag_engine.clear_all_resume_embeddings()
        logger.info(f"📊 Cleared {chromadb_cleared_count} embeddings from ChromaDB")
        
        # Step 2: Get all resumes with embedding_id in PostgreSQL
        resumes = db.query(Resume).filter(Resume.embedding_id.isnot(None)).all()
        
        logger.info(f"📊 Found {len(resumes)} resumes with embedding_id in PostgreSQL")
        
        # Step 3: Clear embedding_id from PostgreSQL
        for resume in resumes:
            resume.embedding_id = None
        
        # Step 4: Clear student-internship matches
        matches_deleted = db.query(StudentInternshipMatch).delete()
        
        # Commit changes
        db.commit()
        
        logger.info(f"✅ ChromaDB cleanup completed!")
        logger.info(f"   - ChromaDB embeddings deleted: {chromadb_cleared_count}")
        logger.info(f"   - PostgreSQL resumes cleared: {len(resumes)}")
        logger.info(f"   - Matches cleared: {matches_deleted}")
        
        return {
            "success": True,
            "message": "Successfully cleared ChromaDB embeddings",
            "resumes_cleared": chromadb_cleared_count,
            "postgres_cleared": len(resumes),
            "matches_cleared": matches_deleted
        }
        
    except Exception as e:
        logger.error(f"  Error clearing ChromaDB: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing ChromaDB: {str(e)}"
        )


@router.post("/reindex-all-students")
def reindex_all_student_resumes(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Re-upload and re-index all 50 student resumes (Admin only)
    
    This will:
    1. Find all resume files in app/public/resumes/
    2. For each resume: extract text → parse with Gemini → generate embeddings
    3. Store in ChromaDB and update database
    4. Recalculate student-internship matches
    
    This is a background task that may take several minutes.
    """
    import logging
    import os
    import glob
    logger = logging.getLogger(__name__)
    
    # Verify user is admin
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reindex resumes"
        )
    
    try:
        from app.services.parser_service import ResumeParser
        from app.services.resume_intelligence_service import ResumeIntelligenceService
        from app.services.rag_engine import rag_engine
        from app.models import Resume, User as UserModel
        
        logger.info(f"🔄 Admin {current_user.email} initiated full resume reindexing")
        
        # Find all resume files in app/public/resumes/
        resume_dir = "app/public/resumes"
        if not os.path.exists(resume_dir):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume directory not found: {resume_dir}"
            )
        
        # Get all PDF, DOCX, and TXT files
        resume_files = []
        for ext in ['*.pdf', '*.docx', '*.txt']:
            resume_files.extend(glob.glob(os.path.join(resume_dir, ext)))
        
        if not resume_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume files found in directory"
            )
        
        logger.info(f"📊 Found {len(resume_files)} resume files to process")
        
        # Initialize services
        parser = ResumeParser()
        intelligence_service = ResumeIntelligenceService()
        
        # Process each resume in background
        def process_all_resumes():
            successful = 0
            failed = 0
            
            # Get all students
            students = db.query(UserModel).filter(UserModel.role == UserRole.student).all()
            student_map = {student.email.split('@')[0].lower(): student for student in students}
            
            for resume_file in resume_files:
                try:
                    file_name = os.path.basename(resume_file)
                    logger.info(f"📄 Processing: {file_name}")
                    
                    # Extract text
                    if resume_file.endswith('.pdf'):
                        text = parser.extract_text_from_pdf(resume_file)
                    elif resume_file.endswith('.docx'):
                        text = parser.extract_text_from_docx(resume_file)
                    else:
                        with open(resume_file, 'r', encoding='utf-8') as f:
                            text = f.read()
                    
                    # Extract structured data using Gemini
                    structured_data = intelligence_service.extract_structured_data(text)
                    
                    # Generate embedding
                    embedding_text = f"{text}\n\nSkills: {', '.join(structured_data.get('all_skills', []))}"
                    embedding = rag_engine.generate_embedding(embedding_text)
                    
                    # Find matching student by filename (e.g., "alex_resume.pdf" -> "alex")
                    student_name = file_name.split('_')[0].lower().replace('-', '').replace('.', '')
                    student = student_map.get(student_name)
                    
                    if not student:
                        logger.warning(f"⚠️  No student found for resume: {file_name}")
                        failed += 1
                        continue
                    
                    # Deactivate old resumes
                    db.query(Resume).filter(
                        Resume.student_id == student.id,
                        Resume.is_active == 1
                    ).update({"is_active": 0})
                    
                    # Create new resume entry
                    resume = Resume(
                        student_id=student.id,
                        file_name=file_name,
                        file_path=resume_file,
                        parsed_data=structured_data,
                        embedding=embedding,
                        is_active=1
                    )
                    db.add(resume)
                    db.flush()  # Get the resume.id
                    
                    # Store in ChromaDB
                    embedding_id = rag_engine.store_resume_embedding(
                        resume_id=str(resume.id),
                        content=text,
                        skills=structured_data.get('all_skills', []),
                        metadata={
                            'student_id': student.id,
                            'file_name': file_name,
                            'total_experience': structured_data.get('total_experience_years', 0)
                        }
                    )
                    
                    # Update resume with embedding_id
                    resume.embedding_id = embedding_id
                    
                    # Update student profile
                    student.skills = structured_data.get('all_skills', [])
                    student.total_experience_years = structured_data.get('total_experience_years', 0)
                    
                    db.commit()
                    successful += 1
                    logger.info(f"✅ Successfully processed: {file_name}")
                    
                except Exception as e:
                    logger.error(f"  Failed to process {file_name}: {str(e)}")
                    db.rollback()
                    failed += 1
            
            logger.info(f"🎉 Reindexing completed! Success: {successful}, Failed: {failed}")
            
            # Recalculate matches
            try:
                logger.info("🔗 Recalculating student-internship matches...")
                match_results = EmbeddingRecomputeService.recalculate_all_matches(db)
                logger.info(f"✅ Matches recalculated: {match_results['successful']}")
            except Exception as e:
                logger.error(f"  Failed to recalculate matches: {str(e)}")
        
        # Add to background tasks
        background_tasks.add_task(process_all_resumes)
        
        return {
            "success": True,
            "message": f"Started reindexing {len(resume_files)} student resumes in background",
            "total_files": len(resume_files),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"  Error starting reindexing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting reindexing: {str(e)}"
        )


@router.get("/system-status")
def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get system status including embedding statistics (Admin only)
    
    Returns counts of resumes, internships, and matches
    """
    from app.models import Resume, Internship, StudentInternshipMatch
    
    # Verify user is admin
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view system status"
        )
    
    try:
        # Count resumes
        total_resumes = db.query(Resume).count()
        base_resumes = db.query(Resume).filter(Resume.is_tailored == 0).count()
        tailored_resumes = db.query(Resume).filter(Resume.is_tailored == 1).count()
        resumes_with_embeddings = db.query(Resume).filter(Resume.embedding_id.isnot(None)).count()
        
        # Count internships
        total_internships = db.query(Internship).count()
        active_internships = db.query(Internship).filter(Internship.is_active == 1).count()
        
        # Count matches
        total_matches = db.query(StudentInternshipMatch).count()
        
        return {
            'resumes': {
                'total': total_resumes,
                'base': base_resumes,
                'tailored': tailored_resumes,
                'with_embeddings': resumes_with_embeddings
            },
            'internships': {
                'total': total_internships,
                'active': active_internships
            },
            'matches': {
                'total': total_matches
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system status: {str(e)}"
        )
