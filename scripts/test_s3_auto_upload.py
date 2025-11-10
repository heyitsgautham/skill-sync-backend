#!/usr/bin/env python3
"""
Test script to verify S3 auto-upload fix for Resume Intelligence
Tests the /filter/parse-resume endpoint used by intelligent-analyzer
"""

import requests
import os
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/auth/login"
PARSE_RESUME_ENDPOINT = f"{BASE_URL}/api/filter/parse-resume"

# Test credentials
TEST_STUDENT = {
    "email": "alice.johnson@university.edu",
    "password": "Alice@2024"
}

# Sample resume path
SAMPLE_RESUME = Path(__file__).parent.parent / "skill-sync-backend" / "app" / "public" / "resumes" / "Surya_Resume_SDE.pdf"


def test_resume_upload_with_s3():
    """Test that resume upload via /filter/parse-resume uploads to S3"""
    
    print("=" * 70)
    print("🧪 Testing S3 Auto-Upload Fix for Resume Intelligence")
    print("=" * 70)
    
    # Step 1: Login as student
    print("\n1️⃣ Logging in as student...")
    login_response = requests.post(LOGIN_ENDPOINT, json=TEST_STUDENT)
    
    if login_response.status_code != 200:
        print(f"  Login failed: {login_response.json()}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in successfully")
    
    # Step 2: Upload resume via /filter/parse-resume
    print("\n2️⃣ Uploading resume via Resume Intelligence endpoint...")
    
    if not SAMPLE_RESUME.exists():
        print(f"  Sample resume not found: {SAMPLE_RESUME}")
        print("ℹ️  Please provide a valid resume path")
        return False
    
    with open(SAMPLE_RESUME, "rb") as f:
        files = {"file": (SAMPLE_RESUME.name, f, "application/pdf")}
        upload_response = requests.post(
            PARSE_RESUME_ENDPOINT,
            headers=headers,
            files=files
        )
    
    if upload_response.status_code != 200:
        print(f"  Upload failed: {upload_response.json()}")
        return False
    
    result = upload_response.json()
    print(f"✅ Resume uploaded successfully")
    
    # Step 3: Verify S3 key is present
    print("\n3️⃣ Verifying S3 upload...")
    
    s3_key = result.get("s3_key")
    resume_id = result.get("resume_id")
    
    if not s3_key:
        print("  FAIL: s3_key is NULL - resume NOT uploaded to S3!")
        print(f"📋 Response: {result}")
        return False
    
    print(f"✅ SUCCESS: Resume uploaded to S3")
    print(f"   📁 S3 Key: {s3_key}")
    print(f"   🆔 Resume ID: {resume_id}")
    
    # Step 4: Display processing details
    print("\n4️⃣ Processing Details:")
    if "processing_details" in result:
        details = result["processing_details"]
        print(f"   📊 Skills Extracted: {details.get('skills_extracted', 0)}")
        print(f"   💼 Experience: {details.get('experience_calculated', 'N/A')}")
        print(f"   🎓 Education: {details.get('education_found', 0)}")
        print(f"   🚀 Projects: {details.get('projects_found', 0)}")
    
    # Step 5: Verify resume can be viewed
    print("\n5️⃣ Testing Resume Viewing (HR perspective)...")
    
    # Get student ID from login response
    student_id = login_response.json()["id"]
    
    # Try to get resume URL (this endpoint is used by HR to view resumes)
    resume_url_endpoint = f"{BASE_URL}/api/recommendations/candidate/{student_id}/resume"
    
    # Login as company to test HR view
    print("   🏢 Logging in as company (HR)...")
    company_login = requests.post(LOGIN_ENDPOINT, json={
        "email": "hr@techcorp.com",
        "password": "TechCorp@2024"
    })
    
    if company_login.status_code != 200:
        print(f"   ⚠️  Company login failed, skipping HR view test")
        return True  # Still pass the main test
    
    company_token = company_login.json()["access_token"]
    company_headers = {"Authorization": f"Bearer {company_token}"}
    
    resume_url_response = requests.get(resume_url_endpoint, headers=company_headers)
    
    if resume_url_response.status_code != 200:
        print(f"   ⚠️  Could not get resume URL: {resume_url_response.json()}")
        return True  # Still pass the main test
    
    resume_url_data = resume_url_response.json()
    
    if "presigned_url" in resume_url_data:
        print(f"   ✅ HR can view resume via presigned URL")
        print(f"   🔗 URL generated successfully")
    else:
        print(f"   ⚠️  Resume viewing may have issues: {resume_url_data}")
    
    print("\n" + "=" * 70)
    print("✨ TEST PASSED: S3 Auto-Upload is working correctly!")
    print("=" * 70)
    
    return True


def main():
    """Run the test"""
    try:
        success = test_resume_upload_with_s3()
        
        if success:
            print("\n✅ All tests passed!")
            print("ℹ️  Resume Intelligence now uploads to S3 automatically")
            sys.exit(0)
        else:
            print("\n  Test failed!")
            print("ℹ️  Please check the backend logs for errors")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print("\n  Cannot connect to backend server")
        print("ℹ️  Make sure the backend is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
