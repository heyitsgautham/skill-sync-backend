"""
Internship API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models import User, Internship, UserRole, Resume, Application, StudentInternshipMatch
from app.services.parser_service import InternshipParser
from app.services.rag_engine import rag_engine
from app.services.matching_engine import MatchingEngine
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
    
    # Add company name and internship_id to each internship
    result = []
    for internship in internships:
        internship_dict = {
            "id": internship.id,
            "internship_id": internship.internship_id,  # Include UUID for intelligent filtering
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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Match internships called by user_id={current_user.id}, role={current_user.role}, top_k={top_k}")
    
    # Only students can get recommendations
    if current_user.role != UserRole.student:
        logger.warning(f"Non-student user {current_user.id} tried to access recommendations")
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
        logger.warning(f"Student {current_user.id} has no active resume")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active resume found. Please upload a resume first to get personalized recommendations."
        )
    
    logger.info(f"Found active resume {resume.id} for student {current_user.id}")
    logger.info(f"Resume details - ID: {resume.id}, file_name: {resume.file_name}, is_active: {resume.is_active}, embedding_id: {resume.embedding_id}")
    
    try:
        # Get matching internships from RAG engine
        resume_id_str = str(resume.id)
        logger.info(f"Calling RAG engine to find matches for resume_id: {resume_id_str} (type: {type(resume_id_str)})")
        matches = rag_engine.find_matching_internships(
            resume_id=resume_id_str,
            top_k=top_k
        )
        
        logger.info(f"RAG engine returned {len(matches) if matches else 0} matches")
        
        if not matches:
            logger.info("No matches found, returning empty list")
            return []
        
        # Fetch full internship details
        internship_ids = [int(m['internship_id']) for m in matches]
        logger.info(f"Fetching details for internship IDs: {internship_ids}")
        
        internships = db.query(Internship).filter(
            Internship.id.in_(internship_ids),
            Internship.is_active == 1
        ).all()
        
        logger.info(f"Found {len(internships)} active internships in database")
        
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
            else:
                logger.warning(f"Internship {match['internship_id']} not found in database")
        
        logger.info(f"Returning {len(recommendations)} recommendations")
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


# Application Management Endpoints
class ApplicationCreate(BaseModel):
    cover_letter: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    student_id: int
    internship_id: int
    resume_id: int
    status: str
    match_score: Optional[int] = None
    application_similarity_score: Optional[int] = None
    used_tailored_resume: int
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/{internship_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_internship(
    internship_id: int,
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Apply to an internship (Student only) - Hybrid Matching Strategy
    
    This endpoint implements the hybrid matching approach:
    1. If student has an active resume, uses it for application
    2. Calculates application_similarity_score using matching engine
    3. Falls back to pre-computed base_similarity if available
    4. Creates application record with hybrid scoring
    
    - **internship_id**: ID of the internship to apply to
    - **cover_letter**: Optional cover letter text
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Only students can apply
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can apply to internships"
        )
    
    # Check if internship exists and is active
    internship = db.query(Internship).filter(
        Internship.id == internship_id,
        Internship.is_active == 1
    ).first()
    
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found or no longer active"
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
    
    # Check if already applied
    existing_application = db.query(Application).filter(
        Application.student_id == current_user.id,
        Application.internship_id == internship_id
    ).first()
    
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied to this internship"
        )
    
    try:
        logger.info(f"Processing application for student {current_user.id} to internship {internship_id}")
        
        # Calculate application-specific similarity score
        matching_engine = MatchingEngine(rag_engine)
        
        # Prepare candidate data from resume
        candidate_data = {
            'all_skills': resume.parsed_data.get('all_skills', []) if resume.parsed_data else [],
            'total_experience_years': resume.parsed_data.get('total_experience_years', 0) if resume.parsed_data else 0,
            'education': resume.parsed_data.get('education', []) if resume.parsed_data else [],
            'projects': resume.parsed_data.get('projects', []) if resume.parsed_data else [],
            'certifications': resume.parsed_data.get('certifications', []) if resume.parsed_data else []
        }
        
        # Prepare internship data
        internship_data = {
            'required_skills': internship.required_skills or [],
            'preferred_skills': internship.preferred_skills or [],
            'min_experience': internship.min_experience or 0,
            'max_experience': internship.max_experience or 10,
            'required_education': internship.required_education or ''
        }
        
        # Get embeddings
        candidate_embedding = resume.embedding or []
        try:
            internship_embedding = rag_engine.get_internship_embedding(str(internship.id))
        except:
            internship_embedding = []
        
        # Calculate match score
        match_result = matching_engine.calculate_match_score(
            candidate_data=candidate_data,
            internship_data=internship_data,
            candidate_embedding=candidate_embedding,
            internship_embedding=internship_embedding
        )
        
        application_similarity = int(match_result['overall_score'])
        logger.info(f"Calculated application similarity: {application_similarity}%")
        
        # Try to get pre-computed base similarity as fallback/comparison
        base_match = db.query(StudentInternshipMatch).filter(
            StudentInternshipMatch.student_id == current_user.id,
            StudentInternshipMatch.internship_id == internship_id
        ).first()
        
        # Use application similarity as primary, base as fallback
        final_match_score = application_similarity
        if base_match and application_similarity == 0:
            final_match_score = int(base_match.base_similarity_score)
            logger.info(f"Using pre-computed base similarity: {final_match_score}%")
        
        # Create application
        new_application = Application(
            student_id=current_user.id,
            internship_id=internship_id,
            resume_id=resume.id,
            cover_letter=application_data.cover_letter,
            match_score=final_match_score,
            application_similarity_score=application_similarity,
            used_tailored_resume=0  # Can be updated later if we support tailored resumes
        )
        
        db.add(new_application)
        db.commit()
        db.refresh(new_application)
        
        logger.info(f"✅ Application created successfully: ID {new_application.id}")
        
        return ApplicationResponse(
            id=new_application.id,
            student_id=new_application.student_id,
            internship_id=new_application.internship_id,
            resume_id=new_application.resume_id,
            status=new_application.status,
            match_score=new_application.match_score,
            application_similarity_score=new_application.application_similarity_score,
            used_tailored_resume=new_application.used_tailored_resume,
            created_at=str(new_application.created_at)
        )
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Error creating application: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating application: {str(e)}"
        )


@router.get("/applications/my-applications", response_model=List[ApplicationResponse])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all applications for the current student
    """
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their applications"
        )
    
    applications = db.query(Application).filter(
        Application.student_id == current_user.id
    ).order_by(Application.created_at.desc()).all()
    
    return [
        ApplicationResponse(
            id=app.id,
            student_id=app.student_id,
            internship_id=app.internship_id,
            resume_id=app.resume_id,
            status=app.status,
            match_score=app.match_score,
            application_similarity_score=app.application_similarity_score,
            used_tailored_resume=app.used_tailored_resume,
            created_at=str(app.created_at)
        )
        for app in applications
    ]
