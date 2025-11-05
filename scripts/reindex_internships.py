"""
Script to re-index all internships in the vector database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.internship import Internship
from app.models.user import User, UserRole
from app.services.rag_engine import rag_engine

def reindex_all_internships():
    """Re-index all active internships in the vector database"""
    db: Session = SessionLocal()
    
    try:
        # Clear existing internship embeddings
        print("=" * 80)
        print("RE-INDEXING INTERNSHIPS IN VECTOR DATABASE")
        print("=" * 80)
        print("\n🗑️  Clearing old internship embeddings...")
        
        # Get all existing internship IDs from vector DB
        existing = rag_engine.internship_collection.get(include=["metadatas"])
        if existing['ids']:
            print(f"   Found {len(existing['ids'])} old embeddings to remove...")
            rag_engine.internship_collection.delete(ids=existing['ids'])
            print("   ✅ Cleared old embeddings")
        else:
            print("   No old embeddings found")
        
        # Get all active internships with company info
        internships = db.query(Internship, User).join(
            User, Internship.company_id == User.id
        ).filter(
            Internship.is_active == 1,
            User.role == UserRole.company
        ).all()
        
        print(f"\n📋 Found {len(internships)} active internships to index...")
        print()
        
        indexed_count = 0
        error_count = 0
        
        for internship, company in internships:
            try:
                # Index the internship
                if internship.description and internship.required_skills:
                    rag_engine.store_internship_embedding(
                        internship_id=str(internship.id),
                        title=internship.title,
                        description=internship.description,
                        required_skills=internship.required_skills,
                        metadata={
                            "company_id": str(company.id),
                            "company_name": company.full_name,
                            "location": internship.location or "",
                            "duration": internship.duration or "",
                            "stipend": internship.stipend or ""
                        }
                    )
                    print(f"✅ Indexed: {internship.title} (ID: {internship.id}) by {company.full_name}")
                    indexed_count += 1
                else:
                    print(f"⚠️  Skipped: {internship.title} (ID: {internship.id}) - No description or skills")
                    
            except Exception as e:
                print(f"❌ Error indexing {internship.title}: {str(e)}")
                error_count += 1
        
        print()
        print("=" * 80)
        print("RE-INDEXING COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully indexed: {indexed_count} internships")
        print(f"❌ Errors: {error_count} internships")
        print()
        
        # Verify final count
        total_in_db = rag_engine.internship_collection.count()
        print(f"📊 Total internships in vector database: {total_in_db}")
        print("=" * 80)
        
        # Show some sample internships
        print("\n📝 Sample indexed internships:")
        sample = rag_engine.internship_collection.get(limit=10, include=["metadatas"])
        if sample['metadatas']:
            for i, meta in enumerate(sample['metadatas'][:5], 1):
                print(f"   {i}. {meta.get('title')} (ID: {meta.get('internship_id')})")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reindex_all_internships()
