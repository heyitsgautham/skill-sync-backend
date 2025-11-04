#!/bin/bash

# Day 5 Testing Script - Test /internship/match endpoint

echo "========================================"
echo "Day 5 - Testing AI Recommendations"
echo "========================================"
echo ""

BASE_URL="http://localhost:8000/api"

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# Test 2: Login as student (use existing credentials)
echo "2. Logging in as student..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=student@test.com&password=password123")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed. Please ensure student@test.com exists with password: password123"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Test 3: Check if student has resume
echo "3. Checking student's resumes..."
RESUMES=$(curl -s -X GET "$BASE_URL/resume/my-resumes" \
  -H "Authorization: Bearer $TOKEN")
echo $RESUMES | python3 -m json.tool
echo ""

# Test 4: Get AI recommendations via /internship/match
echo "4. Testing /internship/match endpoint..."
RECOMMENDATIONS=$(curl -s -X GET "$BASE_URL/internship/match?top_k=5" \
  -H "Authorization: Bearer $TOKEN")

echo $RECOMMENDATIONS | python3 -m json.tool
echo ""

# Check if recommendations were returned
if echo $RECOMMENDATIONS | grep -q "match_score"; then
    echo "✅ AI Recommendations working! Match scores found."
    
    # Count recommendations
    COUNT=$(echo $RECOMMENDATIONS | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    echo "📊 Found $COUNT recommendations"
else
    echo "⚠️ No recommendations found. This could mean:"
    echo "   - Student needs to upload a resume first"
    echo "   - No internships in database"
    echo "   - Embeddings not yet created"
    echo ""
    echo "Response: $RECOMMENDATIONS"
fi

echo ""
echo "========================================"
echo "Day 5 Testing Complete!"
echo "========================================"
