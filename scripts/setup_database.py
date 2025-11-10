"""
Quick Database Setup Script
Interactively configure PostgreSQL connection
"""
import os
import sys
from pathlib import Path

def update_env_file(password):
    """Update the .env file with the database password"""
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        print(f"  .env file not found at {env_path}")
        return False
    
    # Read the file
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update the DATABASE_URL line
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith('DATABASE_URL='):
            if password:
                lines[i] = f'DATABASE_URL=postgresql://gauthamkrishna:{password}@localhost:5432/skillsync\n'
            else:
                # No password (trust authentication)
                lines[i] = f'DATABASE_URL=postgresql://gauthamkrishna@localhost:5432/skillsync\n'
            updated = True
            break
    
    if not updated:
        print("  DATABASE_URL not found in .env file")
        return False
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated DATABASE_URL in {env_path}")
    return True

def main():
    print("\n" + "=" * 60)
    print("PostgreSQL Database Setup - SkillSync")
    print("=" * 60 + "\n")
    
    print("This script will help you configure the PostgreSQL connection.")
    print("\nOptions:")
    print("1. Enter PostgreSQL password")
    print("2. Use trust authentication (no password - local development only)")
    print("3. Exit without changes")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        password = input("\nEnter PostgreSQL password for user 'gauthamkrishna': ").strip()
        if not password:
            print("  Password cannot be empty")
            return False
        
        if update_env_file(password):
            print("\n✅ Configuration updated successfully!")
            print("\nNext steps:")
            print("1. Ensure PostgreSQL is running")
            print("2. Create database: CREATE DATABASE skillsync;")
            print("3. Test connection: python scripts\\test_db_connection.py")
            return True
    
    elif choice == "2":
        print("\n⚠️  Using trust authentication (no password)")
        print("This is only recommended for local development.")
        print("\nYou need to configure PostgreSQL's pg_hba.conf file first:")
        print("1. Find pg_hba.conf (usually in PostgreSQL installation directory)")
        print("2. Add or modify this line:")
        print("   host    all    gauthamkrishna    127.0.0.1/32    trust")
        print("3. Reload PostgreSQL configuration")
        
        proceed = input("\nHave you configured pg_hba.conf? (y/n): ").strip().lower()
        if proceed == 'y':
            if update_env_file(None):
                print("\n✅ Configuration updated successfully!")
                print("\nNext steps:")
                print("1. Reload PostgreSQL: pg_ctl reload")
                print("2. Test connection: python scripts\\test_db_connection.py")
                return True
        else:
            print("Please configure pg_hba.conf first, then run this script again.")
            return False
    
    else:
        print("\nExiting without changes.")
        return False
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        print("\n" + "=" * 60 + "\n")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Error: {e}")
        sys.exit(1)
