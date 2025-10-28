#!/bin/bash
# Comprehensive test script for SkillSync API endpoints

BASE_URL="http://localhost:8000"

echo "========================================"
echo "  SkillSync API - Comprehensive Tests"
echo "========================================"
echo ""

# Test 1: Root endpoint
echo "1. Testing root endpoint..."
curl -s "${BASE_URL}/" | python3 -m json.tool
echo ""
echo ""

# Test 2: Health check
echo "2. Testing health check endpoint..."
curl -s "${BASE_URL}/api/healthcheck" | python3 -m json.tool
echo ""
echo ""

# Test 3: Register student
echo "3. Testing student registration..."
curl -s -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@test.com",
    "password": "Student123",
    "full_name": "Alice Smith",
    "role": "student"
  }' | python3 -m json.tool
echo ""
echo ""

# Test 4: Register company
echo "4. Testing company registration..."
curl -s -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newcompany@test.com",
    "password": "Company123",
    "full_name": "Tech Corp Inc",
    "role": "company"
  }' | python3 -m json.tool
echo ""
echo ""

# Test 5: Login student
echo "5. Testing student login..."
STUDENT_TOKEN=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@test.com",
    "password": "Student123"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@test.com",
    "password": "Student123"
  }' | python3 -m json.tool
echo ""
echo ""

# Test 6: Login company
echo "6. Testing company login..."
curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newcompany@test.com",
    "password": "Company123"
  }' | python3 -m json.tool
echo ""
echo ""

# Test 7: Duplicate registration (should fail)
echo "7. Testing duplicate registration (should fail)..."
curl -s -X POST "${BASE_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@test.com",
    "password": "Test5678",
    "full_name": "Duplicate User",
    "role": "student"
  }' | python3 -m json.tool
echo ""
echo ""

# Test 8: Invalid login (should fail)
echo "8. Testing login with wrong password (should fail)..."
curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@test.com",
    "password": "WrongPassword"
  }' | python3 -m json.tool
echo ""
echo ""

echo "========================================"
echo "  All tests completed!"
echo "========================================"
echo ""
echo "API Documentation available at:"
echo "- Swagger UI: ${BASE_URL}/api/docs"
echo "- ReDoc: ${BASE_URL}/api/redoc"
echo ""

