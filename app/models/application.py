"""
Application Model - Student applications to internships
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


class ApplicationStatus(str, enum.Enum):
    """Application status enumeration"""
    pending = "pending"
    shortlisted = "shortlisted"
    rejected = "rejected"
    accepted = "accepted"


class Application(Base):
    """
    Application database model with hybrid matching support.
    
    Supports both:
    - Pre-computed base similarity (from student_internship_matches)
    - Application-specific similarity (calculated at application time with tailored resume)
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    status = Column(String(50), default=ApplicationStatus.pending.value)
    cover_letter = Column(Text, nullable=True)
    
    # Hybrid matching scores (Strategy B: Application-Specific Similarity)
    match_score = Column(Integer, nullable=True)  # Legacy/overall AI matching score (0-100)
    application_similarity_score = Column(Integer, nullable=True)  # NEW: Score with tailored resume
    used_tailored_resume = Column(Integer, default=0)  # 1 if tailored resume used, 0 if not
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User", backref="applications", foreign_keys=[student_id])
    internship = relationship("Internship", back_populates="applications")
    resume = relationship("Resume", backref="applications", foreign_keys=[resume_id])

    def __repr__(self):
        return f"<Application Student#{self.student_id} -> Internship#{self.internship_id} ({self.status})>"
