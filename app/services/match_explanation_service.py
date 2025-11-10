"""
Match Explanation Service
Generates comprehensive explainability for candidate-internship matches
Integrates all component scores, provenance, and AI recommendations
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import json

from app.services.component_score_service import get_component_score_service
from app.services.provenance_service import get_provenance_service
from app.services.skill_proficiency_service import get_skill_proficiency_service
from app.utils.gemini_key_manager import get_gemini_key_manager
from google.genai import types

logger = logging.getLogger(__name__)


class MatchExplanationService:
    """Service for generating detailed match explanations"""
    
    def __init__(self):
        """Initialize match explanation service"""
        self.component_score_service = get_component_score_service()
        self.provenance_service = get_provenance_service()
        self.skill_proficiency_service = get_skill_proficiency_service()
        self.key_manager = get_gemini_key_manager()
        logger.info("✅ MatchExplanationService initialized")
    
    def generate_explanation(
        self,
        candidate_id: int,
        internship_id: int,
        db_session
    ) -> Optional[Dict]:
        """
        Generate comprehensive explanation for candidate-internship match
        
        Args:
            candidate_id: Candidate user ID
            internship_id: Internship ID
            db_session: Database session
            
        Returns:
            Complete explanation object or None if error
        """
        logger.info(f"🔍 Generating explanation for candidate {candidate_id} x internship {internship_id}")
        
        try:
            from app.models.user import User
            from app.models.internship import Internship
            from app.models.resume import Resume
            from app.models.explainability import CandidateExplanation
            from app.services.rag_engine import RAGEngine
            
            # Fetch candidate, resume, and internship data
            candidate = db_session.query(User).filter(User.id == candidate_id).first()
            if not candidate:
                logger.error(f"  Candidate {candidate_id} not found")
                return None
            
            internship = db_session.query(Internship).filter(Internship.id == internship_id).first()
            if not internship:
                logger.error(f"  Internship {internship_id} not found")
                return None
            
            resume = db_session.query(Resume).filter(
                Resume.student_id == candidate_id,
                Resume.is_active == 1
            ).first()
            
            if not resume:
                logger.error(f"  No active resume found for candidate {candidate_id}")
                return None
            
            # Extract data from resume
            parsed_data = resume.parsed_data or {}
            candidate_skills = resume.extracted_skills or []
            candidate_experience = parsed_data.get('work_experience', [])
            candidate_education = parsed_data.get('education', [])
            candidate_projects = parsed_data.get('projects', [])
            
            # Extract data from internship
            required_skills = internship.required_skills or []
            preferred_skills = internship.preferred_skills or []
            min_years = internship.min_years_experience or 0
            preferred_years = internship.preferred_years or min_years
            required_education = internship.education_level or 'Bachelor'
            skill_weights = internship.skill_weights or []
            rubric_weights = internship.rubric_weights or {}
            
            # Initialize RAG engine for semantic score
            rag_engine = RAGEngine()
            
            # Get embeddings
            resume_embedding = None
            job_embedding = None
            
            try:
                resume_result = rag_engine.resume_collection.get(
                    ids=[f"resume_{resume.resume_id}"],
                    include=["embeddings"]
                )
                if resume_result and resume_result.get('embeddings'):
                    resume_embedding = resume_result['embeddings'][0]
                
                job_result = rag_engine.internship_collection.get(
                    ids=[f"internship_{internship.internship_id}"],
                    include=["embeddings"]
                )
                if job_result and job_result.get('embeddings'):
                    job_embedding = job_result['embeddings'][0]
            except Exception as e:
                logger.warning(f"⚠️  Error fetching embeddings: {e}")
            
            # Calculate all component scores
            logger.info("📊 Calculating component scores...")
            
            # 1. Semantic score
            semantic_score = self.component_score_service.calculate_semantic_score(
                resume_embedding, job_embedding
            ) if resume_embedding and job_embedding else 0
            
            # 2. Skills score
            skills_score, matched_skills, missing_skills = self.component_score_service.calculate_skills_score(
                candidate_skills,
                required_skills,
                preferred_skills,
                skill_weights
            )
            
            # Enhance matched skills with proficiency and evidence
            enhanced_matched_skills = []
            for skill in matched_skills:
                skill_name = skill.get('skill')
                proficiency = self.skill_proficiency_service.calculate_proficiency(
                    skill_name, parsed_data
                )
                evidence = self.skill_proficiency_service.get_skill_evidence(
                    skill_name, resume.parsed_content, parsed_data
                )
                
                enhanced_matched_skills.append({
                    **skill,
                    'proficiency': proficiency,
                    'evidence': evidence,
                    'confidence': skill.get('confidence', 1.0)
                })
            
            # 3. Experience score
            experience_score, experience_analysis = self.component_score_service.calculate_experience_score(
                candidate_experience,
                min_years,
                preferred_years,
                required_skills
            )
            
            # 4. Education score
            education_score, education_analysis = self.component_score_service.calculate_education_score(
                candidate_education,
                required_education
            )
            
            # 5. Projects score
            projects_score, project_analysis = self.component_score_service.calculate_projects_score(
                candidate_projects,
                required_skills
            )
            
            # Aggregate component scores
            component_scores = {
                'semantic': round(semantic_score, 2),
                'skills': round(skills_score, 2),
                'experience': round(experience_score, 2),
                'education': round(education_score, 2),
                'projects': round(projects_score, 2)
            }
            
            # Calculate final weighted score
            overall_score = self.component_score_service.calculate_final_score(
                component_scores, rubric_weights
            )
            
            # Generate AI recommendation
            logger.info("🤖 Generating AI recommendation...")
            ai_recommendation = self._generate_ai_recommendation(
                candidate, resume, internship, component_scores, 
                enhanced_matched_skills, missing_skills,
                experience_analysis, education_analysis, project_analysis
            )
            
            # Determine recommendation badge
            if overall_score >= 80:
                recommendation = "SHORTLIST"
            elif overall_score >= 60:
                recommendation = "MAYBE"
            else:
                recommendation = "REJECT"
            
            # Calculate confidence
            extraction_confidence = resume.extraction_confidence or {}
            component_confidences = {
                'skills': extraction_confidence.get('skills', 0.8),
                'experience': extraction_confidence.get('experience', 0.8),
                'education': extraction_confidence.get('education', 0.9),
                'projects': extraction_confidence.get('projects', 0.7)
            }
            confidence = self.component_score_service.generate_confidence_score(component_confidences)
            
            # Build complete explanation object
            explanation = {
                'candidate_id': candidate_id,
                'internship_id': internship_id,
                'overall_score': round(overall_score, 2),
                'confidence': round(confidence, 2),
                'recommendation': recommendation,
                'component_scores': component_scores,
                'matched_skills': enhanced_matched_skills,
                'missing_skills': missing_skills,
                'experience_analysis': experience_analysis,
                'education_analysis': education_analysis,
                'project_analysis': project_analysis,
                'ai_recommendation': ai_recommendation,
                'provenance': {
                    'extraction_model': 'gemini-2.0-flash-exp',
                    'extract_time': datetime.now().isoformat(),
                    'data_sources': ['resume', 'internship_posting'],
                    'llm_model': 'gemini-2.0-flash-exp'
                },
                'created_at': datetime.now().isoformat()
            }
            
            # Store in database
            logger.info("💾 Storing explanation in database...")
            candidate_explanation = CandidateExplanation(
                candidate_id=candidate_id,
                internship_id=internship_id,
                overall_score=overall_score,
                confidence=confidence,
                recommendation=recommendation,
                component_scores=component_scores,
                matched_skills=enhanced_matched_skills,
                missing_skills=missing_skills,
                experience_analysis=experience_analysis,
                education_analysis=education_analysis,
                project_analysis=project_analysis,
                ai_recommendation=ai_recommendation,
                provenance=explanation['provenance']
            )
            
            db_session.add(candidate_explanation)
            db_session.commit()
            
            explanation['explanation_id'] = candidate_explanation.explanation_id
            
            logger.info(f"✅ Explanation generated successfully (score: {overall_score:.2f})")
            return explanation
            
        except Exception as e:
            logger.error(f"  Error generating explanation: {e}", exc_info=True)
            db_session.rollback()
            return None
    
    def _generate_ai_recommendation(
        self,
        candidate,
        resume,
        internship,
        component_scores: Dict,
        matched_skills: List[Dict],
        missing_skills: List[Dict],
        experience_analysis: Dict,
        education_analysis: Dict,
        project_analysis: List[Dict]
    ) -> Dict:
        """
        Generate AI-powered recommendation using Gemini
        
        Returns:
            AI recommendation object with action, priority, strengths, concerns, questions
        """
        try:
            client = self.key_manager.get_client(purpose="matching_explanation")
            
            # Build context for AI
            matched_skills_str = ", ".join([s['skill'] for s in matched_skills[:10]])
            missing_skills_str = ", ".join([s['skill'] for s in missing_skills[:5]])
            
            prompt = f"""Analyze this candidate for the internship role and provide a detailed recommendation.

