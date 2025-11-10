"""
Test script for Candidate Flagging Service
Tests the detection of duplicate candidates based on mobile number, LinkedIn, and GitHub URLs
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import SessionLocal
from app.models.user import User, UserRole
from app.services.candidate_flagging_service import CandidateFlaggingService


def test_url_normalization():
    """Test URL normalization function"""
    print("=" * 80)
    print("Testing URL Normalization")
    print("=" * 80)
    
    test_cases = [
        ("https://www.linkedin.com/in/john-doe/", "linkedin.com/in/john-doe"),
        ("http://linkedin.com/in/john-doe", "linkedin.com/in/john-doe"),
        ("www.linkedin.com/in/john-doe/", "linkedin.com/in/john-doe"),
        ("linkedin.com/in/john-doe", "linkedin.com/in/john-doe"),
        ("HTTPS://WWW.GITHUB.COM/JOHNDOE", "github.com/johndoe"),
        ("github.com/johndoe/", "github.com/johndoe"),
    ]
    
    for input_url, expected in test_cases:
        result = CandidateFlaggingService.normalize_url(input_url)
        status = "✅ PASS" if result == expected else "  FAIL"
        print(f"{status}: '{input_url}' -> '{result}' (expected: '{expected}')")
    
    print()


def test_phone_normalization():
    """Test phone number normalization function"""
    print("=" * 80)
    print("Testing Phone Number Normalization")
    print("=" * 80)
    
    test_cases = [
        ("+1 (555) 123-4567", "15551234567"),
        ("555-123-4567", "5551234567"),
        ("555.123.4567", "5551234567"),
        ("(555) 123 4567", "5551234567"),
        ("+91 98765 43210", "919876543210"),
        ("555 123 4567", "5551234567"),
    ]
    
    for input_phone, expected in test_cases:
        result = CandidateFlaggingService.normalize_phone(input_phone)
        status = "✅ PASS" if result == expected else "  FAIL"
        print(f"{status}: '{input_phone}' -> '{result}' (expected: '{expected}')")
    
    print()


def test_duplicate_detection():
    """Test duplicate candidate detection in database"""
    print("=" * 80)
    print("Testing Duplicate Candidate Detection")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        from app.models.resume import Resume
        
        # Get all students
        all_students = db.query(User).filter(User.role == UserRole.student).all()
        print(f"📊 Total students in database: {len(all_students)}")
        
        # Get students with resumes
        students_with_resumes = db.query(User.id).join(
            Resume, Resume.student_id == User.id
        ).filter(
            User.role == UserRole.student,
            Resume.is_active == 1
        ).distinct().all()
        
        print(f"📄 Students with uploaded resumes: {len(students_with_resumes)}")
        print(f"ℹ️  Note: Only students with resumes will be checked for duplicates")
        print()
        
        # Detect flagged candidates
        flagged_candidates = CandidateFlaggingService.detect_flagged_candidates(db)
        
        print(f"🚩 Total flagged candidates: {len(flagged_candidates)}")
        print()
        
        if len(flagged_candidates) == 0:
            print("✅ No duplicate candidates found. All candidates have unique contact information.")
        else:
            print("⚠️ Flagged candidates details:")
            print("-" * 80)
            
            for student_id, flag_info in flagged_candidates.items():
                # Get student details
                student = db.query(User).filter(User.id == student_id).first()
                if not student:
                    continue
                
                print(f"\n🚨 Student ID: {student_id} - {student.full_name}")
                print(f"   Email: {student.email}")
                print(f"   Reasons: {', '.join(flag_info['reasons'])}")
                
                for reason, flagged_with_ids in flag_info['flagged_with'].items():
                    print(f"\n   {reason.upper()}:")
                    if reason == 'same_mobile':
                        print(f"      Phone: {student.phone}")
                    elif reason == 'same_linkedin':
                        print(f"      LinkedIn: {student.linkedin_url}")
                    elif reason == 'same_github':
                        print(f"      GitHub: {student.github_url}")
                    
                    print(f"      Flagged with ({len(flagged_with_ids)} candidates):")
                    for flagged_id in flagged_with_ids:
                        flagged_student = db.query(User).filter(User.id == flagged_id).first()
                        if flagged_student:
                            print(f"         - ID {flagged_id}: {flagged_student.full_name} ({flagged_student.email})")
                
                print()
                print("-" * 80)
        
        # Test format_flag_reason
        print("\n" + "=" * 80)
        print("Testing Flag Reason Formatting")
        print("=" * 80)
        
        test_reasons = [
            ['same_mobile'],
            ['same_linkedin'],
            ['same_mobile', 'same_linkedin'],
            ['same_mobile', 'same_linkedin', 'same_github'],
        ]
        
        for reasons in test_reasons:
            formatted = CandidateFlaggingService.format_flag_reason(reasons)
            print(f"{reasons} -> '{formatted}'")
        
    finally:
        db.close()


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CANDIDATE FLAGGING SERVICE - TEST SUITE")
    print("=" * 80)
    print()
    
    # Test URL normalization
    test_url_normalization()
    
    # Test phone normalization
    test_phone_normalization()
    
    # Test duplicate detection
    test_duplicate_detection()
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
