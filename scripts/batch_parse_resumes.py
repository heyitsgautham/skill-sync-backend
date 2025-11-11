"""
Batch Resume Parser with API Key Rotation
Parses all unparsed resumes using multiple Gemini API keys to avoid rate limiting
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import get_db
from app.models.resume import Resume
from app.models.user import User
from app.services.parser_service import ResumeParser
from app.services.resume_intelligence_service import ResumeIntelligenceService
from app.services.rag_engine import rag_engine
import time
from datetime import datetime
import traceback

# List of working API keys (rotate through them)
API_KEYS = [
    ("xmyhiruthik", "AIzaSyBNSlqKRHEbqE3MUtMNAxoJ_h_-MevNEJE"),
    ("hiruthiksudhakar", "AIzaSyCet85qQPbPp_BpMAikbuhqbcTUqXOiSl4"),
    ("vsdeeeksha24", "AIzaSyCGBVUVzxppp64F5CrB0YX2--DOefA1UUY"),
    ("devi", "AIzaSyDUBKEploeK1tm4CQ0GagshxJrJaB2oB7Y"),
    ("heyitsgautham", "AIzaSyA_woTNrFUowjz8R5GLyz9u9TzxzbH9Xl4"),
    ("hiru-viru", "AIzaSyCjbvqqSiWEmQ5RMB7U_DTXiuC7BoTG8as"),
    ("hycinth", "AIzaSyCBwHZm43mmRkFb9CdZNMn2ntx8kZO_OB0"),
    ("kishore3014b", "AIzaSyA597QYBJyhxdVx4uswB2EnQzkD-GS7xVw"),
    ("thennarasu", "AIzaSyBepsyGcWc74wHeoKlq_ME0-NxS03D6sT8"),
    ("yogasundari", "AIzaSyBZbXjFRwjPfP73-UDWGE0bq3hIT1J4_eA")
]

def parse_single_resume(resume, db, api_key_name, api_key):
    """Parse a single resume with error handling"""
    try:
        print(f"   📄 Parsing: {resume.file_name}")
        print(f"   🔑 Using API Key: {api_key_name}")
        
        # Set the API key for this parsing operation
        os.environ['GOOGLE_API_KEY'] = api_key
        
        # First extract raw text
        basic_data = ResumeParser.parse_resume(resume.file_path)
        resume_text = basic_data.get('parsed_content', '')
        
        # Use Gemini for intelligent extraction
        intelligence_service = ResumeIntelligenceService()
        structured_data = intelligence_service.extract_structured_data(resume_text)
        
        # Combine data
        parsed_data = {
            **basic_data,
            **structured_data,
            'parsed_content': resume_text
        }
        
        # Generate embedding (like AI Resume Intelligence does)
        embedding = None
        if resume.parsed_content and resume.extracted_skills:
            embedding_text = f"{resume_text}\n\nSkills: {', '.join(resume.extracted_skills)}"
            embedding = rag_engine.generate_embedding(embedding_text)
            print(f"   🔢 Generated embedding: dimension {len(embedding)}")
        
        # Update resume in database (store only in ChromaDB, not PostgreSQL!)
        resume.parsed_content = resume_text
        resume.parsed_data = parsed_data
        resume.extracted_skills = structured_data.get('all_skills', [])
        # NOTE: No longer storing embedding in PostgreSQL - only in ChromaDB!
        
        # Store in RAG engine (ChromaDB) - single source of truth
        if resume.parsed_content and resume.extracted_skills:
            try:
                embedding_id = rag_engine.store_resume_embedding(
                    resume_id=str(resume.resume_id),
                    content=resume.parsed_content,
                    skills=resume.extracted_skills,
                    metadata={
                        "student_id": resume.student_id,
                        "file_name": resume.file_name
                    }
                )
                resume.embedding_id = embedding_id
                print(f"   ✅ Indexed in ChromaDB: {embedding_id}")
            except Exception as e:
                print(f"   ⚠️  ChromaDB indexing failed: {str(e)[:100]}")
        
        db.commit()
        db.refresh(resume)
        
        return {
            "status": "success",
            "resume_id": resume.id,
            "file_name": resume.file_name,
            "skills_count": len(resume.extracted_skills) if resume.extracted_skills else 0,
            "api_key": api_key_name
        }
        
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        
        # Detect specific error types
        if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
            error_type = "RATE_LIMITED"
        elif "invalid" in error_msg.lower() or "api key" in error_msg.lower():
            error_type = "INVALID_KEY"
        else:
            error_type = "PARSING_ERROR"
        
        return {
            "status": "error",
            "error_type": error_type,
            "resume_id": resume.id,
            "file_name": resume.file_name,
            "error": error_msg[:200],
            "api_key": api_key_name
        }

def main():
    print("=" * 80)
    print("BATCH RESUME PARSER WITH API KEY ROTATION")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db = next(get_db())
    
    # Find all resumes that need parsing (no parsed_data or empty or no skills or no embedding)
    print("🔍 Finding resumes that need re-parsing with Gemini...")
    from sqlalchemy import or_, cast, Text
    
    # Get all resumes and filter in Python (to avoid PostgreSQL JSON comparison issues)
    all_resumes = db.query(Resume).all()
    resumes_to_parse = []
    
    for r in all_resumes:
        # Need to parse if:
        # 1. No parsed_data OR
        # 2. No extracted_skills OR empty extracted_skills OR
        # 3. No embedding field (IMPORTANT: need to generate embeddings!) OR
        # 4. File exists and can be read
        if os.path.exists(r.file_path):
            if not r.parsed_data or not r.extracted_skills or len(r.extracted_skills) == 0 or not r.embedding:
                resumes_to_parse.append(r)
    
    total_resumes = len(resumes_to_parse)
    print(f"📊 Found {total_resumes} resumes to parse")
    print()
    
    if total_resumes == 0:
        print("✨ All resumes are already parsed!")
        return
    
    # Statistics tracking
    results = {
        "success": [],
        "error": [],
        "rate_limited": []
    }
    
    # Process each resume with API key rotation
    current_key_index = 0
    
    for idx, resume in enumerate(resumes_to_parse, 1):
        print(f"\n{'='*80}")
        print(f"📝 Resume {idx}/{total_resumes}")
        print(f"{'='*80}")
        
        # Get current API key
        api_key_name, api_key = API_KEYS[current_key_index]
        
        # Try to parse with current key
        result = parse_single_resume(resume, db, api_key_name, api_key)
        
        # If rate limited, try next key
        if result["status"] == "error" and result["error_type"] == "RATE_LIMITED":
            print(f"   🔴 Rate limited on {api_key_name}, trying next key...")
            results["rate_limited"].append(result)
            
            # Try with next key
            current_key_index = (current_key_index + 1) % len(API_KEYS)
            api_key_name, api_key = API_KEYS[current_key_index]
            
            print(f"   🔄 Retrying with {api_key_name}...")
            result = parse_single_resume(resume, db, api_key_name, api_key)
        
        # Store result
        if result["status"] == "success":
            print(f"   ✅ SUCCESS: Parsed {result['skills_count']} skills")
            results["success"].append(result)
        else:
            print(f"     ERROR: {result['error_type']} - {result['error'][:100]}")
            results["error"].append(result)
        
        # Rotate to next key for next resume
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        
        # Small delay between requests
        time.sleep(1)
    
    # Print Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print(f"✅ Successfully Parsed: {len(results['success'])}/{total_resumes}")
    print(f"  Errors: {len(results['error'])}/{total_resumes}")
    print(f"🔴 Rate Limited Attempts: {len(results['rate_limited'])}")
    print()
    
    if results["success"]:
        print("✅ SUCCESSFUL PARSES:")
        for r in results["success"]:
            print(f"   - Resume {r['resume_id']}: {r['file_name']} ({r['skills_count']} skills) [Key: {r['api_key']}]")
    
    if results["error"]:
        print(f"\n  FAILED PARSES ({len(results['error'])}):")
        for r in results["error"]:
            print(f"   - Resume {r['resume_id']}: {r['file_name']}")
            print(f"     Error Type: {r['error_type']}")
            print(f"     Message: {r['error'][:150]}")
            print(f"     API Key: {r['api_key']}")
    
    print("\n" + "=" * 80)
    
    # Calculate success rate
    success_rate = (len(results['success']) / total_resumes * 100) if total_resumes > 0 else 0
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 All resumes parsed successfully!")
    elif success_rate >= 80:
        print("✅ Most resumes parsed successfully!")
    else:
        print("⚠️  Many resumes failed to parse. Check errors above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n\n  Fatal Error: {str(e)}")
        traceback.print_exc()
