"""
Internship API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models import User, Internship, UserRole
from app.services.parser_service import InternshipParser
from app.services.rag_engine import rag_engine
from app.utils.security import get_current_user

router = APIRouter(prefix="/internship", tags=["Internship"])

# Pydantic schemas
class InternshipCreate(BaseModel):
    title: str
    description: str
    required_skills: Optional[List[str]] = None
    location: Optional[str] = None
    duration: Optional[str] = None
    stipend: Optional[str] = None


class InternshipResponse(BaseModel):
    id: int
    company_id: int
    title: str
    description: str
    required_skills: Optional[List[str]] = None
    location: Optional[str] = None
    duration: Optional[str] = None
    stipend: Optional[str] = None
    is_active: int
    
    class Config:
        from_attributes = True


class InternshipWithMatchScore(InternshipResponse):
    match_score: Optional[int] = None


@router.post("/post", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
def post_internship(
    internship_data: InternshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Post a new internship (Company only)
    
    - **title**: Internship title
    - **description**: Detailed description
    - **required_skills**: List of required skills (auto-extracted if not provided)
    - **location**: Location (optional)
    - **duration**: Duration (optional)
    - **stipend**: Stipend information (optional)
    """
    # Verify user is a company
    if current_user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can post internships"
        )
    
    try:
        # Parse internship data to extract skills if not provided
        parsed_data = InternshipParser.parse_internship(internship_data.dict())
        
        # Create internship record
        new_internship = Internship(
            company_id=current_user.id,
            title=parsed_data['title'],
            description=parsed_data['description'],
            required_skills=parsed_data.get('required_skills'),
            location=parsed_data.get('location'),
            duration=parsed_data.get('duration'),
            stipend=parsed_data.get('stipend'),
            is_active=1
        )
        
        db.add(new_internship)
        db.commit()
        db.refresh(new_internship)
        
        # Store embedding in vector DB
        embedding_id = rag_engine.store_internship_embedding(
            internship_id=str(new_internship.id),
            title=new_internship.title,
            description=new_internship.description,
            required_skills=new_internship.required_skills or [],
            metadata={
                "company_id": current_user.id,
                "location": new_internship.location,
                "duration": new_internship.duration
            }
        )
        
        return new_internship
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error posting internship: {str(e)}"
        )


@router.get("/list", response_model=List[InternshipResponse])
def list_internships(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all active internships (public endpoint, no authentication required)
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    internships = db.query(Internship).filter(
        Internship.is_active == 1
    ).offset(skip).limit(limit).all()
    
    return internships


@router.get("/my-posts", response_model=List[InternshipResponse])
def get_my_internships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all internships posted by current company
    """
    if current_user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can view their posts"
        )
    
    internships = db.query(Internship).filter(
        Internship.company_id == current_user.id
    ).order_by(Internship.created_at.desc()).all()
    
    return internships


@router.get("/{internship_id}", response_model=InternshipResponse)
def get_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get internship details by ID
    """
    internship = db.query(Internship).filter(
        Internship.id == internship_id,
        Internship.is_active == 1
    ).first()
    
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found"
        )
    
    return internship


@router.put("/{internship_id}", response_model=InternshipResponse)
def update_internship(
    internship_id: int,
    internship_data: InternshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an internship posting
    """
    internship = db.query(Internship).filter(
        Internship.id == internship_id,
        Internship.company_id == current_user.id
    ).first()
    
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found"
        )
    
    try:
        # Parse updated data
        parsed_data = InternshipParser.parse_internship(internship_data.dict())
        
        # Update fields
        internship.title = parsed_data['title']
        internship.description = parsed_data['description']
        internship.required_skills = parsed_data.get('required_skills')
        internship.location = parsed_data.get('location')
        internship.duration = parsed_data.get('duration')
        internship.stipend = parsed_data.get('stipend')
        
        db.commit()
        db.refresh(internship)
        
        # Update embedding in vector DB
        rag_engine.store_internship_embedding(
            internship_id=str(internship.id),
            title=internship.title,
            description=internship.description,
            required_skills=internship.required_skills or [],
            metadata={
                "company_id": current_user.id,
                "location": internship.location,
                "duration": internship.duration
            }
        )
        
        return internship
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating internship: {str(e)}"
        )


@router.delete("/{internship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete/deactivate an internship posting
    """
    internship = db.query(Internship).filter(
        Internship.id == internship_id,
        Internship.company_id == current_user.id
    ).first()
    
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found"
        )
    
    # Soft delete - just deactivate
    internship.is_active = 0
    db.commit()
    
    # Delete from vector DB
    rag_engine.delete_internship_embedding(str(internship.id))
    
    return None
