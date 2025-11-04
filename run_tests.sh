#!/bin/bash

echo "🧪 Running Backend Tests..."
echo "================================"

cd /Users/gauthamkrishna/Projects/presidio/skill-sync/skill-sync-backend

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov httpx

# Run tests
echo ""
echo "🚀 Running tests..."
pytest tests/ -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All backend tests passed!"
else
    echo ""
    echo "❌ Some backend tests failed!"
fi
