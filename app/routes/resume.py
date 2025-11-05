"""
Resume API Routes
"""

import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models import User, Resume, UserRole
from app.services.parser_service import ResumeParser
from app.services.rag_engine import rag_engine
from app.utils.security import get_current_user

router = APIRouter(prefix="/resume", tags=["Resume"])

# Pydantic schemas
class ResumeResponse(BaseModel):
    id: int
    student_id: int
    file_name: str
    extracted_skills: List[str] = []
    is_active: int
    created_at: str | None = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        # Try to get skills from extracted_skills field first, then from parsed_data
        skills = []
        if obj.extracted_skills:
            skills = obj.extracted_skills
        elif obj.parsed_data and isinstance(obj.parsed_data, dict):
            skills = obj.parsed_data.get('all_skills', [])
        
        return cls(
            id=obj.id,
            student_id=obj.student_id,
            file_name=obj.file_name,
            extracted_skills=skills,
            is_active=obj.is_active,
            created_at=str(obj.created_at) if obj.created_at else None
        )


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and parse resume for student
    
    - **file**: Resume file (PDF, DOCX, or TXT)
    - Extracts text, skills, and generates embeddings
    - Stores in database and vector DB
    """
    # Verify user is a student
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can upload resumes"
        )
    
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = "app/public/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse resume
        parsed_data = ResumeParser.parse_resume(file_path)
        
        # Deactivate old resumes
        db.query(Resume).filter(
            Resume.student_id == current_user.id,
            Resume.is_active == 1
        ).update({"is_active": 0})
        
        # Create new resume record
        new_resume = Resume(
            student_id=current_user.id,
            file_path=file_path,
            file_name=file.filename,
            parsed_content=parsed_data['parsed_content'],
            extracted_skills=parsed_data['extracted_skills'],
            is_active=1
        )
        
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        
        # Store embedding in vector DB
        embedding_id = rag_engine.store_resume_embedding(
            resume_id=str(new_resume.id),
            content=parsed_data['parsed_content'],
            skills=parsed_data['extracted_skills'],
            metadata={
                "student_id": current_user.id,
                "file_name": file.filename
            }
        )
        
        # Update resume with embedding ID
        new_resume.embedding_id = embedding_id
        db.commit()
        db.refresh(new_resume)
        
        return ResumeResponse.from_orm(new_resume)
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(file_path):
            os.remove(file_path)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing resume: {str(e)}"
        )


@router.get("/my-resumes", response_model=List[ResumeResponse])
def get_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all resumes for current student
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view resumes"
        )
    
    resumes = db.query(Resume).filter(
        Resume.student_id == current_user.id
    ).order_by(Resume.created_at.desc()).all()
    
    return [ResumeResponse.from_orm(resume) for resume in resumes]


@router.put("/{resume_id}/activate", response_model=ResumeResponse)
def activate_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set a resume as active (deactivates all other resumes)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Activating resume {resume_id} for user {current_user.id}")
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.student_id == current_user.id
    ).first()
    
    if not resume:
        logger.warning(f"Resume {resume_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Deactivate all other resumes for this student
    deactivated_count = db.query(Resume).filter(
        Resume.student_id == current_user.id,
        Resume.is_active == 1
    ).update({"is_active": 0})
    
    logger.info(f"Deactivated {deactivated_count} resumes for user {current_user.id}")
    
    # Activate this resume
    resume.is_active = 1
    db.commit()
    db.refresh(resume)
    
    logger.info(f"Resume {resume_id} activated successfully for user {current_user.id}")
    
    return ResumeResponse.from_orm(resume)


@router.get("/{resume_id}/parsed-data")
def get_resume_parsed_data(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get parsed data for a specific resume
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.student_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Return parsed data if available
    if resume.parsed_data:
        # Calculate processing details
        skills_count = len(resume.parsed_data.get('all_skills', []))
        experience = resume.parsed_data.get('total_experience_years', 0)
        education_count = len(resume.parsed_data.get('education', []))
        projects_count = len(resume.parsed_data.get('projects', []))
        certifications_count = len(resume.parsed_data.get('certifications', []))
        
        return {
            "success": True,
            "resume_id": resume.id,
            "file_name": resume.file_name,
            "structured_data": resume.parsed_data,
            "processing_details": {
                "skills_extracted": skills_count,
                "experience_calculated": f"{experience} years",
                "education_found": education_count,
                "projects_found": projects_count,
                "certifications_found": certifications_count
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No parsed data available for this resume"
        )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a resume
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.student_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Delete from vector DB
    if resume.embedding_id:
        rag_engine.delete_resume_embedding(str(resume.id))
    
    # Delete file
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    
    # Delete from database
    db.delete(resume)
    db.commit()
    
    return None
