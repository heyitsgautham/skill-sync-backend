"""
Health check endpoint tests
"""

import pytest
from fastapi import status


def test_root_endpoint(client):
    """Test root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "SkillSync" in data["message"]


def test_healthcheck_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/healthcheck")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check required fields
    assert "status" in data
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data
    assert "database" in data
    
    # Check values
    assert data["service"] == "SkillSync API"
    assert data["version"] == "1.0.0"
    assert data["status"] in ["healthy", "unhealthy"]
