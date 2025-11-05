"""
Clean up ChromaDB by removing duplicate and old resume entries
Keep only UUID-based entries that match current database records
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import get_db
from app.models.resume import Resume
from app.services.rag_engine import rag_engine

def main():
    print("=" * 80)
    print("CHROMADB CLEANUP SCRIPT")
    print("=" * 80)
    
    db = next(get_db())
    
    # Get all active resume UUIDs from database
    active_resumes = db.query(Resume).filter(Resume.is_active == 1).all()
    valid_resume_ids = {str(r.resume_id) for r in active_resumes}
    
    print(f"Valid resume UUIDs in database: {len(valid_resume_ids)}")
    
    # Get all resumes from ChromaDB
    all_chromadb_resumes = rag_engine.resume_collection.get(include=['metadatas'])
    total_chromadb = len(all_chromadb_resumes['ids'])
    
    print(f"Total entries in ChromaDB: {total_chromadb}")
    print()
    
    # Find entries to delete
    to_delete = []
    to_keep = []
    
    for chroma_id, metadata in zip(all_chromadb_resumes['ids'], all_chromadb_resumes['metadatas']):
        resume_id = metadata.get('resume_id', '')
        
        # Delete if:
        # 1. It's an integer-based ID (old format)
        # 2. It's a UUID that's not in the database
        if not resume_id or resume_id.isdigit() or resume_id not in valid_resume_ids:
            to_delete.append(chroma_id)
        else:
            to_keep.append(chroma_id)
    
    print(f"Entries to KEEP: {len(to_keep)}")
    print(f"Entries to DELETE: {len(to_delete)}")
    print()
    
    if to_delete:
        print("Deleting old/duplicate entries...")
        # Delete in batches of 100
        batch_size = 100
        for i in range(0, len(to_delete), batch_size):
            batch = to_delete[i:i+batch_size]
            rag_engine.resume_collection.delete(ids=batch)
            print(f"  Deleted batch {i//batch_size + 1}: {len(batch)} entries")
        
        print()
        print("✅ Cleanup complete!")
        
        # Verify
        final_count = rag_engine.resume_collection.count()
        print(f"Final ChromaDB count: {final_count}")
        print(f"Expected count: {len(to_keep)}")
        
        if final_count == len(to_keep):
            print("✅ Verification passed!")
        else:
            print("⚠️  Count mismatch - please check!")
    else:
        print("✅ No cleanup needed - ChromaDB is already clean!")
    
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
