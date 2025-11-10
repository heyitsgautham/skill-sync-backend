"""
Test script to verify phone number export fix
Tests both CSV and XLSX export formats
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
from pathlib import Path

# API Configuration
BASE_URL = "http://localhost:8000"

def get_auth_token(email, password):
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"  Login failed: {response.text}")
        return None

def get_company_internships(token):
    """Get company's internships"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/internship/my-posts", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"  Failed to get internships: {response.text}")
        return []

def test_export(token, internship_id, format_type):
    """Test export functionality"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n📊 Testing {format_type.upper()} export for internship {internship_id}...")
    
    response = requests.get(
        f"{BASE_URL}/api/filter/export-candidates/{internship_id}",
        headers=headers,
        params={
            "format": format_type,
            "export_type": "all"  # Export all candidates
        }
    )
    
    if response.status_code == 200:
        # Save file
        output_dir = Path("test_exports")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"test_export_internship_{internship_id}.{format_type}"
        filepath = output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Export successful! Saved to: {filepath}")
        print(f"   File size: {len(response.content)} bytes")
        
        # For CSV, let's read and check the phone numbers
        if format_type == "csv":
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n📋 First few lines of CSV:")
                for i, line in enumerate(lines[:3]):
                    print(f"   Line {i+1}: {line.strip()}")
                
                # Check if any phone numbers contain formulas
                phone_column_idx = None
                headers_line = lines[0].strip().split(',')
                for idx, header in enumerate(headers_line):
                    if 'Phone' in header:
                        phone_column_idx = idx
                        break
                
                if phone_column_idx is not None:
                    print(f"\n📞 Checking phone numbers (column {phone_column_idx + 1}):")
                    for i, line in enumerate(lines[1:6], start=2):  # Check first 5 data rows
                        parts = line.strip().split(',')
                        if len(parts) > phone_column_idx:
                            phone = parts[phone_column_idx]
                            print(f"   Row {i}: {phone}")
                            
                            # Check for formula indicators
                            if phone.startswith('=') or phone.startswith('+'):
                                print(f"      ⚠️  WARNING: Phone may be interpreted as formula!")
                            elif phone.startswith("'"):
                                print(f"      ✅ Good: Prefixed with apostrophe (text format)")
        
        return True
    else:
        print(f"  Export failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def main():
    print("=" * 60)
    print("🧪 Testing Phone Number Export Fix")
    print("=" * 60)
    
    # Use a company account (you can change these credentials)
    COMPANY_EMAIL = "hr@techcorp.com"
    COMPANY_PASSWORD = "TechCorp2024"
    
    print(f"\n🔐 Logging in as: {COMPANY_EMAIL}")
    token = get_auth_token(COMPANY_EMAIL, COMPANY_PASSWORD)
    
    if not token:
        print("\n  Failed to authenticate. Please check credentials.")
        return
    
    print("✅ Authentication successful!")
    
    # Get company's internships
    print("\n📋 Fetching company internships...")
    internships = get_company_internships(token)
    
    if not internships:
        print("  No internships found or failed to fetch")
        return
    
    print(f"✅ Found {len(internships)} internship(s)")
    
    # Use the first internship for testing
    if internships:
        internship = internships[0]
        internship_id = internship.get('internship_id') or internship.get('id')
        title = internship.get('title', 'Unknown')
        
        print(f"\n🎯 Testing with internship: '{title}' (ID: {internship_id})")
        
        # Test both CSV and XLSX formats
        test_export(token, internship_id, "csv")
        test_export(token, internship_id, "xlsx")
        
        print("\n" + "=" * 60)
        print("✅ Export testing complete!")
        print("=" * 60)
        print("\n📁 Check the 'test_exports' directory for exported files")
        print("💡 Open the CSV file in a text editor to verify phone format")
        print("💡 Open the XLSX file in Excel to verify phone display")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n  Error: {str(e)}")
        import traceback
        traceback.print_exc()
