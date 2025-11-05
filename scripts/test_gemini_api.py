#!/usr/bin/env python3
"""
Quick test script to verify Gemini API connection
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

print('🔍 Testing Gemini API connection...\n')

api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print('❌ GOOGLE_API_KEY not found in environment')
    exit(1)

print(f'✅ API Key found: {api_key[:10]}...{api_key[-5:]}')

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Simple test
    test_prompt = 'Return a JSON object with a single key "status" and value "ready". Return ONLY the JSON.'
    response = model.generate_content(test_prompt)
    print(f'\n✅ Gemini API Response:\n{response.text.strip()}\n')
    print('🎉 Gemini API is working correctly!')
    print('✅ Ready for intelligent resume parsing!')
    
except Exception as e:
    print(f'\n❌ Gemini API Error: {e}')
    print('Please check your API key and internet connection')
    exit(1)
