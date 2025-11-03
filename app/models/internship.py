"""
Internship Model - Internship postings by companies
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Internship(Base):
    """Internship database model"""
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)  # List of required skills
    location = Column(String(255), nullable=True)
    duration = Column(String(100), nullable=True)  # e.g., "3 months", "6 months"
    stipend = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("User", backref="internships", foreign_keys=[company_id])
    applications = relationship("Application", back_populates="internship", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Internship {self.title} by Company#{self.company_id}>"
