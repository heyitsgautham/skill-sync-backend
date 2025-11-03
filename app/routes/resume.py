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
    extracted_skills: List[str]
    is_active: int
    
    class Config:
        from_attributes = True


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and parse resume for student
    
    - **file**: Resume file (PDF or DOCX)
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
    allowed_extensions = ['.pdf', '.docx', '.doc']
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
        
        return new_resume
        
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
    
    return resumes


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
