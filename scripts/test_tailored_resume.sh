#!/bin/bash

# Test script for Tailored Resume Feature
# Tests the complete flow of applying with a tailored resume

echo "🧪 Testing Tailored Resume Feature"
echo "=================================="
echo ""

# Configuration
BASE_URL="http://localhost:8000"
STUDENT_EMAIL="student1@example.com"
STUDENT_PASSWORD="password123"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📋 Test Plan:"
echo "1. Login as student"
echo "2. Get list of internships"
echo "3. Apply to internship WITHOUT tailored resume"
echo "4. Apply to another internship WITH tailored resume"
echo "5. Verify database records"
echo ""

# Test 1: Login
echo "${YELLOW}Test 1: Student Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${STUDENT_EMAIL}\",\"password\":\"${STUDENT_PASSWORD}\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "${RED}  Login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
else
    echo "${GREEN}✅ Login successful${NC}"
fi
echo ""

# Test 2: Get internships
echo "${YELLOW}Test 2: Fetch Internships${NC}"
INTERNSHIPS=$(curl -s -X GET "${BASE_URL}/api/internship/list" \
  -H "Authorization: Bearer ${TOKEN}")

INTERNSHIP_ID=$(echo $INTERNSHIPS | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$INTERNSHIP_ID" ]; then
    echo "${RED}  No internships found${NC}"
    exit 1
else
    echo "${GREEN}✅ Found internship ID: ${INTERNSHIP_ID}${NC}"
fi
echo ""

# Test 3: Apply without tailored resume
echo "${YELLOW}Test 3: Apply WITHOUT Tailored Resume${NC}"
APPLY_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/internship/${INTERNSHIP_ID}/apply" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: multipart/form-data" \
  -F "cover_letter=I am very interested in this position" \
  -F "use_tailored_resume=false")

USED_TAILORED=$(echo $APPLY_RESPONSE | grep -o '"used_tailored_resume":[0-9]*' | cut -d':' -f2)
MATCH_SCORE=$(echo $APPLY_RESPONSE | grep -o '"application_similarity_score":[0-9]*' | cut -d':' -f2)

if [ "$USED_TAILORED" = "0" ]; then
    echo "${GREEN}✅ Application created with base resume (used_tailored_resume=0)${NC}"
    echo "   Match Score: ${MATCH_SCORE}%"
else
    echo "${RED}  Expected used_tailored_resume=0, got ${USED_TAILORED}${NC}"
fi
echo ""

# Test 4: Create sample resume file
echo "${YELLOW}Test 4: Apply WITH Tailored Resume${NC}"
echo "Creating sample resume file..."
cat > /tmp/test_tailored_resume.txt << 'EOF'
JOHN DOE
Software Engineer

SKILLS:
- Python, JavaScript, React
- Machine Learning, AI
- Cloud Computing (AWS, Azure)
- Database Design

EXPERIENCE:
Software Developer at Tech Corp (2 years)
- Developed web applications
- Implemented ML models
- Worked with cross-functional teams

EDUCATION:
B.S. Computer Science - MIT
EOF

# Find another internship to apply to
INTERNSHIP_ID_2=$(echo $INTERNSHIPS | grep -o '"id":[0-9]*' | head -2 | tail -1 | cut -d':' -f2)

if [ "$INTERNSHIP_ID_2" = "$INTERNSHIP_ID" ]; then
    echo "${YELLOW}⚠️ Only one internship available, skipping tailored resume test${NC}"
else
    APPLY_RESPONSE_2=$(curl -s -X POST "${BASE_URL}/api/internship/${INTERNSHIP_ID_2}/apply" \
      -H "Authorization: Bearer ${TOKEN}" \
      -F "cover_letter=Tailored application with custom resume" \
      -F "use_tailored_resume=true" \
      -F "tailored_resume=@/tmp/test_tailored_resume.txt")

    USED_TAILORED_2=$(echo $APPLY_RESPONSE_2 | grep -o '"used_tailored_resume":[0-9]*' | cut -d':' -f2)
    MATCH_SCORE_2=$(echo $APPLY_RESPONSE_2 | grep -o '"application_similarity_score":[0-9]*' | cut -d':' -f2)

    if [ "$USED_TAILORED_2" = "1" ]; then
        echo "${GREEN}✅ Application created with tailored resume (used_tailored_resume=1)${NC}"
        echo "   Match Score: ${MATCH_SCORE_2}%"
    else
        echo "${RED}  Expected used_tailored_resume=1, got ${USED_TAILORED_2}${NC}"
        echo "Response: $APPLY_RESPONSE_2"
    fi
fi

# Cleanup
rm -f /tmp/test_tailored_resume.txt

echo ""
echo "=================================="
echo "${GREEN}🎉 Testing Complete!${NC}"
echo ""
echo "Manual verification steps:"
echo "1. Check database for tailored resumes:"
echo "   SELECT * FROM resumes WHERE is_tailored = 1;"
echo ""
echo "2. Check applications table:"
echo "   SELECT id, student_id, internship_id, used_tailored_resume, application_similarity_score"
echo "   FROM applications ORDER BY created_at DESC LIMIT 5;"
echo ""
echo "3. Test in browser:"
echo "   - Login as student"
echo "   - Navigate to Internship List"
echo "   - Click 'Apply Now'"
echo "   - Check 'Upload tailored resume'"
echo "   - Upload a file and submit"
