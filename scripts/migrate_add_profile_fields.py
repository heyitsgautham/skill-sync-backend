"""
Database Migration: Add Profile Fields to User Model
Feature 7: User Profile Pages

Adds the following fields to the users table:
- phone (String) - Contact phone number
- phone_visible (Boolean) - Phone visibility toggle
- linkedin_url (String) - LinkedIn profile URL  
- github_url (String) - GitHub profile URL
- hr_contact_name (String) - HR contact name (for companies)
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.connection import engine, get_db


def migrate():
    """Add profile fields to users table"""
    print("\n" + "="*60)
    print("Database Migration: Add Profile Fields")
    print("Feature 7: User Profile Pages")
    print("="*60 + "\n")
    
    db = next(get_db())
    
    try:
        # Check if columns already exist
        print("Checking existing columns...")
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('phone', 'phone_visible', 'linkedin_url', 'github_url', 'hr_contact_name')
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        print(f"Existing columns: {existing_columns if existing_columns else 'None'}\n")
        
        migrations_applied = []
        
        # Add phone column
        if 'phone' not in existing_columns:
            print("Adding 'phone' column...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN phone VARCHAR(50)
            """))
            migrations_applied.append('phone')
            print("✓ Added 'phone' column")
        else:
            print("⊘ 'phone' column already exists")
        
        # Add phone_visible column
        if 'phone_visible' not in existing_columns:
            print("Adding 'phone_visible' column...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN phone_visible BOOLEAN DEFAULT TRUE
            """))
            migrations_applied.append('phone_visible')
            print("✓ Added 'phone_visible' column")
        else:
            print("⊘ 'phone_visible' column already exists")
        
        # Add linkedin_url column
        if 'linkedin_url' not in existing_columns:
            print("Adding 'linkedin_url' column...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN linkedin_url VARCHAR(500)
            """))
            migrations_applied.append('linkedin_url')
            print("✓ Added 'linkedin_url' column")
        else:
            print("⊘ 'linkedin_url' column already exists")
        
        # Add github_url column
        if 'github_url' not in existing_columns:
            print("Adding 'github_url' column...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN github_url VARCHAR(500)
            """))
            migrations_applied.append('github_url')
            print("✓ Added 'github_url' column")
        else:
            print("⊘ 'github_url' column already exists")
        
        # Add hr_contact_name column
        if 'hr_contact_name' not in existing_columns:
            print("Adding 'hr_contact_name' column...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN hr_contact_name VARCHAR(255)
            """))
            migrations_applied.append('hr_contact_name')
            print("✓ Added 'hr_contact_name' column")
        else:
            print("⊘ 'hr_contact_name' column already exists")
        
        # Set default phone_visible values based on role
        if 'phone_visible' in migrations_applied:
            print("\nSetting default phone_visible values...")
            # Students: phone visible by default
            db.execute(text("""
                UPDATE users 
                SET phone_visible = TRUE 
                WHERE role = 'student'
            """))
            # Companies: phone not visible by default (privacy)
            db.execute(text("""
                UPDATE users 
                SET phone_visible = FALSE 
                WHERE role = 'company'
            """))
            print("✓ Set default phone_visible values")
        
        db.commit()
        
        print("\n" + "="*60)
        print("Migration Summary")
        print("="*60)
        if migrations_applied:
            print(f"✓ Successfully added {len(migrations_applied)} column(s):")
            for col in migrations_applied:
                print(f"  - {col}")
        else:
            print("⊘ All columns already exist. No changes made.")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
