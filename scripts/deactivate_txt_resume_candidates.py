"""
Script to deactivate all candidates whose resumes are .txt files
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, engine
from app.models.resume import Resume
from app.models.user import User


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


def deactivate_txt_resume_candidates():
    """
    Find all candidates whose active resumes are .txt files and mark them as inactive
    """
    db = get_db()
    
    try:
        print("=" * 80)
        print("DEACTIVATING CANDIDATES WITH .TXT RESUMES")
        print("=" * 80)
        print()
        
        # Find all active resumes with .txt extension
        txt_resumes = db.query(Resume).filter(
            Resume.is_active == 1,
            Resume.file_name.like('%.txt')
        ).all()
        
        print(f"Found {len(txt_resumes)} active .txt resumes")
        print()
        
        if not txt_resumes:
            print("No .txt resumes found. Nothing to do.")
            return
        
        # Get unique student IDs from these resumes
        student_ids = list(set([resume.student_id for resume in txt_resumes]))
        
        print(f"Candidates to deactivate: {len(student_ids)}")
        print("-" * 80)
        
        deactivated_count = 0
        
        for student_id in student_ids:
            # Get the user
            user = db.query(User).filter(User.id == student_id).first()
            
            if user:
                # Get their active .txt resume(s)
                user_txt_resumes = [r for r in txt_resumes if r.student_id == student_id]
                resume_names = [r.file_name for r in user_txt_resumes]
                
                print(f"\n📋 Student ID: {student_id}")
                print(f"   Name: {user.full_name}")
                print(f"   Email: {user.email}")
                print(f"   Current Status: {'Active' if user.is_active == 1 else 'Inactive'}")
                print(f"   .txt Resume(s): {', '.join(resume_names)}")
                
                # Deactivate the user
                if user.is_active == 1:
                    user.is_active = 0
                    deactivated_count += 1
                    print(f"   ✅ Status changed to: Inactive")
                else:
                    print(f"   ℹ️  Already inactive")
        
        # Commit all changes
        db.commit()
        
        print()
        print("=" * 80)
        print(f"✅ DEACTIVATION COMPLETE")
        print(f"Total candidates deactivated: {deactivated_count}")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error occurred: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    deactivate_txt_resume_candidates()
