"""
Test Admin User Management Endpoints
Tests for update and delete user operations
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.utils.security import create_access_token

client = TestClient(app)

# Test admin credentials
ADMIN_EMAIL = "admin@skillsync.com"
ADMIN_PASSWORD = "admin123"

# Test student credentials
TEST_STUDENT_EMAIL = "test.student@example.com"
TEST_STUDENT_PASSWORD = "testpass123"
TEST_STUDENT_NAME = "Test Student"


class TestAdminUserManagement:
    """Test suite for admin user management operations"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = client.post("/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @pytest.fixture
    def test_user_id(self, admin_token):
        """Create a test user and return their ID"""
        # Register a test student
        response = client.post("/auth/register", json={
            "email": TEST_STUDENT_EMAIL,
            "password": TEST_STUDENT_PASSWORD,
            "full_name": TEST_STUDENT_NAME,
            "role": "student"
        })
        
        # Get all users to find the test user ID
        headers = {"Authorization": f"Bearer {admin_token}"}
        users_response = client.get("/auth/users", headers=headers)
        
        if users_response.status_code == 200:
            users = users_response.json()
            for user in users:
                if user["email"] == TEST_STUDENT_EMAIL:
                    return user["id"]
        return None
    
    def test_list_users_as_admin(self, admin_token):
        """Test that admin can list all users"""
        if not admin_token:
            pytest.skip("Admin credentials not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/auth/users", headers=headers)
        
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) > 0
        
        # Verify user structure
        user = users[0]
        assert "id" in user
        assert "email" in user
        assert "full_name" in user
        assert "role" in user
        assert "created_at" in user
    
    def test_update_user_as_admin(self, admin_token, test_user_id):
        """Test that admin can update user information"""
        if not admin_token or not test_user_id:
            pytest.skip("Admin credentials or test user not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Update user
        update_data = {
            "full_name": "Updated Test Student",
            "role": "student"
        }
        response = client.put(
            f"/auth/users/{test_user_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["full_name"] == "Updated Test Student"
        assert updated_user["id"] == test_user_id
    
    def test_update_user_status(self, admin_token, test_user_id):
        """Test that admin can activate/deactivate users"""
        if not admin_token or not test_user_id:
            pytest.skip("Admin credentials or test user not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Deactivate user
        response = client.put(
            f"/auth/users/{test_user_id}",
            json={"is_active": 0},
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Reactivate user
        response = client.put(
            f"/auth/users/{test_user_id}",
            json={"is_active": 1},
            headers=headers
        )
        
        assert response.status_code == 200
    
    def test_delete_user_as_admin(self, admin_token, test_user_id):
        """Test that admin can delete users"""
        if not admin_token or not test_user_id:
            pytest.skip("Admin credentials or test user not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Delete user
        response = client.delete(
            f"/auth/users/{test_user_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "deleted successfully" in result["message"].lower()
    
    def test_cannot_delete_self(self, admin_token):
        """Test that admin cannot delete their own account"""
        if not admin_token:
            pytest.skip("Admin credentials not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get admin user ID
        users_response = client.get("/auth/users", headers=headers)
        admin_id = None
        
        if users_response.status_code == 200:
            users = users_response.json()
            for user in users:
                if user["email"] == ADMIN_EMAIL:
                    admin_id = user["id"]
                    break
        
        if not admin_id:
            pytest.skip("Could not find admin user ID")
        
        # Try to delete own account
        response = client.delete(
            f"/auth/users/{admin_id}",
            headers=headers
        )
        
        assert response.status_code == 400
        assert "cannot delete your own account" in response.json()["detail"].lower()
    
    def test_non_admin_cannot_update_users(self):
        """Test that non-admin users cannot update other users"""
        # First, create a student user
        student_response = client.post("/auth/register", json={
            "email": "student.nonadmin@example.com",
            "password": "studentpass123",
            "full_name": "Non Admin Student",
            "role": "student"
        })
        
        # Login as student
        login_response = client.post("/auth/login", json={
            "email": "student.nonadmin@example.com",
            "password": "studentpass123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Could not create/login test student")
        
        student_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Try to update any user (using ID 1 as example)
        response = client.put(
            "/auth/users/1",
            json={"full_name": "Hacked Name"},
            headers=headers
        )
        
        assert response.status_code == 403
        assert "only administrators" in response.json()["detail"].lower()
    
    def test_non_admin_cannot_delete_users(self):
        """Test that non-admin users cannot delete other users"""
        # Login as student (from previous test)
        login_response = client.post("/auth/login", json={
            "email": "student.nonadmin@example.com",
            "password": "studentpass123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Could not login test student")
        
        student_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Try to delete any user (using ID 1 as example)
        response = client.delete("/auth/users/1", headers=headers)
        
        assert response.status_code == 403
        assert "only administrators" in response.json()["detail"].lower()
    
    def test_update_nonexistent_user(self, admin_token):
        """Test updating a user that doesn't exist"""
        if not admin_token:
            pytest.skip("Admin credentials not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try to update user with very high ID (unlikely to exist)
        response = client.put(
            "/auth/users/999999",
            json={"full_name": "Ghost User"},
            headers=headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_nonexistent_user(self, admin_token):
        """Test deleting a user that doesn't exist"""
        if not admin_token:
            pytest.skip("Admin credentials not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try to delete user with very high ID (unlikely to exist)
        response = client.delete("/auth/users/999999", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


if __name__ == "__main__":
    print("Run tests using: pytest tests/test_admin_user_management.py -v")
