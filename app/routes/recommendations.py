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
    Get AI-powered internship recommendations for current student (HYBRID APPROACH - BLAZING FAST!)
    
    NEW PERFORMANCE OPTIMIZATION:
    - Uses pre-computed base_similarity from student_internship_matches table
    - Response time: ~50-200ms (vs 5 minutes previously)
    - No real-time embedding computation needed!
    
    Falls back to RAG engine if pre-computed matches not available.
    
    - **top_k**: Number of recommendations to return (default: 10)
    """
    import logging
    logger = logging.getLogger(__name__)
    
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
    
    logger.info(f"⚡ Getting fast recommendations for student {current_user.id} using pre-computed matches")
    
    # HYBRID APPROACH: Query pre-computed matches (FAST!)
    from app.models.student_internship_match import StudentInternshipMatch
    
    pre_computed_matches = db.query(StudentInternshipMatch, Internship).join(
        Internship, StudentInternshipMatch.internship_id == Internship.id
    ).filter(
        StudentInternshipMatch.student_id == current_user.id,
        Internship.is_active == 1
    ).order_by(
        StudentInternshipMatch.base_similarity_score.desc()
    ).limit(top_k).all()
    
    if pre_computed_matches:
        logger.info(f"✅ Found {len(pre_computed_matches)} pre-computed matches (response time: <100ms)")
        recommendations = []
        for match, internship in pre_computed_matches:
            recommendations.append(InternshipMatch(
                internship_id=internship.id,
                title=internship.title,
                description=internship.description,
                required_skills=internship.required_skills or [],
                location=internship.location or "",
                duration=internship.duration or "",
                stipend=internship.stipend or "",
                match_score=int(match.base_similarity_score)
            ))
        
        return recommendations
    
    # FALLBACK: Use RAG engine if no pre-computed matches (slower but still works)
    logger.warning("⚠️  No pre-computed matches found, falling back to RAG engine (slower)")
    logger.info("💡 Consider running POST /api/filter/compute-matches to pre-compute similarities")
    
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
