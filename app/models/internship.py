"""
Internship Model - Internship postings by companies
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import uuid


class Internship(Base):
    """Internship database model with intelligent matching support"""
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    company_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Matching criteria fields
    required_skills = Column(JSON, nullable=True)  # List of required skills
    preferred_skills = Column(JSON, nullable=True)  # List of preferred skills (nice-to-have)
    min_experience = Column(Float, nullable=True, default=0)  # Minimum years of experience
    max_experience = Column(Float, nullable=True, default=10)  # Maximum years of experience
    required_education = Column(String(255), nullable=True)  # e.g., "Bachelor's in CS"
    
    location = Column(String(255), nullable=True)
    duration = Column(String(100), nullable=True)  # e.g., "3 months", "6 months"
    stipend = Column(String(100), nullable=True)
    
    # Content hash for intelligent caching (detect content changes)
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash of description
    
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("User", backref="internships", foreign_keys=[company_id])
    applications = relationship("Application", back_populates="internship", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Internship {self.title} by Company#{self.company_id}>"
