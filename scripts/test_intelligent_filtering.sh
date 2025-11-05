#!/bin/bash

# Test Script for Intelligent Filtering System
# Tests the complete flow: Resume parsing → Matching → Ranking with explanations

echo "🧪 Testing Intelligent Filtering System"
echo "=========================================="

# Base URL
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Register and login as student
echo -e "\n${BLUE}Step 1: Registering student...${NC}"
STUDENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "intelligent.filter.test@example.com",
    "password": "Test123!",
    "full_name": "Test Student Intelligence",
    "role": "student"
  }')

echo "$STUDENT_RESPONSE"

# Login as student
echo -e "\n${BLUE}Step 2: Logging in as student...${NC}"
STUDENT_TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=intelligent.filter.test@example.com&password=Test123!" | jq -r '.access_token')

if [ "$STUDENT_TOKEN" == "null" ] || [ -z "$STUDENT_TOKEN" ]; then
  echo -e "${RED}❌ Student login failed${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Student token: ${STUDENT_TOKEN:0:20}...${NC}"

# Step 3: Upload and parse resume
echo -e "\n${BLUE}Step 3: Uploading and parsing resume...${NC}"

# Create a sample resume file
cat > /tmp/test_resume.txt << 'EOF'
JOHN DOE
Email: john.doe@email.com | Phone: +1-234-567-8900
Location: San Francisco, CA

PROFESSIONAL SUMMARY
Experienced Full Stack Developer with 4+ years of experience in building scalable web applications
using React, Node.js, and cloud technologies.

TECHNICAL SKILLS
Languages: JavaScript, TypeScript, Python, Java
Frontend: React, Redux, HTML5, CSS3, Material-UI
Backend: Node.js, Express, FastAPI, Django
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS, Docker, Kubernetes
Tools: Git, Jenkins, JIRA

WORK EXPERIENCE
Senior Software Engineer | TechCorp Inc. | Jan 2021 - Present
- Led development of microservices architecture serving 1M+ users
- Implemented CI/CD pipelines reducing deployment time by 60%
- Mentored team of 3 junior developers

Software Engineer | StartupXYZ | Jun 2019 - Dec 2020
- Built React-based dashboard for analytics platform
- Developed RESTful APIs using Node.js and Express
- Optimized database queries improving performance by 40%

EDUCATION
Bachelor of Science in Computer Science
Stanford University | 2019
GPA: 3.8/4.0

PROJECTS
E-commerce Platform
- Built full-stack e-commerce platform using MERN stack
- Implemented payment gateway integration with Stripe
- Technologies: React, Node.js, MongoDB, Docker

AI Chatbot
- Developed conversational AI chatbot using Python and OpenAI
- Integrated with Slack for team communication
- Technologies: Python, FastAPI, OpenAI API, Redis

CERTIFICATIONS
- AWS Certified Solutions Architect - Associate (2022)
- Google Cloud Professional Developer (2021)
EOF

echo "Sample resume created at /tmp/test_resume.txt"

# Upload resume
PARSE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/filter/parse-resume" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -F "file=@/tmp/test_resume.txt")

echo "$PARSE_RESPONSE" | jq '.'

RESUME_ID=$(echo "$PARSE_RESPONSE" | jq -r '.resume_id')
echo -e "${GREEN}✅ Resume parsed successfully. ID: $RESUME_ID${NC}"

# Step 4: Register and login as company
echo -e "\n${BLUE}Step 4: Registering company...${NC}"
COMPANY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "intelligent.company.test@example.com",
    "password": "Test123!",
    "full_name": "Test Company Intelligence",
    "role": "company"
  }')

echo "$COMPANY_RESPONSE"

# Login as company
echo -e "\n${BLUE}Step 5: Logging in as company...${NC}"
COMPANY_TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=intelligent.company.test@example.com&password=Test123!" | jq -r '.access_token')

