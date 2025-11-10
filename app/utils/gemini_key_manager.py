"""
Gemini API Key Manager - Centralized key rotation and retry logic
Handles rate limiting by rotating through multiple API keys
Uses the NEW google-genai SDK (not google.generativeai)
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiKeyManager:
    """
    Manages multiple Gemini API keys with automatic rotation and retry logic
    Prevents rate limiting errors by distributing requests across keys
    """
    
    def __init__(self):
        """Initialize key manager with purpose-specific keys from environment variables"""
        # Load API keys from environment variables
        self.purpose_keys = {
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
        self.purpose_keys = {k: v for k, v in self.purpose_keys.items() if v}
        
        if not self.purpose_keys:
            logger.warning("⚠️  No Gemini API keys found in environment variables!")
            logger.warning("⚠️  Please set GEMINI_KEY_* variables in your .env file")
        else:
            logger.info(f"✅ Loaded {len(self.purpose_keys)} Gemini API keys from environment")
        
        self.failed_keys = set()  # Track temporarily failed keys
        self.clients = {}  # Cache clients per key
        
    def get_client(self, purpose: str = "resume_parsing", max_retries: int = 3) -> genai.Client:
        """
        Get a working Gemini client for a specific purpose with retry logic
        
        Args:
            purpose: Purpose of the API call (determines which key to use first)
            max_retries: Maximum number of retry attempts
            
        Returns:
            Configured genai.Client instance
            
        Raises:
            Exception: If all keys are rate limited or failed
        """
        # Get the priority list of keys for this purpose
        keys_to_try = self._get_key_priority_list(purpose)
        
        last_error = None
        for attempt in range(max_retries):
            for key_name in keys_to_try:
                if key_name in self.failed_keys:
                    continue
                    
                api_key = self.purpose_keys.get(key_name)
                if not api_key:
                    continue
                
                try:
                    # Create or reuse cached client
                    if key_name not in self.clients:
                        logger.info(f"🔑 Creating new client for purpose: {purpose} using key: {key_name}")
                        self.clients[key_name] = genai.Client(api_key=api_key)
                    
                    # Test the client with a simple call
                    if attempt == 0:  # Only test on first attempt
                        self._test_client(self.clients[key_name], key_name)
                    
                    logger.info(f"✅ Using key: {key_name} for purpose: {purpose}")
                    return self.clients[key_name]
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Check if it's a rate limit error
                    if "429" in str(e) or "quota" in error_msg or "rate" in error_msg:
                        logger.warning(f"🔴 Key {key_name} rate limited: {str(e)[:100]}")
                        self.failed_keys.add(key_name)
                        last_error = e
                        continue
                    
                    # Check if it's an invalid key
                    elif "invalid" in error_msg or "api key" in error_msg:
                        logger.error(f"  Key {key_name} is invalid: {str(e)[:100]}")
                        self.failed_keys.add(key_name)
                        last_error = e
                        continue
                    
                    # Other errors - retry with backoff
                    else:
                        logger.warning(f"⚠️  Key {key_name} error (attempt {attempt + 1}): {str(e)[:100]}")
                        last_error = e
                        time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                        continue
            
            # Clear failed keys for next attempt (give them another chance)
            if attempt < max_retries - 1:
                logger.info(f"🔄 Clearing failed keys and retrying (attempt {attempt + 2}/{max_retries})")
                self.failed_keys.clear()
                time.sleep(1)  # Wait before retrying all keys
        
        # All keys failed
        error_message = f"All Gemini API keys failed after {max_retries} attempts. Last error: {last_error}"
        logger.error(f"  {error_message}")
        raise Exception(error_message)
    
    def _get_key_priority_list(self, purpose: str) -> List[str]:
        """
        Get priority-ordered list of keys to try for a given purpose
        
        Args:
            purpose: Purpose of the API call
            
        Returns:
            List of key names in priority order
        """
        # Purpose-specific key comes first, then fallbacks
        priority_list = []
        
        if purpose in self.purpose_keys:
            priority_list.append(purpose)
        
        # Add fallback keys
        fallback_keys = [k for k in self.purpose_keys.keys() if k.startswith("fallback")]
        priority_list.extend(fallback_keys)
        
        # Add all other keys as last resort
        other_keys = [k for k in self.purpose_keys.keys() 
                     if k != purpose and not k.startswith("fallback")]
        priority_list.extend(other_keys)
        
        return priority_list
    
    def _test_client(self, client: genai.Client, key_name: str):
        """
        Test if a client is working with a simple API call
        
        Args:
            client: The genai.Client to test
            key_name: Name of the key being tested
            
        Raises:
            Exception: If the test fails
        """
        try:
            # Simple test - just check if the API call succeeds
            # Don't check response.text as it might be empty for very simple prompts
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Say OK",
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                    temperature=0
                )
            )
            
            # Just check that we got a response object, don't validate text content
            if not response:
                raise Exception("No response object from API")
                
        except Exception as e:
            logger.error(f"  Client test failed for {key_name}: {str(e)}")
            raise
    
    def generate_content(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash",
        purpose: str = "resume_parsing",
        temperature: float = 0.2,
        max_output_tokens: int = 8000,
        system_instruction: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Generate content using Gemini with automatic key rotation
        
        Args:
            prompt: The prompt to send to Gemini
            model: Model to use (gemini-2.5-flash or gemini-2.5-pro)
            purpose: Purpose of the call (for key selection)
            temperature: Sampling temperature (0-1)
            max_output_tokens: Maximum tokens to generate
            system_instruction: Optional system instruction
            max_retries: Maximum retry attempts
            
        Returns:
            Generated text content
            
        Raises:
            Exception: If all retries fail
        """
        client = self.get_client(purpose=purpose, max_retries=max_retries)
        
        # Configure generation
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
        
        if system_instruction:
            config.system_instruction = system_instruction
        
        try:
            logger.info(f"📤 Generating content for purpose: {purpose} with model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )
            
            # Check if response exists
            if not response:
                logger.error("  No response object from Gemini API")
                raise Exception("No response from Gemini API")
            
            # Check for blocked content or safety issues
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    logger.info(f"📊 Finish reason: {candidate.finish_reason}")
                    if candidate.finish_reason == 'SAFETY':
                        logger.error("  Response blocked by safety filters")
                        raise Exception("Response blocked by Gemini safety filters")
                if hasattr(candidate, 'safety_ratings'):
                    logger.info(f"📊 Safety ratings: {candidate.safety_ratings}")
            
            # Get response text
            if not response.text or response.text.strip() == "":
                logger.error("  Empty response text from Gemini API")
                logger.error(f"📊 Full response: {response}")
                raise Exception("Empty response from Gemini API")
            
            logger.info(f"✅ Content generated successfully ({len(response.text)} chars)")
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"  Error generating content: {str(e)}")
            raise
    
    def generate_content_stream(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash",
        purpose: str = "resume_parsing",
        temperature: float = 0.2,
        system_instruction: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Generate streaming content using Gemini with automatic key rotation
        
        Args:
            prompt: The prompt to send to Gemini
            model: Model to use (gemini-2.5-flash or gemini-2.5-pro)
            purpose: Purpose of the call (for key selection)
            temperature: Sampling temperature (0-1)
            system_instruction: Optional system instruction
            max_retries: Maximum retry attempts
            
        Yields:
            Content chunks as they arrive
            
        Raises:
            Exception: If all retries fail
        """
        client = self.get_client(purpose=purpose, max_retries=max_retries)
        
        # Configure generation
        config = types.GenerateContentConfig(
            temperature=temperature
        )
        
        if system_instruction:
            config.system_instruction = system_instruction
        
        try:
            logger.info(f"📤 Streaming content for purpose: {purpose} with model: {model}")
            response_stream = client.models.generate_content_stream(
                model=model,
                contents=prompt,
                config=config
            )
            
            for chunk in response_stream:
                if chunk and chunk.text:
                    yield chunk.text
            
            logger.info(f"✅ Streaming completed successfully")
            
        except Exception as e:
            logger.error(f"  Error streaming content: {str(e)}")
            raise
    
    def reset_failed_keys(self):
        """Reset the failed keys set (useful for periodic cleanup)"""
        logger.info(f"🔄 Resetting {len(self.failed_keys)} failed keys")
        self.failed_keys.clear()


# Global singleton instance
_key_manager = None

def get_gemini_key_manager() -> GeminiKeyManager:
    """Get or create the global GeminiKeyManager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = GeminiKeyManager()
    return _key_manager
