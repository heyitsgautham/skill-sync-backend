"""
Authentication endpoint tests
"""

import pytest
from fastapi import status


def test_register_user(client):
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "password": "Test123!@#",
        "full_name": "Test User",
        "role": "student"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    assert "message" in data
    assert user_data["email"] in data["message"]


def test_register_duplicate_email(client):
    """Test registration with duplicate email fails"""
    user_data = {
        "email": "duplicate@example.com",
        "password": "Test123!@#",
        "full_name": "Test User",
        "role": "student"
    }
    
    # First registration should succeed
    response1 = client.post("/api/auth/register", json=user_data)
    assert response1.status_code == status.HTTP_201_CREATED
    
    # Second registration with same email should fail
    response2 = client.post("/api/auth/register", json=user_data)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST


def test_login_success(client):
    """Test successful login"""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "password": "Test123!@#",
        "full_name": "Login Test",
        "role": "student"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Then try to login
    login_data = {
        "email": "login@example.com",
        "password": "Test123!@#"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_invalid_email(client):
    """Test registration with invalid email format"""
    user_data = {
        "email": "invalid-email",
        "password": "Test123!@#",
        "full_name": "Test User",
        "role": "student"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
