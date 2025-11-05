#!/usr/bin/env python3
"""
System Status Check - Verify all components of Intelligent Filtering System
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_status():
    print("=" * 60)
    print("🔍 INTELLIGENT FILTERING SYSTEM - STATUS CHECK")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Check database connection
    print("\n📊 DATABASE:")
    try:
        from app.database.connection import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  ✅ PostgreSQL connection successful")
        
        # Check new columns
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'user_id'
            """))
            if result.scalar() > 0:
                print("  ✅ Database schema migrated (new columns present)")
            else:
                print("  ⚠️  Migration may be needed")
                all_passed = False
                
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        all_passed = False
    
    # 2. Check Gemini API
    print("\n🤖 GEMINI AI:")
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            print("  ❌ GOOGLE_API_KEY not found in .env")
            all_passed = False
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content('Reply with: OK')
            if response.text:
                print(f"  ✅ Gemini API connected (Model: gemini-2.5-flash)")
            else:
                print("  ⚠️  Gemini responded but with empty content")
                
    except Exception as e:
        print(f"  ❌ Gemini API error: {e}")
        all_passed = False
    
    # 3. Check HuggingFace Embeddings
    print("\n🤗 HUGGINGFACE EMBEDDINGS:")
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_embedding = model.encode("test", convert_to_numpy=True)
        
        if len(test_embedding) == 384:
            print(f"  ✅ Embedding model loaded (Dimension: 384)")
        else:
            print(f"  ⚠️  Unexpected embedding dimension: {len(test_embedding)}")
            
    except Exception as e:
        print(f"  ❌ Embedding error: {e}")
        all_passed = False
    
    # 4. Check ChromaDB
    print("\n💾 VECTOR DATABASE (ChromaDB):")
    try:
        import chromadb
        from chromadb.config import Settings
        
        db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        os.makedirs(db_path, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        print(f"  ✅ ChromaDB initialized ({len(collections)} collections)")
        
    except Exception as e:
        print(f"  ❌ ChromaDB error: {e}")
        all_passed = False
    
    # 5. Check Services
    print("\n⚙️  SERVICES:")
    try:
        from app.services.resume_intelligence_service import ResumeIntelligenceService
        print("  ✅ ResumeIntelligenceService")
    except Exception as e:
        print(f"  ❌ ResumeIntelligenceService: {e}")
        all_passed = False
        
    try:
        from app.services.matching_engine import MatchingEngine
        print("  ✅ MatchingEngine")
    except Exception as e:
        print(f"  ❌ MatchingEngine: {e}")
        all_passed = False
        
    try:
        from app.services.rag_engine import RAGEngine
        print("  ✅ RAGEngine")
    except Exception as e:
        print(f"  ❌ RAGEngine: {e}")
        all_passed = False
    
    # 6. Check API Routes
    print("\n🌐 API ROUTES:")
    try:
        from app.routes.intelligent_filtering import router
        from app.main import app
        
        filter_routes = [r for r in app.routes if hasattr(r, 'path') and '/filter' in r.path]
        print(f"  ✅ Intelligent Filtering routes registered ({len(filter_routes)} endpoints)")
        
        for route in filter_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
            print(f"     • {methods:10} {route.path}")
            
    except Exception as e:
        print(f"  ❌ Routes error: {e}")
        all_passed = False
    
    # Final Status
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("=" * 60)
        print("\n🚀 Ready to process resumes!")
        print("📝 Next step: Run ./scripts/test_intelligent_filtering.sh")
        return 0
    else:
        print("⚠️  SOME ISSUES DETECTED")
        print("=" * 60)
        print("\n🔧 Please fix the issues above before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(check_status())
