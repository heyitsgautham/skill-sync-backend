"""
Resume Model - Student resume storage and metadata
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import uuid


class Resume(Base):
    """Resume database model with intelligent parsing support"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to uploaded file (local backup)
    s3_key = Column(String(500), nullable=True)  # S3 object key for cloud storage
    file_name = Column(String(255), nullable=False)
    parsed_content = Column(Text, nullable=True)  # Extracted text from resume
    
    # Intelligent parsing fields
    parsed_data = Column(JSON, nullable=True)  # Structured data from Gemini extraction
    extracted_skills = Column(JSON, nullable=True)  # List of skills extracted from resume
    
    # Vector embedding reference (stored in ChromaDB, not in PostgreSQL)
    # REMOVED: embedding column (redundant - ChromaDB is single source of truth)
    embedding_id = Column(String(255), nullable=True, index=True)  # Reference to ChromaDB embedding
    
    # Tailored resume support for hybrid matching
    is_tailored = Column(Integer, default=0)  # 1 if tailored for specific internship, 0 if base resume
    tailored_for_internship_id = Column(Integer, ForeignKey("internships.id"), nullable=True)  # Reference to internship if tailored
    base_resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)  # Reference to original base resume
    
    # Content hash for intelligent caching (detect content changes)
    content_hash = Column(String(64), nullable=True)  # SHA-256 hash of parsed_content
    
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User", backref="resumes", foreign_keys=[student_id])

    def __repr__(self):
        return f"<Resume {self.file_name} for Student#{self.student_id}>"
