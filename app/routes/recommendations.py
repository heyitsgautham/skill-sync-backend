"""
Recommendations API Routes - AI-powered matching
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models import User, Resume, Internship, UserRole
from app.services.rag_engine import rag_engine
from app.utils.security import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# Pydantic schemas
class InternshipMatch(BaseModel):
    internship_id: int
    title: str
    description: str
    required_skills: List[str]
    location: str
    duration: str
    stipend: str
    match_score: int


class CandidateMatch(BaseModel):
    student_id: int
    student_name: str
    resume_id: int
    skills: List[str]
    match_score: int


@router.get("/for-me", response_model=List[InternshipMatch])
def get_recommendations_for_student(
    top_k: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered internship recommendations for current student
    
    - **top_k**: Number of recommendations to return (default: 10)
    - Uses RAG engine to find best matching internships based on resume
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can get recommendations"
        )
    
    # Get student's active resume
    resume = db.query(Resume).filter(
        Resume.student_id == current_user.id,
        Resume.is_active == 1
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active resume found. Please upload a resume first."
        )
    
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
            recommendations.append(InternshipMatch(
                internship_id=internship.id,
                title=internship.title,
                description=internship.description,
                required_skills=internship.required_skills or [],
                location=internship.location or "",
                duration=internship.duration or "",
                stipend=internship.stipend or "",
                match_score=match['match_score']
            ))
    
    return recommendations


@router.get("/candidates/{internship_id}", response_model=List[CandidateMatch])
def get_recommended_candidates(
    internship_id: int,
    top_k: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered candidate recommendations for an internship (Company only)
    
    - **internship_id**: ID of the internship
    - **top_k**: Number of candidates to return (default: 20)
    - Uses RAG engine to find best matching candidates
    """
    if current_user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can view candidate recommendations"
        )
    
    # Verify internship belongs to current company
    internship = db.query(Internship).filter(
        Internship.id == internship_id,
        Internship.company_id == current_user.id
    ).first()
    
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found"
        )
    
    # Get matching candidates from RAG engine
    matches = rag_engine.find_matching_candidates(
        internship_id=str(internship_id),
        top_k=top_k
    )
    
    if not matches:
        return []
    
    # Fetch full resume and student details
    resume_ids = [int(m['resume_id']) for m in matches]
    resumes = db.query(Resume, User).join(
        User, Resume.student_id == User.id
    ).filter(
        Resume.id.in_(resume_ids),
        Resume.is_active == 1
    ).all()
    
    # Create mapping of resume_id to (resume, user)
    resume_map = {str(r.id): (r, u) for r, u in resumes}
    
    # Combine data with match scores
    recommendations = []
    for match in matches:
        data = resume_map.get(match['resume_id'])
        if data:
            resume, student = data
            recommendations.append(CandidateMatch(
                student_id=student.id,
                student_name=student.full_name,
                resume_id=resume.id,
                skills=match.get('skills', []),
                match_score=match['match_score']
            ))
    
    return recommendations
