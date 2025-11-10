#!/usr/bin/env python3
"""
Script to verify if embeddings are deleted from ChromaDB
Checks all collections and their document counts
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings


def verify_embeddings_deletion():
    """Verify the current state of ChromaDB collections"""
    
    # Initialize ChromaDB client
    chroma_path = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
    
    print(f"\n{'='*60}")
    print(f"ChromaDB Verification Report")
    print(f"{'='*60}")
    print(f"Database Path: {chroma_path}\n")
    
    try:
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # List all collections
        collections = client.list_collections()
        
        if not collections:
            print("✓ No collections found - ChromaDB is empty")
            print("\nStatus: All embeddings have been deleted")
            return True
        
        print(f"Found {len(collections)} collection(s):\n")
        
        total_documents = 0
        collection_details = []
        
        for collection in collections:
            col = client.get_collection(collection.name)
            count = col.count()
            total_documents += count
            
            collection_details.append({
                'name': collection.name,
                'count': count,
                'metadata': collection.metadata
            })
            
            # Get sample documents if any exist
            if count > 0:
                sample = col.get(limit=5)
                print(f"Collection: {collection.name}")
                print(f"  Document count: {count}")
                print(f"  Metadata: {collection.metadata}")
                if sample['ids']:
                    print(f"  Sample IDs: {sample['ids'][:3]}")
                print()
            else:
                print(f"Collection: {collection.name}")
                print(f"  Document count: 0 (EMPTY)")
                print(f"  Metadata: {collection.metadata}")
                print()
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"{'='*60}")
        print(f"Total collections: {len(collections)}")
        print(f"Total documents across all collections: {total_documents}")
        
        if total_documents == 0:
            print(f"\n✓ Status: All embeddings have been DELETED")
            print(f"  All collections exist but contain no documents")
            return True
        else:
            print(f"\n✗ Status: Embeddings still exist")
            print(f"  {total_documents} document(s) found across collections")
            
            # Show which collections have documents
            non_empty = [c for c in collection_details if c['count'] > 0]
            if non_empty:
                print(f"\n  Collections with documents:")
                for col in non_empty:
                    print(f"    - {col['name']}: {col['count']} documents")
            
            return False
            
    except Exception as e:
        print(f"✗ Error accessing ChromaDB: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_specific_collection(collection_name: str):
    """Verify a specific collection"""
    
    chroma_path = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
    
    try:
        client = chromadb.PersistentClient(path=chroma_path)
        
        print(f"\n{'='*60}")
        print(f"Verifying Collection: {collection_name}")
        print(f"{'='*60}\n")
        
        try:
            collection = client.get_collection(collection_name)
            count = collection.count()
            
            print(f"Collection exists: Yes")
            print(f"Document count: {count}")
            print(f"Metadata: {collection.metadata}")
            
            if count > 0:
                # Get all document IDs
                all_docs = collection.get()
                print(f"\nDocument IDs ({len(all_docs['ids'])}):")
                for idx, doc_id in enumerate(all_docs['ids'], 1):
                    print(f"  {idx}. {doc_id}")
                
                print(f"\n✗ Collection '{collection_name}' contains {count} document(s)")
                return False
            else:
                print(f"\n✓ Collection '{collection_name}' is EMPTY")
                return True
                
        except Exception as e:
            print(f"Collection exists: No")
            print(f"Error: {str(e)}")
            return True
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def check_sqlite_database():
    """Check the SQLite database directly"""
    import sqlite3
    
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db", "chroma.sqlite3")
    
    print(f"\n{'='*60}")
    print(f"SQLite Database Analysis")
    print(f"{'='*60}\n")
    
    if not os.path.exists(db_path):
        print(f"✗ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"Total tables in database: {len(tables)}\n")
        
        # Check embeddings table
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        embedding_count = cursor.fetchone()[0]
        print(f"Embeddings table row count: {embedding_count}")
        
        # Check segments table
        cursor.execute("SELECT COUNT(*) FROM segments")
        segment_count = cursor.fetchone()[0]
        print(f"Segments table row count: {segment_count}")
        
        # Check collections table
        cursor.execute("SELECT id, name FROM collections")
        collections = cursor.fetchall()
        print(f"\nCollections in database: {len(collections)}")
        for coll_id, coll_name in collections:
            print(f"  - ID: {coll_id}, Name: {coll_name}")
        
        print(f"\n{'='*60}")
        if embedding_count == 0:
            print("✓ SQLite embeddings table is EMPTY")
        else:
            print(f"✗ SQLite embeddings table contains {embedding_count} rows")
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Error reading SQLite database: {str(e)}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ChromaDB Embeddings Deletion Verification")
    print("="*60)
    
    # Run all verifications
    print("\n[1] Checking ChromaDB Collections...")
    collections_empty = verify_embeddings_deletion()
    
    print("\n[2] Checking SQLite Database...")
    check_sqlite_database()
    
    # Final verdict
    print("\n" + "="*60)
    print("FINAL VERDICT")
    print("="*60)
    
    if collections_empty:
        print("✓ ALL EMBEDDINGS HAVE BEEN SUCCESSFULLY DELETED")
        print("  ChromaDB collections are empty")
    else:
        print("✗ EMBEDDINGS STILL EXIST IN CHROMADB")
        print("  Some collections contain documents")
    
    print("="*60 + "\n")
