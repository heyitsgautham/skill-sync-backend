"""
Resume Intelligence Service - Core Intelligence System for Resume Filtering
Uses Google Gemini for structured extraction and HuggingFace embeddings for matching
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

from app.utils.gemini_key_manager import get_gemini_key_manager

load_dotenv()

logger = logging.getLogger(__name__)


class ResumeIntelligenceService:
    """
    Core Intelligence System for intelligent resume filtering
    Handles structured extraction, skill analysis, and experience calculation
    """
    
    def __init__(self):
        """Initialize Gemini AI key manager for structured extraction"""
        self.key_manager = get_gemini_key_manager()
        logger.info("✅ ResumeIntelligenceService initialized with GeminiKeyManager")
        
    def extract_structured_data(self, resume_text: str) -> Dict:
        """
        Extract structured information from resume using Gemini
        
        Args:
            resume_text: Raw text extracted from resume
            
        Returns:
            Dictionary with structured data:
            - skills: List of technical skills
            - experience: List of work experiences with dates
            - education: List of educational qualifications
            - total_experience_months: Calculated total experience
            - projects: List of projects
            - certifications: List of certifications
        """
        prompt = f"""
You are an expert resume parser. Extract structured information from this resume in valid JSON format.

IMPORTANT RULES:
1. Extract ALL technical skills mentioned (programming languages, frameworks, tools, technologies)
2. For work experience, extract: company, role, start_date, end_date, description, key_achievements
3. If dates are unclear, use "YYYY-MM" format. If only year is given, use "YYYY-01" for start and "YYYY-12" for end
4. For current positions, use "Present" for end_date
5. Extract implicit skills from job descriptions (e.g., "built React apps" → React, JavaScript)
6. Include soft skills if explicitly mentioned (Leadership, Communication, etc.)
7. Education should include: degree, institution, year, grade (if mentioned)
8. Extract projects with: name, description, technologies_used
9. Extract certifications if mentioned

Return ONLY valid JSON in this exact format:
{{
  "personal_info": {{
    "name": "extracted name or 'Not provided'",
    "email": "extracted email or null",
    "phone": "extracted phone or null",
    "location": "city, state/country or null"
  }},
  "skills": {{
    "technical": ["skill1", "skill2", ...],
    "soft": ["skill1", "skill2", ...]
  }},
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "duration_months": 0,
      "description": "Brief description",
      "key_achievements": ["achievement1", "achievement2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "field": "Field of Study",
      "institution": "University/College Name",
      "year": "YYYY",
      "grade": "GPA/Percentage or null"
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["tech1", "tech2"],
      "link": "URL or null"
    }}
  ],
  "certifications": [
    {{
      "name": "Certification Name",
      "issuer": "Issuing Organization",
      "date": "YYYY-MM or null"
    }}
  ],
  "summary": "2-3 sentence professional summary based on the resume"
}}

Resume Text:
{resume_text}

