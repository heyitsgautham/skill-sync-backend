"""
Resume Parser Service - Extract text and metadata from PDF/DOCX/TXT files
"""

import os
import re
from typing import Dict, List, Optional
import fitz  # PyMuPDF
from docx import Document
import pdfplumber


class ResumeParser:
    """Service for parsing resumes and extracting information"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """
        Extract text from DOCX file
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """
        Extract text from TXT file
        
        Args:
            file_path: Path to the TXT file
            
        Returns:
            Extracted text content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from TXT: {str(e)}")
    
    @staticmethod
    def parse_resume(file_path: str) -> Dict[str, any]:
        """
        Parse resume file and extract text content
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary containing parsed content and metadata
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            text = ResumeParser.extract_text_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            text = ResumeParser.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            text = ResumeParser.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Extract basic information
        skills = ResumeParser.extract_skills(text)
        
        return {
            "parsed_content": text,
            "extracted_skills": skills,
            "file_type": file_extension
        }
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """
        Extract skills from resume text using pattern matching
        
        Args:
            text: Resume text content
            
        Returns:
            List of extracted skills
        """
        # Common technical skills to look for
        skill_patterns = [
            r'\b(python|java|javascript|typescript|c\+\+|c#|ruby|php|swift|kotlin|go|rust)\b',
            r'\b(react|angular|vue|node\.?js|express|django|flask|spring|\.net)\b',
            r'\b(sql|nosql|mongodb|postgresql|mysql|redis|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|git|ci/cd)\b',
            r'\b(machine learning|ml|ai|deep learning|nlp|computer vision)\b',
            r'\b(html|css|sass|tailwind|bootstrap)\b',
            r'\b(rest api|graphql|microservices|agile|scrum)\b',
        ]
        
        skills = set()
        text_lower = text.lower()
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                skill = match.group(0).strip()
                skills.add(skill)
        
        # Look for skills section
        skills_section_pattern = r'(?:skills|technical skills|core competencies)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?:\n\n|\n[A-Z]|$)'
        skills_match = re.search(skills_section_pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if skills_match:
            skills_text = skills_match.group(1)
            # Split by common delimiters
            skill_items = re.split(r'[,;•·\|\n]', skills_text)
            for item in skill_items:
                item = item.strip()
                if item and len(item) > 2 and len(item) < 50:
                    skills.add(item.lower())
        
        return list(skills)[:50]  # Limit to 50 skills


class InternshipParser:
    """Service for parsing internship descriptions"""
    
    @staticmethod
    def extract_skills_from_description(description: str) -> List[str]:
        """
        Extract required skills from internship description
        
        Args:
            description: Internship description text
            
        Returns:
            List of required skills
        """
        return ResumeParser.extract_skills(description)
    
    @staticmethod
    def parse_internship(data: Dict) -> Dict[str, any]:
        """
        Parse internship posting data
        
        Args:
            data: Dictionary containing internship data
            
        Returns:
            Dictionary with parsed and enriched data
        """
        description = data.get('description', '')
        
        # Extract skills if not provided
        if not data.get('required_skills'):
            skills = InternshipParser.extract_skills_from_description(description)
            data['required_skills'] = skills
        
        return data
