"""
Migration Script: Upload existing local resumes to S3
This script migrates all resumes from local storage to AWS S3
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database.connection import SessionLocal
from app.models import Resume
from app.services.s3_service import s3_service


def migrate_resumes_to_s3():
    """Upload all existing local resumes to S3"""
    
    if not s3_service.is_enabled():
        print("  S3 service is not enabled. Please configure AWS credentials in .env file.")
        print("Required environment variables:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_S3_BUCKET_NAME")
        print("  - AWS_REGION (optional, defaults to us-east-1)")
        return
    
    db = SessionLocal()
    
    try:
        print("🔄 Starting migration: Upload local resumes to S3")
        print("=" * 60)
        
        # Get all resumes that don't have S3 keys yet
        resumes = db.query(Resume).filter(
            (Resume.s3_key == None) | (Resume.s3_key == '')
        ).all()
        
        if not resumes:
            print("✅ No resumes to migrate. All resumes already in S3.")
            return
        
        print(f"📊 Found {len(resumes)} resumes to migrate")
        print()
        
        success_count = 0
        error_count = 0
        
        for i, resume in enumerate(resumes, 1):
            print(f"[{i}/{len(resumes)}] Processing resume ID {resume.id}...")
            
            # Check if local file exists
            if not os.path.exists(resume.file_path):
                print(f"  ⚠️  Local file not found: {resume.file_path}")
                error_count += 1
                continue
            
            # Upload to S3
            s3_key = s3_service.upload_resume(
                file_path=resume.file_path,
                student_id=resume.student_id,
                file_name=resume.file_name,
                is_tailored=bool(resume.is_tailored),
                internship_id=resume.tailored_for_internship_id
            )
            
            if s3_key:
                # Update database with S3 key
                resume.s3_key = s3_key
                db.commit()
                print(f"  ✅ Uploaded to S3: {s3_key}")
                success_count += 1
            else:
                print(f"    Failed to upload to S3")
                error_count += 1
            
            print()
        
        print("=" * 60)
        print(f"🎉 Migration completed!")
        print(f"  ✅ Successful uploads: {success_count}")
        print(f"    Failed uploads: {error_count}")
        print()
        
        if success_count > 0:
            print("📝 Next steps:")
            print("  1. Verify uploaded files in AWS S3 console")
            print("  2. Test resume access through the application")
            print("  3. Keep local files as backup until fully tested")
            print("  4. Consider adding a cleanup script to remove local files after verification")
        
    except Exception as e:
        db.rollback()
        print(f"  Migration failed: {str(e)}")
        raise
    finally:
        db.close()


def verify_s3_migration():
    """Verify S3 migration status"""
    db = SessionLocal()
    
    try:
        total = db.query(Resume).count()
        with_s3 = db.query(Resume).filter(
            Resume.s3_key != None,
            Resume.s3_key != ''
        ).count()
        without_s3 = total - with_s3
        
        print("📊 S3 Migration Status")
        print("=" * 60)
        print(f"  Total resumes: {total}")
        print(f"  ✅ Migrated to S3: {with_s3} ({with_s3/total*100:.1f}%)")
        print(f"  ⏳ Still local only: {without_s3} ({without_s3/total*100:.1f}%)")
        print("=" * 60)
        
    except Exception as e:
        print(f"  Verification failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate resumes to S3")
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration status without uploading'
    )
    
    args = parser.parse_args()
    
    if args.verify:
        verify_s3_migration()
    else:
        migrate_resumes_to_s3()
