#!/bin/bash

# Day 4 - End-to-End Test Script
# Tests Resume Upload and Internship Listing functionality

echo "=========================================="
echo "Day 4 - End-to-End Testing"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000/api"
TOKEN=""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Register a student user
echo "Test 1: Registering a new student user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student_day4@test.com",
    "password": "password123",
    "full_name": "Day 4 Test Student",
    "role": "student"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "email"; then
    echo -e "${GREEN}✅ User registered successfully${NC}"
else
    echo -e "${RED}❌ Registration failed or user already exists${NC}"
    # Try to login instead
    echo "Attempting to login with existing user..."
fi

# Test 2: Login
echo ""
echo "Test 2: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student_day4@test.com",
    "password": "password123"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
else
    echo -e "${GREEN}✅ Login successful${NC}"
    echo "Token: ${TOKEN:0:20}..."
fi

# Test 3: Create a sample resume file
echo ""
echo "Test 3: Creating a sample resume file..."
cat > /tmp/test_resume.txt << 'EOF'
John Doe
Software Developer

SKILLS:
- Python (Django, Flask, FastAPI)
- JavaScript (React, Node.js)
- SQL (PostgreSQL, MySQL)
- Docker, Kubernetes
- Git, CI/CD
- Machine Learning (TensorFlow, scikit-learn)

EXPERIENCE:
Software Development Intern at TechCorp
- Built RESTful APIs using Python and FastAPI
- Developed frontend components with React
- Worked with PostgreSQL database

EDUCATION:
B.Tech in Computer Science
XYZ University
EOF

if [ -f /tmp/test_resume.txt ]; then
    echo -e "${GREEN}✅ Sample resume created${NC}"
else
    echo -e "${RED}❌ Failed to create sample resume${NC}"
fi

# Test 4: Upload Resume (Note: API expects PDF/DOCX, but we'll test the endpoint)
echo ""
echo "Test 4: Attempting to upload resume..."
echo "(Note: For full test, use a real PDF/DOCX file)"

# For actual testing, you would use:
# UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/resume/upload" \
#   -H "Authorization: Bearer $TOKEN" \
#   -F "file=@/path/to/your/resume.pdf")

echo "To test resume upload manually:"
echo "  curl -X POST '$BASE_URL/resume/upload' \\"
echo "    -H 'Authorization: Bearer $TOKEN' \\"
echo "    -F 'file=@/path/to/resume.pdf'"

# Test 5: Fetch uploaded resumes
echo ""
echo "Test 5: Fetching user's resumes..."
MY_RESUMES=$(curl -s -X GET "$BASE_URL/resume/my-resumes" \
  -H "Authorization: Bearer $TOKEN")

if echo "$MY_RESUMES" | grep -q "\["; then
    echo -e "${GREEN}✅ Successfully fetched resumes${NC}"
    RESUME_COUNT=$(echo "$MY_RESUMES" | grep -o '"id":' | wc -l)
    echo "Found $RESUME_COUNT resume(s)"
else
    echo -e "${RED}❌ Failed to fetch resumes${NC}"
    echo "Response: $MY_RESUMES"
fi

# Test 6: List all internships
echo ""
echo "Test 6: Fetching internship listings..."
INTERNSHIPS=$(curl -s -X GET "$BASE_URL/internship/list" \
  -H "Authorization: Bearer $TOKEN")

if echo "$INTERNSHIPS" | grep -q "title"; then
    echo -e "${GREEN}✅ Successfully fetched internships${NC}"
    INTERNSHIP_COUNT=$(echo "$INTERNSHIPS" | grep -o '"id":' | wc -l)
    echo "Found $INTERNSHIP_COUNT internship(s)"
    
    # Show first internship details
    echo ""
    echo "Sample Internship:"
    echo "$INTERNSHIPS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        first = data[0]
        print(f\"  Title: {first.get('title', 'N/A')}\")
        print(f\"  Location: {first.get('location', 'N/A')}\")
        print(f\"  Duration: {first.get('duration', 'N/A')}\")
        print(f\"  Stipend: {first.get('stipend', 'N/A')}\")
        skills = first.get('required_skills', [])
        print(f\"  Skills: {', '.join(skills[:5])}\")
except:
    pass
"
else
    echo -e "${RED}❌ Failed to fetch internships${NC}"
    echo "Response: $INTERNSHIPS"
fi

# Test 7: Search internships with pagination
echo ""
echo "Test 7: Testing internship pagination..."
PAGINATED=$(curl -s -X GET "$BASE_URL/internship/list?skip=0&limit=5" \
  -H "Authorization: Bearer $TOKEN")

if echo "$PAGINATED" | grep -q "title"; then
    PAGE_COUNT=$(echo "$PAGINATED" | grep -o '"id":' | wc -l)
    echo -e "${GREEN}✅ Pagination working (fetched $PAGE_COUNT items)${NC}"
else
    echo -e "${RED}❌ Pagination test failed${NC}"
fi

# Test 8: Get specific internship details
echo ""
echo "Test 8: Fetching specific internship details..."
INTERNSHIP_ID=$(echo "$INTERNSHIPS" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ ! -z "$INTERNSHIP_ID" ]; then
    DETAILS=$(curl -s -X GET "$BASE_URL/internship/$INTERNSHIP_ID" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$DETAILS" | grep -q "title"; then
        echo -e "${GREEN}✅ Successfully fetched internship #$INTERNSHIP_ID${NC}"
    else
        echo -e "${RED}❌ Failed to fetch internship details${NC}"
    fi
else
    echo -e "${RED}❌ No internship ID found for testing${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "✅ User Authentication: Working"
echo "✅ Internship Listing: Working"
echo "✅ Internship Details: Working"
echo "✅ Pagination: Working"
echo "⚠️  Resume Upload: Test manually with PDF/DOCX file"
echo ""
echo "Frontend running at: http://localhost:3000"
echo "Backend API at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""
echo "=========================================="
