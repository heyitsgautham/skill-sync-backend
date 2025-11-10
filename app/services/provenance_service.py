"""
Provenance Extraction Service
Extracts evidence snippets from resumes to support claims about skills, experience, and projects
Uses Gemini API to identify exact text spans that prove extracted information
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import re

from app.utils.gemini_key_manager import get_gemini_key_manager
from google.genai import types

logger = logging.getLogger(__name__)


class ProvenanceService:
    """Service for extracting and storing provenance information from resumes"""
    
    def __init__(self):
        """Initialize provenance service with Gemini API"""
        self.key_manager = get_gemini_key_manager()
        logger.info("✅ ProvenanceService initialized")
    
    def extract_skill_provenance(
        self, 
        resume_text: str, 
        skills: List[str]
    ) -> Dict[str, any]:
        """
        Extract evidence snippets for each skill from resume text
        
        Args:
            resume_text: Full resume text content
            skills: List of skills to find evidence for
            
        Returns:
            Dict with skill evidences: {skill: [{text, line_numbers, confidence}]}
        """
        logger.info(f"📝 Extracting skill provenance for {len(skills)} skills")
        
        if not skills or not resume_text:
            logger.warning("⚠️  No skills or resume text provided")
            return {}
        
        try:
            client = self.key_manager.get_client(purpose="skills_extraction")
            
            # Build the prompt for Gemini
            prompt = f"""Analyze the following resume text and find evidence for each skill listed.
For each skill, identify specific text snippets that prove the candidate has this skill.
Include the approximate line numbers and a confidence score (0-1).

Resume Text:
{resume_text}

Skills to find evidence for:
{', '.join(skills)}

Return a JSON object in this format:
{{
  "skill_name": [
    {{
      "text": "exact snippet from resume",
      "line_numbers": [start, end],
      "confidence": 0.95,
      "context": "where this was found (e.g., 'Work Experience section')"
    }}
  ]
}}

Only include snippets that clearly demonstrate the skill. If no evidence found for a skill, use an empty array.
"""
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4000
                )
            )
            
            # Parse the JSON response
            response_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            evidences = json.loads(response_text)
            
            logger.info(f"✅ Extracted skill provenance for {len(evidences)} skills")
            return evidences
            
        except json.JSONDecodeError as e:
            logger.error(f"  Failed to parse Gemini response as JSON: {e}")
            # Return empty evidence for all skills
            return {skill: [] for skill in skills}
            
        except Exception as e:
            logger.error(f"  Error extracting skill provenance: {e}")
            return {skill: [] for skill in skills}
    
    def extract_experience_provenance(
        self, 
        resume_text: str, 
        experiences: List[Dict]
    ) -> List[Dict]:
        """
        Extract evidence snippets for work experiences
        
        Args:
            resume_text: Full resume text content
            experiences: List of experience dicts with company, role, dates
            
        Returns:
            List of experience evidences with snippets and metadata
        """
        logger.info(f"📝 Extracting experience provenance for {len(experiences)} experiences")
        
        if not experiences or not resume_text:
            logger.warning("⚠️  No experiences or resume text provided")
            return []
        
        try:
            client = self.key_manager.get_client(purpose="resume_parsing")
            
            # Build experience summary for prompt
            exp_summary = "\n".join([
                f"- {exp.get('role', 'Unknown')} at {exp.get('company', 'Unknown')} ({exp.get('start_date', 'N/A')} - {exp.get('end_date', 'N/A')})"
                for exp in experiences
            ])
            
            prompt = f"""Analyze the following resume and extract detailed evidence for each work experience.
For each experience, find the exact text snippet that describes this role, including responsibilities and achievements.

Resume Text:
{resume_text}

Experiences to find evidence for:
{exp_summary}

Return a JSON array in this format:
[
  {{
    "company": "Company Name",
    "role": "Job Title",
    "snippet": "full text description of this role from resume",
    "dates": "employment period",
    "responsibilities": ["list", "of", "key", "responsibilities"],
    "achievements": ["list", "of", "achievements"],
    "technologies": ["tech", "used"],
    "line_numbers": [start, end]
  }}
]

Extract all relevant details from the resume text.
"""
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4000
                )
            )
            
            # Parse the JSON response
            response_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            evidences = json.loads(response_text)
            
            logger.info(f"✅ Extracted experience provenance for {len(evidences)} experiences")
            return evidences
            
        except json.JSONDecodeError as e:
            logger.error(f"  Failed to parse Gemini response as JSON: {e}")
            return []
            
        except Exception as e:
            logger.error(f"  Error extracting experience provenance: {e}")
            return []
    
    def extract_project_provenance(
        self, 
        resume_text: str, 
        projects: List[Dict]
    ) -> List[Dict]:
        """
        Extract evidence snippets for projects
        
        Args:
            resume_text: Full resume text content
            projects: List of project dicts with name, description
            
        Returns:
            List of project evidences with snippets and tech stack
        """
        logger.info(f"📝 Extracting project provenance for {len(projects)} projects")
        
        if not projects or not resume_text:
            logger.warning("⚠️  No projects or resume text provided")
            return []
        
        try:
            client = self.key_manager.get_client(purpose="achievement_extraction")
            
            # Build project summary for prompt
            proj_summary = "\n".join([
                f"- {proj.get('name', 'Unknown Project')}: {proj.get('description', 'No description')[:100]}"
                for proj in projects
            ])
            
            prompt = f"""Analyze the following resume and extract detailed evidence for each project.
