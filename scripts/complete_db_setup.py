#!/usr/bin/env python3
"""
Complete Database Setup and Test Script
Runs all necessary checks and setups for PostgreSQL
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_dependencies():
    """Check if required packages are installed"""
    print_header("STEP 1: Checking Dependencies")
    
    required_packages = {
        'sqlalchemy': 'SQLAlchemy',
        'psycopg2': 'psycopg2-binary',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"  {package} NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("\n✅ All dependencies installed!")
    return True

def check_env_configuration():
    """Check environment configuration"""
    print_header("STEP 2: Checking Environment Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("  DATABASE_URL not found in .env file")
        return False
    
    print(f"✅ DATABASE_URL found in .env")
    
    # Check for placeholder
    if "YOUR_PASSWORD" in DATABASE_URL:
        print("\n⚠️  DATABASE_URL contains placeholder password!")
        print("   Please update .env with your actual PostgreSQL password.")
        print(f"\n   Current: {DATABASE_URL}")
        print("   Expected: postgresql://gauthamkrishna:YOUR_ACTUAL_PASSWORD@localhost:5432/skillsync")
        return False
    
    # Parse URL
    if "@" in DATABASE_URL:
        try:
            server_part = DATABASE_URL.split("@")[1]
            print(f"   Database server: {server_part}")
        except:
            pass
    
    print("\n✅ Environment configuration looks good!")
    return True

def test_database_connection():
    """Test the actual database connection"""
    print_header("STEP 3: Testing Database Connection")
    
    try:
        from sqlalchemy import create_engine, text
        from dotenv import load_dotenv
        
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        print("Attempting to connect to PostgreSQL...")
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Test query
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            print(f"\n✅ Connection successful!")
            print(f"   PostgreSQL version: {version[:60]}...")
            
            # Check tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\n✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("\n⚠️  No tables found (this is OK for first run)")
                print("   Tables will be created when you start the application")
        
        return True
        
    except Exception as e:
        print(f"\n  Connection failed!")
        print(f"   Error: {str(e)}")
        print("\n   Common solutions:")
        print("   1. Ensure PostgreSQL is running")
        print("   2. Verify password in DATABASE_URL (.env file)")
        print("   3. Check if database 'skillsync' exists")
        print("   4. Verify user 'gauthamkrishna' has permissions")
        return False

def test_table_creation():
    """Test if tables can be created"""
    print_header("STEP 4: Testing Table Creation")
    
    try:
        from sqlalchemy import create_engine
        from dotenv import load_dotenv
        
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        
        # Import Base and models
        from app.database.connection import Base
        from app.models import (
            User, Internship, Resume, Application, 
            StudentInternshipMatch, CandidateExplanation,
            AuditLog, FairnessCheck
        )
        
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("\n✅ Database tables created successfully!")
        print("\n   Tables created:")
        print("   - users")
        print("   - internships")
        print("   - resumes")
        print("   - applications")
        print("   - student_internship_matches")
        print("   - candidate_explanations")
        print("   - audit_logs")
        print("   - fairness_checks")
        
        return True
        
    except Exception as e:
        print(f"\n  Table creation failed!")
        print(f"   Error: {str(e)}")
        return False

def print_next_steps(all_passed):
    """Print next steps based on results"""
    print_header("SUMMARY & NEXT STEPS")
    
    if all_passed:
        print("\n🎉 All checks passed! Your database is ready to use.")
        print("\nNext steps:")
        print("\n1. Start the FastAPI application:")
        print("   uvicorn app.main:app --reload --port 8000")
        print("\n2. Access the API documentation:")
        print("   http://localhost:8000/api/docs")
        print("\n3. Test the endpoints and create users")
        print("\n4. Check the backend README for usage instructions")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("\n1. Update DATABASE_URL in .env file:")
        print("   postgresql://gauthamkrishna:YOUR_PASSWORD@localhost:5432/skillsync")
        print("\n2. Ensure PostgreSQL is running:")
        print("   Get-Service postgresql*")
        print("\n3. Create database if needed:")
        print("   psql -U gauthamkrishna")
        print("   CREATE DATABASE skillsync;")
        print("\n4. Run this script again:")
        print("   python scripts\\complete_db_setup.py")

def main():
    """Main execution flow"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║         SkillSync - Complete Database Setup & Test               ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Run all checks
    results.append(("Dependencies", check_dependencies()))
    
    if results[-1][1]:  # Only proceed if dependencies are OK
        results.append(("Environment", check_env_configuration()))
        
        if results[-1][1]:  # Only proceed if env is OK
            results.append(("Connection", test_database_connection()))
            
            if results[-1][1]:  # Only proceed if connection is OK
                results.append(("Table Creation", test_table_creation()))
    
    # Print summary
    all_passed = all(result[1] for result in results)
    print_next_steps(all_passed)
    
    print("\n" + "=" * 70)
    print(f"  Result: {'✅ SUCCESS' if all_passed else '⚠️  NEEDS ATTENTION'}")
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
