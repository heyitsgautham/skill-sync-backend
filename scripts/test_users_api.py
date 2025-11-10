"""
Test if the /api/auth/users endpoint returns is_active field
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("TESTING /api/auth/users ENDPOINT")
print("=" * 80)

# Login as admin
print("\n1️⃣ Logging in as admin...")
login_data = {
    "email": "admin@gmail.com",
    "password": "Admin2024"
}

response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
print(f"✅ Logged in successfully")

headers = {
    "Authorization": f"Bearer {token}"
}

# Get users list
print("\n2️⃣ Fetching users list...")
response = requests.get(f"{BASE_URL}/api/auth/users", headers=headers)
if response.status_code != 200:
    print(f"❌ Failed to get users: {response.text}")
    exit(1)

users = response.json()
print(f"✅ Received {len(users)} users")

# Check first few students
print("\n3️⃣ Checking first 5 students for is_active field...")
students = [u for u in users if u.get('role') == 'student'][:5]

if not students:
    print("❌ No students found")
    exit(1)

has_is_active_field = False
for student in students:
    is_active = student.get('is_active')
    status = "✅ ACTIVE" if is_active == 1 else "🚫 INACTIVE"
    
    if is_active is not None:
        has_is_active_field = True
        print(f"  - {student['full_name']}: is_active = {is_active} {status}")
    else:
        print(f"  - {student['full_name']}: ❌ MISSING is_active field!")

print("\n" + "=" * 80)
if has_is_active_field:
    print("✅ SUCCESS: is_active field is present in API response!")
else:
    print("❌ FAILURE: is_active field is missing from API response!")
print("=" * 80)
