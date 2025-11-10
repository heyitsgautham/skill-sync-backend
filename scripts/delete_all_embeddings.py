#!/usr/bin/env python3
"""
Script to delete ALL embeddings from ChromaDB (both resumes and internships)
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings


def delete_all_embeddings():
    """Delete all embeddings from all collections"""
    
    chroma_path = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
    
    print(f"\n{'='*60}")
    print(f"Deleting ALL Embeddings from ChromaDB")
    print(f"{'='*60}\n")
    
    try:
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        collections = client.list_collections()
        
        if not collections:
            print("✓ No collections found - ChromaDB is already empty")
            return
        
        for collection in collections:
            col = client.get_collection(collection.name)
            count = col.count()
            
            print(f"Collection: {collection.name}")
            print(f"  Documents before: {count}")
            
            if count > 0:
                # Get all document IDs
                all_docs = col.get()
                doc_ids = all_docs['ids']
                
                # Delete all documents
                col.delete(ids=doc_ids)
                
                # Verify deletion
                new_count = col.count()
                print(f"  Documents after: {new_count}")
                
                if new_count == 0:
                    print(f"  ✓ Successfully deleted {count} documents")
                else:
                    print(f"  ✗ Failed to delete all documents")
            else:
                print(f"  Already empty")
            
            print()
        
        print(f"{'='*60}")
        print("✓ Deletion complete - running verification...")
        print(f"{'='*60}\n")
        
        # Verify all collections are empty
        all_empty = True
        for collection in collections:
            col = client.get_collection(collection.name)
            count = col.count()
            if count > 0:
                all_empty = False
                print(f"✗ {collection.name}: Still has {count} documents")
            else:
                print(f"✓ {collection.name}: Empty")
        
        print()
        if all_empty:
            print("✓ ALL EMBEDDINGS SUCCESSFULLY DELETED")
        else:
            print("✗ Some embeddings still remain")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    response = input("⚠️  This will delete ALL embeddings (resumes + internships). Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        delete_all_embeddings()
    else:
        print("Aborted.")
