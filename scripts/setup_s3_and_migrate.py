"""
Complete S3 Setup and Migration Script
This script:
1. Verifies AWS S3 configuration
2. Tests S3 connectivity
3. Migrates all existing local resumes to S3
4. Provides detailed status and recommendations
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


def check_s3_configuration():
    """Check if S3 is properly configured"""
    print("🔍 Checking S3 Configuration")
    print("=" * 70)
    
    required_vars = {
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'AWS_S3_BUCKET_NAME': os.getenv('AWS_S3_BUCKET_NAME'),
        'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1')
    }
    
    missing = []
    for var, value in required_vars.items():
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'KEY' in var:
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                print(f"  ✅ {var}: {masked}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"    {var}: NOT SET")
            missing.append(var)
    
    print("=" * 70)
    
    if missing:
        print(f"\n  Missing required environment variables: {', '.join(missing)}")
        print("\n📝 To configure AWS S3:")
        print("1. Create/edit .env file in skill-sync-backend directory")
        print("2. Add the following variables:")
        print("   AWS_ACCESS_KEY_ID=your-access-key-id")
        print("   AWS_SECRET_ACCESS_KEY=your-secret-access-key")
        print("   AWS_S3_BUCKET_NAME=skillsync-resumes")
        print("   AWS_REGION=us-east-1")
        print("\n3. Get AWS credentials from: https://console.aws.amazon.com/iam/")
        return False
    
    return True


def test_s3_connectivity():
    """Test S3 connection and bucket access"""
    print("\n🔗 Testing S3 Connectivity")
    print("=" * 70)
    
    if not s3_service.is_enabled():
        print("  S3 service is not enabled")
        return False
    
    try:
        # Test by listing bucket (doesn't require any objects)
        s3_service.s3_client.head_bucket(Bucket=s3_service.bucket_name)
        print(f"✅ Successfully connected to S3 bucket: {s3_service.bucket_name}")
        print(f"✅ Region: {s3_service.aws_region}")
        return True
    except Exception as e:
        print(f"  Failed to connect to S3: {str(e)}")
        print("\n📝 Possible issues:")
        print("  - Incorrect AWS credentials")
        print("  - Bucket doesn't exist")
        print("  - Insufficient permissions")
        print("  - Incorrect region")
        return False


def get_migration_status():
    """Get current migration status"""
    db = SessionLocal()
    
    try:
        total = db.query(Resume).count()
        
        if total == 0:
            print("\n📊 Migration Status")
            print("=" * 70)
            print("  No resumes found in database")
            print("=" * 70)
            return 0, 0, 0
        
        with_s3 = db.query(Resume).filter(
            Resume.s3_key != None,
            Resume.s3_key != ''
        ).count()
        without_s3 = total - with_s3
        
        print("\n📊 Migration Status")
        print("=" * 70)
        print(f"  Total resumes: {total}")
        print(f"  ✅ Migrated to S3: {with_s3} ({with_s3/total*100:.1f}%)")
        print(f"  ⏳ Still local only: {without_s3} ({without_s3/total*100:.1f}%)")
        print("=" * 70)
        
        return total, with_s3, without_s3
        
    except Exception as e:
        print(f"  Failed to check migration status: {str(e)}")
        return 0, 0, 0
    finally:
        db.close()


def migrate_resumes_to_s3(force=False):
    """Upload all existing local resumes to S3"""
    
    db = SessionLocal()
    
    try:
        print("\n🔄 Starting Resume Migration to S3")
        print("=" * 70)
        
        # Get resumes that need migration
        if force:
            resumes = db.query(Resume).all()
            print("⚠️  FORCE MODE: Re-uploading ALL resumes (including already migrated)")
        else:
            resumes = db.query(Resume).filter(
                (Resume.s3_key == None) | (Resume.s3_key == '')
            ).all()
        
        if not resumes:
            print("✅ No resumes to migrate. All resumes already in S3.")
            return True
        
        print(f"📦 Found {len(resumes)} resumes to migrate\n")
        
        success_count = 0
        error_count = 0
        missing_file_count = 0
        
        for i, resume in enumerate(resumes, 1):
            print(f"[{i}/{len(resumes)}] Processing Resume ID {resume.id}")
            print(f"  Student ID: {resume.student_id}")
            print(f"  File: {resume.file_name}")
            
            # Check if local file exists
            if not os.path.exists(resume.file_path):
                print(f"  ⚠️  Local file not found: {resume.file_path}")
                missing_file_count += 1
                error_count += 1
                print()
                continue
            
            file_size = os.path.getsize(resume.file_path)
            print(f"  Size: {file_size / 1024:.2f} KB")
            
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
        
        print("=" * 70)
        print("🎉 Migration Completed!")
        print("=" * 70)
        print(f"  ✅ Successful uploads: {success_count}")
        print(f"    Failed uploads: {error_count}")
        if missing_file_count > 0:
            print(f"  ⚠️  Missing local files: {missing_file_count}")
        print("=" * 70)
        
        if success_count > 0:
            print("\n✅ Next Steps:")
            print("  1. Verify uploaded files in AWS S3 console")
            print("  2. Test resume viewing in the application (Company AI Candidate Ranking)")
            print("  3. Local files are kept as backup")
            print("  4. New resume uploads will automatically go to S3")
        
        return success_count > 0
        
    except Exception as e:
        db.rollback()
        print(f"  Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def verify_resume_access():
    """Verify that resumes can be accessed from S3"""
    db = SessionLocal()
    
    try:
        print("\n🔍 Verifying Resume Access")
        print("=" * 70)
        
        # Get a few resumes with S3 keys
        sample_resumes = db.query(Resume).filter(
            Resume.s3_key != None,
            Resume.s3_key != ''
        ).limit(5).all()
        
        if not sample_resumes:
            print("  No resumes with S3 keys found to verify")
            return True
        
        print(f"  Testing {len(sample_resumes)} sample resumes...\n")
        
        success = 0
        failed = 0
        
        for resume in sample_resumes:
            print(f"  Resume ID {resume.id}: {resume.file_name}")
            url = s3_service.generate_presigned_url(resume.s3_key)
            
            if url:
                print(f"    ✅ URL generated successfully")
                print(f"    🔗 {url[:80]}...")
                success += 1
            else:
                print(f"      Failed to generate URL")
                failed += 1
            print()
        
        print("=" * 70)
        print(f"  ✅ Successful: {success}/{len(sample_resumes)}")
        print(f"    Failed: {failed}/{len(sample_resumes)}")
        print("=" * 70)
        
        return failed == 0
        
    except Exception as e:
        print(f"  Verification failed: {str(e)}")
        return False
    finally:
        db.close()


def main():
    """Main execution flow"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup S3 and migrate resumes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_s3_and_migrate.py              # Check status only
  python scripts/setup_s3_and_migrate.py --migrate    # Migrate resumes to S3
  python scripts/setup_s3_and_migrate.py --force      # Re-upload all resumes
  python scripts/setup_s3_and_migrate.py --verify     # Verify S3 access
        """
    )
    
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Migrate local resumes to S3'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-upload of all resumes (including already migrated)'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify S3 access for existing resumes'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("   SkillSync - S3 Setup and Migration Tool")
    print("=" * 70)
    
    # Step 1: Check configuration
    if not check_s3_configuration():
        print("\n  S3 not configured. Please set up AWS credentials first.")
        return 1
    
    # Step 2: Test connectivity
    if not test_s3_connectivity():
        print("\n  S3 connectivity test failed. Please check your configuration.")
        return 1
    
    # Step 3: Get current status
    total, with_s3, without_s3 = get_migration_status()
    
    # Step 4: Migrate if requested
    if args.migrate or args.force:
        if not migrate_resumes_to_s3(force=args.force):
            print("\n  Migration encountered errors")
            return 1
    elif without_s3 > 0:
        print(f"\n💡 To migrate {without_s3} local resumes to S3, run:")
        print("   python scripts/setup_s3_and_migrate.py --migrate")
    
    # Step 5: Verify if requested
    if args.verify or args.migrate:
        if not verify_resume_access():
            print("\n⚠️  Some resumes may not be accessible from S3")
    
    print("\n✅ All checks completed successfully!")
    print("=" * 70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
