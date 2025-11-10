"""
PostgreSQL Connection Helper
Helps diagnose and fix PostgreSQL connection issues
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_env_file():
    """Check if .env file is properly configured"""
    print("=" * 60)
    print("CHECKING ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        print("  .env file not found!")
        print(f"   Expected location: {os.path.abspath(env_path)}")
        return False
    
    print(f"✅ .env file found: {os.path.abspath(env_path)}")
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("  DATABASE_URL not set in .env file")
        return False
    
    print(f"✅ DATABASE_URL is set")
    
    # Parse the URL
    if "YOUR_PASSWORD" in DATABASE_URL or "your-password" in DATABASE_URL.lower():
        print("\n⚠️  WARNING: DATABASE_URL contains placeholder password!")
        print("   Please update .env file with your actual PostgreSQL password.")
        print(f"\n   Current: {DATABASE_URL}")
        print(f"   Update to: postgresql://gauthamkrishna:YOUR_ACTUAL_PASSWORD@localhost:5432/skillsync")
        return False
    
    # Check URL format
    if not DATABASE_URL.startswith("postgresql://"):
        print(f"  Invalid DATABASE_URL format: {DATABASE_URL}")
        print("   Should start with: postgresql://")
        return False
    
    # Extract components
    try:
        url_parts = DATABASE_URL.replace("postgresql://", "").split("@")
        if len(url_parts) != 2:
            print("  Invalid URL format - missing @ separator")
            return False
        
        auth_part = url_parts[0]
        server_part = url_parts[1]
        
        if ":" in auth_part:
            username, password = auth_part.split(":", 1)
            print(f"   Username: {username}")
            print(f"   Password: {'*' * len(password)} ({len(password)} chars)")
        else:
            print(f"   Username: {auth_part}")
            print("   ⚠️  No password found in URL")
        
        print(f"   Server: {server_part}")
        
    except Exception as e:
        print(f"  Error parsing DATABASE_URL: {e}")
        return False
    
    return True

def suggest_fixes():
    """Suggest common fixes"""
    print("\n" + "=" * 60)
    print("SUGGESTED FIXES")
    print("=" * 60)
    
    print("\n1. UPDATE .ENV FILE:")
    print("   Open: skill-sync-backend\\.env")
    print("   Find: DATABASE_URL=...")
    print("   Update to: postgresql://gauthamkrishna:YOUR_PASSWORD@localhost:5432/skillsync")
    print("   (Replace YOUR_PASSWORD with your actual PostgreSQL password)")
    
    print("\n2. ALTERNATIVE: Use PostgreSQL without password (for local development)")
    print("   Open PostgreSQL's pg_hba.conf file")
    print("   Change authentication method to 'trust' for local connections")
    print("   Then use: postgresql://gauthamkrishna@localhost:5432/skillsync")
    
    print("\n3. CREATE DATABASE (if not exists):")
    print("   Run in psql or pgAdmin:")
    print("   CREATE DATABASE skillsync;")
    
    print("\n4. TEST CONNECTION:")
    print("   python scripts\\test_db_connection.py")

if __name__ == "__main__":
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║       PostgreSQL Connection Helper - SkillSync         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("\n")
    
    is_valid = check_env_file()
    suggest_fixes()
    
    print("\n" + "=" * 60)
    if is_valid:
        print("✅ Configuration looks good! Try testing the connection.")
    else:
        print("⚠️  Please fix the issues above and try again.")
    print("=" * 60 + "\n")
    
    sys.exit(0 if is_valid else 1)
