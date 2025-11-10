"""
Test PostgreSQL Database Connection
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test database connection"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        print(f"Testing connection to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")
        
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print("\n✓ PostgreSQL connection successful!")
            print(f"✓ PostgreSQL version: {version[:50]}...")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\n✓ Found {len(tables)} tables in database:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠ No tables found. Run the application to create tables.")
            
        print("\n✓ Database connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Database connection failed!")
        print(f"Error: {str(e)}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. DATABASE_URL in .env is correct")
        print("3. Database 'skillsync' exists")
        print("4. User has proper permissions")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
