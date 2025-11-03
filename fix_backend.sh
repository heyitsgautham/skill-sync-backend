#!/bin/bash

# Quick fix script for Pydantic/SQLAlchemy compatibility issue
# Run this to fix the 500 Internal Server Error

echo "🔧 Fixing Pydantic/SQLAlchemy compatibility issue..."
echo ""

cd /Users/gauthamkrishna/Projects/presidio/skill-sync/skill-sync-backend

echo "📦 Installing SQLAlchemy 1.4.53..."
pip install sqlalchemy==1.4.53

echo ""
echo "✅ Fix applied!"
echo ""
echo "Next steps:"
echo "1. Stop the backend server if running (Ctrl+C)"
echo "2. Restart it with: uvicorn app.main:app --reload"
echo "3. Refresh your browser at http://localhost:3000/upload-resume"
