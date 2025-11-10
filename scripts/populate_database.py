"""
Populate SkillSync Database
Creates admin, 50 students with resumes, and 3 companies with internships
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, engine, Base
from app.models import User, UserRole, Resume, Internship
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import shutil

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_admin_user(db: Session):
    """Create admin user"""
    print("\n" + "="*60)
    print("CREATING ADMIN USER")
    print("="*60)
    
    # Check if admin exists
    existing_admin = db.query(User).filter(User.email == "admin@skillsync.com").first()
    if existing_admin:
        print("⚠ Admin user already exists. Skipping...")
        return existing_admin
    
    admin = User(
        email="admin@skillsync.com",
        hashed_password=hash_password("Admin@123"),
        full_name="System Administrator",
        role=UserRole.admin,
        is_active=1
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"✓ Admin user created")
    print(f"  Email: admin@skillsync.com")
    print(f"  Password: Admin@123")
    
    return admin

def create_50_students(db: Session):
    """Create all 50 students with their resumes"""
    print("\n" + "="*60)
    print("CREATING 50 STUDENTS")
    print("="*60)
    
    students_data = [
        ("Aarav Sharma", "aarav.sharma@student.com", "aarav_sharma_resume.txt"),
        ("Diya Patel", "diya.patel@student.com", "diya_patel_resume.txt"),
        ("Arjun Reddy", "arjun.reddy@student.com", "arjun_reddy_resume.txt"),
        ("Ananya Singh", "ananya.singh@student.com", "ananya_singh_resume.txt"),
        ("Kabir Mehta", "kabir.mehta@student.com", "kabir_mehta_resume.txt"),
        ("Ishita Kumar", "ishita.kumar@student.com", "ishita_kumar_resume.txt"),
        ("Vihaan Joshi", "vihaan.joshi@student.com", "vihaan_joshi_resume.txt"),
        ("Aanya Gupta", "aanya.gupta@student.com", "aanya_gupta_resume.txt"),
        ("Reyansh Verma", "reyansh.verma@student.com", "reyansh_verma_resume.txt"),
        ("Saanvi Rao", "saanvi.rao@student.com", "saanvi_rao_resume.txt"),
        ("Aditya Nair", "aditya.nair@student.com", "aditya_nair_resume.txt"),
        ("Myra Shah", "myra.shah@student.com", "myra_shah_resume.txt"),
        ("Advait Desai", "advait.desai@student.com", "advait_desai_resume.txt"),
        ("Kiara Iyer", "kiara.iyer@student.com", "kiara_iyer_resume.txt"),
        ("Dhruv Malhotra", "dhruv.malhotra@student.com", "dhruv_malhotra_resume.txt"),
        ("Navya Pillai", "navya.pillai@student.com", "navya_pillai_resume.txt"),
        ("Shaurya Kapoor", "shaurya.kapoor@student.com", "shaurya_kapoor_resume.txt"),
        ("Avni Menon", "avni.menon@student.com", "avni_menon_resume.txt"),
        ("Rudra Agarwal", "rudra.agarwal@student.com", "rudra_agarwal_resume.txt"),
        ("Ira Bhatt", "ira.bhatt@student.com", "ira_bhatt_resume.txt"),
        ("Ayaan Bose", "ayaan.bose@student.com", "ayaan_bose_resume.txt"),
        ("Zara Khan", "zara.khan@student.com", "zara_khan_resume.txt"),
        ("Vivaan Saxena", "vivaan.saxena@student.com", "vivaan_saxena_resume.txt"),
        ("Pihu Sinha", "pihu.sinha@student.com", "pihu_sinha_resume.txt"),
        ("Atharv Mishra", "atharv.mishra@student.com", "atharv_mishra_resume.txt"),
        ("Prisha Dutta", "prisha.dutta@student.com", "prisha_dutta_resume.txt"),
        ("Shivansh Pandey", "shivansh.pandey@student.com", "shivansh_pandey_resume.txt"),
        ("Riya Ghosh", "riya.ghosh@student.com", "riya_ghosh_resume.txt"),
        ("Arnav Choudhary", "arnav.choudhary@student.com", "arnav_choudhary_resume.txt"),
        ("Tara Roy", "tara.roy@student.com", "tara_roy_resume.txt"),
        ("Karan Bansal", "karan.bansal@student.com", "karan_bansal_resume.txt"),
        ("Mira Bajaj", "mira.bajaj@student.com", "mira_bajaj_resume.txt"),
        ("Yash Arora", "yash.arora@student.com", "yash_arora_resume.txt"),
        ("Aadhya Kohli", "aadhya.kohli@student.com", "aadhya_kohli_resume.txt"),
        ("Sai Reddy", "sai.reddy@student.com", "sai_reddy_resume.txt"),
        ("Nora Das", "nora.das@student.com", "nora_das_resume.txt"),
        ("Rohan Kulkarni", "rohan.kulkarni@student.com", "rohan_kulkarni_resume.txt"),
        ("Kavya Hegde", "kavya.hegde@student.com", "kavya_hegde_resume.txt"),
        ("Pranav Jain", "pranav.jain@student.com", "pranav_jain_resume.txt"),
        ("Aarohi Mukherjee", "aarohi.mukherjee@student.com", "aarohi_mukherjee_resume.txt"),
        ("Vedant Trivedi", "vedant.trivedi@student.com", "vedant_trivedi_resume.txt"),
        ("Samara Yadav", "samara.yadav@student.com", "samara_yadav_resume.txt"),
        ("Lakshya Soni", "lakshya.soni@student.com", "lakshya_soni_resume.txt"),
        ("Advika Tiwari", "advika.tiwari@student.com", "advika_tiwari_resume.txt"),
        ("Krish Mathur", "krish.mathur@student.com", "krish_mathur_resume.txt"),
        ("Shanaya Chopra", "shanaya.chopra@student.com", "shanaya_chopra_resume.txt"),
        ("Ayan Chatterjee", "ayan.chatterjee@student.com", "ayan_chatterjee_resume.txt"),
        ("Aadhira Sharma", "aadhira.sharma@student.com", "aadhira_sharma_resume.txt"),
        ("Mihir Bhattacharya", "mihir.bhattacharya@student.com", "mihir_bhattacharya_resume.txt"),
        ("Keya Dubey", "keya.dubey@student.com", "keya_dubey_resume.txt"),
    ]
    
    # Also add the 3 special students from DATABASE_CREDENTIALS
    special_students = [
        ("Alex Kumar", "alex.kumar@email.com", "software_engineer_resume.txt"),
        ("Priya Sharma", "priya.sharma@email.com", "game_developer_resume.txt"),
        ("Rahul Verma", "rahul.verma@email.com", "blockchain_developer_resume.txt"),
    ]
    
    all_students = students_data + special_students
    created_count = 0
    resume_path = Path(__file__).parent.parent / "app" / "public" / "resumes"
    
    for name, email, resume_file in all_students:
        # Check if student already exists
        existing_student = db.query(User).filter(User.email == email).first()
        if existing_student:
            print(f"⚠ {name} already exists. Skipping...")
            continue
        
        # Determine password based on which list
        if email in [s[1] for s in special_students]:
            password = name.split()[0] + "2024"  # Alex2024, Priya2024, Rahul2024
        else:
            password = "Student@123"
        
        # Create student user
        student = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=name,
            role=UserRole.student,
            is_active=1
        )
        
        db.add(student)
        db.flush()  # Get the student ID
        
        # Create resume entry if file exists
        resume_file_path = resume_path / resume_file
        if resume_file_path.exists():
            resume = Resume(
                student_id=student.id,
                file_path=f"resumes/{resume_file}",
                file_name=resume_file
            )
            db.add(resume)
        
        created_count += 1
        print(f"✓ Created: {name} ({email})")
    
    db.commit()
    
    print(f"\n✓ Successfully created {created_count} students")
    print(f"  Password for students 1-50: Student@123")
    print(f"  Password for Alex Kumar: Alex2024")
    print(f"  Password for Priya Sharma: Priya2024")
    print(f"  Password for Rahul Verma: Rahul2024")
    
    return created_count

def create_companies_and_internships(db: Session):
    """Create 3 companies with their internships"""
    print("\n" + "="*60)
    print("CREATING COMPANIES AND INTERNSHIPS")
    print("="*60)
    
    companies_data = [
        {
            "name": "TechCorp Solutions",
            "email": "hr@techcorp.com",
            "password": "TechCorp2024",
            "internships": [
                {
                    "title": "Full Stack Software Engineer Intern",
                    "description": "Join our team to build scalable web applications using React, Node.js, and PostgreSQL. Work on real-world projects and learn from experienced engineers.",
                    "required_skills": ["React", "Node.js", "PostgreSQL", "JavaScript", "TypeScript", "REST API", "Git"],
                    "location": "Bangalore, India",
                    "duration": "6 months",
                    "stipend": 30000
                },
                {
                    "title": "Backend Developer Intern",
                    "description": "Develop robust backend services using Python, FastAPI, Docker, and AWS. Learn microservices architecture and cloud deployment.",
                    "required_skills": ["Python", "FastAPI", "Docker", "AWS", "PostgreSQL", "REST API", "CI/CD"],
                    "location": "Mumbai, India",
                    "duration": "6 months",
                    "stipend": 28000
                },
                {
                    "title": "Mobile App Developer Intern",
                    "description": "Build cross-platform mobile applications using React Native. Work on iOS and Android apps with modern UI/UX.",
                    "required_skills": ["React Native", "JavaScript", "TypeScript", "Mobile Development", "Redux", "Firebase"],
                    "location": "Hyderabad, India",
                    "duration": "4 months",
                    "stipend": 25000
                }
            ]
        },
        {
            "name": "Epic Game Studios",
            "email": "careers@gamestudio.com",
            "password": "GameStudio2024",
            "internships": [
                {
                    "title": "Game Developer Intern",
                    "description": "Create immersive gaming experiences using Unity and C#. Work on gameplay mechanics, physics, and AI systems.",
                    "required_skills": ["Unity", "C#", "Game Development", "3D Modeling", "Physics", "AI"],
                    "location": "Pune, India",
                    "duration": "6 months",
                    "stipend": 32000
                },
                {
                    "title": "Graphics Programming Intern",
                    "description": "Develop stunning graphics using Unreal Engine and C++. Work on shaders, rendering, and optimization.",
                    "required_skills": ["Unreal Engine", "C++", "Shaders", "Graphics Programming", "OpenGL", "DirectX"],
                    "location": "Bangalore, India",
                    "duration": "6 months",
                    "stipend": 35000
                },
                {
                    "title": "Game Design Intern",
                    "description": "Design engaging game levels and mechanics. Work on user experience, game balance, and player engagement.",
                    "required_skills": ["Game Design", "Level Design", "UX", "Unity", "Game Mechanics", "Balancing"],
                    "location": "Remote",
                    "duration": "4 months",
                    "stipend": 20000
                }
            ]
        },
        {
            "name": "Blockchain Labs Inc",
            "email": "hiring@blockchainlabs.com",
            "password": "BlockLabs2024",
            "internships": [
                {
                    "title": "Blockchain Developer Intern",
                    "description": "Build decentralized applications and smart contracts using Solidity and Ethereum. Learn Web3 development.",
                    "required_skills": ["Solidity", "Ethereum", "Smart Contracts", "Web3.js", "Blockchain", "DeFi"],
                    "location": "Delhi, India",
                    "duration": "6 months",
                    "stipend": 40000
                },
                {
                    "title": "DeFi Protocol Engineer Intern",
                    "description": "Develop DeFi protocols and ensure smart contract security. Work on lending, staking, and DEX platforms.",
                    "required_skills": ["DeFi", "Solidity", "Smart Contract Security", "Ethereum", "Hardhat", "Testing"],
                    "location": "Bangalore, India",
                    "duration": "6 months",
                    "stipend": 45000
                },
                {
                    "title": "Crypto Backend Developer Intern",
                    "description": "Build backend services for blockchain applications using Node.js and blockchain APIs.",
                    "required_skills": ["Node.js", "Blockchain APIs", "Web3.js", "MongoDB", "REST API", "Microservices"],
                    "location": "Mumbai, India",
                    "duration": "5 months",
                    "stipend": 35000
                }
            ]
        }
    ]
    
    company_count = 0
    internship_count = 0
    
    for company_data in companies_data:
        # Check if company exists
        existing_company = db.query(User).filter(User.email == company_data["email"]).first()
        if existing_company:
            print(f"\n⚠ {company_data['name']} already exists. Skipping...")
            continue
        
        # Create company user
        company = User(
            email=company_data["email"],
            hashed_password=hash_password(company_data["password"]),
            full_name=company_data["name"],
            role=UserRole.company,
            is_active=1
        )
        
        db.add(company)
        db.flush()  # Get company ID
        
        print(f"\n✓ Created company: {company_data['name']}")
        print(f"  Email: {company_data['email']}")
        print(f"  Password: {company_data['password']}")
        
        company_count += 1
        
        # Create internships for this company
        for internship_data in company_data["internships"]:
            internship = Internship(
                company_id=company.id,
                title=internship_data["title"],
                description=internship_data["description"],
                required_skills=internship_data["required_skills"],
                location=internship_data["location"],
                duration=internship_data["duration"],
                stipend=str(internship_data["stipend"]),
                is_active=1
            )
            
            db.add(internship)
            internship_count += 1
            print(f"  ✓ Posted: {internship_data['title']}")
        
        db.commit()
    
    print(f"\n✓ Successfully created {company_count} companies")
    print(f"✓ Successfully posted {internship_count} internships")
    
    return company_count, internship_count

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("SKILLSYNC DATABASE POPULATION SCRIPT")
    print("="*60)
    
    # Create tables
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # 1. Create admin user
        admin = create_admin_user(db)
        
        # 2. Create 50 students with resumes
        student_count = create_50_students(db)
        
        # 3. Create companies and internships
        company_count, internship_count = create_companies_and_internships(db)
        
        # Summary
        print("\n" + "="*60)
        print("DATABASE POPULATION COMPLETE!")
        print("="*60)
        print(f"\n✓ Admin user: 1")
        print(f"✓ Students: {student_count}")
        print(f"✓ Companies: {company_count}")
        print(f"✓ Internships: {internship_count}")
        
        print("\n" + "="*60)
        print("LOGIN CREDENTIALS SUMMARY")
        print("="*60)
        
        print("\n🔐 ADMIN:")
        print("  Email: admin@skillsync.com")
        print("  Password: Admin@123")
        
        print("\n👥 STUDENTS (50):")
        print("  Email: [name]@student.com (e.g., aarav.sharma@student.com)")
        print("  Password: Student@123")
        
        print("\n👥 SPECIAL STUDENTS (3):")
        print("  alex.kumar@email.com / Alex2024")
        print("  priya.sharma@email.com / Priya2024")
        print("  rahul.verma@email.com / Rahul2024")
        
        print("\n🏢 COMPANIES:")
        print("  hr@techcorp.com / TechCorp2024")
        print("  careers@gamestudio.com / GameStudio2024")
        print("  hiring@blockchainlabs.com / BlockLabs2024")
        
        print("\n" + "="*60)
        print("Next Steps:")
        print("1. Start backend: uvicorn app.main:app --reload")
        print("2. Start frontend: npm run dev")
        print("3. Login and test the platform!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())