# Day 1 Implementation - Setup Guide

## Overview
This guide covers the Day 1 implementation which includes:
- ✅ Database models (User, Internship, Resume, Application)
- ✅ API routes (/resume/upload, /internship/post, /internship/list, /recommendations)
- ✅ Parser service (PyMuPDF, python-docx for PDF/DOCX parsing)
- ✅ Vector DB setup (ChromaDB with HuggingFace embeddings)
- ✅ RAG engine for AI-powered matching
- ✅ Google Gemini API integration for LLM capabilities

## Prerequisites

1. **Python 3.9+** installed
2. **PostgreSQL** database running
3. **Google API Key** (for Gemini API)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- FastAPI & Uvicorn (web framework)
- SQLAlchemy & psycopg2 (database)
- PyMuPDF, python-docx, pdfplumber (document parsing)
- ChromaDB & sentence-transformers (vector database & embeddings)
- google-generativeai (Google Gemini API)

### 2. Configure Environment

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL`: Your PostgreSQL connection string
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `GOOGLE_API_KEY`: Get from https://makersuite.google.com/app/apikey

### 3. Create Database Tables

Run the migration script to create all tables:

```bash
python scripts/migrate_db.py create
```

This creates:
- `users` - Student, Company, Admin accounts
- `internships` - Internship postings by companies
- `resumes` - Student resume files and metadata
- `applications` - Student applications to internships

### 4. Test the Components

#### Test Parser Service

```bash
python scripts/test_parser.py
```

This tests:
- Skill extraction from text
- PDF/DOCX parsing (if sample files exist)

#### Test RAG Engine

```bash
python scripts/test_rag.py
```

This tests:
- Resume embedding generation and storage
- Internship embedding generation and storage
- Semantic similarity matching (resume to internship)
- Candidate recommendation (internship to resumes)

### 5. Run the Application

Start the FastAPI server:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Or use the main.py directly:

```bash
python app/main.py
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Resume Management
- `POST /api/resume/upload` - Upload resume (Student only)
- `GET /api/resume/my-resumes` - Get all resumes for current student
- `DELETE /api/resume/{resume_id}` - Delete resume

### Internship Management
- `POST /api/internship/post` - Post internship (Company only)
- `GET /api/internship/list` - List all active internships
- `GET /api/internship/my-posts` - Get company's posted internships
- `GET /api/internship/{internship_id}` - Get internship details
- `PUT /api/internship/{internship_id}` - Update internship
- `DELETE /api/internship/{internship_id}` - Delete internship

### AI Recommendations
- `GET /api/recommendations/for-me` - Get AI-matched internships for student
- `GET /api/recommendations/candidates/{internship_id}` - Get AI-matched candidates for internship

## Testing the Flow

### 1. Register Users

```bash
# Register a student
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123",
    "full_name": "John Doe",
    "role": "student"
  }'

# Register a company
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "company@example.com",
    "password": "password123",
    "full_name": "Tech Corp",
    "role": "company"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123"
  }'
```

Save the `access_token` from the response.

### 3. Upload Resume (Student)

```bash
curl -X POST http://localhost:8000/api/resume/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@/path/to/your/resume.pdf"
```

### 4. Post Internship (Company)

```bash
curl -X POST http://localhost:8000/api/internship/post \
  -H "Authorization: Bearer YOUR_COMPANY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Backend Developer Intern",
    "description": "Looking for Python developer with Django experience",
    "required_skills": ["python", "django", "rest api", "postgresql"],
    "location": "San Francisco, CA",
    "duration": "3 months",
    "stipend": "$2000/month"
  }'
```

### 5. Get AI Recommendations (Student)

```bash
curl -X GET http://localhost:8000/api/recommendations/for-me?top_k=10 \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN"
```

## RAG Engine Details

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` from sentence-transformers
- **Dimension**: 384-dimensional vectors
- **Performance**: Fast inference, good quality for semantic search

### Vector Database
- **Database**: ChromaDB (persistent storage)
- **Location**: `./data/chroma_db/`
- **Collections**:
  - `resumes` - Student resume embeddings
  - `internships` - Internship posting embeddings

### Matching Algorithm
1. Generate embedding for resume/internship using HuggingFace model
2. Store in ChromaDB with metadata
3. Query using cosine similarity for semantic matching
4. Return top-k matches with similarity scores (0-100)

### LLM Integration
- **Model**: Google Gemini Pro
- **Purpose**: Future enhancements for natural language generation
- **Current**: Set up for advanced matching explanations

## Project Structure

```
app/
├── models/              # Database models
│   ├── user.py         # User, UserRole
│   ├── internship.py   # Internship postings
│   ├── resume.py       # Resume files and metadata
│   └── application.py  # Student applications
├── routes/             # API endpoints
│   ├── auth.py        # Authentication
│   ├── resume.py      # Resume management
│   ├── internship.py  # Internship CRUD
│   └── recommendations.py  # AI matching
├── services/           # Business logic
│   ├── auth_service.py    # Auth helpers
│   ├── parser_service.py  # Document parsing
│   └── rag_engine.py      # RAG & embeddings
├── database/           # Database connection
└── utils/              # Helper functions

scripts/
├── migrate_db.py      # Database setup
├── test_parser.py     # Test parsing
└── test_rag.py        # Test RAG engine

data/
└── chroma_db/         # Vector database storage
```

## Deliverables ✅

✅ **Working RAG engine** integrated with resume and internship embeddings
✅ **All core models** functional and persisted in PostgreSQL
✅ **Parser service** extracts text and skills from PDF/DOCX files
✅ **Vector database** stores embeddings for semantic search
✅ **API routes** for all core operations
✅ **AI-powered matching** using cosine similarity

## Next Steps

- Add more sophisticated skill extraction (NER models)
- Implement application workflow
- Add admin dashboard endpoints
- Enhance matching with weighted scoring
- Add analytics and reporting
- Implement real-time notifications
