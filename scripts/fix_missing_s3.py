"""
Quick Fix Script - Upload Missing Resumes to S3
This script fixes resumes that have local files but no S3 keys
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database.connection import SessionLocal
from app.models import Resume
from app.services.s3_service import s3_service
import os


def fix_missing_s3_uploads(student_name=None):
    """
    Fix resumes that have local files but no S3 keys
    
    Args:
        student_name: Optional student name to fix specific student
    """
    db = SessionLocal()
    
    try:
        print("🔍 Searching for resumes without S3 keys...")
        print("=" * 70)
        
        # Query resumes without S3 keys
        query = db.query(Resume).filter(
            (Resume.s3_key == None) | (Resume.s3_key == '')
        )
        
        # Filter by student name if provided
        if student_name:
            from app.models import User
            user = db.query(User).filter(
                User.full_name.ilike(f'%{student_name}%')
            ).first()
            
            if not user:
                print(f"  User '{student_name}' not found")
                return
            
            query = query.filter(Resume.student_id == user.id)
            print(f"🎯 Filtering for student: {user.full_name} (ID: {user.id})")
        
        resumes = query.all()
        
        if not resumes:
            print("✅ No resumes need fixing. All resumes have S3 keys!")
            return
        
        print(f"📋 Found {len(resumes)} resume(s) to fix\n")
        
        fixed_count = 0
        missing_file_count = 0
        failed_count = 0
        
        for i, resume in enumerate(resumes, 1):
            print(f"[{i}/{len(resumes)}] Processing Resume ID {resume.id}")
            print(f"  Student ID: {resume.student_id}")
            print(f"  File: {resume.file_name}")
            
            # Check if local file exists
            if not os.path.exists(resume.file_path):
                print(f"  ⚠️  Local file not found: {resume.file_path}")
                print(f"  ⏭️  Skipping...")
                missing_file_count += 1
                print()
                continue
            
            file_size = os.path.getsize(resume.file_path) / 1024
            print(f"  Size: {file_size:.2f} KB")
            
            # Upload to S3
            print(f"  📤 Uploading to S3...")
            s3_key = s3_service.upload_resume(
                file_path=resume.file_path,
                student_id=resume.student_id,
                file_name=resume.file_name,
                is_tailored=bool(resume.is_tailored),
                internship_id=resume.tailored_for_internship_id
            )
            
            if s3_key:
                # Update database
                resume.s3_key = s3_key
                db.commit()
                
                print(f"  ✅ SUCCESS! Uploaded to: {s3_key}")
                
                # Test URL generation
                url = s3_service.generate_presigned_url(s3_key)
                if url:
                    print(f"  🔗 URL: {url[:70]}...")
                
                fixed_count += 1
            else:
                print(f"    Failed to upload to S3")
                failed_count += 1
            
            print()
        
        print("=" * 70)
        print("🎉 Fix Completed!")
        print("=" * 70)
        print(f"  ✅ Fixed: {fixed_count}")
        print(f"    Failed: {failed_count}")
        print(f"  ⚠️  Missing files: {missing_file_count}")
        print("=" * 70)
        
        if fixed_count > 0:
            print("\n✅ Resumes can now be viewed by HR in AI Candidate Ranking!")
        
    except Exception as e:
        db.rollback()
        print(f"  Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fix resumes with missing S3 uploads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/fix_missing_s3.py                    # Fix all resumes
  python scripts/fix_missing_s3.py --student surya    # Fix specific student
  python scripts/fix_missing_s3.py --student "John"   # Fix by partial name match
        """
    )
    
    parser.add_argument(
        '--student',
        type=str,
        help='Student name to fix (case-insensitive partial match)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("   SkillSync - S3 Resume Fix Utility")
    print("=" * 70 + "\n")
    
    fix_missing_s3_uploads(student_name=args.student)
