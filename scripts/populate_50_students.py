"""
Script to create 50 students with resumes that match internships
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.resume import Resume
from app.models.internship import Internship
from app.utils.security import get_password_hash
import json
from datetime import datetime

# Create all tables
Base.metadata.create_all(bind=engine)

# Student data with diverse skills matching various internships
STUDENTS_DATA = [
    # Full Stack Developers (10 students)
    {
        "name": "Aarav Sharma", 
        "email": "aarav.sharma@student.com",
        "skills": ["Python", "JavaScript", "React", "Node.js", "MongoDB", "Express.js", "REST API", "Git"],
        "experience": "Built 3 full-stack projects including e-commerce platform and social media app"
    },
    {
        "name": "Diya Patel", 
        "email": "diya.patel@student.com",
        "skills": ["Java", "Spring Boot", "React", "PostgreSQL", "Docker", "AWS", "Microservices", "Git"],
        "experience": "Developed microservices-based applications with Spring Boot and React frontend"
    },
    {
        "name": "Arjun Reddy", 
        "email": "arjun.reddy@student.com",
        "skills": ["TypeScript", "Next.js", "Node.js", "GraphQL", "MongoDB", "Redis", "Jest", "Git"],
        "experience": "Created real-time collaboration tools and GraphQL APIs"
    },
    {
        "name": "Ananya Singh", 
        "email": "ananya.singh@student.com",
        "skills": ["Python", "Django", "Vue.js", "MySQL", "Docker", "CI/CD", "REST API", "Git"],
        "experience": "Built scalable web applications using Django and Vue.js"
    },
    {
        "name": "Kabir Mehta", 
        "email": "kabir.mehta@student.com",
        "skills": ["JavaScript", "React", "Node.js", "Express", "MongoDB", "Socket.io", "AWS", "Git"],
        "experience": "Developed real-time chat applications and REST APIs"
    },
    {
        "name": "Ishita Kumar", 
        "email": "ishita.kumar@student.com",
        "skills": ["Python", "Flask", "React", "PostgreSQL", "Docker", "Kubernetes", "REST API", "Git"],
        "experience": "Created containerized applications with Flask backend and React frontend"
    },
    {
        "name": "Vihaan Joshi", 
        "email": "vihaan.joshi@student.com",
        "skills": ["Java", "Spring Boot", "Angular", "MySQL", "Docker", "Jenkins", "Microservices", "Git"],
        "experience": "Built enterprise applications using Spring Boot and Angular"
    },
    {
        "name": "Aanya Gupta", 
        "email": "aanya.gupta@student.com",
        "skills": ["TypeScript", "React", "Node.js", "PostgreSQL", "GraphQL", "Docker", "AWS", "Git"],
        "experience": "Developed GraphQL APIs and React applications with TypeScript"
    },
    {
        "name": "Reyansh Verma", 
        "email": "reyansh.verma@student.com",
        "skills": ["Python", "FastAPI", "React", "MongoDB", "Docker", "Redis", "Celery", "Git"],
        "experience": "Created high-performance APIs using FastAPI and async programming"
    },
    {
        "name": "Saanvi Rao", 
        "email": "saanvi.rao@student.com",
        "skills": ["JavaScript", "Vue.js", "Node.js", "MySQL", "Docker", "CI/CD", "REST API", "Git"],
        "experience": "Built progressive web apps using Vue.js and Node.js"
    },
    
    # Data Science & ML (10 students)
    {
        "name": "Aditya Nair", 
        "email": "aditya.nair@student.com",
        "skills": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Machine Learning", "Deep Learning"],
        "experience": "Developed ML models for image classification and NLP tasks"
    },
    {
        "name": "Myra Shah", 
        "email": "myra.shah@student.com",
        "skills": ["Python", "Data Analysis", "SQL", "Tableau", "Power BI", "Statistics", "Excel", "Pandas"],
        "experience": "Analyzed large datasets and created interactive dashboards"
    },
    {
        "name": "Advait Desai", 
        "email": "advait.desai@student.com",
        "skills": ["Python", "Machine Learning", "Deep Learning", "Computer Vision", "OpenCV", "TensorFlow", "Keras", "Git"],
        "experience": "Built computer vision models for object detection and facial recognition"
    },
    {
        "name": "Kiara Iyer", 
        "email": "kiara.iyer@student.com",
        "skills": ["Python", "NLP", "NLTK", "spaCy", "Transformers", "Hugging Face", "PyTorch", "Git"],
        "experience": "Created NLP models for sentiment analysis and text classification"
    },
    {
        "name": "Dhruv Malhotra", 
        "email": "dhruv.malhotra@student.com",
        "skills": ["Python", "Data Science", "Pandas", "NumPy", "Matplotlib", "Seaborn", "SQL", "Git"],
        "experience": "Performed data analysis and visualization for business insights"
    },
    {
        "name": "Navya Pillai", 
        "email": "navya.pillai@student.com",
        "skills": ["Python", "Machine Learning", "Scikit-learn", "TensorFlow", "Feature Engineering", "Model Deployment", "Flask", "Git"],
        "experience": "Deployed ML models in production using Flask and Docker"
    },
    {
        "name": "Shaurya Kapoor", 
        "email": "shaurya.kapoor@student.com",
        "skills": ["Python", "Deep Learning", "PyTorch", "CNNs", "RNNs", "GANs", "Transfer Learning", "Git"],
        "experience": "Implemented deep learning models for image generation and sequence modeling"
    },
    {
        "name": "Avni Menon", 
        "email": "avni.menon@student.com",
        "skills": ["Python", "Data Analysis", "SQL", "Big Data", "Spark", "Hadoop", "ETL", "Git"],
        "experience": "Processed large datasets using Spark and Hadoop"
    },
    {
        "name": "Rudra Agarwal", 
        "email": "rudra.agarwal@student.com",
        "skills": ["Python", "Machine Learning", "Time Series Analysis", "Forecasting", "Statistics", "R", "SQL", "Git"],
        "experience": "Built forecasting models for sales and demand prediction"
    },
    {
        "name": "Ira Bhatt", 
        "email": "ira.bhatt@student.com",
        "skills": ["Python", "Deep Learning", "Reinforcement Learning", "TensorFlow", "PyTorch", "OpenAI Gym", "Neural Networks", "Git"],
        "experience": "Developed reinforcement learning agents for game playing"
    },
    
    # Mobile App Developers (8 students)
    {
        "name": "Ayaan Bose", 
        "email": "ayaan.bose@student.com",
        "skills": ["React Native", "JavaScript", "TypeScript", "Redux", "Firebase", "REST API", "Mobile Development", "Git"],
        "experience": "Built cross-platform mobile apps using React Native"
    },
    {
        "name": "Zara Khan", 
        "email": "zara.khan@student.com",
        "skills": ["Flutter", "Dart", "Firebase", "Provider", "REST API", "Mobile Development", "Git", "SQLite"],
        "experience": "Developed beautiful mobile apps using Flutter and Firebase"
    },
    {
        "name": "Vivaan Saxena", 
        "email": "vivaan.saxena@student.com",
        "skills": ["Android", "Kotlin", "Java", "Jetpack Compose", "Room", "Retrofit", "MVVM", "Git"],
        "experience": "Created native Android apps with modern architecture"
    },
    {
        "name": "Pihu Sinha", 
        "email": "pihu.sinha@student.com",
        "skills": ["iOS", "Swift", "SwiftUI", "Core Data", "Combine", "REST API", "MVVM", "Git"],
        "experience": "Built iOS applications using SwiftUI and modern design patterns"
    },
    {
        "name": "Atharv Mishra", 
        "email": "atharv.mishra@student.com",
        "skills": ["React Native", "JavaScript", "Redux", "GraphQL", "Firebase", "Push Notifications", "Mobile Development", "Git"],
        "experience": "Developed social media mobile apps with real-time features"
    },
    {
        "name": "Prisha Dutta", 
        "email": "prisha.dutta@student.com",
        "skills": ["Flutter", "Dart", "BLoC", "Firebase", "Google Maps API", "REST API", "Mobile Development", "Git"],
        "experience": "Created location-based mobile applications"
    },
    {
        "name": "Shivansh Pandey", 
        "email": "shivansh.pandey@student.com",
        "skills": ["Android", "Kotlin", "Jetpack", "Compose", "Coroutines", "Retrofit", "Clean Architecture", "Git"],
        "experience": "Built scalable Android apps with clean architecture"
    },
    {
        "name": "Riya Ghosh", 
        "email": "riya.ghosh@student.com",
        "skills": ["iOS", "Swift", "UIKit", "SwiftUI", "Core Data", "Alamofire", "MVC", "Git"],
        "experience": "Developed feature-rich iOS applications"
    },
    
    # DevOps & Cloud (6 students)
    {
        "name": "Arnav Choudhary", 
        "email": "arnav.choudhary@student.com",
        "skills": ["AWS", "Docker", "Kubernetes", "Jenkins", "Terraform", "CI/CD", "Linux", "Git"],
        "experience": "Implemented CI/CD pipelines and managed cloud infrastructure"
    },
    {
        "name": "Tara Roy", 
        "email": "tara.roy@student.com",
        "skills": ["Azure", "Docker", "Kubernetes", "Ansible", "CI/CD", "Monitoring", "Linux", "Git"],
        "experience": "Automated infrastructure deployment using Ansible and Terraform"
    },
    {
        "name": "Karan Bansal", 
        "email": "karan.bansal@student.com",
        "skills": ["GCP", "Docker", "Kubernetes", "GitLab CI", "Terraform", "Cloud Architecture", "Linux", "Git"],
        "experience": "Designed and deployed scalable cloud architectures"
    },
    {
        "name": "Mira Bajaj", 
        "email": "mira.bajaj@student.com",
        "skills": ["AWS", "Docker", "Jenkins", "Python", "Bash", "CI/CD", "Monitoring", "Git"],
        "experience": "Built automated deployment pipelines and monitoring systems"
    },
    {
        "name": "Yash Arora", 
        "email": "yash.arora@student.com",
        "skills": ["Docker", "Kubernetes", "Helm", "Prometheus", "Grafana", "ELK Stack", "Linux", "Git"],
        "experience": "Set up monitoring and logging infrastructure"
    },
    {
        "name": "Aadhya Kohli", 
        "email": "aadhya.kohli@student.com",
        "skills": ["AWS", "Serverless", "Lambda", "API Gateway", "DynamoDB", "CloudFormation", "Python", "Git"],
        "experience": "Built serverless applications on AWS"
    },
    
    # Blockchain & Web3 (5 students)
    {
        "name": "Sai Reddy", 
        "email": "sai.reddy@student.com",
        "skills": ["Solidity", "Ethereum", "Web3.js", "Hardhat", "Smart Contracts", "DeFi", "React", "Git"],
        "experience": "Developed DeFi protocols and smart contracts"
    },
    {
        "name": "Nora Das", 
        "email": "nora.das@student.com",
        "skills": ["Blockchain", "Solidity", "Ethers.js", "NFTs", "IPFS", "React", "Web3", "Git"],
        "experience": "Created NFT marketplaces and Web3 applications"
    },
    {
        "name": "Rohan Kulkarni", 
        "email": "rohan.kulkarni@student.com",
        "skills": ["Rust", "Solana", "Smart Contracts", "Web3", "Blockchain", "TypeScript", "React", "Git"],
        "experience": "Built applications on Solana blockchain"
    },
    {
        "name": "Kavya Hegde", 
        "email": "kavya.hegde@student.com",
        "skills": ["Solidity", "Ethereum", "Truffle", "Web3.js", "Smart Contract Security", "DApps", "JavaScript", "Git"],
        "experience": "Audited smart contracts and developed secure DApps"
    },
    {
        "name": "Pranav Jain", 
        "email": "pranav.jain@student.com",
        "skills": ["Blockchain", "Hyperledger Fabric", "Chaincode", "Node.js", "Docker", "Smart Contracts", "Go", "Git"],
        "experience": "Developed enterprise blockchain solutions"
    },
    
    # Cybersecurity (4 students)
    {
        "name": "Aarohi Mukherjee", 
        "email": "aarohi.mukherjee@student.com",
        "skills": ["Cybersecurity", "Penetration Testing", "Ethical Hacking", "Python", "Kali Linux", "Network Security", "OWASP", "Git"],
        "experience": "Conducted security assessments and vulnerability testing"
    },
    {
        "name": "Vedant Trivedi", 
        "email": "vedant.trivedi@student.com",
        "skills": ["Security", "Cryptography", "Python", "C++", "Network Security", "Firewalls", "IDS/IPS", "Git"],
        "experience": "Implemented security solutions and encryption systems"
    },
    {
        "name": "Samara Yadav", 
        "email": "samara.yadav@student.com",
        "skills": ["Cybersecurity", "SOC", "SIEM", "Splunk", "Threat Analysis", "Incident Response", "Python", "Git"],
        "experience": "Monitored security events and responded to incidents"
    },
    {
        "name": "Lakshya Soni", 
        "email": "lakshya.soni@student.com",
        "skills": ["Application Security", "OWASP", "Burp Suite", "Python", "Security Testing", "Web Security", "Penetration Testing", "Git"],
        "experience": "Performed web application security testing"
    },
    
    # Game Development (3 students)
    {
        "name": "Advika Tiwari", 
        "email": "advika.tiwari@student.com",
        "skills": ["Unity", "C#", "Game Development", "3D Modeling", "Blender", "Game Design", "Physics", "Git"],
        "experience": "Created 3D games using Unity and C#"
    },
    {
        "name": "Krish Mathur", 
        "email": "krish.mathur@student.com",
        "skills": ["Unreal Engine", "C++", "Game Development", "Blueprints", "3D Graphics", "Game Design", "Animation", "Git"],
        "experience": "Developed AAA-quality games using Unreal Engine"
    },
    {
        "name": "Shanaya Chopra", 
        "email": "shanaya.chopra@student.com",
        "skills": ["Unity", "C#", "2D Game Development", "Mobile Games", "AR/VR", "Game Design", "Photoshop", "Git"],
        "experience": "Built mobile and AR games"
    },
    
    # UI/UX & Frontend (4 students)
    {
        "name": "Ayan Chatterjee", 
        "email": "ayan.chatterjee@student.com",
        "skills": ["UI/UX Design", "Figma", "Adobe XD", "User Research", "Wireframing", "Prototyping", "HTML", "CSS"],
        "experience": "Designed user interfaces for web and mobile applications"
    },
    {
        "name": "Aadhira Sharma", 
        "email": "aadhira.sharma@student.com",
        "skills": ["React", "TypeScript", "Tailwind CSS", "Responsive Design", "HTML5", "CSS3", "JavaScript", "Git"],
        "experience": "Built beautiful responsive websites with modern frameworks"
    },
    {
        "name": "Mihir Bhattacharya", 
        "email": "mihir.bhattacharya@student.com",
        "skills": ["Frontend", "Vue.js", "Nuxt.js", "Sass", "Webpack", "JavaScript", "HTML", "Git"],
        "experience": "Created dynamic web applications with Vue.js"
    },
    {
        "name": "Keya Dubey", 
        "email": "keya.dubey@student.com",
        "skills": ["UI/UX", "Figma", "React", "Animation", "Framer Motion", "Design Systems", "HTML", "CSS"],
        "experience": "Designed and implemented interactive user interfaces"
    },
]

def create_resume_content(student):
    """Generate resume content for a student"""
    skills_str = ", ".join(student["skills"])
    
    content = f"""
{student['name'].upper()}
Email: {student['email']} | Phone: +91-{9000000000 + STUDENTS_DATA.index(student)}
LinkedIn: linkedin.com/in/{student['name'].lower().replace(' ', '')} | GitHub: github.com/{student['name'].lower().replace(' ', '')}

