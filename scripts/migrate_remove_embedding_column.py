"""Remove redundant embedding column from resumes table

This migration removes the redundant 'embedding' column from the resumes table.
Embeddings will only be stored in ChromaDB going forward.

The 'embedding_id' column is kept as a reference to ChromaDB.

Revision ID: remove_embedding_001
Revises: N/A
Create Date: 2025-11-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'remove_embedding_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Remove the redundant embedding column"""
    print("🗑️  Removing redundant 'embedding' column from resumes table...")
    
    # PostgreSQL
    try:
        op.drop_column('resumes', 'embedding')
        print("✅ Successfully removed 'embedding' column")
    except Exception as e:
        print(f"⚠️  Could not remove embedding column (might already be removed): {e}")


def downgrade():
    """Add the embedding column back (for rollback)"""
    print("⏪ Rolling back: Adding 'embedding' column back to resumes table...")
    
    # PostgreSQL - Add ARRAY(Float) column
    try:
        op.add_column('resumes', 
            sa.Column('embedding', 
                     postgresql.ARRAY(sa.Float()), 
                     nullable=True)
        )
        print("✅ Successfully added 'embedding' column back")
    except Exception as e:
        print(f"⚠️  Could not add embedding column back: {e}")
