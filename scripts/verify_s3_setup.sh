#!/bin/bash

# Quick S3 Setup Verification Script
# This script helps verify your S3 configuration and provides next steps

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================================================"
echo "   SkillSync - AWS S3 Quick Setup Verification"
echo "========================================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}  .env file not found!${NC}"
    echo ""
    echo "Please create a .env file with the following AWS S3 configuration:"
    echo ""
    echo "AWS_ACCESS_KEY_ID=your-access-key-id"
    echo "AWS_SECRET_ACCESS_KEY=your-secret-access-key"
    echo "AWS_S3_BUCKET_NAME=skillsync-resumes"
    echo "AWS_REGION=us-east-1"
    echo ""
    echo "See docs/S3_SETUP_GUIDE.md for detailed instructions"
    exit 1
fi

# Load .env file
export $(cat .env | grep -v '^#' | xargs)

echo -e "${BLUE}🔍 Checking S3 Configuration...${NC}"
echo ""

# Check required environment variables
MISSING=0

check_var() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}  $1 is not set${NC}"
        MISSING=1
    else
        # Mask sensitive values
        if [[ $1 == *"SECRET"* ]] || [[ $1 == *"KEY"* ]]; then
            MASKED="${!1:0:4}****${!1: -4}"
            echo -e "${GREEN}✅ $1: $MASKED${NC}"
        else
            echo -e "${GREEN}✅ $1: ${!1}${NC}"
        fi
    fi
}

check_var AWS_ACCESS_KEY_ID
check_var AWS_SECRET_ACCESS_KEY
check_var AWS_S3_BUCKET_NAME
check_var AWS_REGION

echo ""

if [ $MISSING -eq 1 ]; then
    echo -e "${RED}  Missing required environment variables${NC}"
    echo ""
    echo "Please update your .env file with all required AWS S3 credentials"
    echo "See docs/S3_SETUP_GUIDE.md for instructions"
    exit 1
fi

echo -e "${GREEN}✅ All required environment variables are set${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}  Python 3 not found${NC}"
    echo "Please install Python 3 to continue"
    exit 1
fi

echo -e "${BLUE}🔗 Testing S3 Connectivity...${NC}"
echo ""
echo "Running: python scripts/setup_s3_and_migrate.py"
echo ""

# Run the Python verification script
python3 scripts/setup_s3_and_migrate.py

echo ""
echo "========================================================================"
echo -e "${GREEN}✅ Setup verification complete!${NC}"
echo "========================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. To migrate existing resumes to S3:"
echo "   python scripts/setup_s3_and_migrate.py --migrate"
echo ""
echo "2. To verify S3 access for existing resumes:"
echo "   python scripts/setup_s3_and_migrate.py --verify"
echo ""
echo "3. To re-upload all resumes (force):"
echo "   python scripts/setup_s3_and_migrate.py --force"
echo ""
echo "For detailed instructions, see: docs/S3_SETUP_GUIDE.md"
echo ""
