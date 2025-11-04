"""
Database models tests
"""

import pytest
from app.models.user import User, UserRole
from app.models.internship import Internship
from app.utils.security import get_password_hash


def test_user_model_creation(db_session):
    """Test creating a user model"""
    user = User(
        email="model@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Model Test User",
        role=UserRole.student
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "model@example.com"
    assert user.full_name == "Model Test User"
    assert user.role == UserRole.student
    assert user.created_at is not None


def test_internship_model_creation(db_session):
    """Test creating an internship model"""
    # First create a company user
    company = User(
        email="company@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Test Company",
        role=UserRole.company
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    
    # Now create internship
    internship = Internship(
        company_id=company.id,
        title="Software Engineering Intern",
        description="Test internship description",
        required_skills=["Python", "FastAPI"],
        location="Remote",
        duration="3 months",
        stipend="5000/month"
    )
    
    db_session.add(internship)
    db_session.commit()
    db_session.refresh(internship)
    
    assert internship.id is not None
    assert internship.title == "Software Engineering Intern"
    assert internship.company_id == company.id
    assert internship.is_active == 1
    assert internship.created_at is not None
