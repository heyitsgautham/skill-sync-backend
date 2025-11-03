"""
Resume Model - Student resume storage and metadata
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Resume(Base):
    """Resume database model"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to uploaded file
    file_name = Column(String(255), nullable=False)
    parsed_content = Column(Text, nullable=True)  # Extracted text from resume
    extracted_skills = Column(JSON, nullable=True)  # List of skills extracted from resume
    embedding_id = Column(String(255), nullable=True)  # Reference to vector DB embedding
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User", backref="resumes", foreign_keys=[student_id])

    def __repr__(self):
        return f"<Resume {self.file_name} for Student#{self.student_id}>"