**Candidate:** {candidate.full_name}
**Role:** {internship.title} at {internship.company_name}

**Component Scores:**
- Semantic Match: {component_scores['semantic']:.1f}%
- Skills Match: {component_scores['skills']:.1f}%
- Experience Match: {component_scores['experience']:.1f}%
- Education Match: {component_scores['education']:.1f}%
- Projects Match: {component_scores['projects']:.1f}%

**Matched Skills ({len(matched_skills)}):** {matched_skills_str}
**Missing Skills ({len(missing_skills)}):** {missing_skills_str}

**Experience:** {experience_analysis['total_years']} years total, {experience_analysis['relevant_years']} relevant
**Education:** {education_analysis['highest_degree']} ({education_analysis['match_level']} requirement)
**Relevant Projects:** {sum(1 for p in project_analysis if p.get('is_relevant', False))}/{len(project_analysis)}

Provide:
1. **Action:** SHORTLIST | MAYBE | REJECT
2. **Priority:** High | Medium | Low
3. **Top 3 Strengths:** (bullet points showing what makes this candidate strong)
4. **Top 2 Concerns:** (bullet points showing potential weak areas or gaps)
5. **3 Interview Focus Questions:** (specific technical/behavioral questions to ask)
6. **Overall Justification:** (2-3 sentences explaining your recommendation)

