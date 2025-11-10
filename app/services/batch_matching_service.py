"""
Batch Matching Service - Pre-compute similarity scores for all student-internship pairs
Part of the Hybrid Matching Strategy for performance optimization

This service implements "Strategy A: Pre-computed Base Similarity"
- Runs as a batch job (nightly, on-demand, or after bulk uploads)
- Calculates similarity between ALL students and ALL open internships
- Stores results in student_internship_matches table
- Enables millisecond-fast recommendations and candidate discovery
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete
from datetime import datetime

from app.models.user import User, UserRole
from app.models.resume import Resume
from app.models.internship import Internship
from app.models.student_internship_match import StudentInternshipMatch
from app.services.matching_engine import MatchingEngine
from app.services.rag_engine import rag_engine

logger = logging.getLogger(__name__)


class BatchMatchingService:
    """
    Service for batch computation of base similarity scores.
    
    Usage:
        service = BatchMatchingService(db_session)
        result = service.compute_all_matches()
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.matching_engine = MatchingEngine(rag_engine)
    
    def compute_all_matches(
        self, 
        force_recompute: bool = False,
        student_ids: Optional[List[int]] = None,
        internship_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        Compute base similarity scores for all student-internship pairs.
        
        Args:
            force_recompute: If True, delete existing matches and recompute all
            student_ids: Optional list of specific student IDs to compute (None = all)
            internship_ids: Optional list of specific internship IDs to compute (None = all)
        
        Returns:
            Dictionary with computation statistics
        """
        logger.info("🚀 Starting batch similarity computation...")
        start_time = datetime.now()
        
        # Step 1: Get all students with active resumes
        students_query = self.db.query(User, Resume).join(
            Resume, Resume.student_id == User.id
        ).filter(
            User.role == UserRole.student,
            Resume.is_active == 1
        )
        
        if student_ids:
            students_query = students_query.filter(User.id.in_(student_ids))
        
        students_with_resumes = students_query.all()
        logger.info(f"📊 Found {len(students_with_resumes)} students with active resumes")
        
        # Step 2: Get all active internships
        internships_query = self.db.query(Internship).filter(
            Internship.is_active == 1
        )
        
        if internship_ids:
            internships_query = internships_query.filter(Internship.id.in_(internship_ids))
        
        internships = internships_query.all()
        logger.info(f"📊 Found {len(internships)} active internships")
        
        if not students_with_resumes or not internships:
            logger.warning("⚠️  No students or internships to process")
            return {
                "success": True,
                "students_processed": 0,
                "internships_processed": 0,
                "matches_computed": 0,
                "duration_seconds": 0
            }
        
        # Step 3: Delete existing matches if force_recompute
        if force_recompute:
            delete_query = delete(StudentInternshipMatch)
            if student_ids:
                delete_query = delete_query.where(StudentInternshipMatch.student_id.in_(student_ids))
            if internship_ids:
                delete_query = delete_query.where(StudentInternshipMatch.internship_id.in_(internship_ids))
            
            deleted = self.db.execute(delete_query)
            self.db.commit()
            logger.info(f"🗑️  Deleted {deleted.rowcount} existing matches")
        
        # Step 4: Compute matches for all pairs
        matches_computed = 0
        matches_failed = 0
        
        for student, resume in students_with_resumes:
            student_matches = []
            
            for internship in internships:
                try:
                    # Calculate match score using matching engine
                    match_result = self._calculate_match(
                        student=student,
                        resume=resume,
                        internship=internship
                    )
                    
                    if match_result:
                        student_matches.append(match_result)
                        matches_computed += 1
                    
                except Exception as e:
                    logger.error(f"  Error computing match for student {student.id} and internship {internship.id}: {str(e)}")
                    matches_failed += 1
                    continue
            
            # Batch insert matches for this student
            if student_matches:
                self.db.bulk_insert_mappings(StudentInternshipMatch, student_matches)
                self.db.commit()
                logger.info(f"✅ Computed {len(student_matches)} matches for student {student.id} ({student.full_name})")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            "success": True,
            "students_processed": len(students_with_resumes),
            "internships_processed": len(internships),
            "matches_computed": matches_computed,
            "matches_failed": matches_failed,
            "duration_seconds": duration,
            "avg_time_per_match": duration / matches_computed if matches_computed > 0 else 0
        }
        
        logger.info(f"🎉 Batch computation complete!")
        logger.info(f"   Students: {result['students_processed']}")
        logger.info(f"   Internships: {result['internships_processed']}")
        logger.info(f"   Matches computed: {result['matches_computed']}")
        logger.info(f"   Failed: {result['matches_failed']}")
        logger.info(f"   Duration: {result['duration_seconds']:.2f}s")
        logger.info(f"   Avg time per match: {result['avg_time_per_match']:.3f}s")
        
        return result
    
    def _calculate_match(
        self, 
        student: User, 
        resume: Resume, 
        internship: Internship
    ) -> Optional[Dict]:
        """
        Calculate similarity score between a student and an internship.
        
        Returns dictionary with match data for bulk insert, or None on failure.
        """
        # Prepare candidate data
        candidate_data = {
            'all_skills': resume.parsed_data.get('all_skills', []) if resume.parsed_data else [],
            'total_experience_years': resume.parsed_data.get('total_experience_years', 0) if resume.parsed_data else 0,
            'education': resume.parsed_data.get('education', []) if resume.parsed_data else [],
            'projects': resume.parsed_data.get('projects', []) if resume.parsed_data else [],
            'certifications': resume.parsed_data.get('certifications', []) if resume.parsed_data else []
        }
        
        # Prepare internship data
        internship_data = {
            'required_skills': internship.required_skills or [],
            'preferred_skills': internship.preferred_skills or [],
            'min_experience': internship.min_experience or 0,
            'max_experience': internship.max_experience or 10,
            'required_education': internship.required_education or ''
        }
        
        # Get embeddings from ChromaDB (fallback to empty if not available)
        # Note: get_resume_embedding expects ID without "resume_" prefix
        try:
            resume_chroma_id = resume.embedding_id.replace('resume_', '') if resume.embedding_id else str(resume.id)
            candidate_embedding = rag_engine.get_resume_embedding(resume_chroma_id)
            if candidate_embedding is None:
                candidate_embedding = []
        except Exception as e:
            candidate_embedding = []
        
        # Get internship embedding from RAG engine
        try:
            internship_chroma_id = str(internship.id)
            internship_embedding = rag_engine.get_internship_embedding(internship_chroma_id)
            if internship_embedding is None:
                internship_embedding = []
        except Exception as e:
            internship_embedding = []
        
        # Calculate match score
        match_result = self.matching_engine.calculate_match_score(
            candidate_data=candidate_data,
            internship_data=internship_data,
            candidate_embedding=candidate_embedding,
            internship_embedding=internship_embedding
        )
        
        # Prepare data for insertion
        return {
            'student_id': student.id,
            'internship_id': internship.id,
            'resume_id': resume.id,
            'base_similarity_score': match_result['overall_score'],
            'semantic_similarity': match_result['component_scores'].get('semantic_similarity'),
            'skills_match_score': match_result['component_scores'].get('skills_match'),
            'experience_match_score': match_result['component_scores'].get('experience_match'),
            'last_computed': datetime.now()
        }
    
    def compute_matches_for_student(self, student_id: int) -> Dict:
        """
        Compute matches for a specific student (useful after resume upload).
        
        Args:
            student_id: ID of the student to compute matches for
        
        Returns:
            Dictionary with computation statistics
        """
        logger.info(f"Computing matches for student {student_id}...")
        return self.compute_all_matches(
            force_recompute=True,
            student_ids=[student_id]
        )
    
    def compute_matches_for_internship(self, internship_id: int) -> Dict:
        """
        Compute matches for a specific internship (useful after internship posting).
        
        Args:
            internship_id: ID of the internship to compute matches for
        
        Returns:
            Dictionary with computation statistics
        """
        logger.info(f"Computing matches for internship {internship_id}...")
        return self.compute_all_matches(
            force_recompute=True,
            internship_ids=[internship_id]
        )
