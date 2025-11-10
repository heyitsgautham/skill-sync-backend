#!/usr/bin/env python3
"""
Recompute all student-internship matches with new scoring weights
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gauthamkrishna@localhost:5432/skillsync")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

from app.models.user import User
from app.models.resume import Resume
from app.models.student_internship_match import StudentInternshipMatch
from app.models.internship import Internship
from app.services.matching_engine import MatchingEngine
from app.services.rag_engine import RAGEngine

print("=" * 80)
print("RECOMPUTING MATCHES WITH NEW WEIGHTS")
print("=" * 80)
print("\nNew Weights:")
print("  Skills Match: 45% (was 30%)")
print("  Experience Match: 25% (was 20%)")
print("  Semantic Similarity: 10% (was 35%)")
print("  Education Match: 10% (was 10%)")
print("  Projects/Certifications: 10% (was 5%)")
print("=" * 80)

# Initialize services
rag_engine = RAGEngine()
matching_engine = MatchingEngine(rag_engine)

# Get all matches
all_matches = db.query(StudentInternshipMatch).all()
print(f"\nFound {len(all_matches)} existing matches to recompute")

updated_count = 0
error_count = 0

for match in all_matches:
    try:
        # Get student, resume, and internship
        student = db.query(User).filter(User.id == match.student_id).first()
        resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
        internship = db.query(Internship).filter(Internship.id == match.internship_id).first()
        
        if not student or not resume or not internship:
            print(f"⚠️  Skipping match {match.id} - missing data")
            error_count += 1
            continue
        
        # Prepare candidate data
        candidate_data = {
            'all_skills': resume.parsed_data.get('all_skills', []) if resume.parsed_data else [],
            'total_experience_years': resume.parsed_data.get('total_experience_years', 0) if resume.parsed_data else 0,
            'education': resume.parsed_data.get('education', []) if resume.parsed_data else [],
            'certifications': resume.parsed_data.get('certifications', []) if resume.parsed_data else [],
            'projects': resume.parsed_data.get('projects', []) if resume.parsed_data else []
        }
        
        # Prepare internship data
        internship_data = {
            'required_skills': internship.required_skills or [],
            'preferred_skills': internship.preferred_skills or [],
            'min_experience': internship.min_experience or 0,
            'max_experience': internship.max_experience or 10,
            'required_education': internship.required_education or ''
        }
        
        # Get embeddings
        try:
            resume_chroma_id = match.resume_id if match.resume_id else resume.id
            resume_embedding = rag_engine.get_resume_embedding(str(resume_chroma_id))
            internship_embedding = rag_engine.get_internship_embedding(str(internship.id))
            
            if resume_embedding is None or len(resume_embedding) == 0:
                print(f"⚠️  Skipping match {match.id} - missing resume embedding")
                error_count += 1
                continue
            
            if internship_embedding is None or len(internship_embedding) == 0:
                print(f"⚠️  Skipping match {match.id} - missing internship embedding")
                error_count += 1
                continue
            
        except Exception as e:
            print(f"⚠️  Skipping match {match.id} - embedding error: {e}")
            error_count += 1
            continue
        
        # Calculate new match score
        match_result = matching_engine.calculate_match_score(
            candidate_data=candidate_data,
            internship_data=internship_data,
            candidate_embedding=resume_embedding,
            internship_embedding=internship_embedding
        )
        
        # Store old score for comparison
        old_score = match.base_similarity_score
        
        # Update match with new scores
        match.base_similarity_score = match_result['overall_score']
        match.semantic_similarity = match_result['component_scores']['semantic_similarity']
        match.skills_match_score = match_result['component_scores']['skills_match']
        match.experience_match_score = match_result['component_scores']['experience_match']
        
        updated_count += 1
        
        # Show progress for significant changes
        score_diff = abs(match_result['overall_score'] - old_score)
        if score_diff > 5:
            print(f"📊 Student {student.id} → Internship {internship.id}: {old_score:.1f}% → {match_result['overall_score']:.1f}% (Δ {score_diff:+.1f}%)")
        
        if updated_count % 50 == 0:
            print(f"   Progress: {updated_count}/{len(all_matches)} matches updated...")
            db.commit()
    
    except Exception as e:
        print(f"  Error updating match {match.id}: {e}")
        error_count += 1
        continue

# Final commit
db.commit()

print("\n" + "=" * 80)
print("RECOMPUTATION COMPLETE")
print("=" * 80)
print(f"✅ Successfully updated: {updated_count} matches")
print(f"⚠️  Errors/Skipped: {error_count} matches")
print(f"📊 Total processed: {updated_count + error_count} matches")

# Show example: Aanya vs Hari
print("\n" + "=" * 80)
print("EXAMPLE: Aanya vs Hari (Full Stack Software Engineer Intern)")
print("=" * 80)

aanya_match = db.query(StudentInternshipMatch).filter(
    StudentInternshipMatch.student_id == 15,
    StudentInternshipMatch.internship_id == 1
).first()

hari_match = db.query(StudentInternshipMatch).filter(
    StudentInternshipMatch.student_id == 63,
    StudentInternshipMatch.internship_id == 1
).first()

if aanya_match and hari_match:
    print("\nAanya Gupta (missing 2 skills):")
    print(f"  Overall Score: {aanya_match.base_similarity_score:.1f}%")
    print(f"  Skills Match: {aanya_match.skills_match_score:.1f}% (80% - has 5/7 skills)")
    print(f"  Semantic Similarity: {aanya_match.semantic_similarity:.1f}% (75.8%)")
    
    print("\nHari (has all 7 skills):")
    print(f"  Overall Score: {hari_match.base_similarity_score:.1f}%")
    print(f"  Skills Match: {hari_match.skills_match_score:.1f}% (100% - has 7/7 skills)")
    print(f"  Semantic Similarity: {hari_match.semantic_similarity:.1f}% (55.6%)")
    
    if hari_match.base_similarity_score > aanya_match.base_similarity_score:
        print(f"\n✅ FIXED! Hari now ranks higher ({hari_match.base_similarity_score:.1f}% vs {aanya_match.base_similarity_score:.1f}%)")
    else:
        print(f"\n⚠️  Aanya still ranks higher ({aanya_match.base_similarity_score:.1f}% vs {hari_match.base_similarity_score:.1f}%)")

db.close()
print("\n" + "=" * 80)