Return ONLY the JSON object, no markdown, no explanation.
"""
        
        try:
            logger.info("📤 Extracting structured data from resume using Gemini...")
            
            # Use key manager with retry logic
            result_text = self.key_manager.generate_content(
                prompt=prompt,
                model="gemini-2.5-flash",
                purpose="resume_parsing",
                temperature=0.1,
                max_output_tokens=8000,
                max_retries=3
            )
            
            # Clean up markdown code blocks if present
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'^```\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            
            structured_data = json.loads(result_text)
            
            # Calculate total experience
            total_months = self._calculate_total_experience(structured_data.get('experience', []))
            structured_data['total_experience_months'] = total_months
            structured_data['total_experience_years'] = round(total_months / 12, 1)
            
            # Normalize skills
            all_skills = structured_data.get('skills', {}).get('technical', []) + \
                        structured_data.get('skills', {}).get('soft', [])
            structured_data['all_skills'] = list(set(all_skills))  # Remove duplicates
            
            logger.info(f"✅ Extracted {len(all_skills)} skills, {len(structured_data.get('experience', []))} experiences")
            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"  JSON parsing error: {e}")
            logger.error(f"Response text: {result_text}")
            # Return minimal valid structure
            return self._create_fallback_structure(resume_text)
        except Exception as e:
            logger.error(f"  Error in structured extraction: {e}")
            return self._create_fallback_structure(resume_text)
    
    def _calculate_total_experience(self, experiences: List[Dict]) -> int:
        """
        Calculate total months of work experience, handling overlaps
        
        Args:
            experiences: List of work experience dictionaries
            
        Returns:
            Total months of experience (non-overlapping)
        """
        if not experiences:
            return 0
        
        date_ranges = []
        
        for exp in experiences:
            try:
                start_str = exp.get('start_date', '')
                end_str = exp.get('end_date', 'Present')
                
                # Parse start date
                if '-' in start_str:
                    year, month = start_str.split('-')
                    start_date = datetime(int(year), int(month), 1)
                else:
                    start_date = datetime(int(start_str), 1, 1)
                
                # Parse end date
                if end_str.lower() in ['present', 'current', 'now']:
                    end_date = datetime.now()
                elif '-' in end_str:
                    year, month = end_str.split('-')
                    end_date = datetime(int(year), int(month), 1)
                else:
                    end_date = datetime(int(end_str), 12, 31)
                
                date_ranges.append((start_date, end_date))
                
            except (ValueError, AttributeError) as e:
                print(f"Date parsing error: {e}")
                continue
        
        if not date_ranges:
            return 0
        
        # Sort by start date
        date_ranges.sort(key=lambda x: x[0])
        
        # Merge overlapping ranges
        merged_ranges = [date_ranges[0]]
        for start, end in date_ranges[1:]:
            last_start, last_end = merged_ranges[-1]
            
            if start <= last_end:
                # Overlapping, merge
                merged_ranges[-1] = (last_start, max(last_end, end))
            else:
                # Non-overlapping, add new range
                merged_ranges.append((start, end))
        
        # Calculate total months
        total_months = 0
        for start, end in merged_ranges:
            months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += max(0, months)
        
        return total_months
    
    def _create_fallback_structure(self, resume_text: str) -> Dict:
        """
        Create a fallback structure when Gemini parsing fails
        Uses basic regex extraction
        """
        # Basic email extraction
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text)
        email = email_match.group(0) if email_match else None
        
        # Basic phone extraction
        phone_match = re.search(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', resume_text)
        phone = phone_match.group(0) if phone_match else None
        
        return {
            "personal_info": {
                "name": "Not provided",
                "email": email,
                "phone": phone,
                "location": None
            },
            "skills": {
                "technical": [],
                "soft": []
            },
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "summary": "Resume parsing failed. Manual review required.",
            "total_experience_months": 0,
            "total_experience_years": 0,
            "all_skills": []
        }
    
    def generate_candidate_summary(self, structured_data: Dict) -> str:
        """
        Generate a concise candidate summary using Gemini
        
        Args:
            structured_data: Structured resume data
            
        Returns:
            2-3 sentence professional summary
        """
        if structured_data.get('summary'):
            return structured_data['summary']
        
        prompt = f"""
Generate a concise 2-3 sentence professional summary for this candidate based on their profile:

Skills: {', '.join(structured_data.get('all_skills', [])[:15])}
Experience: {structured_data.get('total_experience_years', 0)} years
Education: {structured_data.get('education', [{}])[0].get('degree', 'N/A') if structured_data.get('education') else 'N/A'}

Write in third person. Be specific and highlight key strengths.
"""
        
        try:
            logger.info("📤 Generating candidate summary...")
            result = self.key_manager.generate_content(
                prompt=prompt,
                model="gemini-2.5-flash",
                purpose="candidate_summary",
                temperature=0.3,
                max_output_tokens=200,
                max_retries=3
            )
            logger.info("✅ Candidate summary generated")
            return result
        except Exception as e:
            logger.error(f"  Error generating summary: {e}")
            return f"Candidate with {structured_data.get('total_experience_years', 0)} years of experience"
    
    def extract_key_achievements(self, structured_data: Dict) -> List[str]:
        """
        Extract top 3-5 key achievements from experience using Gemini
        
        Args:
            structured_data: Structured resume data
            
        Returns:
            List of key achievements
        """
        experiences = structured_data.get('experience', [])
        if not experiences:
            return []
        
        all_achievements = []
        for exp in experiences:
            all_achievements.extend(exp.get('key_achievements', []))
        
        if not all_achievements:
            return []
        
        prompt = f"""
From this list of achievements, select the top 3-5 most impressive and quantifiable ones:

{chr(10).join([f"- {ach}" for ach in all_achievements])}

Return ONLY the selected achievements as a JSON array of strings.
Format: ["achievement 1", "achievement 2", ...]
"""
        
        try:
            logger.info("📤 Extracting key achievements...")
            result_text = self.key_manager.generate_content(
                prompt=prompt,
                model="gemini-2.5-flash",
                purpose="achievement_extraction",
                temperature=0.2,
                max_output_tokens=500,
                max_retries=3
            )
            
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'^```\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            
            top_achievements = json.loads(result_text)
            logger.info(f"✅ Extracted {len(top_achievements)} key achievements")
            return top_achievements[:5]
        except Exception as e:
            logger.error(f"  Error extracting achievements: {e}")
            return all_achievements[:5]
