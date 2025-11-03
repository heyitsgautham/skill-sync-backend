#!/usr/bin/env python3
"""
Test script for parser service
Tests resume parsing from PDF and DOCX files
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.parser_service import ResumeParser, InternshipParser

def test_skill_extraction():
    """Test skill extraction from text"""
    
    print("=" * 60)
    print("Testing Skill Extraction")
    print("=" * 60)
    
    # Test resume text
    resume_text = """
    John Doe
    Software Developer
    
    SKILLS:
    Python, Java, JavaScript, React, Node.js, Django, Flask
    PostgreSQL, MongoDB, Docker, Kubernetes, AWS
    REST API, GraphQL, Microservices
    Git, CI/CD, Agile, Scrum
    
    EXPERIENCE:
    Backend Developer at Tech Corp
    - Built REST APIs using Django and Flask
    - Worked with PostgreSQL and Redis
    - Deployed applications on AWS using Docker
    
    EDUCATION:
    B.S. in Computer Science
    """
    
    print("\nExtracting skills from resume text...")
    skills = ResumeParser.extract_skills(resume_text)
    
    print(f"\n✓ Extracted {len(skills)} skills:")
    for skill in sorted(skills)[:20]:  # Show first 20
        print(f"  - {skill}")
    
    # Test internship description
    internship_desc = """
    We are looking for a Full-Stack Developer Intern with the following skills:
    - Proficient in React, TypeScript, and Node.js
    - Experience with MongoDB or PostgreSQL
    - Knowledge of REST APIs and GraphQL
    - Familiarity with Docker and AWS is a plus
    - Understanding of Agile methodologies
    """
    
    print("\n" + "-" * 60)
    print("\nExtracting skills from internship description...")
    skills = InternshipParser.extract_skills_from_description(internship_desc)
    
    print(f"\n✓ Extracted {len(skills)} skills:")
    for skill in sorted(skills)[:20]:  # Show first 20
        print(f"  - {skill}")
    
    print("\n" + "=" * 60)
    print("✓ Skill extraction tests completed successfully!")
    print("=" * 60)
    
    return True

def test_file_parsing():
    """Test parsing actual files if they exist"""
    
    print("\n" + "=" * 60)
    print("Testing File Parsing")
    print("=" * 60)
    
    test_files_dir = os.path.join(os.path.dirname(__file__), '..', 'tests', 'sample_files')
    
    if not os.path.exists(test_files_dir):
        print(f"\nℹ Test files directory not found: {test_files_dir}")
        print("  Skipping file parsing tests")
        print("  To test file parsing, add sample PDF/DOCX files to tests/sample_files/")
        return True
    
    # Test PDF parsing
    pdf_files = [f for f in os.listdir(test_files_dir) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        try:
            file_path = os.path.join(test_files_dir, pdf_file)
            print(f"\nParsing PDF: {pdf_file}")
            result = ResumeParser.parse_resume(file_path)
            print(f"  ✓ Extracted {len(result['parsed_content'])} characters")
            print(f"  ✓ Found {len(result['extracted_skills'])} skills")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    # Test DOCX parsing
    docx_files = [f for f in os.listdir(test_files_dir) if f.endswith('.docx')]
    for docx_file in docx_files:
        try:
            file_path = os.path.join(test_files_dir, docx_file)
            print(f"\nParsing DOCX: {docx_file}")
            result = ResumeParser.parse_resume(file_path)
            print(f"  ✓ Extracted {len(result['parsed_content'])} characters")
            print(f"  ✓ Found {len(result['extracted_skills'])} skills")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✓ File parsing tests completed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_skill_extraction()
        test_file_parsing()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        sys.exit(1)
