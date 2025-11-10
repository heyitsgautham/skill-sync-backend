"""
Student Routes
Endpoints for student-specific operations like profile management
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.utils.security import get_current_user

router = APIRouter()

# Request/Response Models
class UpdateProfileRequest(BaseModel):
    """Student profile update request model"""
    skills: List[str] = Field(default=None, description="List of student skills")
    total_experience_years: float = Field(default=None, description="Total years of experience")

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

@router.put("/profile", response_model=MessageResponse)
async def update_student_profile(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update student profile (Student only)
    
    Updates student-specific fields like skills and experience.
    Only accessible by student users.
    
    - **skills**: List of skills (optional)
    - **total_experience_years**: Total years of experience (optional)
    """
    # Verify user is a student
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can update their profile"
        )
    
    try:
        # Update fields if provided
        if request.skills is not None:
            current_user.skills = request.skills
        if request.total_experience_years is not None:
            current_user.total_experience_years = request.total_experience_years
        
        db.commit()
        
        return MessageResponse(
            message="Student profile updated successfully"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )
