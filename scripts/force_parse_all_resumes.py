"""
Force Parse All Resumes - Parse resume files and extract content
This script reads resume text files and updates the database with parsed content
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.services.parser_service import ResumeParser
from app.services.rag_engine import rag_engine
import hashlib

def hash_content(content: str) -> str:
    """Generate SHA-256 hash of content"""
    return hashlib.sha256(content.encode()).hexdigest()

def read_resume_file(file_path: str) -> str:
    """Read resume text file"""
    try:
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("FORCE PARSE ALL RESUMES")
    print("="*80 + "\n")
    
    db: Session = SessionLocal()
    
    try:
        # Get all resumes
        resumes = db.query(Resume, User).join(
            User, Resume.student_id == User.id
        ).filter(
            Resume.is_active == 1,
            User.role == UserRole.student
        ).all()
        
        print(f"Found {len(resumes)} resumes to process\n")
        
        base_path = Path(__file__).parent.parent / "app" / "public"
        
        parsed_count = 0
        error_count = 0
        
        for resume, student in resumes:
            try:
                # Construct file path
                file_path = base_path / resume.file_path
                
                if not file_path.exists():
                    print(f"  File not found: {student.full_name} - {file_path}")
                    error_count += 1
                    continue
                
                # Read resume content
                content = read_resume_file(file_path)
                
                if not content:
                    print(f"  Could not read: {student.full_name}")
                    error_count += 1
                    continue
                
                print(f"📄 Processing: {student.full_name} ({resume.file_name})")
                
                # Store basic content (no Gemini parsing for now)
                resume.parsed_content = content
                resume.content_hash = hash_content(content)
                
                # Extract basic skills from content (simple keyword matching)
                skills = []
                skill_keywords = ['python', 'java', 'javascript', 'react', 'node', 'sql', 'docker', 'aws', 
                                'git', 'typescript', 'c++', 'c#', 'unity', 'unreal', 'flutter', 'android', 
                                'ios', 'machine learning', 'ai', 'blockchain', 'solidity', 'web3']
                content_lower = content.lower()
                for skill in skill_keywords:
                    if skill in content_lower:
                        skills.append(skill.title())
                
                resume.extracted_skills = skills
                student.skills = skills
                
                print(f"  ✅ Parsed successfully")
                print(f"     Skills found: {len(skills)}")
                
                # Index in ChromaDB
                try:
                    rag_engine.store_resume_embedding(
                        resume_id=str(resume.id),
                        content=content,
                        skills=skills,
                        metadata={
                            'student_name': student.full_name,
                            'email': student.email,
                            'file_name': resume.file_name,
                            'resume_id': resume.id
                        }
                    )
                    print(f"  ✅ Indexed in ChromaDB")
                except Exception as e:
                    print(f"  ⚠️  ChromaDB indexing failed: {str(e)[:100]}")
                
                parsed_count += 1
                db.commit()
                
            except Exception as e:
                print(f"  Error processing {student.full_name}: {str(e)[:100]}")
                error_count += 1
                db.rollback()
                continue
        
        print("\n" + "="*80)
        print("PARSING COMPLETE")
        print("="*80)
        print(f"✅ Successfully parsed: {parsed_count}")
        print(f"  Errors: {error_count}")
        print(f"📊 Total: {len(resumes)}\n")
        
        # Verify ChromaDB
        count = rag_engine.resume_collection.count()
        print(f"📊 Resumes in ChromaDB: {count}\n")
        
    except Exception as e:
        print(f"\n  Fatal error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
