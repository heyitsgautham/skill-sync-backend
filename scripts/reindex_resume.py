"""
Reindex a specific resume - parse it and create embeddings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.models import Resume
from app.services.parser_service import ResumeParser
from app.services.rag_engine import rag_engine

def reindex_resume(resume_id: int):
    """Reindex a single resume"""
    db = SessionLocal()
    try:
        # Get resume
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume:
            print(f"❌ Resume {resume_id} not found")
            return
        
        print(f"\n📄 Reindexing Resume {resume_id}:")
        print(f"   File: {resume.file_name}")
        print(f"   Path: {resume.file_path}")
        print(f"   Student ID: {resume.student_id}")
        
        # Check if file exists
        if not os.path.exists(resume.file_path):
            print(f"❌ Resume file not found at: {resume.file_path}")
            return
        
        # Parse resume if not already parsed
        if not resume.parsed_content or not resume.extracted_skills:
            print("   Parsing resume...")
            try:
                parsed_data = ResumeParser.parse_resume(resume.file_path)
                resume.parsed_content = parsed_data['parsed_content']
                resume.extracted_skills = parsed_data['extracted_skills']
                print(f"   ✅ Parsed! Extracted {len(parsed_data['extracted_skills'])} skills")
            except Exception as e:
                print(f"   ❌ Parsing failed: {str(e)}")
                return
        else:
            print(f"   ✅ Already parsed ({len(resume.extracted_skills)} skills)")
        
        # Store embedding in vector DB
        if not resume.embedding_id:
            print("   Creating embedding...")
            try:
                embedding_id = rag_engine.store_resume_embedding(
                    resume_id=str(resume.id),
                    content=resume.parsed_content,
                    skills=resume.extracted_skills,
                    metadata={
                        "student_id": resume.student_id,
                        "file_name": resume.file_name
                    }
                )
                resume.embedding_id = embedding_id
                print(f"   ✅ Embedding created: {embedding_id}")
            except Exception as e:
                print(f"   ❌ Embedding creation failed: {str(e)}")
                return
        else:
            print(f"   ✅ Embedding already exists: {resume.embedding_id}")
        
        # Save changes
        db.commit()
        print(f"\n✅ Resume {resume_id} successfully reindexed!\n")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

def reindex_all_student_resumes(student_id: int):
    """Reindex all resumes for a student"""
    db = SessionLocal()
    try:
        resumes = db.query(Resume).filter(Resume.student_id == student_id).all()
        print(f"\nFound {len(resumes)} resumes for student {student_id}")
        
        for resume in resumes:
            reindex_resume(resume.id)
            
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "student":
            student_id = int(sys.argv[2])
            print(f"Reindexing all resumes for student {student_id}...")
            reindex_all_student_resumes(student_id)
        else:
            resume_id = int(sys.argv[1])
            reindex_resume(resume_id)
    else:
        print("Usage:")
        print("  python scripts/reindex_resume.py <resume_id>")
        print("  python scripts/reindex_resume.py student <student_id>")
        print("\nExample:")
        print("  python scripts/reindex_resume.py 63")
        print("  python scripts/reindex_resume.py student 4")
