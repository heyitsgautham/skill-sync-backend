"""
Database Migration Script - Update schema for Intelligent Filtering System
Adds fields for structured resume parsing and intelligent matching
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import engine, Base
from app.models.user import User
from app.models.resume import Resume
from app.models.internship import Internship
from app.models.application import Application
from sqlalchemy import text


def migrate_database():
    """Run database migrations"""
    print("🔄 Starting database migration...")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Add new columns to users table
            print("  ➜ Adding columns to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS user_id VARCHAR(36) UNIQUE,
                ADD COLUMN IF NOT EXISTS skills JSON,
                ADD COLUMN IF NOT EXISTS total_experience_years FLOAT DEFAULT 0
            """))
            
            # Update existing users with UUIDs if they don't have one
            conn.execute(text("""
                UPDATE users 
                SET user_id = gen_random_uuid()::text 
                WHERE user_id IS NULL
            """))
            
            # Add new columns to resumes table
            print("  ➜ Adding columns to resumes table...")
            conn.execute(text("""
                ALTER TABLE resumes 
                ADD COLUMN IF NOT EXISTS resume_id VARCHAR(36) UNIQUE,
                ADD COLUMN IF NOT EXISTS parsed_data JSON,
                ADD COLUMN IF NOT EXISTS embedding FLOAT[],
                ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            """))
            
            # Update existing resumes with UUIDs
            conn.execute(text("""
                UPDATE resumes 
                SET resume_id = gen_random_uuid()::text 
                WHERE resume_id IS NULL
            """))
            
            # Add new columns to internships table
            print("  ➜ Adding columns to internships table...")
            conn.execute(text("""
                ALTER TABLE internships 
                ADD COLUMN IF NOT EXISTS internship_id VARCHAR(36) UNIQUE,
                ADD COLUMN IF NOT EXISTS preferred_skills JSON,
                ADD COLUMN IF NOT EXISTS min_experience FLOAT DEFAULT 0,
                ADD COLUMN IF NOT EXISTS max_experience FLOAT DEFAULT 10,
                ADD COLUMN IF NOT EXISTS required_education VARCHAR(255)
            """))
            
            # Update existing internships with UUIDs
            conn.execute(text("""
                UPDATE internships 
                SET internship_id = gen_random_uuid()::text 
                WHERE internship_id IS NULL
            """))
            
            # Commit transaction
            trans.commit()
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise


def create_indexes():
    """Create additional indexes for performance"""
    print("🔄 Creating indexes...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_resume_id ON resumes(resume_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_student_id ON resumes(student_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_internships_internship_id ON internships(internship_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_internships_company_id ON internships(company_id)"))
            trans.commit()
            print("✅ Indexes created successfully!")
        except Exception as e:
            trans.rollback()
            print(f"⚠️  Warning: Could not create some indexes: {str(e)}")


def recreate_tables():
    """Drop and recreate all tables (USE WITH CAUTION - WILL DELETE DATA)"""
    print("⚠️  WARNING: This will delete all existing data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Operation cancelled")
        return
    
    print("🔄 Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("🔄 Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Tables recreated successfully!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration script")
    parser.add_argument(
        "--mode",
        choices=["migrate", "recreate", "indexes"],
        default="migrate",
        help="Migration mode: migrate (add columns), recreate (drop and recreate), indexes (create indexes)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "migrate":
            migrate_database()
            create_indexes()
        elif args.mode == "recreate":
            recreate_tables()
            create_indexes()
        elif args.mode == "indexes":
            create_indexes()
        else:
            print(f"❌ Unknown mode: {args.mode}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