if [ "$COMPANY_TOKEN" == "null" ] || [ -z "$COMPANY_TOKEN" ]; then
  echo -e "${RED}❌ Company login failed${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Company token: ${COMPANY_TOKEN:0:20}...${NC}"

# Step 6: Create internship
echo -e "\n${BLUE}Step 6: Creating internship posting...${NC}"
INTERNSHIP_RESPONSE=$(curl -s -X POST "$BASE_URL/api/internship/create" \
  -H "Authorization: Bearer $COMPANY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Full Stack Developer Intern",
    "description": "We are looking for a talented full stack developer to join our team. You will work on building scalable web applications using modern technologies.",
    "required_skills": ["React", "Node.js", "JavaScript", "PostgreSQL"],
    "preferred_skills": ["TypeScript", "Docker", "AWS"],
    "min_experience": 2,
    "max_experience": 5,
    "required_education": "Bachelor in Computer Science or related field",
    "location": "San Francisco, CA",
    "duration": "6 months",
    "stipend": "$3000/month"
  }')

echo "$INTERNSHIP_RESPONSE" | jq '.'

INTERNSHIP_ID=$(echo "$INTERNSHIP_RESPONSE" | jq -r '.internship_id // .internship.internship_id')
echo -e "${GREEN}✅ Internship created. ID: $INTERNSHIP_ID${NC}"

# Step 7: Student applies to internship
echo -e "\n${BLUE}Step 7: Student applying to internship...${NC}"
APPLICATION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/internship/apply" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"internship_id\": \"$INTERNSHIP_ID\"
  }")

echo "$APPLICATION_RESPONSE" | jq '.'
echo -e "${GREEN}✅ Application submitted${NC}"

# Step 8: Company ranks candidates
echo -e "\n${BLUE}Step 8: Ranking candidates with intelligent matching...${NC}"
RANKING_RESPONSE=$(curl -s -X POST "$BASE_URL/api/filter/rank-candidates/$INTERNSHIP_ID?limit=10" \
  -H "Authorization: Bearer $COMPANY_TOKEN")

echo "$RANKING_RESPONSE" | jq '.'

# Extract and display key metrics
TOTAL_APPLICANTS=$(echo "$RANKING_RESPONSE" | jq -r '.total_applicants')
TOP_CANDIDATE=$(echo "$RANKING_RESPONSE" | jq -r '.ranked_candidates[0].candidate_name')
TOP_SCORE=$(echo "$RANKING_RESPONSE" | jq -r '.ranked_candidates[0].match_score')
EXPLANATION=$(echo "$RANKING_RESPONSE" | jq -r '.ranked_candidates[0].explanation')

echo -e "\n${GREEN}=========================================="
echo "📊 RANKING RESULTS"
echo "==========================================${NC}"
echo -e "Total Applicants: ${BLUE}$TOTAL_APPLICANTS${NC}"
echo -e "Top Candidate: ${BLUE}$TOP_CANDIDATE${NC}"
echo -e "Match Score: ${BLUE}$TOP_SCORE/100${NC}"
echo -e "\n${GREEN}Match Explanation:${NC}"
echo "$EXPLANATION"

# Step 9: Get detailed candidate profile
echo -e "\n${BLUE}Step 9: Getting detailed candidate profile...${NC}"
STUDENT_ID=$(echo "$PARSE_RESPONSE" | jq -r '.structured_data.personal_info.email // "N/A"')

# Get student ID from database (in real scenario, you'd have this from previous steps)
PROFILE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/filter/match-score?student_id=$STUDENT_ID&internship_id=$INTERNSHIP_ID" \
  -H "Authorization: Bearer $COMPANY_TOKEN")

echo "$PROFILE_RESPONSE" | jq '.'

echo -e "\n${GREEN}✅ Intelligent Filtering System Test Complete!${NC}"
echo "=========================================="

# Cleanup
rm -f /tmp/test_resume.txt
