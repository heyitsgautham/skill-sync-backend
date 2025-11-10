#!/usr/bin/env python3
"""
Remove redundant embedding column from resumes table

This script removes the 'embedding' column from PostgreSQL as it's redundant.
Embeddings are already stored in ChromaDB, which is the single source of truth.

Usage:
    python scripts/remove_embedding_column.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.connection import engine, SessionLocal
from sqlalchemy import text, inspect


def check_column_exists():
    """Check if embedding column exists"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('resumes')]
        return 'embedding' in columns
    except Exception as e:
        print(f"  Error checking columns: {e}")
        return False


def remove_embedding_column():
    """Remove the embedding column from resumes table"""
    print("=" * 80)
    print("🔧 Removing Redundant Embedding Column from PostgreSQL")
    print("=" * 80)
    
    # Check if column exists
    print("\n📊 Step 1: Checking if 'embedding' column exists...")
    if not check_column_exists():
        print("✅ Column 'embedding' does not exist. Nothing to do!")
        return
    
    print("✅ Column 'embedding' found in resumes table")
    
    # Show current state
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as with_embedding
            FROM resumes
        """))
        row = result.fetchone()
        print(f"\n📊 Current state:")
        print(f"   Total resumes: {row[0]}")
        print(f"   Resumes with embedding in PostgreSQL: {row[1]}")
        print(f"   This column is REDUNDANT - embeddings are in ChromaDB!")
    except Exception as e:
        print(f"⚠️  Could not check current state: {e}")
    finally:
        db.close()
    
    # Confirm with user
    print(f"\n⚠️  WARNING: This will permanently remove the 'embedding' column!")
    print(f"   Embeddings will only be stored in ChromaDB going forward.")
    print(f"   The 'embedding_id' column will remain as a reference.\n")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("  Migration cancelled by user")
        return
    
    # Remove the column
    print("\n🗑️  Step 2: Removing 'embedding' column...")
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE resumes DROP COLUMN IF EXISTS embedding"))
        db.commit()
        print("✅ Successfully removed 'embedding' column!")
    except Exception as e:
        db.rollback()
        print(f"  Error removing column: {e}")
        return
    finally:
        db.close()
    
    # Verify removal
    print("\n✓ Step 3: Verifying column was removed...")
    if not check_column_exists():
        print("✅ Verification successful! Column 'embedding' has been removed.")
    else:
        print("⚠️  Warning: Column still exists. Manual intervention may be needed.")
    
    print("\n" + "=" * 80)
    print("🎉 Migration Complete!")
    print("=" * 80)
    print("\n📝 Summary:")
    print("   ✅ Removed redundant 'embedding' column from PostgreSQL")
    print("   ✅ embedding_id column retained (references ChromaDB)")
    print("   ✅ ChromaDB is now the single source of truth for vectors")
    print("\n💡 Next steps:")
    print("   1. Update Resume model to remove embedding field")
    print("   2. Update code that references resume.embedding")
    print("   3. Restart the application")
    print()


if __name__ == "__main__":
    try:
        remove_embedding_column()
    except KeyboardInterrupt:
        print("\n\n  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n  Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
