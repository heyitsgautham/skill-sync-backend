import sys
sys.path.append('.')
from app.database.connection import SessionLocal
from app.models.resume import Resume
from app.models.user import User
from app.services.rag_engine import rag_engine

# Test matching for Game Developer Intern (ID: 4)
print('🎮 Testing matches for Game Developer Intern (ID: 4)')
print('=' * 80)

matches = rag_engine.find_matching_candidates('4', top_k=10)
print(f'\n✅ Found {len(matches)} matching candidates!\n')

db = SessionLocal()

print('Top 10 Matched Candidates:')
print('-' * 80)

for i, match in enumerate(matches, 1):
    resume = db.query(Resume).filter(Resume.id == int(match['resume_id'])).first()
    if resume:
        student = db.query(User).filter(User.id == resume.student_id).first()
        if student:
            skills_str = ', '.join(match['skills'][:4])
            print(f'{i:2d}. {student.full_name:25s} | Score: {match["match_score"]:3d}% | Skills: {skills_str}...')

db.close()
