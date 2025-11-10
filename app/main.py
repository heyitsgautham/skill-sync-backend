"""
SkillSync Backend - Main Application Entry Point
FastAPI application for intelligent internship matching platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, health, resume, internship, recommendations, intelligent_filtering, students, admin, notifications, profile, resume_view, candidate_emails
import os

# Initialize FastAPI app
app = FastAPI(
    title="SkillSync API",
    description="Intelligent internship matching platform with AI-powered recommendations",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Try to initialize database tables (optional for initial setup)
try:
    from app.database.connection import engine, Base
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
except Exception as e:
    print(f"⚠ Warning: Could not connect to database: {str(e)}")
    print("  API will start but database-dependent endpoints will fail")
    print("  Please ensure PostgreSQL is running and DATABASE_URL is configured correctly")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(resume.router, prefix="/api", tags=["Resume"])
app.include_router(resume_view.router, prefix="/api", tags=["Resume Viewing"])  # Anonymization support
app.include_router(internship.router, prefix="/api", tags=["Internship"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(intelligent_filtering.router, tags=["Intelligent Filtering"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])
app.include_router(candidate_emails.router, prefix="/api", tags=["Candidate Emails"])
app.include_router(profile.router, prefix="/api", tags=["Profile"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SkillSync API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
