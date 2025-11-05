"""
User Model - Base user model for all user types (Student, Company, Admin)
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, JSON, Float
from sqlalchemy.sql import func
from app.database.connection import Base
import enum
import uuid

class UserRole(str, enum.Enum):
    """User role enumeration"""
    student = "student"
    company = "company"
    admin = "admin"

class User(Base):
    """User database model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    
    # Student-specific fields (populated from resume parsing)
    skills = Column(JSON, nullable=True)  # List of extracted skills
    total_experience_years = Column(Float, nullable=True, default=0)  # Calculated experience
    
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
