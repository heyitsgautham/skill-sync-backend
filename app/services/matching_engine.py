"""
Matching Engine - Core system for matching candidates to internships
Combines semantic matching (embeddings) with rule-based scoring
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

from app.utils.gemini_key_manager import get_gemini_key_manager

load_dotenv()

logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    Intelligent matching engine that combines:
    1. Semantic similarity (HuggingFace embeddings)
    2. Rule-based scoring (skills, experience, education)
    3. Explainable ranking with reasons
    """
    
    def __init__(self, rag_engine):
        """
        Initialize matching engine
        
        Args:
            rag_engine: RAGEngine instance for embedding generation
        """
        self.rag_engine = rag_engine
        
        # Initialize Gemini key manager for explanations
        self.key_manager = get_gemini_key_manager()
        logger.info("✅ MatchingEngine initialized with GeminiKeyManager")
        
        # Scoring weights - Rebalanced to prioritize actual qualifications over semantic similarity
        self.weights = {
            'skills_match': 0.45,             # 45% - Specific skills required (increased from 30%)
            'experience_match': 0.25,         # 25% - Years of experience (increased from 20%)
            'semantic_similarity': 0.10,      # 10% - Overall resume-JD match (reduced from 35%)
            'education_match': 0.10,          # 10% - Education level (same)
            'projects_certifications': 0.10   # 10% - Additional credentials (increased from 5%)
        }
    
    def calculate_match_score(
        self,
        candidate_data: Dict,
        internship_data: Dict,
        candidate_embedding: List[float],
        internship_embedding: List[float]
    ) -> Dict:
        """
        Calculate comprehensive match score between candidate and internship
        
        Args:
            candidate_data: Structured candidate profile
            internship_data: Internship posting details
            candidate_embedding: Candidate resume embedding vector
            internship_embedding: Internship JD embedding vector
            
        Returns:
            Dictionary with overall score, component scores, and match details
        """
        scores = {}
        
        # 1. Semantic Similarity (using embeddings)
        scores['semantic_similarity'] = self._calculate_cosine_similarity(
            candidate_embedding,
            internship_embedding
        ) * 100  # Convert to percentage
        
        # 2. Skills Match
        scores['skills_match'] = self._calculate_skills_match(
            candidate_data.get('all_skills', []),
            internship_data.get('required_skills', []),
            internship_data.get('preferred_skills', [])
        )
        
        # 3. Experience Match
        scores['experience_match'] = self._calculate_experience_match(
            candidate_data.get('total_experience_years', 0),
            internship_data.get('min_experience', 0),
            internship_data.get('max_experience', 10)
        )
        
        # 4. Education Match
        scores['education_match'] = self._calculate_education_match(
            candidate_data.get('education', []),
            internship_data.get('required_education', '')
        )
        
        # 5. Projects & Certifications
        scores['projects_certifications'] = self._calculate_additional_credentials(
            candidate_data.get('projects', []),
            candidate_data.get('certifications', [])
        )
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[key] * self.weights[key]
            for key in self.weights.keys()
        )
        
        # Prepare detailed match result
        match_result = {
            'overall_score': round(overall_score, 2),
            'component_scores': {k: round(v, 2) for k, v in scores.items()},
            'weights': self.weights,
            'match_details': {
                'matched_skills': self._get_matched_skills(
                    candidate_data.get('all_skills', []),
                    internship_data.get('required_skills', []) + 
                    internship_data.get('preferred_skills', [])
                ),
                'missing_skills': self._get_missing_skills(
                    candidate_data.get('all_skills', []),
                    internship_data.get('required_skills', [])
                ),
                'experience_gap': self._get_experience_gap(
                    candidate_data.get('total_experience_years', 0),
                    internship_data.get('min_experience', 0)
                )
            }
        }
        
        return match_result
    
    def _calculate_cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""
        # DO NOT USE FALLBACK SCORES - Log error and raise exception instead
        if vec1 is None or vec2 is None or len(vec1) == 0 or len(vec2) == 0:
            error_msg = "  CRITICAL: Missing embeddings detected! Cannot calculate similarity."
            logger.error(error_msg)
            logger.error(f"   vec1 present: {vec1 is not None and len(vec1) > 0}")
            logger.error(f"   vec2 present: {vec2 is not None and len(vec2) > 0}")
            raise ValueError("Cannot calculate similarity: embeddings are missing or empty")
        
        logger.debug(f"✅ Calculating cosine similarity (vec1: {len(vec1)}D, vec2: {len(vec2)}D)")
        
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            logger.error("  Zero vector detected - cannot calculate similarity")
            raise ValueError("Cannot calculate similarity: zero vector detected")
        
        similarity = float(dot_product / (norm1 * norm2))
        logger.debug(f"   Calculated similarity: {similarity:.4f}")
        return similarity
    
    def _calculate_skills_match(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str] = []
    ) -> float:
        """
        Calculate skills match score
        
        Returns:
            Score from 0-100
        """
        if not required_skills:
            return 100.0
        
        # Normalize skills for comparison (lowercase, trim)
        candidate_skills_normalized = [s.lower().strip() for s in candidate_skills]
        required_skills_normalized = [s.lower().strip() for s in required_skills]
        preferred_skills_normalized = [s.lower().strip() for s in preferred_skills]
        
        # Count matched required skills
        matched_required = sum(
            1 for skill in required_skills_normalized
            if any(skill in cand_skill or cand_skill in skill 
                   for cand_skill in candidate_skills_normalized)
        )
        
        # Required skills score (70% weight)
        required_score = (matched_required / len(required_skills_normalized)) * 70
        
        # Count matched preferred skills
        preferred_score = 0
        if preferred_skills_normalized:
            matched_preferred = sum(
                1 for skill in preferred_skills_normalized
                if any(skill in cand_skill or cand_skill in skill 
                       for cand_skill in candidate_skills_normalized)
            )
            preferred_score = (matched_preferred / len(preferred_skills_normalized)) * 30
        else:
            preferred_score = 30  # Full points if no preferred skills specified
        
        return required_score + preferred_score
    
    def _calculate_experience_match(
        self,
        candidate_exp: float,
        min_exp: float,
        max_exp: float
    ) -> float:
        """
        Calculate experience match score
        
        Returns:
            Score from 0-100
        """
        if candidate_exp >= min_exp and candidate_exp <= max_exp:
            return 100.0
        elif candidate_exp < min_exp:
            # Below minimum - penalize based on gap
            gap = min_exp - candidate_exp
            if gap <= 0.5:
                return 90.0
            elif gap <= 1:
                return 70.0
            elif gap <= 2:
                return 50.0
            else:
                return 30.0
        else:
            # Above maximum - slight penalty for overqualification
            return 85.0
    
    def _calculate_education_match(
        self,
        candidate_education: List[Dict],
        required_education: str
    ) -> float:
        """
        Calculate education match score
        
        Returns:
            Score from 0-100
        """
        if not required_education or not candidate_education:
            return 70.0  # Neutral score if no education requirement
        
        required_lower = required_education.lower()
        
        education_hierarchy = {
            'phd': 5,
            'doctorate': 5,
            'master': 4,
            'mba': 4,
            'bachelor': 3,
            'diploma': 2,
            'certificate': 1
        }
        
        # Determine required level
        required_level = 0
        for key, level in education_hierarchy.items():
            if key in required_lower:
                required_level = level
                break
        
        # Determine candidate's highest level
        candidate_level = 0
        for edu in candidate_education:
            degree = edu.get('degree', '').lower()
            for key, level in education_hierarchy.items():
                if key in degree:
                    candidate_level = max(candidate_level, level)
        
        if candidate_level >= required_level:
            return 100.0
        elif candidate_level == required_level - 1:
            return 80.0
        else:
            return 50.0
    
    def _calculate_additional_credentials(
        self,
        projects: List[Dict],
        certifications: List[Dict]
    ) -> float:
        """
        Calculate score based on projects and certifications
        
        Returns:
            Score from 0-100
        """
        score = 0
        
        # Projects (up to 60 points)
        if projects:
            num_projects = len(projects)
            if num_projects >= 5:
                score += 60
            else:
                score += num_projects * 12
        
        # Certifications (up to 40 points)
        if certifications:
            num_certs = len(certifications)
            if num_certs >= 4:
                score += 40
            else:
                score += num_certs * 10
        
        return min(score, 100)
    
    def _get_matched_skills(
        self,
        candidate_skills: List[str],
        required_skills: List[str]
    ) -> List[str]:
        """Get list of matched skills"""
        candidate_skills_normalized = [s.lower().strip() for s in candidate_skills]
        matched = []
        
        for skill in required_skills:
            skill_lower = skill.lower().strip()
            if any(skill_lower in cand_skill or cand_skill in skill_lower
                   for cand_skill in candidate_skills_normalized):
                matched.append(skill)
        
        return matched
    
    def _get_missing_skills(
        self,
        candidate_skills: List[str],
        required_skills: List[str]
    ) -> List[str]:
        """Get list of missing required skills"""
        matched = self._get_matched_skills(candidate_skills, required_skills)
        return [skill for skill in required_skills if skill not in matched]
    
    def _get_experience_gap(
        self,
        candidate_exp: float,
        min_exp: float
    ) -> float:
        """Calculate experience gap (negative = under, positive = over, 0 = perfect)"""
        return candidate_exp - min_exp
    
    def generate_match_explanation(
        self,
        candidate_data: Dict,
        internship_data: Dict,
        match_result: Dict
    ) -> str:
        """
        Generate human-readable explanation for match score using Gemini
        
        Args:
            candidate_data: Candidate profile
            internship_data: Internship details
            match_result: Match calculation results
            
        Returns:
            Detailed explanation string
        """
        prompt = f"""
You are an HR assistant explaining why a candidate matches (or doesn't match) an internship position.

CANDIDATE PROFILE:
- Total Experience: {candidate_data.get('total_experience_years', 0)} years
- Skills: {', '.join(candidate_data.get('all_skills', [])[:10])}
- Education: {candidate_data.get('education', [{}])[0].get('degree', 'N/A') if candidate_data.get('education') else 'N/A'}
- Projects: {len(candidate_data.get('projects', []))} projects
- Certifications: {len(candidate_data.get('certifications', []))} certifications

INTERNSHIP REQUIREMENTS:
- Position: {internship_data.get('title', 'N/A')}
- Required Skills: {', '.join(internship_data.get('required_skills', []))}
- Min Experience: {internship_data.get('min_experience', 0)} years
- Education: {internship_data.get('required_education', 'N/A')}

MATCH SCORES:
- Overall: {match_result['overall_score']}/100
- Skills Match: {match_result['component_scores']['skills_match']}/100
- Experience Match: {match_result['component_scores']['experience_match']}/100
- Matched Skills: {', '.join(match_result['match_details']['matched_skills'])}
- Missing Skills: {', '.join(match_result['match_details']['missing_skills'])}

Generate a concise 3-4 bullet point explanation of:
1. Why this candidate is a good/moderate/weak match
2. Key strengths that align with the position
3. Any gaps or areas of concern
4. Overall recommendation (Strong Fit / Moderate Fit / Weak Fit)

Format as bullet points. Be specific and reference actual skills/experience.
"""
        
        try:
            logger.info("📤 Generating match explanation...")
            result = self.key_manager.generate_content(
                prompt=prompt,
                model="gemini-2.5-flash",
                purpose="matching_explanation",
                temperature=0.3,
                max_output_tokens=500,
                max_retries=3
            )
            logger.info("✅ Match explanation generated")
            return result
        except Exception as e:
            logger.error(f"  Error generating explanation: {e}")
            return self._generate_fallback_explanation(match_result)
    
    def _generate_fallback_explanation(self, match_result: Dict) -> str:
        """Generate basic explanation without LLM"""
        score = match_result['overall_score']
        matched = match_result['match_details']['matched_skills']
        missing = match_result['match_details']['missing_skills']
        
        if score >= 80:
            fit_level = "Strong Match"
        elif score >= 60:
            fit_level = "Moderate Match"
        else:
            fit_level = "Weak Match"
        
        explanation = f"**{fit_level}** (Score: {score}/100)\n\n"
        explanation += f"• Matched {len(matched)}/{len(matched) + len(missing)} required skills\n"
        
        if matched:
            explanation += f"• Strong in: {', '.join(matched[:3])}\n"
        
        if missing:
            explanation += f"• Missing: {', '.join(missing[:3])}\n"
        
        return explanation
    
    def rank_candidates(
        self,
        candidates: List[Dict],
        internship_data: Dict,
        limit: int = 50
    ) -> List[Dict]:
        """
        Rank all candidates for an internship with explanations
        
        Args:
            candidates: List of candidate profiles with embeddings
            internship_data: Internship details with embedding
            limit: Maximum number of candidates to return
            
        Returns:
            Sorted list of candidates with match scores and explanations
        """
        ranked_candidates = []
        
        internship_embedding = internship_data.get('embedding')
        if not internship_embedding:
            # Generate embedding if not exists
            jd_text = f"{internship_data.get('title')} {internship_data.get('description')} "
            jd_text += f"Skills: {', '.join(internship_data.get('required_skills', []))}"
            internship_embedding = self.rag_engine.generate_embedding(jd_text)
        
        print(f"\n🔍 RANKING {len(candidates)} CANDIDATES")
        print(f"=" * 70)
        
        candidates_with_embedding = 0
        candidates_without_embedding = 0
        
        for idx, candidate in enumerate(candidates, 1):
            candidate_embedding = candidate.get('embedding')
            candidate_name = candidate.get('personal_info', {}).get('name', f"Candidate {candidate.get('student_id', 'Unknown')}")
            
            if candidate_embedding:
                candidates_with_embedding += 1
                print(f"✅ Candidate {idx}: {candidate_name} - HAS embedding")
            else:
                candidates_without_embedding += 1
                print(f"⚠️  Candidate {idx}: {candidate_name} - NO embedding (will use fallback)")
            
            # Calculate match score
            match_result = self.calculate_match_score(
                candidate_data=candidate,
                internship_data=internship_data,
                candidate_embedding=candidate_embedding,
                internship_embedding=internship_embedding
            )
            
            # Generate explanation
            explanation = self.generate_match_explanation(
                candidate_data=candidate,
                internship_data=internship_data,
                match_result=match_result
            )
            
            ranked_candidates.append({
                'candidate_id': candidate.get('student_id'),
                'candidate_name': candidate.get('personal_info', {}).get('name', 'N/A'),
                'match_score': match_result['overall_score'],
                'component_scores': match_result['component_scores'],
                'match_details': match_result['match_details'],
                'explanation': explanation,
                'candidate_summary': candidate.get('summary', '')
            })
        
        print(f"\n📊 RANKING SUMMARY:")
        print(f"   Total candidates: {len(candidates)}")
        print(f"   ✅ With embeddings: {candidates_with_embedding}")
        print(f"   ⚠️  Without embeddings: {candidates_without_embedding}")
        print(f"=" * 70)
        print()
        
        # Sort by match score (descending)
        ranked_candidates.sort(key=lambda x: x['match_score'], reverse=True)
        
        return ranked_candidates[:limit]
