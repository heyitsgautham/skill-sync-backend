#!/bin/bash

echo "🧪 Final Test: Resume Manager with Real Authentication"
echo "======================================================="
echo ""

# First, let's try to register and login
echo "Step 1: Trying to register (might already exist)..."
curl -s -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "role": "student"
  }' | python3 -m json.tool
echo ""

echo "Step 2: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }')

echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo ""

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi

echo "✅ Got token: ${TOKEN:0:50}..."
echo ""

echo "Step 3: Testing /api/resume/my-resumes with valid token..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "http://localhost:8000/api/resume/my-resumes" \
  -H "Authorization: Bearer $TOKEN")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Status: $HTTP_STATUS"
echo "Response:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✅ SUCCESS! Resume endpoint is working!"
    echo ""
    echo "🎉 All issues resolved! The frontend should now work."
    echo ""
    echo "Next: Refresh http://localhost:3000/upload-resume in your browser"
else
    echo "❌ Still got error. Status: $HTTP_STATUS"
fi
