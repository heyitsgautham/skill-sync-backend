#!/bin/bash

echo "Testing resume endpoint..."
echo ""

# First login to get a token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"heyitsgautham@gmail.com","password":"password"}')

echo "Login response: $LOGIN_RESPONSE"
echo ""

# Extract token (basic parsing - in production use jq)
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token. Trying to register first..."
    echo ""
    
    # Try to register
    echo "2. Registering..."
    REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/register" \
      -H "Content-Type: application/json" \
      -d '{"email":"heyitsgautham@gmail.com","password":"password","full_name":"Gautham Krishna S","role":"student"}')
    
    echo "Register response: $REGISTER_RESPONSE"
    echo ""
    
    # Try login again
    echo "3. Logging in again..."
    LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"email":"heyitsgautham@gmail.com","password":"password"}')
    
    echo "Login response: $LOGIN_RESPONSE"
    echo ""
    
    TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
fi

if [ -z "$TOKEN" ]; then
    echo "❌ Still no token. Cannot proceed."
    exit 1
fi

echo "✅ Got token: ${TOKEN:0:50}..."
echo ""

# Test resume endpoint
echo "4. Testing /api/resume/my-resumes..."
curl -s -X GET "http://localhost:8000/api/resume/my-resumes" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "Done!"
