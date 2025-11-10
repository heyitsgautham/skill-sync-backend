#!/bin/bash

# Test Admin ChromaDB Management Endpoints
# Usage: ./test_admin_chromadb.sh

BASE_URL="http://localhost:8000"

echo "🔐 Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@skillsync.com", "password": "admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
  echo "  Failed to login as admin"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Admin login successful"
echo ""

# Test 1: Get system status before clearing
echo "📊 Test 1: Get system status (before clearing)"
echo "============================================="
curl -s -X GET "$BASE_URL/api/admin/system-status" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
echo ""

# Test 2: Clear ChromaDB (with confirmation)
read -p "⚠️  Do you want to CLEAR all ChromaDB embeddings? (yes/no): " CONFIRM_CLEAR
if [ "$CONFIRM_CLEAR" = "yes" ]; then
  echo "🗑️  Test 2: Clear ChromaDB embeddings"
  echo "============================================="
  curl -s -X POST "$BASE_URL/api/admin/clear-chromadb" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
  echo ""
  echo ""
fi

# Test 3: Get system status after clearing
echo "📊 Test 3: Get system status (after clearing)"
echo "============================================="
curl -s -X GET "$BASE_URL/api/admin/system-status" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
echo ""

# Test 4: Reindex all student resumes (with confirmation)
read -p "🔄 Do you want to RE-INDEX all student resumes? This may take several minutes. (yes/no): " CONFIRM_REINDEX
if [ "$CONFIRM_REINDEX" = "yes" ]; then
  echo "🔄 Test 4: Reindex all student resumes"
  echo "============================================="
  curl -s -X POST "$BASE_URL/api/admin/reindex-all-students" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
  echo ""
  echo "⏳ Background task started. Check server logs for progress..."
  echo ""
  
  # Wait a bit and check status again
  echo "⏰ Waiting 30 seconds before checking status..."
  sleep 30
  
  echo "📊 Test 5: Get system status (after reindexing)"
  echo "============================================="
  curl -s -X GET "$BASE_URL/api/admin/system-status" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
  echo ""
fi

echo "✅ All tests completed!"
