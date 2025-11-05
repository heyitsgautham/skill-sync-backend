"""
Test script to check which Gemini API keys are working
Uses the NEW google-genai SDK (not google.generativeai)
"""
import os
import time

# List of API keys to test
api_keys = {
    "xmyhiruthik": "AIzaSyBNSlqKRHEbqE3MUtMNAxoJ_h_-MevNEJE",
    "hiruthiksudhakar": "AIzaSyCet85qQPbPp_BpMAikbuhqbcTUqXOiSl4",
    "vsdeeeksha24": "AIzaSyCGBVUVzxppp64F5CrB0YX2--DOefA1UUY",
    "devi": "AIzaSyDUBKEploeK1tm4CQ0GagshxJrJaB2oB7Y",
    "heyitsgautham": "AIzaSyA_woTNrFUowjz8R5GLyz9u9TzxzbH9Xl4",
    "hiru-viru": "AIzaSyCjbvqqSiWEmQ5RMB7U_DTXiuC7BoTG8as",
    "hycinth": "AIzaSyCBwHZm43mmRkFb9CdZNMn2ntx8kZO_OB0",
    "kishore3014b": "AIzaSyA597QYBJyhxdVx4uswB2EnQzkD-GS7xVw",
    "thennarasu": "AIzaSyBepsyGcWc74wHeoKlq_ME0-NxS03D6sT8",
    "yogasundari": "AIzaSyBZbXjFRwjPfP73-UDWGE0bq3hIT1J4_eA"
}

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
            print("❌ INVALID KEY")
            invalid_keys.append((username, api_key, error_msg[:100]))
        else:
            print(f"❌ ERROR: {error_msg[:50]}")
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
print(f"❌ Invalid/Error Keys: {len(invalid_keys)}")
for username, key, error in invalid_keys:
    print(f"   - {username}: {error}")

print()
print("=" * 80)

if working_keys:
    print(f"\n✨ You can use {len(working_keys)} working key(s) to parse resumes!")
else:
    print("\n⚠️  No working keys found. All keys are either rate-limited or invalid.")
