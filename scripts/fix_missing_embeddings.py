#!/usr/bin/env python3
"""
Fix Missing Embeddings Script
==============================

This script identifies resumes without embeddings and regenerates them.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import get_db
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.services.rag_engine import rag_engine
from app.services.parser_service import ResumeParser

def find_missing_embeddings():
    """Find all resumes without embeddings"""
    print("\n" + "=" * 70)
    print("  FINDING RESUMES WITHOUT EMBEDDINGS")
    print("=" * 70)
    
    db = next(get_db())
    
    # Get all students with active resumes
    students_with_resumes = db.query(User, Resume).join(
        Resume, Resume.student_id == User.id
    ).filter(
        User.role == UserRole.student,
        Resume.is_active == 1
    ).all()
    
    print(f"\n📊 Checking {len(students_with_resumes)} students with active resumes...")
    
    missing_embeddings = []
    for student, resume in students_with_resumes:
        if resume.embedding_id:
            resume_chroma_id = resume.embedding_id.replace('resume_', '')
            embedding = rag_engine.get_resume_embedding(resume_chroma_id)
        else:
            embedding = None
        
        if embedding is None or len(embedding) == 0:
            missing_embeddings.append({
                'student': student,
                'resume': resume
            })
    
    if missing_embeddings:
        print(f"\n  Found {len(missing_embeddings)} resumes WITHOUT embeddings:")
        for item in missing_embeddings:
            print(f"   - Student {item['student'].id} ({item['student'].full_name})")
            print(f"     Resume ID: {item['resume'].id}")
            print(f"     File: {item['resume'].file_path}")
            print(f"     Embedding ID: {item['resume'].embedding_id}")
    else:
        print("\n✅ All resumes have embeddings!")
    
    return missing_embeddings


def fix_missing_embeddings(missing_embeddings):
    """Generate embeddings for resumes that don't have them"""
    print("\n" + "=" * 70)
    print("  GENERATING MISSING EMBEDDINGS")
    print("=" * 70)
    
    if not missing_embeddings:
        print("\n✅ No missing embeddings to fix!")
        return True
    
    db = next(get_db())
    parser = ResumeParser()
    
    success_count = 0
    fail_count = 0
    
    for item in missing_embeddings:
        student = item['student']
        resume = item['resume']
        
        print(f"\n📄 Processing Resume ID {resume.id} for {student.full_name}...")
        
        try:
            # Get the resume file path
            file_path = resume.file_path
            
            if not os.path.exists(file_path):
                print(f"     File not found: {file_path}")
                fail_count += 1
                continue
            
            # Parse and index the resume
            print(f"   📖 Parsing resume...")
            parsed_data = parser.parse_resume(file_path)
            
            if not parsed_data:
                print(f"     Failed to parse resume")
                fail_count += 1
                continue
            
            # Update parsed data
            resume.parsed_data = parsed_data
            
            # Generate embedding
            print(f"   🔢 Generating embedding...")
            embedding_id = rag_engine.add_resume_to_vector_db(
                resume_id=str(resume.id),
                parsed_data=parsed_data
            )
            
            if embedding_id:
                resume.embedding_id = embedding_id
                db.commit()
                print(f"   ✅ Successfully generated embedding: {embedding_id}")
                success_count += 1
            else:
                print(f"     Failed to generate embedding")
                fail_count += 1
                
        except Exception as e:
            print(f"     Error: {str(e)}")
            fail_count += 1
            continue
    
    print("\n" + "=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"\n✅ Successfully fixed: {success_count}")
    print(f"  Failed: {fail_count}")
    
    return fail_count == 0


def main():
    """Main workflow"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║              FIX MISSING RESUME EMBEDDINGS                         ║
║                                                                    ║
║  This script finds and fixes resumes without embeddings.          ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Find missing embeddings
    missing_embeddings = find_missing_embeddings()
    
    if not missing_embeddings:
        print("\n✅ All resumes have embeddings! Nothing to fix.")
        return
    
    # Step 2: Ask for confirmation
    print(f"\n❓ Found {len(missing_embeddings)} resumes without embeddings.")
    response = input("   Fix them now? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("\n  Operation cancelled.")
        return
    
    # Step 3: Fix missing embeddings
    if fix_missing_embeddings(missing_embeddings):
        print("\n✅ All embeddings fixed successfully!")
        print("\n📋 Next step: Run the backfill script:")
        print("   python3 scripts/backfill_student_matches.py")
    else:
        print("\n⚠️  Some embeddings could not be fixed. Please check errors above.")


if __name__ == "__main__":
    main()
