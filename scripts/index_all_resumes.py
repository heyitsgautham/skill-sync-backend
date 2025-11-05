"""
Script to index all resumes in the vector database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.services.rag_engine import rag_engine

def index_all_resumes():
    """Index all active resumes in the vector database"""
    db: Session = SessionLocal()
    
    try:
        # Get all active resumes with student info
        resumes = db.query(Resume, User).join(
            User, Resume.student_id == User.id
        ).filter(
            Resume.is_active == 1,
            User.role == UserRole.student
        ).all()
        
        print("=" * 80)
        print("INDEXING RESUMES IN VECTOR DATABASE")
        print("=" * 80)
        print(f"\nFound {len(resumes)} resumes to index...")
        print()
        
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        
        for resume, student in resumes:
            try:
                # Check if already indexed
                existing = rag_engine.resume_collection.get(
                    ids=[f"resume_{resume.id}"],
                    include=["metadatas"]
                )
                
                if existing['ids'] and len(existing['ids']) > 0:
                    print(f"⏭️  Skipped: {student.full_name} (Resume #{resume.id}) - Already indexed")
                    skipped_count += 1
                    continue
                
                # Index the resume
                if resume.parsed_content and resume.extracted_skills:
                    rag_engine.store_resume_embedding(
                        resume_id=str(resume.id),
                        content=resume.parsed_content,
                        skills=resume.extracted_skills,
                        metadata={
                            "student_id": str(student.id),
                            "student_name": student.full_name
                        }
                    )
                    print(f"✅ Indexed: {student.full_name} (Resume #{resume.id})")
                    indexed_count += 1
                else:
                    print(f"⚠️  Skipped: {student.full_name} (Resume #{resume.id}) - No content or skills")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"❌ Error indexing {student.full_name}: {str(e)}")
                error_count += 1
        
        print()
        print("=" * 80)
        print("INDEXING COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully indexed: {indexed_count} resumes")
        print(f"⏭️  Skipped (already indexed): {skipped_count} resumes")
        print(f"❌ Errors: {error_count} resumes")
        print()
        
        # Verify final count
        total_in_db = rag_engine.resume_collection.count()
        print(f"📊 Total resumes in vector database: {total_in_db}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    index_all_resumes()
