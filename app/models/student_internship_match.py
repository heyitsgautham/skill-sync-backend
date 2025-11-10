"""
Student-Internship Match Model - Pre-computed similarity scores
Part of the Hybrid Matching Strategy for performance optimization
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class StudentInternshipMatch(Base):
    """
    Pre-computed base similarity scores between students and internships.
    
    This model implements the "Strategy A: Pre-computed Base Similarity" 
    from the hybrid approach:
    - Batch computation of similarity between ALL students and ALL internships
    - Used for discovery phase (recommendations, candidate suggestions)
    - Enables fast queries without real-time embedding computation
    - Updated periodically or on-demand when new resumes/internships are added
    """
    __tablename__ = "student_internship_matches"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    
    # Base similarity score (0-100) computed from embeddings
    base_similarity_score = Column(Float, nullable=False)
    
    # Component scores for transparency
    semantic_similarity = Column(Float, nullable=True)  # Embedding-based similarity
    skills_match_score = Column(Float, nullable=True)   # Skills overlap score
    experience_match_score = Column(Float, nullable=True)  # Experience alignment
    
    # Metadata
    last_computed = Column(DateTime(timezone=True), server_default=func.now())
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)  # Which resume was used
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    internship = relationship("Internship", foreign_keys=[internship_id])
    resume = relationship("Resume", foreign_keys=[resume_id])

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_student_match_score', 'student_id', 'base_similarity_score'),
        Index('idx_internship_match_score', 'internship_id', 'base_similarity_score'),
        Index('idx_unique_student_internship', 'student_id', 'internship_id', unique=True),
    )

    def __repr__(self):
        return f"<Match Student#{self.student_id} -> Internship#{self.internship_id} ({self.base_similarity_score:.1f}%)>"
