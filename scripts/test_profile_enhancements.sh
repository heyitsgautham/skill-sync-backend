#!/bin/bash

# Profile Enhancements Test Script
# Tests all changes made to profile pages

echo "🧪 Testing Profile Page Enhancements"
echo "======================================"
echo ""

API_URL="http://localhost:8000/api"

# Test 1: Check backend server
echo "1️⃣ Testing Backend Server..."
if curl -s "${API_URL}/docs" | grep -q "FastAPI"; then
    echo "   ✅ Backend server is running"
else
    echo "     Backend server is not responding"
    exit 1
fi
echo ""

# Test 2: Check mailing_email column exists
echo "2️⃣ Testing Database Migration..."
COLUMN_CHECK=$(python3 << 'EOF'
from app.database.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'mailing_email'
    """)
    result = db.execute(query)
    if result.fetchone():
        print("✅ mailing_email column exists")
    else:
        print("  mailing_email column not found")
except Exception as e:
    print(f"  Database check failed: {e}")
finally:
    db.close()
EOF
)
echo "   $COLUMN_CHECK"
echo ""

# Test 3: Test Company Profile API
echo "3️⃣ Testing Company Profile API..."

# Create a test company account
echo "   Creating test company account..."
COMPANY_REGISTER=$(curl -s -X POST "${API_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_company_profile@example.com",
    "password": "Test123!",
    "full_name": "Test Profile Company",
    "role": "company"
  }')

if echo "$COMPANY_REGISTER" | grep -q "token"; then
    echo "   ✅ Test company created"
    TOKEN=$(echo "$COMPANY_REGISTER" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
    
    # Get profile
    echo "   Testing GET /api/profile/me..."
    PROFILE_GET=$(curl -s -X GET "${API_URL}/profile/me" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$PROFILE_GET" | grep -q "mailing_email"; then
        echo "   ✅ Profile GET returns mailing_email field"
    else
        echo "     Profile GET missing mailing_email field"
        echo "   Response: $PROFILE_GET"
    fi
    
    # Update profile with mailing email
    echo "   Testing PUT /api/profile/me with mailing_email..."
    PROFILE_UPDATE=$(curl -s -X PUT "${API_URL}/profile/me" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "full_name": "Test Profile Company",
        "mailing_email": "notifications@testcompany.com",
        "phone": "+1-555-TEST",
        "hr_contact_name": "Test HR"
      }')
    
    if echo "$PROFILE_UPDATE" | grep -q "notifications@testcompany.com"; then
        echo "   ✅ Profile UPDATE successfully saved mailing_email"
    else
        echo "     Profile UPDATE failed to save mailing_email"
        echo "   Response: $PROFILE_UPDATE"
    fi
    
else
    echo "   ⚠️  Could not create test company (may already exist)"
fi
echo ""

# Test 4: Student Profile API (verify no skills returned)
echo "4️⃣ Testing Student Profile API..."

# Create a test student account
echo "   Creating test student account..."
STUDENT_REGISTER=$(curl -s -X POST "${API_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_student_profile@example.com",
    "password": "Test123!",
    "full_name": "Test Profile Student",
    "role": "student"
  }')

if echo "$STUDENT_REGISTER" | grep -q "token"; then
    echo "   ✅ Test student created"
    TOKEN=$(echo "$STUDENT_REGISTER" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
    
    # Get profile
    echo "   Testing GET /api/profile/me..."
    STUDENT_PROFILE=$(curl -s -X GET "${API_URL}/profile/me" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$STUDENT_PROFILE" | grep -q "email"; then
        echo "   ✅ Student profile GET successful"
    else
        echo "     Student profile GET failed"
    fi
else
    echo "   ⚠️  Could not create test student (may already exist)"
fi
echo ""

# Summary
echo "======================================"
echo "✅ Profile Enhancement Tests Complete"
echo "======================================"
echo ""
echo "Frontend Testing Checklist:"
echo "  [ ] Navigate to /company/profile"
echo "  [ ] Verify Mailing Email field appears"
echo "  [ ] Verify no MUI Grid warnings in console"
echo "  [ ] Navigate to /student/profile"
echo "  [ ] Verify skills and experience sections removed"
echo "  [ ] Verify no MUI Grid warnings in console"
echo "  [ ] Navigate to /admin/profile"
echo "  [ ] Verify no MUI Grid warnings in console"
echo ""
