"""
Script to populate LinkedIn and GitHub URLs for all students based on their names.
Converts student names to URL-friendly format (lowercase, spaces to hyphens).
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.user import User, UserRole


def name_to_url_slug(name: str) -> str:
    """
    Convert a student name to a URL-friendly slug.
    
    Examples:
    - "Durga" -> "durga"
    - "Durga Devi" -> "durga-devi"
    - "John Smith Jr." -> "john-smith-jr"
    """
    # Convert to lowercase, replace spaces with hyphens, remove special chars except hyphens
    slug = name.lower()
    slug = slug.replace(" ", "-")
    # Remove any characters that aren't alphanumeric or hyphens
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    # Remove consecutive hyphens
    while '--' in slug:
        slug = slug.replace('--', '-')
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def populate_social_urls():
    """Populate LinkedIn and GitHub URLs for all students."""
    db: Session = SessionLocal()
    
    try:
        # Get all students (users with role 'student')
        students = db.query(User).filter(User.role == UserRole.student).all()
        
        if not students:
            print("No students found in the database.")
            return
        
        print(f"Found {len(students)} students. Updating social URLs...")
        print("-" * 80)
        
        updated_count = 0
        
        for student in students:
            # Generate URL slug from student name
            url_slug = name_to_url_slug(student.full_name)
            
            # Create LinkedIn and GitHub URLs
            linkedin_url = f"linkedin.com/in/{url_slug}"
            github_url = f"github.com/{url_slug}"
            
            # Update student record
            student.linkedin_url = linkedin_url
            student.github_url = github_url
            
            print(f"Student: {student.full_name}")
            print(f"  LinkedIn: {linkedin_url}")
            print(f"  GitHub: {github_url}")
            print()
            
            updated_count += 1
        
        # Commit all changes
        db.commit()
        
        print("-" * 80)
        print(f"✓ Successfully updated social URLs for {updated_count} students!")
        
    except Exception as e:
        print(f"✗ Error updating social URLs: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 80)
    print("POPULATE SOCIAL URLS FOR STUDENTS")
    print("=" * 80)
    print()
    
    populate_social_urls()
    
    print()
    print("=" * 80)
    print("SCRIPT COMPLETED")
    print("=" * 80)
