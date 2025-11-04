"""
Authentication Routes
Endpoints for user registration and login
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.database.connection import get_db
from app.services.auth_service import AuthService
from app.models.user import User, UserRole
from app.utils.security import get_current_user

router = APIRouter()

# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole
    
    class Config:
        use_enum_values = True

class LoginRequest(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Authentication token response model"""
    access_token: str
    token_type: str
    user: dict

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

class UserResponse(BaseModel):
    """User information response"""
    id: int
    email: str
    full_name: str
    role: str
    created_at: str
    
    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    """Analytics data response"""
    total_users: int
    total_students: int
    total_companies: int
    total_admins: int
    total_internships: int
    active_internships: int
    total_resumes: int

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **role**: User role (student, company, admin)
    """
    try:
        user = AuthService.register_user(
            db=db,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role
        )
        
        return MessageResponse(
            message=f"User registered successfully with email: {user.email}"
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and receive access token
    
    - **email**: Registered email address
    - **password**: User password
    
    Returns JWT access token for authenticated requests
    """
    try:
        auth_result = AuthService.authenticate_user(
            db=db,
            email=request.email,
            password=request.password
        )
        
        return TokenResponse(**auth_result)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all users (Admin only)
    
    Returns a list of all registered users in the system.
    Only accessible by admin users.
    """
    # Verify user is an admin
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access user list"
        )
    
    try:
        users = db.query(User).all()
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value if hasattr(user.role, 'value') else user.role,
                created_at=user.created_at.isoformat() if user.created_at else ""
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get system analytics (Admin only)
    
    Returns statistics about users, internships, and resumes in the system.
    Only accessible by admin users.
    """
    # Verify user is an admin
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access analytics"
        )
    
    try:
        from app.models.internship import Internship
        from app.models.resume import Resume
        
        # Count users by role
        total_users = db.query(User).count()
        total_students = db.query(User).filter(User.role == UserRole.student).count()
        total_companies = db.query(User).filter(User.role == UserRole.company).count()
        total_admins = db.query(User).filter(User.role == UserRole.admin).count()
        
        # Count internships
        total_internships = db.query(Internship).count()
        active_internships = db.query(Internship).filter(Internship.is_active == 1).count()
        
        # Count resumes
        total_resumes = db.query(Resume).filter(Resume.is_active == 1).count()
        
        return AnalyticsResponse(
            total_users=total_users,
            total_students=total_students,
            total_companies=total_companies,
            total_admins=total_admins,
            total_internships=total_internships,
            active_internships=active_internships,
            total_resumes=total_resumes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )
