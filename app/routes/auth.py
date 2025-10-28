"""
Authentication Routes
Endpoints for user registration and login
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.database.connection import get_db
from app.services.auth_service import AuthService
from app.models.user import UserRole

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
