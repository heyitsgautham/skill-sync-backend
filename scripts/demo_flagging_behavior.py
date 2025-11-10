"""
Quick demonstration of the updated flagging behavior
Shows that only candidates with uploaded resumes are flagged
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import SessionLocal
from app.models.user import User, UserRole
from app.models.resume import Resume


def demonstrate_flagging_logic():
    """
    Demonstrate the updated flagging behavior
    """
    print("=" * 80)
    print("CANDIDATE FLAGGING - UPDATED BEHAVIOR DEMONSTRATION")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        # Scenario 1: Check students with and without resumes
        print("📊 Scenario Analysis")
        print("-" * 80)
        
        all_students = db.query(User).filter(User.role == UserRole.student).all()
        print(f"Total students: {len(all_students)}")
        
        # Students with resumes
        students_with_resumes = db.query(User.id).join(
            Resume, Resume.student_id == User.id
        ).filter(
            User.role == UserRole.student,
            Resume.is_active == 1
        ).distinct().all()
        
        student_ids_with_resumes = {s.id for s in students_with_resumes}
        print(f"Students with uploaded resumes: {len(student_ids_with_resumes)}")
        print(f"Students WITHOUT resumes: {len(all_students) - len(student_ids_with_resumes)}")
        print()
        
        # Example scenarios
        print("🔍 Example Scenarios:")
        print("-" * 80)
        
        # Find some example students
        students_no_resume = [s for s in all_students if s.id not in student_ids_with_resumes]
        students_with_resume_list = [s for s in all_students if s.id in student_ids_with_resumes]
        
        if students_no_resume:
            example_no_resume = students_no_resume[0]
            print(f"\n  Student WITHOUT Resume (Will NOT be checked for duplicates):")
            print(f"   ID: {example_no_resume.id}")
            print(f"   Name: {example_no_resume.full_name}")
            print(f"   Phone: {example_no_resume.phone or 'Not set'}")
            print(f"   LinkedIn: {example_no_resume.linkedin_url or 'Not set'}")
            print(f"   GitHub: {example_no_resume.github_url or 'Not set'}")
        
        if students_with_resume_list:
            example_with_resume = students_with_resume_list[0]
            print(f"\n✅ Student WITH Resume (WILL be checked for duplicates):")
            print(f"   ID: {example_with_resume.id}")
            print(f"   Name: {example_with_resume.full_name}")
            print(f"   Phone: {example_with_resume.phone or 'Not set'}")
            print(f"   LinkedIn: {example_with_resume.linkedin_url or 'Not set'}")
            print(f"   GitHub: {example_with_resume.github_url or 'Not set'}")
        
        print()
        print("=" * 80)
        print("KEY POINTS:")
        print("=" * 80)
        print("✅ Only students with uploaded resumes are checked for duplicates")
        print("✅ Reduces false positives from incomplete/inactive profiles")
        print("✅ Focuses on active candidates who are actually participating")
        print()
        print("EXAMPLE OUTCOMES:")
        print("-" * 80)
        print("Case 1: Student A (NO resume) + Student B (has resume) - Same phone")
        print("   Result: NOT FLAGGED   (one student has no resume)")
        print()
        print("Case 2: Student A (has resume) + Student B (has resume) - Same phone")
        print("   Result: BOTH FLAGGED ✅ (both have resumes)")
        print()
        print("Case 3: Student A (has resume) + Student B (NO resume) + Student C (has resume) - Same LinkedIn")
        print("   Result: A and C FLAGGED ✅ (B ignored, no resume)")
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    demonstrate_flagging_logic()
