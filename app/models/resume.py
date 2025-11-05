"""
Resume Model - Student resume storage and metadata
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, ARRAY, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base, DATABASE_URL
import uuid
import os


class Resume(Base):
    """Resume database model with intelligent parsing support"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to uploaded file
    file_name = Column(String(255), nullable=False)
    parsed_content = Column(Text, nullable=True)  # Extracted text from resume
    
    # Intelligent parsing fields
    parsed_data = Column(JSON, nullable=True)  # Structured data from Gemini extraction
    extracted_skills = Column(JSON, nullable=True)  # List of skills extracted from resume
    # Use JSON for SQLite compatibility, ARRAY for PostgreSQL
    embedding = Column(JSON if DATABASE_URL.startswith("sqlite") else ARRAY(Float), nullable=True)
    embedding_id = Column(String(255), nullable=True)  # Reference to vector DB embedding
    
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User", backref="resumes", foreign_keys=[student_id])

    def __repr__(self):
        return f"<Resume {self.file_name} for Student#{self.student_id}>"
