"""
Test script to verify the new Gemini API key manager works correctly
Tests key rotation, retry logic, and API calls
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.gemini_key_manager import get_gemini_key_manager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_basic_generation():
    """Test basic content generation"""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Content Generation")
    print("=" * 80)
    
    try:
        key_manager = get_gemini_key_manager()
        
        response = key_manager.generate_content(
            prompt="What is the capital of France? Answer in one word.",
            purpose="resume_parsing",
            temperature=0,
            max_output_tokens=10
        )
        
        print(f"✅ SUCCESS: Got response: {response}")
        return True
        
    except Exception as e:
        print(f"  FAILED: {str(e)}")
        return False


def test_multiple_purposes():
    """Test using different purposes (different keys)"""
    print("\n" + "=" * 80)
    print("TEST 2: Multiple Purpose Keys")
    print("=" * 80)
    
    purposes = [
        "resume_parsing",
        "matching_explanation", 
        "skills_extraction",
        "candidate_summary"
    ]
    
    results = []
    key_manager = get_gemini_key_manager()
    
    for purpose in purposes:
        try:
            print(f"\nTesting purpose: {purpose}")
            response = key_manager.generate_content(
                prompt="Say 'OK'",
                purpose=purpose,
                temperature=0,
                max_output_tokens=5
            )
            print(f"✅ {purpose}: {response}")
            results.append(True)
        except Exception as e:
            print(f"  {purpose} failed: {str(e)}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Success rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    return all(results)


def test_json_extraction():
    """Test structured JSON extraction (like resume parsing)"""
    print("\n" + "=" * 80)
    print("TEST 3: Structured JSON Extraction")
    print("=" * 80)
    
    try:
        key_manager = get_gemini_key_manager()
        
        prompt = """
Extract this person's info as JSON:
"John Doe, Software Engineer with 5 years experience in Python, Java, React"

Return ONLY valid JSON in this format:
{
  "name": "...",
  "experience_years": 0,
  "skills": ["skill1", "skill2"]
}
"""
        
        response = key_manager.generate_content(
            prompt=prompt,
            purpose="resume_parsing",
            temperature=0,
            max_output_tokens=200
        )
        
        print(f"Response:\n{response}")
        
        # Try to parse as JSON
        import json
        import re
        
        # Clean up markdown
        cleaned = re.sub(r'^```json\s*', '', response)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        
        parsed = json.loads(cleaned)
        print(f"✅ SUCCESS: Parsed JSON with keys: {list(parsed.keys())}")
        return True
        
    except Exception as e:
        print(f"  FAILED: {str(e)}")
        return False


def test_retry_mechanism():
    """Test that retry mechanism works"""
    print("\n" + "=" * 80)
    print("TEST 4: Retry Mechanism")
    print("=" * 80)
    
    try:
        key_manager = get_gemini_key_manager()
        
        # Force one key to fail by marking it as failed
        key_manager.failed_keys.add("resume_parsing")
        print("Marked 'resume_parsing' key as failed to test retry...")
        
        response = key_manager.generate_content(
            prompt="Say 'Retry worked'",
            purpose="resume_parsing",  # This key is marked as failed
            temperature=0,
            max_output_tokens=10,
            max_retries=3
        )
        
        print(f"✅ SUCCESS: Retry mechanism worked! Response: {response}")
        
        # Reset failed keys
        key_manager.reset_failed_keys()
        return True
        
    except Exception as e:
        print(f"  FAILED: {str(e)}")
        return False


def test_streaming():
    """Test streaming content generation"""
    print("\n" + "=" * 80)
    print("TEST 5: Streaming Generation")
    print("=" * 80)
    
    try:
        key_manager = get_gemini_key_manager()
        
        print("Streaming response: ", end="", flush=True)
        
        chunks = []
        for chunk in key_manager.generate_content_stream(
            prompt="Count from 1 to 5 separated by commas",
            purpose="candidate_summary",
            temperature=0
        ):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        
        print()
        
        if len(chunks) > 0:
            print(f"✅ SUCCESS: Received {len(chunks)} chunks")
            return True
        else:
            print("  FAILED: No chunks received")
            return False
        
    except Exception as e:
        print(f"  FAILED: {str(e)}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 80)
    print("GEMINI KEY MANAGER TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Basic Generation", test_basic_generation),
        ("Multiple Purposes", test_multiple_purposes),
        ("JSON Extraction", test_json_extraction),
        ("Retry Mechanism", test_retry_mechanism),
        ("Streaming", test_streaming)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "  FAILED"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print("\n" + "=" * 80)
    print(f"OVERALL: {passed}/{total} tests passed ({success_rate:.1f}%)")
    print("=" * 80)
    
    return success_rate == 100


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
