#!/usr/bin/env python3
"""
ChromaDB Inspector - View embeddings stored in ChromaDB
This script helps you verify if embeddings were actually cleared or still exist.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rag_engine import rag_engine


def inspect_sqlite():
    """Inspect the ChromaDB SQLite database directly"""
    db_path = Path("data/chroma_db/chroma.sqlite3")
    
    if not db_path.exists():
        print("  ChromaDB SQLite file not found!")
        return
    
    print(f"📊 Inspecting SQLite database: {db_path}")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    print("\n📁 Tables in database:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")
    
    print("\n" + "=" * 80)
    
    # Check collections
    print("\n📦 Collections:")
    try:
        cursor.execute("SELECT * FROM collections;")
        collections = cursor.fetchall()
        if collections:
            for col in collections:
                print(f"   ID: {col[0]}, Name: {col[1]}")
        else:
            print("   No collections found")
    except sqlite3.OperationalError as e:
        print(f"   Error reading collections: {e}")
    
    print("\n" + "=" * 80)
    
    # Check embeddings count
    print("\n🔢 Embeddings count per collection:")
    try:
        cursor.execute("""
            SELECT c.name, COUNT(e.id) 
            FROM collections c
            LEFT JOIN embeddings e ON c.id = e.collection_id
            GROUP BY c.id, c.name
        """)
        counts = cursor.fetchall()
        if counts:
            for name, count in counts:
                print(f"   {name}: {count} embeddings")
        else:
            print("   No data found")
    except sqlite3.OperationalError as e:
        print(f"   Error counting embeddings: {e}")
    
    print("\n" + "=" * 80)
    
    # Check segments (vector data)
    print("\n📊 Segments (Vector Storage):")
    try:
        cursor.execute("SELECT * FROM segments;")
        segments = cursor.fetchall()
        if segments:
            print(f"   Found {len(segments)} segments")
            for seg in segments:
                print(f"   - Segment ID: {seg[0]}, Type: {seg[1]}, Collection: {seg[3]}")
        else:
            print("   No segments found")
    except sqlite3.OperationalError as e:
        print(f"   Error reading segments: {e}")
    
    conn.close()


def inspect_chroma_collections():
    """Inspect ChromaDB collections using the RAG engine"""
    print("\n" + "=" * 80)
    print("🔍 Inspecting ChromaDB Collections via RAG Engine")
    print("=" * 80)
    
    # Resume collection
    print("\n📄 Resume Collection:")
    try:
        resume_count = rag_engine.resume_collection.count()
        print(f"   Total items: {resume_count}")
        
        if resume_count > 0:
            # Get a sample
            sample = rag_engine.resume_collection.peek(limit=5)
            print(f"\n   Sample IDs (first 5):")
            for i, doc_id in enumerate(sample['ids'][:5], 1):
                print(f"   {i}. {doc_id}")
                if sample['metadatas'] and i-1 < len(sample['metadatas']):
                    meta = sample['metadatas'][i-1]
                    print(f"      Metadata: {meta}")
    except Exception as e:
        print(f"   Error inspecting resume collection: {e}")
    
    # Internship collection
    print("\n💼 Internship Collection:")
    try:
        internship_count = rag_engine.internship_collection.count()
        print(f"   Total items: {internship_count}")
        
        if internship_count > 0:
            # Get a sample
            sample = rag_engine.internship_collection.peek(limit=5)
            print(f"\n   Sample IDs (first 5):")
            for i, doc_id in enumerate(sample['ids'][:5], 1):
                print(f"   {i}. {doc_id}")
                if sample['metadatas'] and i-1 < len(sample['metadatas']):
                    meta = sample['metadatas'][i-1]
                    print(f"      Metadata: {meta}")
    except Exception as e:
        print(f"   Error inspecting internship collection: {e}")


def inspect_filesystem():
    """Inspect the ChromaDB directory structure"""
    print("\n" + "=" * 80)
    print("📂 ChromaDB Directory Structure")
    print("=" * 80)
    
    chroma_dir = Path("data/chroma_db")
    
    if not chroma_dir.exists():
        print("  ChromaDB directory not found!")
        return
    
    print(f"\n📍 Location: {chroma_dir.absolute()}")
    
    # List all files and directories
    print("\n📁 Contents:")
    for item in sorted(chroma_dir.rglob("*")):
        if item.is_file():
            size = item.stat().st_size
            size_str = format_bytes(size)
            rel_path = item.relative_to(chroma_dir)
            print(f"   📄 {rel_path} ({size_str})")
        elif item.is_dir() and item != chroma_dir:
            rel_path = item.relative_to(chroma_dir)
            print(f"   📁 {rel_path}/")
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in chroma_dir.rglob("*") if f.is_file())
    print(f"\n💾 Total size: {format_bytes(total_size)}")


def format_bytes(bytes):
    """Format bytes to human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"


def check_database_embeddings():
    """Check PostgreSQL database for embedding data"""
    print("\n" + "=" * 80)
    print("🗄️  PostgreSQL Database Check")
    print("=" * 80)
    
    try:
        from app.database.connection import get_db
        from app.models import Resume
        from sqlalchemy import func
        
        db = next(get_db())
        
        # Count resumes with embeddings
        total_resumes = db.query(Resume).count()
        resumes_with_embedding = db.query(Resume).filter(Resume.embedding.isnot(None)).count()
        resumes_with_embedding_id = db.query(Resume).filter(Resume.embedding_id.isnot(None)).count()
        
        print(f"\n📊 Resume Statistics:")
        print(f"   Total resumes: {total_resumes}")
        print(f"   With embedding vector: {resumes_with_embedding}")
        print(f"   With embedding_id: {resumes_with_embedding_id}")
        
        # Sample resume with embedding
        if resumes_with_embedding > 0:
            sample = db.query(Resume).filter(Resume.embedding.isnot(None)).first()
            if sample:
                print(f"\n   Sample resume with embedding:")
                print(f"   - Resume ID: {sample.id}")
                print(f"   - Student ID: {sample.student_id}")
                print(f"   - Embedding ID: {sample.embedding_id}")
                print(f"   - File: {sample.file_name}")
                if sample.embedding:
                    print(f"   - Embedding dimensions: {len(sample.embedding)} (should be 384 for all-MiniLM-L6-v2)")
        
        db.close()
        
    except Exception as e:
        print(f"     Error checking database: {e}")


def main():
    print("🔍 ChromaDB Embeddings Inspector")
    print("=" * 80)
    print("\nThis script will show you where embeddings are stored and verify if they were cleared.\n")
    
    # Run all inspections
    inspect_filesystem()
    inspect_sqlite()
    inspect_chroma_collections()
    check_database_embeddings()
    
    print("\n" + "=" * 80)
    print("✅ Inspection Complete!")
    print("=" * 80)
    
    print("\n📝 Summary:")
    print("   1. SQLite file: data/chroma_db/chroma.sqlite3 (metadata)")
    print("   2. Vector data: data/chroma_db/<UUID>/ directories (binary files)")
    print("   3. PostgreSQL: 'resumes' table (embedding column)")
    print("\n   When you clear embeddings:")
    print("   - ChromaDB collections become empty (count = 0)")
    print("   - Vector binary files may still exist (but contain no data)")
    print("   - PostgreSQL embedding and embedding_id columns are set to NULL")
    print("\n   🔍 Check the counts above to verify if clear was successful!")


if __name__ == "__main__":
    main()
