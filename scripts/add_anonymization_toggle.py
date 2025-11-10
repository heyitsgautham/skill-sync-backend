"""
Database Migration Script - Add anonymization_enabled field to users table
Run this script to add the resume anonymization toggle for companies
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database.connection import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_anonymization_toggle():
    """Add anonymization_enabled column to users table"""
    
    db = SessionLocal()
    
    try:
        logger.info("🔄 Starting migration: Add anonymization_enabled to users table")
        
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='anonymization_enabled'
        """)
        
        result = db.execute(check_query).fetchone()
        
        if result:
            logger.info("✅ Column 'anonymization_enabled' already exists. Skipping migration.")
            return
        
        # Add the column
        alter_query = text("""
            ALTER TABLE users 
            ADD COLUMN anonymization_enabled BOOLEAN DEFAULT FALSE
        """)
        
        db.execute(alter_query)
        db.commit()
        
        logger.info("✅ Successfully added 'anonymization_enabled' column to users table")
        
        # Verify the column was added
        verify_query = text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='anonymization_enabled'
        """)
        
        result = db.execute(verify_query).fetchone()
        
        if result:
            logger.info(f"✅ Verification successful:")
            logger.info(f"   Column: {result[0]}")
            logger.info(f"   Type: {result[1]}")
            logger.info(f"   Default: {result[2]}")
        
        logger.info("🎉 Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"  Migration failed: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    add_anonymization_toggle()
