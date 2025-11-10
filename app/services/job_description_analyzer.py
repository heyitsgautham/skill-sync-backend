"""
Job Description Analyzer Service
Extracts required and preferred skills from job descriptions using Gemini AI
"""

import json
import re
import logging
from typing import Dict, List
from app.utils.gemini_key_manager import get_gemini_key_manager

logger = logging.getLogger(__name__)


class JobDescriptionAnalyzer:
    """
    Service for analyzing job descriptions and extracting structured skill requirements
    """
    
    def __init__(self):
        """Initialize Gemini AI key manager for skill extraction"""
        self.key_manager = get_gemini_key_manager()
        logger.info("✅ JobDescriptionAnalyzer initialized with GeminiKeyManager")
    
    def extract_skills(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract required and preferred skills from job description using Gemini AI
        
        Args:
            job_description: The full job description text
            
        Returns:
            Dictionary with:
            - required_skills: List of must-have skills
            - preferred_skills: List of nice-to-have skills
        """
        prompt = f"""Extract technical skills from this job description.

IMPORTANT LIMITS:
- Extract MAX 7 required skills
- Extract MAX 7 preferred skills  
- Total skills (required + preferred) must NOT exceed 15
- Prioritize the MOST IMPORTANT and SPECIFIC skills

REQUIRED SKILLS = Explicitly required/mandatory/must-have
PREFERRED SKILLS = Nice-to-have/preferred/bonus/plus

Extract ONLY: programming languages, frameworks, tools, platforms, databases, methodologies
Normalize names: "React.js"→"React", "nodejs"→"Node.js"
If unclear, classify as REQUIRED

Job Description:
{job_description}

Return JSON only (no markdown, no explanation):
{{"required_skills":["skill1","skill2"],"preferred_skills":["skill3","skill4"]}}"""
        
        try:
            logger.info("📤 Extracting skills from job description using Gemini...")
            
            # Try primary extraction
            try:
                result_text = self.key_manager.generate_content(
                    prompt=prompt,
                    model="gemini-2.5-flash",
                    purpose="job_description_analysis",
                    temperature=0.1,
                    max_output_tokens=4000,  # Increased for large job descriptions
                    max_retries=3
                )
                
                if not result_text or result_text.strip() == "":
                    logger.warning("⚠️ Empty response from Gemini, trying fallback method...")
                    raise Exception("Empty response from primary method")
                    
            except Exception as primary_error:
                logger.warning(f"⚠️ Primary extraction failed: {primary_error}")
                logger.info("🔄 Attempting fallback keyword extraction...")
                return self._fallback_keyword_extraction(job_description)
            
            # Clean up markdown code blocks if present
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'^```\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            result_text = result_text.strip()
            
            logger.info(f"📝 Response text: {result_text[:200]}...")
            
            # Parse JSON response
            extracted_data = json.loads(result_text)
            
            # Validate and clean data
            required_skills = extracted_data.get('required_skills', [])
            preferred_skills = extracted_data.get('preferred_skills', [])
            
            # If empty, try fallback
            if not required_skills and not preferred_skills:
                logger.warning("⚠️ No skills extracted, using fallback method...")
                return self._fallback_keyword_extraction(job_description)
            
            # Remove duplicates (case-insensitive)
            required_skills_lower = {s.lower(): s for s in required_skills}
            preferred_skills_cleaned = [
                s for s in preferred_skills 
                if s.lower() not in required_skills_lower
            ]
            
            # Apply skill limits: max 7 required, max 7 preferred, max 15 total
            required_skills_list = list(required_skills_lower.values())
            original_required = len(required_skills_list)
            original_preferred = len(preferred_skills_cleaned)
            
            # Limit required to 7
            if len(required_skills_list) > 7:
                logger.warning(f"⚠️ Required skills ({len(required_skills_list)}) exceeds limit. Trimming to 7.")
                required_skills_list = required_skills_list[:7]
            
            # Limit preferred to 7
            if len(preferred_skills_cleaned) > 7:
                logger.warning(f"⚠️ Preferred skills ({len(preferred_skills_cleaned)}) exceeds limit. Trimming to 7.")
                preferred_skills_cleaned = preferred_skills_cleaned[:7]
            
            # Ensure total doesn't exceed 15
            total = len(required_skills_list) + len(preferred_skills_cleaned)
            if total > 15:
                available_for_preferred = 15 - len(required_skills_list)
                logger.warning(f"⚠️ Total skills ({total}) exceeds 15. Trimming preferred to {available_for_preferred}.")
                preferred_skills_cleaned = preferred_skills_cleaned[:available_for_preferred]
            
            result = {
                'required_skills': required_skills_list,
                'preferred_skills': preferred_skills_cleaned
            }
            
            # Log if trimming occurred
            final_required = len(result['required_skills'])
            final_preferred = len(result['preferred_skills'])
            if original_required != final_required or original_preferred != final_preferred:
                logger.info(f"📊 Skills adjusted: Required {original_required}→{final_required}, Preferred {original_preferred}→{final_preferred}, Total: {final_required + final_preferred}/15")
            
            logger.info(f"✅ Extracted {final_required} required skills and {final_preferred} preferred skills")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"  JSON parsing error: {e}")
            logger.error(f"Response text: {result_text if 'result_text' in locals() else 'N/A'}")
            logger.info("🔄 Using fallback keyword extraction...")
            return self._fallback_keyword_extraction(job_description)
            
        except Exception as e:
            logger.error(f"  Error extracting skills: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.info("🔄 Using fallback keyword extraction...")
            return self._fallback_keyword_extraction(job_description)
    
    def _fallback_keyword_extraction(self, job_description: str) -> Dict[str, List[str]]:
        """
        Fallback method to extract skills using keyword matching
        When AI fails, this ensures we still extract some skills
        """
        logger.info("🔍 Using fallback keyword extraction method...")
        
        # Common technical skills and patterns
        skill_patterns = {
            # Programming Languages
            'python': 'Python', 'java': 'Java', 'javascript': 'JavaScript', 
            'typescript': 'TypeScript', 'c++': 'C++', 'c#': 'C#', 'go': 'Go',
            'rust': 'Rust', 'kotlin': 'Kotlin', 'swift': 'Swift', 'php': 'PHP',
            'ruby': 'Ruby', 'scala': 'Scala', 'r': 'R',
            
            # Frontend
            'react': 'React', 'react.js': 'React', 'reactjs': 'React',
            'vue': 'Vue.js', 'vue.js': 'Vue.js', 'angular': 'Angular',
            'html': 'HTML', 'css': 'CSS', 'sass': 'SASS', 'scss': 'SCSS',
            'tailwind': 'Tailwind CSS', 'bootstrap': 'Bootstrap',
            'next.js': 'Next.js', 'nextjs': 'Next.js',
            
            # Backend
            'node.js': 'Node.js', 'nodejs': 'Node.js', 'node': 'Node.js',
            'express': 'Express.js', 'express.js': 'Express.js',
            'django': 'Django', 'flask': 'Flask', 'fastapi': 'FastAPI',
            'spring': 'Spring Boot', 'spring boot': 'Spring Boot',
            
            # Databases
            'mongodb': 'MongoDB', 'mysql': 'MySQL', 'postgresql': 'PostgreSQL',
            'postgres': 'PostgreSQL', 'redis': 'Redis', 'cassandra': 'Cassandra',
            'dynamodb': 'DynamoDB', 'sql': 'SQL', 'nosql': 'NoSQL',
            
            # Cloud & DevOps
            'aws': 'AWS', 'azure': 'Azure', 'gcp': 'Google Cloud', 
            'google cloud': 'Google Cloud', 'docker': 'Docker',
            'kubernetes': 'Kubernetes', 'k8s': 'Kubernetes',
            'jenkins': 'Jenkins', 'ci/cd': 'CI/CD', 'terraform': 'Terraform',
            'ansible': 'Ansible', 'git': 'Git', 'github': 'GitHub',
            'gitlab': 'GitLab', 'bitbucket': 'Bitbucket',
            
            # Testing
            'jest': 'Jest', 'mocha': 'Mocha', 'junit': 'JUnit',
            'pytest': 'PyTest', 'selenium': 'Selenium', 'cypress': 'Cypress',
            
            # Others
            'graphql': 'GraphQL', 'rest': 'REST API', 'restful': 'RESTful API',
            'api': 'API Development', 'microservices': 'Microservices',
            'agile': 'Agile', 'scrum': 'Scrum', 'jira': 'Jira',
            'kafka': 'Apache Kafka', 'rabbitmq': 'RabbitMQ',
            'elasticsearch': 'Elasticsearch', 'redis': 'Redis',
        }
        
        description_lower = job_description.lower()
        found_skills = set()
        
        # Extract skills based on patterns
        for pattern, skill_name in skill_patterns.items():
            if pattern in description_lower:
                found_skills.add(skill_name)
        
        # Convert to list and categorize
        all_skills = list(found_skills)
        
        # Try to categorize based on context
        required_skills = []
        preferred_skills = []
        
        # Split description into sections
        lines = job_description.split('\n')
        current_section = 'required'  # Default to required
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if this line indicates a section change
            if any(keyword in line_lower for keyword in ['required', 'must have', 'mandatory', 'essential', 'qualifications']):
                current_section = 'required'
            elif any(keyword in line_lower for keyword in ['preferred', 'nice to have', 'plus', 'bonus', 'desirable']):
                current_section = 'preferred'
            
            # Extract skills from this line
            for pattern, skill_name in skill_patterns.items():
                if pattern in line_lower and skill_name in all_skills:
                    if current_section == 'required':
                        required_skills.append(skill_name)
                    else:
                        preferred_skills.append(skill_name)
        
        # Remove duplicates while preserving order
        required_skills = list(dict.fromkeys(required_skills))
        preferred_skills = list(dict.fromkeys(preferred_skills))
        
        # Remove preferred skills that are already in required
        preferred_skills = [s for s in preferred_skills if s not in required_skills]
        
        # If we couldn't categorize, put all in required (as per user's request)
        if not required_skills and not preferred_skills:
            required_skills = all_skills
        
        # Apply skill limits: max 7 required, max 7 preferred, max 15 total
        original_required = len(required_skills)
        original_preferred = len(preferred_skills)
        
        if len(required_skills) > 7:
            logger.warning(f"⚠️ Fallback: Required skills ({len(required_skills)}) exceeds limit. Trimming to 7.")
            required_skills = required_skills[:7]
        
        if len(preferred_skills) > 7:
            logger.warning(f"⚠️ Fallback: Preferred skills ({len(preferred_skills)}) exceeds limit. Trimming to 7.")
            preferred_skills = preferred_skills[:7]
        
        total = len(required_skills) + len(preferred_skills)
        if total > 15:
            available = 15 - len(required_skills)
            logger.warning(f"⚠️ Fallback: Total skills ({total}) exceeds 15. Trimming preferred to {available}.")
            preferred_skills = preferred_skills[:available]
        
        result = {
            'required_skills': required_skills,
            'preferred_skills': preferred_skills
        }
        
        final_required = len(required_skills)
        final_preferred = len(preferred_skills)
        if original_required != final_required or original_preferred != final_preferred:
            logger.info(f"📊 Fallback skills adjusted: Required {original_required}→{final_required}, Preferred {original_preferred}→{final_preferred}")
        
        logger.info(f"✅ Fallback extracted {final_required} required skills and {final_preferred} preferred skills")
        return result
    
    def validate_and_enhance_skills(
        self, 
        required_skills: List[str], 
        preferred_skills: List[str]
    ) -> Dict[str, List[str]]:
        """
        Validate and enhance skill lists using Gemini AI
        - Normalize skill names
        - Remove duplicates
        - Categorize properly
        
        Args:
            required_skills: List of required skills (possibly user-edited)
            preferred_skills: List of preferred skills (possibly user-edited)
            
        Returns:
            Dictionary with validated and enhanced skill lists
        """
        prompt = f"""
You are an expert technical skill validator. Review and normalize these skill lists:

REQUIRED SKILLS:
{json.dumps(required_skills)}

PREFERRED SKILLS:
{json.dumps(preferred_skills)}

Tasks:
1. Normalize skill names (e.g., "react.js" → "React", "nodejs" → "Node.js")
2. Remove exact duplicates (case-insensitive)
3. If a skill appears in both lists, keep it ONLY in required_skills
4. Fix common misspellings
5. Merge similar skills (e.g., "JavaScript" and "JS" → "JavaScript")
6. Keep the lists concise but complete

Return ONLY valid JSON in this exact format:
{{
  "required_skills": ["skill1", "skill2", ...],
  "preferred_skills": ["skill1", "skill2", ...]
}}

Return ONLY the JSON object, no markdown, no explanation.
"""
        
        try:
            logger.info("📤 Validating and enhancing skills...")
            
            result_text = self.key_manager.generate_content(
                prompt=prompt,
                model="gemini-2.5-flash",
                purpose="skill_validation",
                temperature=0.1,
                max_output_tokens=1500,
                max_retries=3
            )
            
            # Clean up markdown
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'^```\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            result_text = result_text.strip()
            
            validated_data = json.loads(result_text)
            
            logger.info("✅ Skills validated and enhanced")
            return validated_data
            
        except Exception as e:
            logger.error(f"  Error validating skills: {e}")
            # Return original data on error
            return {
                'required_skills': required_skills,
                'preferred_skills': preferred_skills
            }


# Singleton instance
_job_description_analyzer = None

def get_job_description_analyzer() -> JobDescriptionAnalyzer:
    """Get singleton instance of JobDescriptionAnalyzer"""
    global _job_description_analyzer
    if _job_description_analyzer is None:
        _job_description_analyzer = JobDescriptionAnalyzer()
    return _job_description_analyzer
