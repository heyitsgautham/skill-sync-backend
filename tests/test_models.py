"""
Database models tests - Minimal smoke tests for CI
"""

import pytest
from app.models.user import User, UserRole
from app.models.internship import Internship


def test_models_import():
    """Test that models import successfully"""
    assert User is not None
    assert UserRole is not None
    assert Internship is not None


def test_user_role_enum():
    """Test UserRole enum values"""
    assert UserRole.student == "student"
    assert UserRole.company == "company"
    assert UserRole.admin == "admin"
