#!/bin/bash

# Quick restart script for SkillSync backend after adding new features
# This ensures all new routes and services are loaded

echo "======================================"
echo "SkillSync Backend - Quick Restart"
echo "======================================"
echo ""

# Find the backend directory
BACKEND_DIR="/Users/gauthamkrishna/Projects/presidio/skill-sync/skill-sync-backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "  Backend directory not found: $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR" || exit 1

echo "📍 Current directory: $(pwd)"
echo ""

# Check if server is running
echo "Checking for running uvicorn processes..."
PIDS=$(pgrep -f "uvicorn app.main:app")

if [ -n "$PIDS" ]; then
    echo "Found running server processes: $PIDS"
    echo "Stopping existing servers..."
    pkill -f "uvicorn app.main:app"
    sleep 2
    echo "✓ Servers stopped"
else
    echo "No running servers found"
fi

echo ""
echo "Starting backend server..."
echo "Command: uvicorn app.main:app --reload"
echo ""
echo "======================================"
echo "Server will start now..."
echo "======================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload
