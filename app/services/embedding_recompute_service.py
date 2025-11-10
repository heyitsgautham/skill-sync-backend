"""
Embedding Recompute Service
Handles recomputing embeddings for resumes and internships with intelligent caching
"""

import hashlib
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Resume, Internship, StudentInternshipMatch
from app.services.rag_engine import rag_engine
from app.services.resume_intelligence_service import ResumeIntelligenceService
from app.services.parser_service import ResumeParser


class EmbeddingRecomputeService:
    """Service for recomputing embeddings with caching"""
    
    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Compute SHA-256 hash of content for cache detection
        
        Args:
            content: Text content to hash
            
        Returns:
            Hex string of hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def should_recompute_resume(resume: Resume) -> bool:
        """
        Check if resume embedding should be recomputed
        
        Args:
            resume: Resume object
            
        Returns:
            True if should recompute, False if cached
        """
        # No parsed content = can't compute
        if not resume.parsed_content or resume.parsed_content.strip() == '':
            return False
        
        # No embedding_id = must compute
        if not resume.embedding_id:
            return True
        
        # Compute current hash
        current_hash = EmbeddingRecomputeService.compute_content_hash(resume.parsed_content)
        
        # No stored hash = first time, must compute
        if not resume.content_hash:
            return True
        
        # Hash changed = content updated, must recompute
        if current_hash != resume.content_hash:
            return True
        
        # Everything matches = use cache
        return False
    
    @staticmethod
    def should_recompute_internship(internship: Internship) -> bool:
        """
        Check if internship embedding should be recomputed
        
        Args:
            internship: Internship object
            
        Returns:
            True if should recompute, False if cached
        """
        # No description = can't compute
        if not internship.description:
            return False
        
        # Compute current hash
        content = f"{internship.title}\n{internship.description}"
        if internship.required_skills:
            content += f"\n{' '.join(internship.required_skills)}"
        
        current_hash = EmbeddingRecomputeService.compute_content_hash(content)
        
        # No stored hash = first time, must compute
        if not internship.content_hash:
            return True
        
        # Hash changed = content updated, must recompute
        if current_hash != internship.content_hash:
            return True
        
        # Everything matches = use cache
        return False
    
    @staticmethod
    def recompute_resume_embedding(resume: Resume, db: Session) -> Dict:
        """
        Recompute embedding for a single resume
        
        Args:
            resume: Resume object
            db: Database session
            
        Returns:
            Dict with status and details
        """
        try:
            # Check if we should recompute
            should_recompute = EmbeddingRecomputeService.should_recompute_resume(resume)
            
            if not should_recompute:
                return {
                    'success': True,
                    'cached': True,
                    'resume_id': resume.id,
                    'message': 'Using cached embedding'
                }
            
            # Recompute embedding
            # 1. Generate embedding
            extracted_skills = resume.extracted_skills or []
            if isinstance(extracted_skills, str):
                import json
                try:
                    extracted_skills = json.loads(extracted_skills)
                except:
                    extracted_skills = []
            
            # 2. Store embedding in ChromaDB and get embedding_id
            embedding_id = rag_engine.store_resume_embedding(
                resume_id=str(resume.id),
                content=resume.parsed_content,
                skills=extracted_skills,
                metadata={
                    "student_id": resume.student_id,
                    "file_name": resume.file_name,
                    "is_tailored": bool(resume.is_tailored)
                }
            )
            
            # 3. Update PostgreSQL with embedding_id and content hash
            resume.embedding_id = embedding_id
            resume.content_hash = EmbeddingRecomputeService.compute_content_hash(resume.parsed_content)
            
            db.commit()
            
            return {
                'success': True,
                'cached': False,
                'resume_id': resume.id,
                'message': 'Embedding recomputed successfully'
            }
            
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'cached': False,
                'resume_id': resume.id,
                'error': str(e)
            }
    
    @staticmethod
    def recompute_internship_embedding(internship: Internship, db: Session) -> Dict:
        """
        Recompute embedding for a single internship
        
        Args:
            internship: Internship object
            db: Database session
            
        Returns:
            Dict with status and details
        """
        try:
            # Check if we should recompute
            should_recompute = EmbeddingRecomputeService.should_recompute_internship(internship)
            
            if not should_recompute:
                return {
                    'success': True,
                    'cached': True,
                    'internship_id': internship.id,
                    'message': 'Using cached embedding'
                }
            
            # Recompute embedding
            # 1. Store in vector DB (which generates embedding)
            embedding_id = rag_engine.store_internship_embedding(
                internship_id=str(internship.id),
                title=internship.title,
                description=internship.description,
                required_skills=internship.required_skills or [],
                metadata={
                    "company_id": internship.company_id,
                    "location": internship.location
                }
            )
            
            # 2. Compute content hash
            content = f"{internship.title}\n{internship.description}"
            if internship.required_skills:
                content += f"\n{' '.join(internship.required_skills)}"
            
            internship.content_hash = EmbeddingRecomputeService.compute_content_hash(content)
            
            db.commit()
            
            return {
                'success': True,
                'cached': False,
                'internship_id': internship.id,
                'message': 'Embedding recomputed successfully'
            }
            
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'cached': False,
                'internship_id': internship.id,
                'error': str(e)
            }
    
    @staticmethod
    def recompute_all_embeddings(db: Session) -> Dict:
        """
        Recompute all embeddings for resumes and internships
        
        Args:
            db: Database session
            
        Returns:
            Dict with progress and results
        """
        results = {
            'resumes': {
                'total': 0,
                'cached': 0,
                'recomputed': 0,
                'failed': 0,
                'details': []
            },
            'internships': {
                'total': 0,
                'cached': 0,
                'recomputed': 0,
                'failed': 0,
                'details': []
            }
        }
        
        # Process all resumes (base + tailored)
        resumes = db.query(Resume).all()
        results['resumes']['total'] = len(resumes)
        
        for resume in resumes:
            result = EmbeddingRecomputeService.recompute_resume_embedding(resume, db)
            results['resumes']['details'].append(result)
            
            if result['success']:
                if result['cached']:
                    results['resumes']['cached'] += 1
                else:
                    results['resumes']['recomputed'] += 1
            else:
                results['resumes']['failed'] += 1
        
        # Process all active internships
        internships = db.query(Internship).filter(Internship.is_active == 1).all()
        results['internships']['total'] = len(internships)
        
        for internship in internships:
            result = EmbeddingRecomputeService.recompute_internship_embedding(internship, db)
            results['internships']['details'].append(result)
            
            if result['success']:
                if result['cached']:
                    results['internships']['cached'] += 1
                else:
                    results['internships']['recomputed'] += 1
            else:
                results['internships']['failed'] += 1
        
        return results
    
    @staticmethod
    def recalculate_all_matches(db: Session) -> Dict:
        """
        Recalculate student-internship matches after embeddings are updated
        
        Args:
            db: Database session
            
        Returns:
            Dict with results
        """
        from app.services.matching_engine import MatchingEngine
        
        results = {
            'total_matches': 0,
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        # Get all students with resumes
        students_with_resumes = db.query(Resume.student_id).filter(
            Resume.is_active == 1
        ).distinct().all()
        
        student_ids = [s[0] for s in students_with_resumes]
        
        # Get all active internships
        internships = db.query(Internship).filter(Internship.is_active == 1).all()
        
        # Clear existing matches
        db.query(StudentInternshipMatch).delete()
        db.commit()
        
        matching_engine = MatchingEngine(rag_engine)
        
        # Calculate matches for each student-internship pair
        for student_id in student_ids:
            # Get active resume (base resume)
            resume = db.query(Resume).filter(
                Resume.student_id == student_id,
                Resume.is_active == 1,
                Resume.is_tailored == 0
            ).first()
            
            if not resume:
                continue
            
            for internship in internships:
                try:
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
                    
                    # Get embeddings from ChromaDB
                    # Note: get_resume_embedding expects ID without "resume_" prefix
                    try:
                        resume_chroma_id = resume.embedding_id.replace('resume_', '') if resume.embedding_id else str(resume.id)
                        candidate_embedding = rag_engine.get_resume_embedding(resume_chroma_id)
                        if candidate_embedding is None:
                            candidate_embedding = []
                    except Exception as e:
                        candidate_embedding = []
                    
                    try:
                        internship_chroma_id = str(internship.id)  # Just use ID directly
                        internship_embedding = rag_engine.get_internship_embedding(internship_chroma_id)
                        if internship_embedding is None:
                            internship_embedding = []
                    except Exception as e:
                        internship_embedding = []
                    
                    # Calculate match
                    match_result = matching_engine.calculate_match_score(
                        candidate_data=candidate_data,
                        internship_data=internship_data,
                        candidate_embedding=candidate_embedding,
                        internship_embedding=internship_embedding
                    )
                    
                    # Store match
                    match_record = StudentInternshipMatch(
                        student_id=student_id,
                        internship_id=internship.id,
                        base_similarity_score=int(match_result['overall_score']),
                        semantic_similarity=match_result['component_scores'].get('semantic_similarity', 0),
                        skills_match_score=int(match_result['component_scores'].get('skills_match', 0)),
                        experience_match_score=int(match_result['component_scores'].get('experience_match', 0)),
                        resume_id=resume.id
                    )
                    
                    db.add(match_record)
                    results['total_matches'] += 1
                    results['successful'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['details'].append({
                        'student_id': student_id,
                        'internship_id': internship.id,
                        'error': str(e)
                    })
        
        db.commit()
        return results
