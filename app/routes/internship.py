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
    company_name: Optional[str] = None
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
    
    # Add company name to each internship
    result = []
    for internship in internships:
        internship_dict = {
            "id": internship.id,
            "company_id": internship.company_id,
            "company_name": internship.company.full_name if internship.company else "Unknown Company",
            "title": internship.title,
            "description": internship.description,
            "required_skills": internship.required_skills,
            "location": internship.location,
            "duration": internship.duration,
            "stipend": internship.stipend,
            "is_active": internship.is_active
        }
        result.append(internship_dict)
    
    return result


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
    
    # Add company name to each internship
    result = []
    for internship in internships:
        internship_dict = {
            "id": internship.id,
            "company_id": internship.company_id,
            "company_name": current_user.full_name,
            "title": internship.title,
            "description": internship.description,
            "required_skills": internship.required_skills,
            "location": internship.location,
            "duration": internship.duration,
            "stipend": internship.stipend,
            "is_active": internship.is_active
        }
        result.append(internship_dict)
    
    return result


@router.get("/match", response_model=List[InternshipWithMatchScore])
def match_internships(
    top_k: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered internship recommendations based on student's resume
    
    - **top_k**: Number of recommendations to return (default: 10, max: 50)
    - Uses RAG engine to find best matching internships based on resume embeddings
    - Requires student to have an active resume uploaded
    """
    # Only students can get recommendations
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can get internship recommendations"
        )
    
    # Validate top_k parameter
    if top_k < 1 or top_k > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="top_k must be between 1 and 50"
        )
    
    # Get student's active resume
    from app.models import Resume
    resume = db.query(Resume).filter(
        Resume.student_id == current_user.id,
        Resume.is_active == 1
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active resume found. Please upload a resume first to get personalized recommendations."
        )
    
    try:
        # Get matching internships from RAG engine
        matches = rag_engine.find_matching_internships(
            resume_id=str(resume.id),
            top_k=top_k
        )
        
        if not matches:
            return []
        
        # Fetch full internship details
        internship_ids = [int(m['internship_id']) for m in matches]
        internships = db.query(Internship).filter(
            Internship.id.in_(internship_ids),
            Internship.is_active == 1
        ).all()
        
        # Create mapping of internship_id to internship
        internship_map = {str(i.id): i for i in internships}
        
        # Combine data with match scores
        recommendations = []
        for match in matches:
            internship = internship_map.get(match['internship_id'])
            if internship:
                # Convert to dict and add match_score
                internship_dict = {
                    "id": internship.id,
                    "company_id": internship.company_id,
                    "company_name": internship.company.full_name if internship.company else "Unknown Company",
                    "title": internship.title,
                    "description": internship.description,
                    "required_skills": internship.required_skills or [],
                    "location": internship.location or "",
                    "duration": internship.duration or "",
                    "stipend": internship.stipend or "",
                    "is_active": internship.is_active,
                    "match_score": match['match_score']
                }
                recommendations.append(InternshipWithMatchScore(**internship_dict))
        
        return recommendations
        
    except Exception as e:
        import traceback
        print(f"Error in match_internships: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


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
    
    # Return internship with company name
    internship_dict = {
        "id": internship.id,
        "company_id": internship.company_id,
        "company_name": internship.company.full_name if internship.company else "Unknown Company",
        "title": internship.title,
        "description": internship.description,
        "required_skills": internship.required_skills,
        "location": internship.location,
        "duration": internship.duration,
        "stipend": internship.stipend,
        "is_active": internship.is_active
    }
    
    return internship_dict


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
