"""
Health Check Routes
System health and status endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.connection import get_db
from datetime import datetime

router = APIRouter()

@router.get("/healthcheck")
async def healthcheck(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database connectivity
    
    Returns system status, timestamp, and database connectivity
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "SkillSync API",
        "version": "1.0.0",
        "database": db_status
    }
