"""
Quick diagnostic script to test the API endpoint directly
"""
import requests
import json

# Test the actual API endpoint
BASE_URL = "http://localhost:8000"

print("=" * 80)
print("TESTING LIVE API ENDPOINT")
print("=" * 80)

# First, let's login as a company user
print("\n1️⃣ Logging in as company user...")
login_data = {
    "email": "hr@techcorp.com",
    "password": "TechCorp2024"
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

# Use a known internship ID (from database)
print("\n2️⃣ Using internship ID 1 (Full Stack Software Engineer Intern)...")
internship_id = 1
internship_title = "Full Stack Software Engineer Intern"
print(f"✅ Testing with: {internship_title} (ID: {internship_id})")

# Test ranking endpoint with discovery mode (all candidates)
print(f"\n3️⃣ Testing ranking endpoint (discovery mode)...")
response = requests.post(
    f"{BASE_URL}/api/filter/rank-candidates/{internship_id}",
    headers=headers,
    params={
        "only_applicants": False,
        "limit": 100
    }
)

if response.status_code != 200:
    print(f"❌ Ranking request failed: {response.text}")
    exit(1)

data = response.json()
candidates = data.get("ranked_candidates", [])

print(f"✅ Received {len(candidates)} candidates")

# Check if inactive students are in results
print("\n4️⃣ Checking for inactive students (ID 71 'Gautham', ID 72 'Virat')...")
inactive_found = []
for candidate in candidates:
    candidate_id = candidate.get("candidate_id") or candidate.get("student_id")
    candidate_name = candidate.get("candidate_name") or candidate.get("student_name")
    
    if candidate_id in [71, 72]:
        inactive_found.append(f"ID {candidate_id}: {candidate_name}")
        print(f"  🐛 BUG: Found inactive student - {candidate_name} (ID: {candidate_id})")

if not inactive_found:
    print(f"  ✅ SUCCESS: No inactive students found in results!")
    print(f"  ✅ Filter is working correctly in the API!")
else:
    print(f"\n  ❌ PROBLEM: Found {len(inactive_found)} inactive students:")
    for student in inactive_found:
        print(f"    - {student}")
    print(f"\n  ⚠️ The backend server may not have reloaded yet.")
    print(f"  ⚠️ Try restarting the uvicorn server manually.")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
