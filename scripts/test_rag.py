#!/usr/bin/env python3
"""
Test script for RAG engine functionality
Tests resume and internship embedding storage and matching
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rag_engine import rag_engine

def test_rag_engine():
    """Test RAG engine with dummy data"""
    
    print("=" * 60)
    print("Testing RAG Engine")
    print("=" * 60)
    
    # Test 1: Store resume embeddings
    print("\n1. Storing resume embeddings...")
    
    resume_1 = {
        "id": "test_1",
        "content": "Experienced Python developer with expertise in Django, Flask, and REST APIs. Strong knowledge of SQL databases, Docker, and AWS. Built multiple web applications.",
        "skills": ["python", "django", "flask", "sql", "docker", "aws", "rest api"]
    }
    
    resume_2 = {
        "id": "test_2",
        "content": "Frontend developer specializing in React, TypeScript, and modern web technologies. Experience with Redux, Next.js, and responsive design. Strong CSS skills.",
        "skills": ["react", "typescript", "javascript", "redux", "nextjs", "css", "html"]
    }
    
    resume_3 = {
        "id": "test_3",
        "content": "Full-stack Java developer with Spring Boot experience. Knowledge of microservices, Hibernate, and PostgreSQL. Familiar with CI/CD and Jenkins.",
        "skills": ["java", "spring", "spring boot", "microservices", "postgresql", "jenkins"]
    }
    
    try:
        rag_engine.store_resume_embedding(
            resume_id=resume_1["id"],
            content=resume_1["content"],
            skills=resume_1["skills"]
        )
        print(f"  ✓ Stored resume {resume_1['id']}")
        
        rag_engine.store_resume_embedding(
            resume_id=resume_2["id"],
            content=resume_2["content"],
            skills=resume_2["skills"]
        )
        print(f"  ✓ Stored resume {resume_2['id']}")
        
        rag_engine.store_resume_embedding(
            resume_id=resume_3["id"],
            content=resume_3["content"],
            skills=resume_3["skills"]
        )
        print(f"  ✓ Stored resume {resume_3['id']}")
        
    except Exception as e:
        print(f"  ✗ Error storing resumes: {str(e)}")
        return False
    
    # Test 2: Store internship embeddings
    print("\n2. Storing internship embeddings...")
    
    internship_1 = {
        "id": "intern_1",
        "title": "Backend Python Developer Intern",
        "description": "Looking for a Python developer intern with experience in Django/Flask. Must know REST APIs, SQL, and have basic AWS knowledge.",
        "skills": ["python", "django", "flask", "rest api", "sql", "aws"]
    }
    
    internship_2 = {
        "id": "intern_2",
        "title": "Frontend React Developer Intern",
        "description": "Seeking a React developer intern. Must be proficient in TypeScript, React, and modern frontend tools. Experience with Next.js is a plus.",
        "skills": ["react", "typescript", "javascript", "nextjs", "html", "css"]
    }
    
    try:
        rag_engine.store_internship_embedding(
            internship_id=internship_1["id"],
            title=internship_1["title"],
            description=internship_1["description"],
            required_skills=internship_1["skills"]
        )
        print(f"  ✓ Stored internship {internship_1['id']}")
        
        rag_engine.store_internship_embedding(
            internship_id=internship_2["id"],
            title=internship_2["title"],
            description=internship_2["description"],
            required_skills=internship_2["skills"]
        )
        print(f"  ✓ Stored internship {internship_2['id']}")
        
    except Exception as e:
        print(f"  ✗ Error storing internships: {str(e)}")
        return False
    
    # Test 3: Find matching internships for resume
    print("\n3. Finding matching internships for Python developer resume...")
    
    try:
        matches = rag_engine.find_matching_internships(resume_id=resume_1["id"], top_k=5)
        print(f"  Found {len(matches)} matches:")
        for match in matches:
            print(f"    - {match['title']} (Score: {match['match_score']})")
    except Exception as e:
        print(f"  ✗ Error finding matches: {str(e)}")
        return False
    
    # Test 4: Find matching candidates for internship
    print("\n4. Finding matching candidates for Backend Python internship...")
    
    try:
        matches = rag_engine.find_matching_candidates(internship_id=internship_1["id"], top_k=5)
        print(f"  Found {len(matches)} matches:")
        for match in matches:
            print(f"    - Resume {match['resume_id']} (Score: {match['match_score']})")
    except Exception as e:
        print(f"  ✗ Error finding matches: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ RAG Engine tests completed successfully!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_rag_engine()
    sys.exit(0 if success else 1)
