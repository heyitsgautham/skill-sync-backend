"""
Check resume 62 in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.models import Resume

def check_resume():
    db = SessionLocal()
    try:
        # Get resume 62
        resume = db.query(Resume).filter(Resume.id == 62).first()
        
        if resume:
            print(f"Resume 62 found:")
            print(f"  ID: {resume.id}")
            print(f"  Resume ID (UUID): {resume.resume_id}")
            print(f"  Student ID: {resume.student_id}")
            print(f"  File name: {resume.file_name}")
            print(f"  Is active: {resume.is_active}")
            print(f"  Embedding ID: {resume.embedding_id}")
            print(f"  Has parsed content: {resume.parsed_content is not None}")
            print(f"  Has extracted skills: {resume.extracted_skills is not None}")
            if resume.extracted_skills:
                print(f"  Skills: {resume.extracted_skills[:5]}...")
        else:
            print("Resume 62 not found in database")
            
        # Check all resumes for your student
        print("\n\nAll resumes in database (showing last 10):")
        all_resumes = db.query(Resume).order_by(Resume.id.desc()).limit(10).all()
        for r in all_resumes:
            print(f"  Resume {r.id}: student_id={r.student_id}, is_active={r.is_active}, embedding_id={r.embedding_id}, file={r.file_name}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_resume()
