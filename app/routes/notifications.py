"""
Email Notification Routes - Handle email notification endpoints
"""

from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models import User, Internship, Application, Resume, UserRole
from app.services.email_service import email_service
from app.utils.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class DailySummaryResponse(BaseModel):
    """Response model for daily summary generation"""
    success: bool
    message: str
    total_applications: int
    internships_with_applications: int
    email_sent: bool
    preview_html: Optional[str] = None


class EmailPreviewRequest(BaseModel):
    """Request model for email preview"""
    hours: int = 24  # Number of hours to look back for applications


@router.post("/send-daily-summary", response_model=DailySummaryResponse)
def send_daily_summary(
    hours: int = 24,
    preview_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send daily summary of new applicants to company email (Manual trigger for demo)
    
    - **hours**: Number of hours to look back for applications (default: 24)
    - **preview_only**: If True, generates preview without sending email (default: False)
    
    This endpoint allows companies to manually trigger a daily summary email.
    In production, this would be scheduled to run automatically at midnight.
    
    Only companies can use this endpoint.
    """
    # Verify user is a company
    if current_user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can access daily summary reports"
        )
    
    # Get cutoff time (last N hours)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all internships posted by this company
    internships = db.query(Internship).filter(
        Internship.company_id == current_user.id,
        Internship.is_active == 1
    ).all()
    
    if not internships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active internship postings found"
        )
    
    # Get all applications for these internships within the time window
    internship_ids = [i.id for i in internships]
    
    recent_applications = db.query(Application).filter(
        and_(
            Application.internship_id.in_(internship_ids),
            Application.created_at >= cutoff_time
        )
    ).order_by(Application.created_at.desc()).all()
    
    # Group applications by internship
    internship_summaries = []
    total_applications = 0
    
    for internship in internships:
        # Get applications for this internship
        internship_apps = [
            app for app in recent_applications 
            if app.internship_id == internship.id
        ]
        
        if not internship_apps:
            continue
        
        applicants = []
        for app in internship_apps:
            # Get student details
            student = db.query(User).filter(User.id == app.student_id).first()
            
            # Get resume details
            resume = db.query(Resume).filter(Resume.id == app.resume_id).first()
            
            if not student:
                continue
            
            # Extract phone from student profile if available
            # (Would need to add phone field to User model in future)
            phone = None  # Placeholder for future implementation
            
            # Extract top skills from student profile
            top_skills = student.skills[:5] if student.skills else []
            
            # Generate key strengths summary (simplified version)
            key_strengths = ""
            if student.skills:
                key_strengths = f"Proficient in {', '.join(student.skills[:3])}"
            if student.total_experience_years:
                if key_strengths:
                    key_strengths += f", {student.total_experience_years} years experience"
                else:
                    key_strengths = f"{student.total_experience_years} years of experience"
            
            applicants.append({
                'name': student.full_name,
                'email': student.email,
                'phone': phone,
                'match_score': app.match_score or app.application_similarity_score or 0,
                'top_skills': top_skills,
                'experience_years': student.total_experience_years,
                'applied_at': app.created_at.strftime("%b %d, %Y at %I:%M %p"),
                'key_strengths': key_strengths or "Details available in dashboard"
            })
        
        if applicants:
            internship_summaries.append({
                'internship_title': internship.title,
                'applicants': applicants
            })
            total_applications += len(applicants)
    
    # Generate email content
    date = datetime.utcnow()
    html_content = email_service.generate_daily_summary_html(
        company_name=current_user.full_name,
        internship_summaries=internship_summaries,
        date=date
    )
    
    text_content = email_service.generate_daily_summary_text(
        company_name=current_user.full_name,
        internship_summaries=internship_summaries,
        date=date
    )
    
    # If preview only, return HTML without sending
    if preview_only:
        return DailySummaryResponse(
            success=True,
            message="Email preview generated successfully",
            total_applications=total_applications,
            internships_with_applications=len(internship_summaries),
            email_sent=False,
            preview_html=html_content
        )
    
    # Send email
    email_sent = email_service.send_email(
        to_email=current_user.email,
        subject=f"SkillSync Daily Summary - {total_applications} New Application(s) - {date.strftime('%b %d, %Y')}",
        html_content=html_content,
        text_content=text_content
    )
    
    if not email_sent:
        return DailySummaryResponse(
            success=False,
            message="Failed to send email. Please check email configuration.",
            total_applications=total_applications,
            internships_with_applications=len(internship_summaries),
            email_sent=False
        )
    
    return DailySummaryResponse(
        success=True,
        message=f"Daily summary email sent successfully to {current_user.email}",
        total_applications=total_applications,
        internships_with_applications=len(internship_summaries),
        email_sent=True
    )


@router.get("/preview-daily-summary")
def preview_daily_summary(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview daily summary email without sending
    
    - **hours**: Number of hours to look back for applications (default: 24)
    
    Returns HTML preview of the daily summary email.
    Only companies can use this endpoint.
    """
    result = send_daily_summary(
        hours=hours,
        preview_only=True,
        db=db,
        current_user=current_user
    )
    
    return {
        "success": result.success,
        "message": result.message,
        "total_applications": result.total_applications,
        "internships_with_applications": result.internships_with_applications,
        "preview_html": result.preview_html
    }


@router.get("/email-settings")
def get_email_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Get current email notification settings for the user
    
    Returns:
    - Email preferences (enabled/disabled)
    - Last email sent timestamp
    - Email delivery status
    
    Only authenticated users can access this endpoint.
    """
    # Placeholder for future email preferences implementation
    # Would store preferences in database
    
    return {
        "email": current_user.email,
        "daily_summary_enabled": True,  # Default enabled for companies
        "email_verified": True,  # Placeholder
        "last_email_sent": None,  # Would track in database
        "preferences": {
            "new_applications": True,
            "daily_summary": True,
            "weekly_report": False
        }
    }


@router.put("/email-settings")
def update_email_settings(
    daily_summary_enabled: bool = True,
    new_applications_enabled: bool = True,
    weekly_report_enabled: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Update email notification preferences
    
    - **daily_summary_enabled**: Enable/disable daily summary emails
    - **new_applications_enabled**: Enable/disable immediate notifications for new applications
    - **weekly_report_enabled**: Enable/disable weekly analytics reports
    
    Only authenticated users can update their email settings.
    """
    # Placeholder for future email preferences implementation
    # Would update preferences in database
    
    return {
        "success": True,
        "message": "Email preferences updated successfully",
        "preferences": {
            "daily_summary": daily_summary_enabled,
            "new_applications": new_applications_enabled,
            "weekly_report": weekly_report_enabled
        }
    }
