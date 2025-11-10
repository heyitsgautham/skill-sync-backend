#!/usr/bin/env python3
"""
Check candidate matching details for Aanya vs Hari
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

print("=" * 80)
print("CANDIDATE MATCHING ANALYSIS")
print("=" * 80)

# Get Aanya (ID: 15) and Hari (ID: 63)
aanya = db.query(User).filter(User.id == 15).first()
hari = db.query(User).filter(User.id == 63).first()

print('\n### AANYA GUPTA (ID: 15) ###')
print(f'Name: {aanya.full_name}')
print(f'Email: {aanya.email}')
print(f'User Skills: {aanya.skills}')
print(f'Total Experience: {aanya.total_experience_years} years')

aanya_resume = db.query(Resume).filter(Resume.student_id == 15, Resume.is_active == 1).first()
if aanya_resume:
    print(f'\nActive Resume ID: {aanya_resume.id}')
    print(f'File: {aanya_resume.file_name}')
    if aanya_resume.parsed_data:
        print(f'Parsed Skills ({len(aanya_resume.parsed_data.get("all_skills", []))}): {aanya_resume.parsed_data.get("all_skills", [])}')
        print(f'Total Experience: {aanya_resume.parsed_data.get("total_experience_years", 0)} years')

print('\n### HARI (ID: 63) ###')
print(f'Name: {hari.full_name}')
print(f'Email: {hari.email}')
print(f'User Skills: {hari.skills}')
print(f'Total Experience: {hari.total_experience_years} years')

hari_resume = db.query(Resume).filter(Resume.student_id == 63, Resume.is_active == 1).first()
if hari_resume:
    print(f'\nActive Resume ID: {hari_resume.id}')
    print(f'File: {hari_resume.file_name}')
    if hari_resume.parsed_data:
        print(f'Parsed Skills ({len(hari_resume.parsed_data.get("all_skills", []))}): {hari_resume.parsed_data.get("all_skills", [])}')
        print(f'Total Experience: {hari_resume.parsed_data.get("total_experience_years", 0)} years')

# Find a common internship they both match with
print("\n" + "=" * 80)
print("FINDING COMMON INTERNSHIPS")
print("=" * 80)

aanya_matches = db.query(StudentInternshipMatch).filter(
    StudentInternshipMatch.student_id == 15
).all()

hari_matches = db.query(StudentInternshipMatch).filter(
    StudentInternshipMatch.student_id == 63
).all()

print(f'\nAanya has {len(aanya_matches)} matches')
print(f'Hari has {len(hari_matches)} matches')

# Find common internships
aanya_internship_ids = {m.internship_id for m in aanya_matches}
hari_internship_ids = {m.internship_id for m in hari_matches}
common_internship_ids = aanya_internship_ids & hari_internship_ids

print(f'\nCommon internships: {len(common_internship_ids)}')

if common_internship_ids:
    # Pick the first common internship
    internship_id = list(common_internship_ids)[0]
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    
    print(f'\n### ANALYZING INTERNSHIP: {internship.title} ###')
    print(f'ID: {internship.id}')
    print(f'Required Skills: {internship.required_skills}')
    print(f'Preferred Skills: {internship.preferred_skills}')
    print(f'Min Experience: {internship.min_experience}')
    print(f'Max Experience: {internship.max_experience}')
    
    # Get matches for both candidates
    aanya_match = db.query(StudentInternshipMatch).filter(
        StudentInternshipMatch.student_id == 15,
        StudentInternshipMatch.internship_id == internship_id
    ).first()
    
    hari_match = db.query(StudentInternshipMatch).filter(
        StudentInternshipMatch.student_id == 63,
        StudentInternshipMatch.internship_id == internship_id
    ).first()
    
    print("\n" + "-" * 80)
    print("AANYA'S MATCH SCORES")
    print("-" * 80)
    if aanya_match:
        print(f'Overall Score: {aanya_match.base_similarity_score:.1f}%')
        print(f'Semantic Similarity: {aanya_match.semantic_similarity:.1f}%')
        print(f'Skills Match: {aanya_match.skills_match_score:.1f}%')
        print(f'Experience Match: {aanya_match.experience_match_score:.1f}%')
        
        # Calculate matched/missing skills
        if aanya_resume and aanya_resume.parsed_data:
            candidate_skills = [s.lower() for s in aanya_resume.parsed_data.get('all_skills', [])]
            required_skills = [s.lower() for s in (internship.required_skills or [])]
            preferred_skills = [s.lower() for s in (internship.preferred_skills or [])]
            all_internship_skills = required_skills + preferred_skills
            
            matched = [s for s in all_internship_skills if any(s in cs or cs in s for cs in candidate_skills)]
            missing = [s for s in required_skills if not any(s in cs or cs in s for cs in candidate_skills)]
            
            print(f'\nMatched Skills ({len(matched)}): {matched}')
            print(f'Missing Skills ({len(missing)}): {missing}')
    
    print("\n" + "-" * 80)
    print("HARI'S MATCH SCORES")
    print("-" * 80)
    if hari_match:
        print(f'Overall Score: {hari_match.base_similarity_score:.1f}%')
        print(f'Semantic Similarity: {hari_match.semantic_similarity:.1f}%')
        print(f'Skills Match: {hari_match.skills_match_score:.1f}%')
        print(f'Experience Match: {hari_match.experience_match_score:.1f}%')
        
        # Calculate matched/missing skills
        if hari_resume and hari_resume.parsed_data:
            candidate_skills = [s.lower() for s in hari_resume.parsed_data.get('all_skills', [])]
            required_skills = [s.lower() for s in (internship.required_skills or [])]
            preferred_skills = [s.lower() for s in (internship.preferred_skills or [])]
            all_internship_skills = required_skills + preferred_skills
            
            matched = [s for s in all_internship_skills if any(s in cs or cs in s for cs in candidate_skills)]
            missing = [s for s in required_skills if not any(s in cs or cs in s for cs in candidate_skills)]
            
            print(f'\nMatched Skills ({len(matched)}): {matched}')
            print(f'Missing Skills ({len(missing)}): {missing}')
    
    print("\n" + "=" * 80)
    print("SCORING WEIGHTS (from MatchingEngine)")
    print("=" * 80)
    print("Semantic Similarity: 35%")
    print("Skills Match: 30%")
    print("Experience Match: 20%")
    print("Education Match: 10%")
    print("Projects/Certifications: 5%")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    if aanya_match and hari_match:
        print(f"\nOverall Score Difference: {abs(aanya_match.base_similarity_score - hari_match.base_similarity_score):.1f}%")
        print(f"  Aanya: {aanya_match.base_similarity_score:.1f}%")
        print(f"  Hari:  {hari_match.base_similarity_score:.1f}%")
        
        print(f"\nSemantic Similarity Difference: {abs(aanya_match.semantic_similarity - hari_match.semantic_similarity):.1f}%")
        print(f"  Aanya: {aanya_match.semantic_similarity:.1f}%")
        print(f"  Hari:  {hari_match.semantic_similarity:.1f}%")
        
        print(f"\nSkills Match Difference: {abs(aanya_match.skills_match_score - hari_match.skills_match_score):.1f}%")
        print(f"  Aanya: {aanya_match.skills_match_score:.1f}%")
        print(f"  Hari:  {hari_match.skills_match_score:.1f}%")
        
        print(f"\nExperience Match Difference: {abs(aanya_match.experience_match_score - hari_match.experience_match_score):.1f}%")
        print(f"  Aanya: {aanya_match.experience_match_score:.1f}%")
        print(f"  Hari:  {hari_match.experience_match_score:.1f}%")
        
        # Calculate weighted contribution
        print("\n" + "-" * 80)
        print("WEIGHTED CONTRIBUTION TO OVERALL SCORE")
        print("-" * 80)
        
        aanya_semantic_contrib = aanya_match.semantic_similarity * 0.35
        hari_semantic_contrib = hari_match.semantic_similarity * 0.35
        print(f"Semantic Similarity (35%):")
        print(f"  Aanya: {aanya_match.semantic_similarity:.1f}% × 0.35 = {aanya_semantic_contrib:.2f}")
        print(f"  Hari:  {hari_match.semantic_similarity:.1f}% × 0.35 = {hari_semantic_contrib:.2f}")
        print(f"  Difference: {abs(aanya_semantic_contrib - hari_semantic_contrib):.2f}")
        
        aanya_skills_contrib = aanya_match.skills_match_score * 0.30
        hari_skills_contrib = hari_match.skills_match_score * 0.30
        print(f"\nSkills Match (30%):")
        print(f"  Aanya: {aanya_match.skills_match_score:.1f}% × 0.30 = {aanya_skills_contrib:.2f}")
        print(f"  Hari:  {hari_match.skills_match_score:.1f}% × 0.30 = {hari_skills_contrib:.2f}")
        print(f"  Difference: {abs(aanya_skills_contrib - hari_skills_contrib):.2f}")
        
        aanya_exp_contrib = aanya_match.experience_match_score * 0.20
        hari_exp_contrib = hari_match.experience_match_score * 0.20
        print(f"\nExperience Match (20%):")
        print(f"  Aanya: {aanya_match.experience_match_score:.1f}% × 0.20 = {aanya_exp_contrib:.2f}")
        print(f"  Hari:  {hari_match.experience_match_score:.1f}% × 0.20 = {hari_exp_contrib:.2f}")
        print(f"  Difference: {abs(aanya_exp_contrib - hari_exp_contrib):.2f}")

db.close()
print("\n" + "=" * 80)
