"""
Check ChromaDB collections status
Run this to see what's stored in the vector database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_engine import rag_engine

def check_collections():
    """Check what's in ChromaDB collections"""
    
    print("=" * 60)
    print("CHROMADB STATUS CHECK")
    print("=" * 60)
    
    # Check resume collection
    print("\n📄 RESUME COLLECTION:")
    print("-" * 60)
    resume_data = rag_engine.resume_collection.get()
    print(f"Total resumes: {len(resume_data['ids']) if resume_data['ids'] else 0}")
    if resume_data['ids']:
        print(f"Resume IDs: {resume_data['ids']}")
        print(f"\nResume Metadata:")
        for i, (id, metadata) in enumerate(zip(resume_data['ids'], resume_data['metadatas'])):
            print(f"  {i+1}. {id}")
            print(f"     - Resume ID: {metadata.get('resume_id')}")
            print(f"     - Student ID: {metadata.get('student_id')}")
            print(f"     - Skills: {metadata.get('skills', 'N/A')[:100]}...")
            print(f"     - Num Skills: {metadata.get('num_skills')}")
    else:
        print("⚠️  NO RESUMES FOUND IN COLLECTION!")
    
    # Check internship collection
    print("\n\n💼 INTERNSHIP COLLECTION:")
    print("-" * 60)
    internship_data = rag_engine.internship_collection.get()
    print(f"Total internships: {len(internship_data['ids']) if internship_data['ids'] else 0}")
    if internship_data['ids']:
        print(f"Internship IDs: {internship_data['ids'][:10]}...")  # Show first 10
        print(f"\nSample Internship Metadata:")
        for i, (id, metadata) in enumerate(zip(internship_data['ids'][:5], internship_data['metadatas'][:5])):
            print(f"  {i+1}. {id}")
            print(f"     - Internship ID: {metadata.get('internship_id')}")
            print(f"     - Title: {metadata.get('title')}")
            print(f"     - Company ID: {metadata.get('company_id')}")
            print(f"     - Required Skills: {metadata.get('required_skills', 'N/A')[:80]}...")
    else:
        print("⚠️  NO INTERNSHIPS FOUND IN COLLECTION!")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if not resume_data['ids']:
        print("❌ No resumes in vector DB. Upload a resume to populate.")
    if not internship_data['ids']:
        print("❌ No internships in vector DB. Create internships to populate.")
    if resume_data['ids'] and internship_data['ids']:
        print("✅ Both collections have data. Matching should work!")
    
    print("\n")

if __name__ == "__main__":
    check_collections()