EDUCATION
Bachelor of Technology in Computer Science
Prestigious Institute of Technology | 2022 - 2026 | CGPA: {8.0 + (STUDENTS_DATA.index(student) % 20) * 0.05:.1f}/10

TECHNICAL SKILLS
{skills_str}

EXPERIENCE
{student['experience']}

PROJECTS
Project 1: Built innovative solutions using {student['skills'][0]} and {student['skills'][1]}
• Implemented core features with {student['skills'][2]}
• Collaborated with team using Git and Agile methodologies
• Achieved 95% test coverage and optimized performance

Project 2: Developed application using {student['skills'][3]} and {student['skills'][4]}
• Designed scalable architecture
• Integrated with third-party APIs
• Deployed to production environment

ACHIEVEMENTS
• Won hackathon for innovative solution
• Contributed to open-source projects
• Published technical blog posts
• Mentored junior students

CERTIFICATIONS
• Certified in {student['skills'][0]}
• Completed online courses in {student['skills'][1]} and {student['skills'][2]}
"""
    return content

def populate_students():
    """Populate database with 50 students and their resumes"""
    db: Session = SessionLocal()
    
    try:
        # Default password for all students
        default_password = "Student@123"
        hashed_password = get_password_hash(default_password)
        
        print("Creating 50 students with resumes...")
        print("=" * 80)
        
        created_students = []
        
        for student_data in STUDENTS_DATA:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == student_data["email"]).first()
            if existing_user:
                print(f"✓ Student {student_data['name']} already exists, skipping...")
                continue
            
            # Create user
            user = User(
                email=student_data["email"],
                hashed_password=hashed_password,
                full_name=student_data["name"],
                role=UserRole.student,
                is_active=1
            )
            db.add(user)
            db.flush()  # Get the user ID
            
            # Generate resume content
            resume_content = create_resume_content(student_data)
            
            # Create resume file
            resume_dir = "app/public/resumes"
            os.makedirs(resume_dir, exist_ok=True)
            file_name = f"{student_data['name'].lower().replace(' ', '_')}_resume.txt"
            file_path = os.path.join(resume_dir, file_name)
            
            with open(file_path, 'w') as f:
                f.write(resume_content)
            
            # Create resume record
            resume = Resume(
                student_id=user.id,
                file_path=file_path,
                file_name=file_name,
                parsed_content=resume_content,
                extracted_skills=student_data["skills"],
                is_active=1
            )
            db.add(resume)
            
            created_students.append({
                "name": student_data["name"],
                "email": student_data["email"],
                "password": default_password
            })
            
            print(f"✓ Created: {student_data['name']} ({student_data['email']})")
        
        db.commit()
        
        print("\n" + "=" * 80)
        print(f"Successfully created {len(created_students)} students!")
        print("=" * 80)
        
        # Generate credentials file
        credentials_file = "STUDENT_CREDENTIALS.txt"
        with open(credentials_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("STUDENT LOGIN CREDENTIALS\n")
            f.write("=" * 80 + "\n\n")
            f.write("All students have the same password: Student@123\n\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'#':<5} {'Name':<25} {'Email':<40} {'Password':<15}\n")
            f.write("-" * 80 + "\n")
            
            for idx, student in enumerate(created_students, 1):
                f.write(f"{idx:<5} {student['name']:<25} {student['email']:<40} {student['password']:<15}\n")
            
            f.write("-" * 80 + "\n")
            f.write(f"\nTotal Students: {len(created_students)}\n")
        
        print(f"\n✓ Credentials saved to: {credentials_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("STUDENT CREDENTIALS SUMMARY")
        print("=" * 80)
        print(f"\nAll 50 students have been created with the password: {default_password}")
        print("\nEmail addresses follow the pattern: firstname.lastname@student.com")
        print(f"\nDetailed credentials have been saved to: {credentials_file}")
        
        return created_students
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    students = populate_students()
    
    print("\n" + "=" * 80)
    print("QUICK REFERENCE - SAMPLE STUDENT CREDENTIALS")
    print("=" * 80)
    print("\nPassword for all students: Student@123")
    print("\nSample emails:")
    for i, student in enumerate(students[:10], 1):
        print(f"{i}. {student['email']}")
    print(f"\n... and {len(students) - 10} more students")
    print(f"\nCheck STUDENT_CREDENTIALS.txt for complete list")