Return as JSON:
{{
  "action": "SHORTLIST|MAYBE|REJECT",
  "priority": "High|Medium|Low",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "concerns": ["concern 1", "concern 2"],
  "interview_questions": ["question 1?", "question 2?", "question 3?"],
  "justification": "2-3 sentence explanation"
}}
"""
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            ai_rec = json.loads(response_text)
            
            # Add prompt and response for provenance
            ai_rec['prompt'] = prompt
            ai_rec['response'] = response.text
            
            return ai_rec
            
        except Exception as e:
            logger.error(f"  Error generating AI recommendation: {e}")
            # Return default recommendation
            return {
                'action': 'MAYBE',
                'priority': 'Medium',
                'strengths': ['Skills match requirements', 'Relevant experience', 'Strong educational background'],
                'concerns': ['Some required skills missing', 'Limited project portfolio'],
                'interview_questions': [
                    'Can you describe your experience with the required technologies?',
                    'What projects have you worked on that are similar to our work?',
                    'How do you approach learning new technologies?'
                ],
                'justification': 'Candidate shows potential but requires interview to assess skill gaps.',
                'prompt': 'Error generating recommendation',
                'response': str(e)
            }
    
    def generate_comparison_explanation(
        self,
        candidate_id_1: int,
        candidate_id_2: int,
        internship_id: int,
        db_session
    ) -> Optional[Dict]:
        """
        Generate side-by-side comparison of two candidates
        
        Args:
            candidate_id_1: First candidate ID
            candidate_id_2: Second candidate ID
            internship_id: Internship ID
            db_session: Database session
            
        Returns:
            Comparison object with side-by-side analysis
        """
        logger.info(f"📊 Comparing candidates {candidate_id_1} vs {candidate_id_2} for internship {internship_id}")
        
        try:
            # Get explanations for both candidates
            explanation_1 = self.generate_explanation(candidate_id_1, internship_id, db_session)
            explanation_2 = self.generate_explanation(candidate_id_2, internship_id, db_session)
            
            if not explanation_1 or not explanation_2:
                logger.error("  Failed to generate explanations for comparison")
                return None
            
            # Build comparison structure
            comparison = {
                'internship_id': internship_id,
                'candidate_1': {
                    'candidate_id': candidate_id_1,
                    'overall_score': explanation_1['overall_score'],
                    'recommendation': explanation_1['recommendation'],
                    'component_scores': explanation_1['component_scores'],
                    'matched_skills_count': len(explanation_1['matched_skills']),
                    'missing_skills_count': len(explanation_1['missing_skills']),
                    'experience_years': explanation_1['experience_analysis']['total_years'],
                    'relevant_experience_years': explanation_1['experience_analysis']['relevant_years']
                },
                'candidate_2': {
                    'candidate_id': candidate_id_2,
                    'overall_score': explanation_2['overall_score'],
                    'recommendation': explanation_2['recommendation'],
                    'component_scores': explanation_2['component_scores'],
                    'matched_skills_count': len(explanation_2['matched_skills']),
                    'missing_skills_count': len(explanation_2['missing_skills']),
                    'experience_years': explanation_2['experience_analysis']['total_years'],
                    'relevant_experience_years': explanation_2['experience_analysis']['relevant_years']
                }
            }
            
            # Highlight decisive differences
            score_diff = explanation_1['overall_score'] - explanation_2['overall_score']
            comparison['score_difference'] = round(score_diff, 2)
            comparison['better_candidate'] = candidate_id_1 if score_diff > 0 else candidate_id_2
            
            # Component-wise comparison
            comparison['component_differences'] = {}
            for component in explanation_1['component_scores'].keys():
                diff = explanation_1['component_scores'][component] - explanation_2['component_scores'][component]
                comparison['component_differences'][component] = round(diff, 2)
            
            # Generate natural language summary
            comparison['summary'] = self._generate_comparison_summary(
                explanation_1, explanation_2, comparison
            )
            
            # Actionable next steps
            comparison['next_steps'] = {
                'candidate_1': self._generate_next_steps(explanation_1),
                'candidate_2': self._generate_next_steps(explanation_2)
            }
            
            logger.info(f"✅ Comparison generated (better: candidate {comparison['better_candidate']})")
            return comparison
            
        except Exception as e:
            logger.error(f"  Error generating comparison: {e}", exc_info=True)
            return None
    
    def _generate_comparison_summary(
        self,
        exp1: Dict,
        exp2: Dict,
        comparison: Dict
    ) -> str:
        """Generate natural language summary of comparison"""
        
        better_id = comparison['better_candidate']
        score_diff = abs(comparison['score_difference'])
        
        better_exp = exp1 if better_id == exp1['candidate_id'] else exp2
        weaker_exp = exp2 if better_id == exp1['candidate_id'] else exp1
        
        # Find strongest differentiator
        max_diff_component = max(
            comparison['component_differences'].items(),
            key=lambda x: abs(x[1])
        )
        
        summary = f"Candidate {better_id} scores {score_diff:.1f} points higher overall. "
        summary += f"The biggest difference is in {max_diff_component[0]} ({abs(max_diff_component[1]):.1f} points). "
        
        # Skills comparison
        if len(better_exp['matched_skills']) > len(weaker_exp['matched_skills']):
            skill_diff = len(better_exp['matched_skills']) - len(weaker_exp['matched_skills'])
            summary += f"Candidate {better_id} matches {skill_diff} more required skills. "
        
        # Experience comparison
        if better_exp['experience_analysis']['relevant_years'] > weaker_exp['experience_analysis']['relevant_years']:
            exp_diff = better_exp['experience_analysis']['relevant_years'] - weaker_exp['experience_analysis']['relevant_years']
            summary += f"Candidate {better_id} has {exp_diff:.1f} more years of relevant experience."
        
        return summary
    
    def _generate_next_steps(self, explanation: Dict) -> List[str]:
        """Generate actionable next steps for a candidate"""
        
        next_steps = []
        
        if explanation['recommendation'] == 'SHORTLIST':
            next_steps.append("Schedule technical interview")
            next_steps.append("Request portfolio/GitHub review")
        elif explanation['recommendation'] == 'MAYBE':
            next_steps.append("Conduct phone screening to assess skill gaps")
            next_steps.append("Request additional information on missing skills")
        else:
            next_steps.append("Send polite rejection email")
            next_steps.append("Provide feedback on skills to develop")
        
        # Add specific steps based on missing skills
        critical_missing = [s for s in explanation['missing_skills'] if s.get('impact') == 'critical']
        if critical_missing and explanation['recommendation'] != 'REJECT':
            next_steps.append(f"Ask about plans to learn: {', '.join([s['skill'] for s in critical_missing[:2]])}")
        
        return next_steps
    
    def generate_short_reason(self, explanation: Dict) -> str:
        """
        Generate one-sentence summary for card header
        
        Args:
            explanation: Full explanation object
            
        Returns:
            One-sentence reason string
        """
        matched_count = len(explanation['matched_skills'])
        total_required = matched_count + len(explanation['missing_skills'])
        exp_years = explanation['experience_analysis']['relevant_years']
        
        if explanation['recommendation'] == 'SHORTLIST':
            return f"Strong match: {matched_count}/{total_required} skills, {exp_years:.1f} years relevant experience"
        elif explanation['recommendation'] == 'MAYBE':
            return f"Potential fit: {matched_count}/{total_required} skills matched, needs skills assessment"
        else:
            missing_critical = [s for s in explanation['missing_skills'] if s.get('impact') == 'critical']
            if missing_critical:
                return f"Missing critical skills: {', '.join([s['skill'] for s in missing_critical[:2]])}"
            return f"Limited match: {matched_count}/{total_required} skills, insufficient experience"


# Singleton instance
_match_explanation_service_instance = None


def get_match_explanation_service() -> MatchExplanationService:
    """Get or create singleton MatchExplanationService instance"""
    global _match_explanation_service_instance
    if _match_explanation_service_instance is None:
        _match_explanation_service_instance = MatchExplanationService()
    return _match_explanation_service_instance
