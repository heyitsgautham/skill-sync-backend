#!/usr/bin/env python3
"""
Create varied internships to test RAG matching system
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import get_db
from app.models import Internship, User, UserRole
from app.services.rag_engine import rag_engine

def create_varied_internships():
    """Create internships with varying skill matches"""
    db = next(get_db())
    
    # Get a company user (or create one)
    company = db.query(User).filter(User.role == UserRole.company).first()
    if not company:
        print("No company user found in database!")
        return
    
    internships_data = [
        {
            "title": "Senior Full Stack Engineer Intern (Perfect Match)",
            "description": "Looking for a talented developer with strong Python, React, Node.js, and cloud experience. Work on microservices architecture using Docker and Kubernetes. Deploy on AWS and GCP. Use PostgreSQL and MongoDB databases. Implement CI/CD pipelines.",
            "required_skills": ["Python", "React", "Node.js", "Docker", "Kubernetes", "AWS", "GCP", "PostgreSQL", "MongoDB", "CI/CD", "Microservices"],
            "location": "Remote",
            "duration": "6 months",
            "stipend": "$3000/month"
        },
        {
            "title": "AI/ML Research Intern (High Match)",
            "description": "Join our AI team to work on machine learning models using Python, TensorFlow, and PyTorch. Experience with Flask APIs, Docker containers, and SQL databases required. Deploy ML models on cloud platforms.",
            "required_skills": ["Python", "Machine Learning", "AI", "Flask", "Docker", "SQL", "TensorFlow", "PyTorch"],
            "location": "Hybrid - San Francisco",
            "duration": "4 months",
            "stipend": "$3500/month"
        },
        {
            "title": "Backend Developer Intern (Good Match)",
            "description": "Build scalable backend services using Python and Java. Work with Express.js for APIs, PostgreSQL for data storage, and Git for version control. Some cloud experience helpful.",
            "required_skills": ["Python", "Java", "Express", "PostgreSQL", "Git", "REST APIs"],
            "location": "New York, NY",
            "duration": "3 months",
            "stipend": "$2500/month"
        },
        {
            "title": "Cloud Infrastructure Intern (Moderate Match)",
            "description": "Help manage our cloud infrastructure on AWS and Azure. Use Terraform, Docker, and Kubernetes for deployment automation. Some Python scripting required.",
            "required_skills": ["AWS", "Azure", "Docker", "Kubernetes", "Terraform", "Python", "Bash"],
            "location": "Remote",
            "duration": "6 months",
            "stipend": "$2800/month"
        },
        {
            "title": "Frontend React Developer Intern (Moderate Match)",
            "description": "Create beautiful user interfaces using React, JavaScript, TypeScript, and Tailwind CSS. Work with modern frontend tools and Git version control.",
            "required_skills": ["React", "JavaScript", "TypeScript", "Tailwind", "CSS", "HTML", "Git"],
            "location": "Austin, TX",
            "duration": "4 months",
            "stipend": "$2200/month"
        },
        {
            "title": "iOS Mobile Developer Intern (Low Match)",
            "description": "Develop native iOS applications using Swift and SwiftUI. Experience with Xcode, iOS SDK, and Apple's Human Interface Guidelines required. Knowledge of RESTful APIs helpful.",
            "required_skills": ["Swift", "SwiftUI", "iOS", "Xcode", "Mobile Development", "REST APIs"],
            "location": "Cupertino, CA",
            "duration": "5 months",
            "stipend": "$2700/month"
        },
        {
            "title": "Embedded Systems Intern (Low Match)",
            "description": "Work on embedded systems programming using C and C++. Experience with microcontrollers, RTOS, and hardware debugging required. Some Python for testing.",
            "required_skills": ["C", "C++", "Embedded Systems", "RTOS", "Hardware", "Python"],
            "location": "Boston, MA",
            "duration": "6 months",
            "stipend": "$2400/month"
        },
        {
            "title": "Blockchain Developer Intern (Low Match)",
            "description": "Develop smart contracts using Solidity and Web3.js. Work with Ethereum, blockchain protocols, and cryptocurrency systems. JavaScript knowledge required.",
            "required_skills": ["Solidity", "Blockchain", "Web3", "Ethereum", "JavaScript", "Cryptography"],
            "location": "Miami, FL",
            "duration": "3 months",
            "stipend": "$3200/month"
        },
        {
            "title": "Game Developer Intern (Very Low Match)",
            "description": "Create video games using Unity and C#. Work on game mechanics, physics, and 3D graphics. Experience with Unity Engine and game design principles essential.",
            "required_skills": ["Unity", "C#", "Game Development", "3D Graphics", "Game Design"],
            "location": "Los Angeles, CA",
            "duration": "4 months",
            "stipend": "$2000/month"
        },
        {
            "title": "Graphic Designer Intern (No Match)",
            "description": "Create visual designs using Adobe Photoshop, Illustrator, and InDesign. Work on branding, marketing materials, and social media graphics. Strong portfolio required.",
            "required_skills": ["Photoshop", "Illustrator", "InDesign", "Graphic Design", "Branding"],
            "location": "Chicago, IL",
            "duration": "3 months",
            "stipend": "$1800/month"
        }
    ]
    
    print("Creating varied internships for testing RAG matching...\n")
    
    for data in internships_data:
        # Check if internship already exists
        existing = db.query(Internship).filter(
            Internship.title == data["title"],
            Internship.company_id == company.id
        ).first()
        
        if existing:
            print(f"⏭️  Skipping: {data['title']} (already exists)")
            continue
        
        # Create internship
        internship = Internship(
            company_id=company.id,
            title=data["title"],
            description=data["description"],
            required_skills=data["required_skills"],
            location=data["location"],
            duration=data["duration"],
            stipend=data["stipend"],
            is_active=1
        )
        
        db.add(internship)
        db.commit()
        db.refresh(internship)
        
        # Create embedding
        embedding_id = rag_engine.store_internship_embedding(
            internship_id=str(internship.id),
            title=internship.title,
            description=internship.description,
            required_skills=internship.required_skills,
            metadata={
                "company_id": company.id,
                "location": internship.location,
                "duration": internship.duration
            }
        )
        
        print(f"✅ Created: {data['title']}")
        print(f"   Skills: {', '.join(data['required_skills'][:3])}...")
        print(f"   Embedding ID: {embedding_id}\n")
    
    print(f"\n🎉 Successfully created varied internships!")
    print(f"Total active internships: {db.query(Internship).filter(Internship.is_active == 1).count()}")

if __name__ == "__main__":
    create_varied_internships()
