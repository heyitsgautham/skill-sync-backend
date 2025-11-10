"""
Migration Script: Add indexes for candidate flagging performance
Adds indexes on phone, linkedin_url, and github_url columns for faster duplicate detection
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_index, Index, text
from app.database.connection import engine, SessionLocal
from app.models.user import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_indexes():
    """Add indexes for phone, linkedin_url, github_url for faster duplicate detection"""
    
    logger.info("=" * 80)
    logger.info("MIGRATION: Add indexes for candidate flagging")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Check if indexes already exist
        result = db.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'users' 
            AND indexname IN ('idx_users_phone', 'idx_users_linkedin_url', 'idx_users_github_url')
        """))
        existing_indexes = [row[0] for row in result]
        
        logger.info(f"Existing indexes: {existing_indexes}")
        
        # Add phone index
        if 'idx_users_phone' not in existing_indexes:
            logger.info("Creating index on users.phone...")
            db.execute(text("""
                CREATE INDEX idx_users_phone ON users(phone) 
                WHERE phone IS NOT NULL AND role = 'student'
            """))
            logger.info("✅ Index idx_users_phone created successfully")
        else:
            logger.info("⏭️  Index idx_users_phone already exists, skipping")
        
        # Add LinkedIn URL index
        if 'idx_users_linkedin_url' not in existing_indexes:
            logger.info("Creating index on users.linkedin_url...")
            db.execute(text("""
                CREATE INDEX idx_users_linkedin_url ON users(linkedin_url) 
                WHERE linkedin_url IS NOT NULL AND role = 'student'
            """))
            logger.info("✅ Index idx_users_linkedin_url created successfully")
        else:
            logger.info("⏭️  Index idx_users_linkedin_url already exists, skipping")
        
        # Add GitHub URL index
        if 'idx_users_github_url' not in existing_indexes:
            logger.info("Creating index on users.github_url...")
            db.execute(text("""
                CREATE INDEX idx_users_github_url ON users(github_url) 
                WHERE github_url IS NOT NULL AND role = 'student'
            """))
            logger.info("✅ Index idx_users_github_url created successfully")
        else:
            logger.info("⏭️  Index idx_users_github_url already exists, skipping")
        
        db.commit()
        logger.info("=" * 80)
        logger.info("✅ Migration completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"  Error during migration: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def rollback_indexes():
    """Remove the indexes (rollback migration)"""
    
    logger.info("=" * 80)
    logger.info("ROLLBACK: Remove candidate flagging indexes")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        indexes_to_drop = ['idx_users_phone', 'idx_users_linkedin_url', 'idx_users_github_url']
        
        for index_name in indexes_to_drop:
            logger.info(f"Dropping index {index_name}...")
            db.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
            logger.info(f"✅ Index {index_name} dropped")
        
        db.commit()
        logger.info("=" * 80)
        logger.info("✅ Rollback completed successfully")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"  Error during rollback: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Candidate Flagging Index Migration")
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        rollback_indexes()
    else:
        add_indexes()
