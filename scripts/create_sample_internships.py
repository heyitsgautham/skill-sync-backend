"""
Script to add sample internships to the database for testing
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import SessionLocal
from app.models import User, Internship, UserRole
from app.services.rag_engine import rag_engine


def create_sample_internships():
    """Create sample internship postings"""
    db = SessionLocal()
    
    try:
        # First, check if we have a company user, if not create one
        company_user = db.query(User).filter(User.role == UserRole.company).first()
        
        if not company_user:
            print("No company user found. Creating a sample company user...")
            from app.utils.security import hash_password
            
            company_user = User(
                email="techcorp@example.com",
                password_hash=hash_password("password123"),
                full_name="TechCorp Inc.",
                role=UserRole.company
            )
            db.add(company_user)
            db.commit()
            db.refresh(company_user)
            print(f"✅ Created company user: {company_user.full_name}")
        
        # Sample internships data
        sample_internships = [
            {
                "title": "Full Stack Developer Intern",
                "description": "Join our development team to work on cutting-edge web applications. You'll be working with React, Node.js, and PostgreSQL to build scalable solutions. Perfect for students looking to gain hands-on experience in modern web development.",
                "required_skills": ["React", "Node.js", "JavaScript", "PostgreSQL", "Git"],
                "location": "Bangalore, India",
                "duration": "6 months",
                "stipend": "₹25,000/month"
            },
            {
                "title": "Data Science Intern",
                "description": "Work with our data science team on machine learning projects. You'll be analyzing large datasets, building predictive models, and creating data visualizations. Experience with Python, pandas, and scikit-learn is required.",
                "required_skills": ["Python", "Machine Learning", "Pandas", "NumPy", "SQL"],
                "location": "Mumbai, India",
                "duration": "4 months",
                "stipend": "₹30,000/month"
            },
            {
                "title": "Mobile App Development Intern",
                "description": "Help us build amazing mobile applications for iOS and Android platforms. You'll work with Flutter/React Native to create cross-platform applications. Great opportunity to learn mobile development best practices.",
                "required_skills": ["Flutter", "Dart", "React Native", "JavaScript", "Mobile UI/UX"],
                "location": "Hyderabad, India",
                "duration": "5 months",
                "stipend": "₹22,000/month"
            },
            {
                "title": "DevOps Engineer Intern",
                "description": "Join our infrastructure team to learn about cloud computing, CI/CD pipelines, and container orchestration. You'll work with AWS, Docker, Kubernetes, and Jenkins to automate deployment processes.",
                "required_skills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD"],
                "location": "Pune, India",
                "duration": "6 months",
                "stipend": "₹28,000/month"
            },
            {
                "title": "UI/UX Design Intern",
                "description": "Work alongside our design team to create beautiful and intuitive user interfaces. You'll be involved in user research, wireframing, prototyping, and visual design. Experience with Figma and Adobe XD is preferred.",
                "required_skills": ["Figma", "Adobe XD", "UI Design", "UX Research", "Prototyping"],
                "location": "Delhi, India",
                "duration": "3 months",
                "stipend": "₹20,000/month"
            },
            {
                "title": "Backend Developer Intern",
                "description": "Build robust and scalable backend systems using Python/Django or Java/Spring Boot. You'll work on RESTful APIs, database design, and microservices architecture. Strong understanding of OOP and design patterns required.",
                "required_skills": ["Python", "Django", "REST API", "PostgreSQL", "Redis"],
                "location": "Bangalore, India",
                "duration": "6 months",
                "stipend": "₹26,000/month"
            },
            {
                "title": "Machine Learning Engineer Intern",
                "description": "Contribute to our AI/ML projects by developing and deploying machine learning models. You'll work on natural language processing, computer vision, and recommendation systems using TensorFlow and PyTorch.",
                "required_skills": ["TensorFlow", "PyTorch", "Python", "Deep Learning", "NLP"],
                "location": "Bangalore, India",
                "duration": "6 months",
                "stipend": "₹35,000/month"
            },
            {
                "title": "Frontend Developer Intern",
                "description": "Create responsive and interactive user interfaces using modern JavaScript frameworks. You'll work with React, Vue.js, or Angular to build single-page applications with great user experiences.",
                "required_skills": ["React", "JavaScript", "HTML", "CSS", "TypeScript"],
                "location": "Chennai, India",
                "duration": "4 months",
                "stipend": "₹24,000/month"
            },
            {
                "title": "Cybersecurity Intern",
                "description": "Learn about security best practices and help protect our infrastructure. You'll work on vulnerability assessments, penetration testing, and security monitoring. Knowledge of networking and security tools is beneficial.",
                "required_skills": ["Network Security", "Python", "Linux", "Penetration Testing", "Security Tools"],
                "location": "Mumbai, India",
                "duration": "5 months",
                "stipend": "₹27,000/month"
            },
            {
                "title": "Business Analyst Intern",
                "description": "Bridge the gap between business and technology teams. You'll gather requirements, create documentation, and analyze business processes. Strong analytical and communication skills are essential.",
                "required_skills": ["Business Analysis", "SQL", "Excel", "Documentation", "Agile"],
                "location": "Gurgaon, India",
                "duration": "4 months",
                "stipend": "₹21,000/month"
            }
        ]
        
        # Check if internships already exist
        existing_count = db.query(Internship).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} internships.")
            response = input("Do you want to add more sample internships? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        
        # Create internships
        created_count = 0
        for internship_data in sample_internships:
            internship = Internship(
                company_id=company_user.id,
                title=internship_data["title"],
                description=internship_data["description"],
                required_skills=internship_data["required_skills"],
                location=internship_data["location"],
                duration=internship_data["duration"],
                stipend=internship_data["stipend"],
                is_active=1
            )
            
            db.add(internship)
            db.commit()
            db.refresh(internship)
            
            # Store in vector DB
            try:
                rag_engine.store_internship_embedding(
                    internship_id=str(internship.id),
                    title=internship.title,
                    description=internship.description,
                    required_skills=internship.required_skills,
                    metadata={
                        "company_id": company_user.id,
                        "location": internship.location,
                        "duration": internship.duration
                    }
                )
            except Exception as e:
                print(f"⚠️  Warning: Could not create embedding for {internship.title}: {e}")
            
            created_count += 1
            print(f"✅ Created: {internship.title}")
        
        print(f"\n🎉 Successfully created {created_count} sample internships!")
        print(f"📊 Total internships in database: {db.query(Internship).count()}")
        
    except Exception as e:
        print(f"❌ Error creating sample internships: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Sample Internships for Testing")
    print("=" * 60)
    create_sample_internships()
