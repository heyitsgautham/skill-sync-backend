"""
Database Migration Script: Add Tailored Resume Support
Adds columns to resumes table to support hybrid matching with tailored resumes
"""

import sys
import os
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import engine


def migrate_add_tailored_resume_support():
    """Add tailored resume support columns to resumes table"""
    
    print("🔄 Starting migration: Add tailored resume support...")
    
    migrations = [
        # Add is_tailored column
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS is_tailored INTEGER DEFAULT 0;",
        
        # Add tailored_for_internship_id column
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS tailored_for_internship_id INTEGER;",
        
        # Add base_resume_id column
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS base_resume_id INTEGER;",
    ]
    
    try:
        with engine.begin() as conn:
            for i, migration in enumerate(migrations, 1):
                try:
                    print(f"  ✅ Executing migration {i}/{len(migrations)}...")
                    conn.execute(text(migration))
                except Exception as e:
                    # Check if error is because column already exists
                    if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                        print(f"  ℹ️ Migration {i}: Column already exists, skipping...")
                    else:
                        print(f"  ⚠️ Migration {i} note: {str(e)}")
                    # Continue even if column already exists
                    continue
        
        print("✅ Migration completed successfully!")
        print("\nAdded columns:")
        print("  - is_tailored (INTEGER): Flag for tailored resumes")
        print("  - tailored_for_internship_id (INTEGER): Reference to internship")
        print("  - base_resume_id (INTEGER): Reference to original base resume")
        
        # Verify columns were added (PostgreSQL)
        print("\n🔍 Verifying migration...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'resumes'
                AND column_name IN ('is_tailored', 'tailored_for_internship_id', 'base_resume_id');
            """))
            columns = [row[0] for row in result]
            
            required_columns = ['is_tailored', 'tailored_for_internship_id', 'base_resume_id']
            for col in required_columns:
                if col in columns:
                    print(f"  ✅ Column '{col}' exists")
                else:
                    print(f"  ⚠️ Column '{col}' might not exist (check manually)")
        
    except Exception as e:
        print(f"  Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    migrate_add_tailored_resume_support()