For each project, find the exact text snippet that describes it, including technologies used and outcomes.

Resume Text:
{resume_text}

Projects to find evidence for:
{proj_summary}

Return a JSON array in this format:
[
  {{
    "name": "Project Name",
    "snippet": "full text description from resume",
    "technologies": ["React", "Node.js", "MongoDB"],
    "role": "role in project",
    "duration": "time period",
    "outcomes": ["specific results or achievements"],
    "github_link": "link if mentioned",
    "line_numbers": [start, end]
  }}
]

Extract all relevant technical details.
"""
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4000
                )
            )
            
            # Parse the JSON response
            response_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            evidences = json.loads(response_text)
            
            logger.info(f"✅ Extracted project provenance for {len(evidences)} projects")
            return evidences
            
        except json.JSONDecodeError as e:
            logger.error(f"  Failed to parse Gemini response as JSON: {e}")
            return []
            
        except Exception as e:
            logger.error(f"  Error extracting project provenance: {e}")
            return []
    
    def calculate_extraction_confidence(
        self, 
        evidences: Dict[str, List[Dict]]
    ) -> Dict[str, float]:
        """
        Calculate confidence scores for extraction quality
        
        Args:
            evidences: Dict of evidences by section (skills, experience, projects)
            
        Returns:
            Dict of confidence scores by section (0-1 scale)
        """
        logger.info("📊 Calculating extraction confidence scores")
        
        confidence_scores = {}
        
        for section, evidence_list in evidences.items():
            if not evidence_list:
                confidence_scores[section] = 0.0
                continue
            
            # Calculate confidence based on:
            # 1. Number of evidences found
            # 2. Average confidence of individual evidences
            # 3. Completeness of information
            
            if isinstance(evidence_list, dict):
                # For skills (dict format)
                total_skills = len(evidence_list)
                skills_with_evidence = sum(1 for evs in evidence_list.values() if evs)
                
                if total_skills == 0:
                    confidence_scores[section] = 0.0
                else:
                    # Average confidence from individual skills
                    all_confidences = []
                    for skill_evidences in evidence_list.values():
                        if skill_evidences:
                            all_confidences.extend([
                                ev.get('confidence', 0.5) 
                                for ev in skill_evidences
                            ])
                    
                    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5
                    coverage = skills_with_evidence / total_skills
                    
                    # Final confidence is weighted average of coverage and individual confidence
                    confidence_scores[section] = (0.6 * coverage) + (0.4 * avg_confidence)
            
            elif isinstance(evidence_list, list):
                # For experience/projects (list format)
                if not evidence_list:
                    confidence_scores[section] = 0.0
                else:
                    # Check completeness of each evidence
                    completeness_scores = []
                    for ev in evidence_list:
                        # Count how many expected fields are present and non-empty
                        expected_fields = ['snippet', 'technologies', 'line_numbers']
                        present_fields = sum(1 for field in expected_fields if ev.get(field))
                        completeness_scores.append(present_fields / len(expected_fields))
                    
                    confidence_scores[section] = sum(completeness_scores) / len(completeness_scores)
        
        logger.info(f"✅ Calculated confidence scores: {confidence_scores}")
        return confidence_scores
    
    def store_provenance(
        self,
        resume_id: int,
        skill_evidences: Dict,
        experience_evidences: List[Dict],
        project_evidences: List[Dict],
        confidence_scores: Dict[str, float],
        db_session
    ) -> bool:
        """
        Store provenance data in the resume record
        
        Args:
            resume_id: Resume database ID
            skill_evidences: Skill evidence dict
            experience_evidences: Experience evidence list
            project_evidences: Project evidence list
            confidence_scores: Confidence scores by section
            db_session: Database session
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"💾 Storing provenance for resume_id: {resume_id}")
        
        try:
            from app.models.resume import Resume
            
            # Get the resume record
            resume = db_session.query(Resume).filter(Resume.id == resume_id).first()
            
            if not resume:
                logger.error(f"  Resume {resume_id} not found")
                return False
            
            # Store provenance data
            resume.skill_evidences = skill_evidences
            resume.experience_evidences = experience_evidences
            resume.project_evidences = project_evidences
            resume.extraction_confidence = confidence_scores
            
            # Store extraction metadata
            resume.extraction_metadata = {
                "model": "gemini-2.0-flash-exp",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "source": "ProvenanceService"
            }
            
            db_session.commit()
            logger.info(f"✅ Provenance stored successfully for resume {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"  Error storing provenance: {e}")
            db_session.rollback()
            return False


# Singleton instance
_provenance_service_instance = None


def get_provenance_service() -> ProvenanceService:
    """Get or create singleton ProvenanceService instance"""
    global _provenance_service_instance
    if _provenance_service_instance is None:
        _provenance_service_instance = ProvenanceService()
    return _provenance_service_instance
