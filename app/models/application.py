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
    """Application database model"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    status = Column(String(50), default=ApplicationStatus.pending.value)
    cover_letter = Column(Text, nullable=True)
    match_score = Column(Integer, nullable=True)  # AI matching score (0-100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User", backref="applications", foreign_keys=[student_id])
    internship = relationship("Internship", back_populates="applications")
    resume = relationship("Resume", backref="applications", foreign_keys=[resume_id])

    def __repr__(self):
        return f"<Application Student#{self.student_id} -> Internship#{self.internship_id} ({self.status})>"
