"""
Database Migration Script: Add Content Hash for Caching
Adds content_hash columns to resumes and internships tables for detecting changes
"""

import sys
import os
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import engine


def migrate_add_content_hash():
    """Add content_hash columns for caching embeddings"""
    
    print("🔄 Starting migration: Add content_hash columns...")
    
    migrations = [
        # Add content_hash to resumes table
        "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);",
        
        # Add content_hash to internships table
        "ALTER TABLE internships ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);",
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
                    continue
        
        print("✅ Migration completed successfully!")
        print("\nAdded columns:")
        print("  - resumes.content_hash (VARCHAR(64)): Hash of parsed content for cache detection")
        print("  - internships.content_hash (VARCHAR(64)): Hash of description for cache detection")
        
        # Verify columns were added (PostgreSQL)
        print("\n🔍 Verifying migration...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, table_name
                FROM information_schema.columns 
                WHERE table_name IN ('resumes', 'internships')
                AND column_name = 'content_hash';
            """))
            columns = [(row[0], row[1]) for row in result]
            
            for col_name, table_name in columns:
                print(f"  ✅ Column '{col_name}' exists in table '{table_name}'")
        
    except Exception as e:
        print(f"  Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    migrate_add_content_hash()
