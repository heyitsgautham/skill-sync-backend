"""
Health check endpoint tests - Minimal smoke tests for CI
"""

import pytest
from fastapi import status


def test_root_endpoint(client):
    """Test root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data


def test_health_module_imports():
    """Test that health module imports successfully"""
    from app.routes import health
    assert health is not None
