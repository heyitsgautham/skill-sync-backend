"""
Recommendations API Routes - AI-powered matching
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models import User, Resume, Internship, UserRole
from app.services.rag_engine import rag_engine
from app.services.s3_service import s3_service
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
    posted_date: Optional[str] = None
    experience_level: Optional[str] = None

class PaginatedInternshipResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[InternshipMatch]


class CandidateMatch(BaseModel):
    student_id: int
    student_name: str
    resume_id: int
    skills: List[str]
    match_score: int


@router.get("/for-me", response_model=PaginatedInternshipResponse)
def get_recommendations_for_student(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    # Filtering
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum match score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum match score"),
    skills: Optional[str] = Query(None, description="Comma-separated skills to filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    experience_level: Optional[str] = Query(None, description="Experience level filter"),
    days_posted: Optional[int] = Query(None, ge=1, description="Filter by days since posted"),
    # Sorting
    sort_by: Optional[str] = Query("score", description="Sort by: score, date, title"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered internship recommendations with advanced filtering and pagination
    
    PERFORMANCE OPTIMIZATION:
    - Uses pre-computed base_similarity from student_internship_matches table
    - Response time: ~50-200ms with filtering and pagination
    
    Filtering Options:
    - **min_score/max_score**: Filter by match score range (0-100)
    - **skills**: Filter by required skills (comma-separated)
    - **location**: Filter by location
    - **experience_level**: Filter by experience level
    - **days_posted**: Filter internships posted within N days
    
    Sorting Options:
    - **sort_by**: score (default), date, title
    - **sort_order**: desc (default), asc
    
    Pagination:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
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
    
    logger.info(f"⚡ Getting recommendations with filters for student {current_user.id}")
    
    # HYBRID APPROACH: Query pre-computed matches with filtering
    from app.models.student_internship_match import StudentInternshipMatch
    
    # Build base query
    query = db.query(StudentInternshipMatch, Internship).join(
        Internship, StudentInternshipMatch.internship_id == Internship.id
    ).filter(
        StudentInternshipMatch.student_id == current_user.id,
        Internship.is_active == 1
    )
    
    # Apply filters
    filters = []
    
    # Score range filter
    if min_score is not None:
        filters.append(StudentInternshipMatch.base_similarity_score >= min_score)
    if max_score is not None:
        filters.append(StudentInternshipMatch.base_similarity_score <= max_score)
    
    # Skills filter (check if any of the specified skills are in required_skills)
    if skills:
        skill_list = [s.strip() for s in skills.split(',')]
        skill_filters = [func.json_contains(Internship.required_skills, f'"{skill}"') for skill in skill_list]
        filters.append(or_(*skill_filters))
    
    # Location filter
    if location:
        filters.append(Internship.location.ilike(f'%{location}%'))
    
    # Experience level filter
    if experience_level:
        filters.append(Internship.experience_level == experience_level)
    
    # Days posted filter
    if days_posted:
        cutoff_date = datetime.utcnow() - timedelta(days=days_posted)
        filters.append(Internship.created_at >= cutoff_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply sorting
    if sort_by == "score":
        if sort_order == "asc":
            query = query.order_by(StudentInternshipMatch.base_similarity_score.asc())
        else:
            query = query.order_by(StudentInternshipMatch.base_similarity_score.desc())
    elif sort_by == "date":
        if sort_order == "asc":
            query = query.order_by(Internship.created_at.asc())
        else:
            query = query.order_by(Internship.created_at.desc())
    elif sort_by == "title":
        if sort_order == "asc":
            query = query.order_by(Internship.title.asc())
        else:
            query = query.order_by(Internship.title.desc())
    else:
        # Default: sort by score descending
        query = query.order_by(StudentInternshipMatch.base_similarity_score.desc())
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    results = query.all()
    
    logger.info(f"✅ Found {total} total matches, returning page {page} ({len(results)} items)")
    
    # Build response
    recommendations = []
    for match, internship in results:
        recommendations.append(InternshipMatch(
            internship_id=internship.id,
            title=internship.title,
            description=internship.description,
            required_skills=internship.required_skills or [],
            location=internship.location or "",
            duration=internship.duration or "",
            stipend=internship.stipend or "",
            match_score=int(match.base_similarity_score),
            posted_date=internship.created_at.isoformat() if internship.created_at else None,
            experience_level=internship.experience_level
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedInternshipResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=recommendations
    )


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


@router.get("/resume/{student_id}")
def get_candidate_resume_url(
    student_id: int,
    internship_id: Optional[int] = Query(None, description="Internship ID to verify access"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get URL to view candidate's resume (Company only) - with anonymization support
    
    - **student_id**: ID of the student/candidate
    - **internship_id**: Optional internship ID to verify company owns the internship
    - Returns URL with temporary token to view resume (anonymized if company has anonymization enabled)
    - Tracks resume views for analytics
    """
    import logging
    import jwt
    from datetime import datetime, timedelta
    
    logger = logging.getLogger(__name__)
    
    if current_user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can view candidate resumes"
        )
    
    # If internship_id provided, verify company owns it
    if internship_id:
        internship = db.query(Internship).filter(
            Internship.id == internship_id,
            Internship.company_id == current_user.id
        ).first()
        
        if not internship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this internship"
            )
    
    # Get student's active resume
    resume = db.query(Resume).filter(
        Resume.student_id == student_id,
        Resume.is_active == 1
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check if company has anonymization enabled
    anonymization_enabled = getattr(current_user, 'anonymization_enabled', False)
    
    # If anonymization is DISABLED, return direct S3 presigned URL
    if not anonymization_enabled:
        if s3_service.is_enabled() and resume.s3_key:
            logger.info(f"📄 Generating S3 presigned URL for resume: {resume.s3_key}")
            presigned_url = s3_service.generate_presigned_url(resume.s3_key, expiration=3600)
            
            if presigned_url:
                logger.info(f"📄 Company {current_user.id} viewing original resume {resume.id} from S3")
                return {
                    "resume_id": resume.id,
                    "file_name": resume.file_name,
                    "url": presigned_url,
                    "storage_type": "s3",
                    "anonymized": False,
                    "expires_in": 3600,
                    "message": "Direct S3 URL - expires in 1 hour"
                }
            else:
                logger.warning(f"⚠️ Failed to generate presigned URL for {resume.s3_key}")
        
        # Fallback to local file if S3 not available
        if not os.path.exists(resume.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file not found"
            )
        
        logger.info(f"📄 Company {current_user.id} viewing original resume {resume.id} (local file)")
        return {
            "resume_id": resume.id,
            "file_name": resume.file_name,
            "file_path": resume.file_path,
            "storage_type": "local",
            "anonymized": False,
            "message": "Resume stored locally. Use appropriate endpoint to download."
        }
    
    # If anonymization is ENABLED, generate temporary token and use API endpoint
    import os
    TEMP_TOKEN_SECRET = os.getenv("TEMP_TOKEN_SECRET", "your-secret-key-change-in-production")
    
    token_payload = {
        "resume_id": resume.id,
        "anonymize": True,
        "company_id": current_user.id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    temp_token = jwt.encode(token_payload, TEMP_TOKEN_SECRET, algorithm="HS256")
    
    # Return URL to our anonymization-aware endpoint with temporary token
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    resume_view_url = f"{base_url}/api/resumes/{resume.id}/view?token={temp_token}"
    
    logger.info(f"🔒 Company {current_user.id} viewing anonymized resume {resume.id}")
    
    return {
        "resume_id": resume.id,
        "file_name": resume.file_name,
        "url": resume_view_url,
        "storage_type": "api",
        "anonymized": True,
        "message": "Resume will be anonymized (names/emails/phone redacted)"
    }
