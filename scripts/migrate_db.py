#!/usr/bin/env python3
"""
Database Migration Script
Creates all database tables based on SQLAlchemy models
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import engine, Base
from app.models import User, Internship, Resume, Application

def create_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Successfully created all tables:")
        print("  - users")
        print("  - internships")
        print("  - resumes")
        print("  - applications")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {str(e)}")
        return False

def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        response = input("Are you sure you want to drop all tables? This cannot be undone! (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return False
        
        print("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ Successfully dropped all tables")
        return True
    except Exception as e:
        print(f"✗ Error dropping tables: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database migration script')
    parser.add_argument('action', choices=['create', 'drop', 'recreate'], 
                       help='Action to perform: create, drop, or recreate tables')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        success = create_tables()
    elif args.action == 'drop':
        success = drop_tables()
    elif args.action == 'recreate':
        print("Recreating database tables...")
        if drop_tables():
            success = create_tables()
        else:
            success = False
    
    sys.exit(0 if success else 1)
