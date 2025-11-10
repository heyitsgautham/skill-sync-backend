"""
Test script to check which Gemini API keys are working
Uses the NEW google-genai SDK (not google.generativeai)
Reads API keys from .env file
"""
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# List of API keys to test from environment variables
api_keys = {
    "resume_parsing": os.getenv("GEMINI_KEY_RESUME_PARSING"),
    "matching_explanation": os.getenv("GEMINI_KEY_MATCHING_EXPLANATION"),
    "skills_extraction": os.getenv("GEMINI_KEY_SKILLS_EXTRACTION"),
    "embedding_generation": os.getenv("GEMINI_KEY_EMBEDDING_GENERATION"),
    "candidate_summary": os.getenv("GEMINI_KEY_CANDIDATE_SUMMARY"),
    "internship_analysis": os.getenv("GEMINI_KEY_INTERNSHIP_ANALYSIS"),
    "achievement_extraction": os.getenv("GEMINI_KEY_ACHIEVEMENT_EXTRACTION"),
    "fallback_1": os.getenv("GEMINI_KEY_FALLBACK_1"),
    "fallback_2": os.getenv("GEMINI_KEY_FALLBACK_2"),
    "fallback_3": os.getenv("GEMINI_KEY_FALLBACK_3")
}

# Remove None values (keys not set in .env)
api_keys = {k: v for k, v in api_keys.items() if v}

if not api_keys:
    print("  ERROR: No API keys found in .env file!")
    print("Please set GEMINI_KEY_* variables in your .env file")
    sys.exit(1)

print("=" * 80)
print("TESTING GEMINI API KEYS (NEW SDK)")
print("=" * 80)
print()

working_keys = []
rate_limited_keys = []
invalid_keys = []

for username, api_key in api_keys.items():
    print(f"Testing: {username}...", end=" ")
    
    try:
        # Set the API key as environment variable (new SDK requirement)
        os.environ['GEMINI_API_KEY'] = api_key
        
        # Import the NEW SDK
        from google import genai
        
        # Create client
        client = genai.Client(api_key=api_key)
        
        # Try a simple generation with Gemini 2.5 Flash
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'OK'"
        )
        
        if response and response.text:
            print("✅ WORKING")
            working_keys.append((username, api_key))
        else:
            print("⚠️  NO RESPONSE")
            invalid_keys.append((username, api_key, "No response"))
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            print("🔴 RATE LIMITED")
            rate_limited_keys.append((username, api_key, error_msg[:100]))
        elif "invalid" in error_msg.lower() or "api key" in error_msg.lower():
            print("  INVALID KEY")
            invalid_keys.append((username, api_key, error_msg[:100]))
        else:
            print(f"  ERROR: {error_msg[:50]}")
            invalid_keys.append((username, api_key, error_msg[:100]))
    
    # Small delay to avoid hitting rate limits during testing
    time.sleep(1)

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print(f"✅ Working Keys: {len(working_keys)}")
for username, key in working_keys:
    print(f"   - {username}: {key}")

print()
print(f"🔴 Rate Limited Keys: {len(rate_limited_keys)}")
for username, key, error in rate_limited_keys:
    print(f"   - {username}: {error}")

print()
print(f"  Invalid/Error Keys: {len(invalid_keys)}")
for username, key, error in invalid_keys:
    print(f"   - {username}: {error}")

print()
print("=" * 80)

if working_keys:
    print(f"\n✨ You can use {len(working_keys)} working key(s) to parse resumes!")
else:
    print("\n⚠️  No working keys found. All keys are either rate-limited or invalid.")
