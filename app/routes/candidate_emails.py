"""
Candidate Email Routes - Send emails to selected candidates
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from app.database.connection import get_db
from app.models import User, Internship, UserRole
from app.services.email_service import email_service
from app.utils.security import get_current_user

router = APIRouter(prefix="/candidate-emails", tags=["Candidate Emails"])


class CandidateEmailRequest(BaseModel):
    """Request model for sending emails to candidates"""
    internship_id: int
    candidate_ids: List[int]
    subject: str
    message: str


class CandidateEmailResponse(BaseModel):
    """Response model for candidate email sending"""
    success: bool
    message: str
    emails_sent: int
    failed_emails: int
    details: List[dict]


@router.post("/send-to-candidates", response_model=CandidateEmailResponse)
def send_email_to_candidates(
    request: CandidateEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send personalized emails to selected candidates
    
    - **internship_id**: ID of the internship the candidates are for
    - **candidate_ids**: List of student IDs to send emails to
    - **subject**: Email subject line
    - **message**: Email body message
    
    Only companies can use this endpoint.
    """
    # Verify user is a company
    if current_user.role != UserRole.company:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only companies can send emails to candidates"
        )
    
    # Verify internship belongs to this company
    internship = db.query(Internship).filter(
        Internship.id == request.internship_id,
        Internship.company_id == current_user.id
    ).first()
    
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship not found or doesn't belong to your company"
        )
    
    # Get all candidate details
    candidates = db.query(User).filter(
        User.id.in_(request.candidate_ids),
        User.role == UserRole.student
    ).all()
    
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid candidates found"
        )
    
    # Track email sending results
    emails_sent = 0
    failed_emails = 0
    details = []
    
    # Send email to each candidate
    for candidate in candidates:
        try:
            # Generate personalized HTML email
            html_content = generate_candidate_selection_email_html(
                candidate_name=candidate.full_name,
                company_name=current_user.full_name,
                internship_title=internship.title,
                message=request.message
            )
            
            # Generate plain text version
            text_content = generate_candidate_selection_email_text(
                candidate_name=candidate.full_name,
                company_name=current_user.full_name,
                internship_title=internship.title,
                message=request.message
            )
            
            # Send email
            email_sent = email_service.send_email(
                to_email=candidate.email,
                subject=request.subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if email_sent:
                emails_sent += 1
                details.append({
                    "candidate_id": candidate.id,
                    "candidate_name": candidate.full_name,
                    "email": candidate.email,
                    "status": "sent",
                    "error": None
                })
            else:
                failed_emails += 1
                details.append({
                    "candidate_id": candidate.id,
                    "candidate_name": candidate.full_name,
                    "email": candidate.email,
                    "status": "failed",
                    "error": "Email delivery failed"
                })
        except Exception as e:
            failed_emails += 1
            details.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.full_name,
                "email": candidate.email,
                "status": "error",
                "error": str(e)
            })
    
    return CandidateEmailResponse(
        success=emails_sent > 0,
        message=f"Successfully sent {emails_sent} email(s) to candidates. {failed_emails} failed.",
        emails_sent=emails_sent,
        failed_emails=failed_emails,
        details=details
    )


def generate_candidate_selection_email_html(
    candidate_name: str,
    company_name: str,
    internship_title: str,
    message: str
) -> str:
    """Generate HTML email for candidate selection notification"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.8;
                color: #2c3e50;
                max-width: 650px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f6f9;
                font-size: 16px;
            }}
            .container {{
                background-color: white;
                border-radius: 10px;
                padding: 40px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.08);
            }}
            .header {{
                background: #1a73e8;
                color: white;
                padding: 35px;
                border-radius: 10px 10px 0 0;
                margin: -40px -40px 35px -40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
                font-weight: 600;
                letter-spacing: -0.5px;
            }}
            .header p {{
                margin: 12px 0 0 0;
                opacity: 0.95;
                font-size: 18px;
                font-weight: 400;
            }}
            .greeting {{
                font-size: 19px;
                color: #2c3e50;
                margin-bottom: 25px;
                font-weight: 500;
            }}
            .body-text {{
                font-size: 17px;
                line-height: 1.9;
                color: #34495e;
                margin-bottom: 25px;
            }}
            .message-box {{
                background-color: #f8f9fa;
                border-left: 4px solid #1a73e8;
                padding: 25px;
                margin: 30px 0;
                border-radius: 6px;
            }}
            .message-content {{
                color: #2c3e50;
                white-space: pre-line;
                line-height: 2;
                font-size: 17px;
            }}
            .internship-info {{
                background-color: #e8f4fd;
                padding: 20px 25px;
                border-radius: 8px;
                margin: 25px 0;
                border: 1px solid #bee5f8;
            }}
            .internship-info h3 {{
                margin: 0 0 8px 0;
                color: #1a73e8;
                font-size: 20px;
                font-weight: 600;
            }}
            .internship-info p {{
                margin: 0;
                color: #5a6c7d;
                font-size: 16px;
            }}
            .cta-button {{
                display: inline-block;
                background: #1a73e8;
                color: white !important;
                padding: 16px 32px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                margin-top: 25px;
                text-align: center;
                font-size: 16px;
                transition: background 0.3s;
            }}
            .cta-button:hover {{
                background: #1557b0;
            }}
            .footer {{
                margin-top: 45px;
                padding-top: 25px;
                border-top: 2px solid #e8eef3;
                text-align: center;
                color: #7f8c8d;
                font-size: 15px;
            }}
            .footer p {{
                margin: 8px 0;
            }}
            .footer strong {{
                color: #34495e;
            }}
            .disclaimer {{
                margin-top: 25px;
                font-size: 13px;
                color: #95a5a6;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Congratulations!</h1>
                <p>You've been selected for the next round</p>
            </div>
            
            <div class="greeting">
                Dear {candidate_name},
            </div>
            
            <p class="body-text">
                We are pleased to inform you that you have been selected to proceed to the next round 
                of the recruitment process for the following position:
            </p>
            
            <div class="internship-info">
                <h3>{internship_title}</h3>
                <p>at {company_name}</p>
            </div>
            
            <div class="message-box">
                <div class="message-content">{message}</div>
            </div>
            
            <p class="body-text">
                Please log in to your SkillSync dashboard to view more details and next steps.
            </p>
            
            <div style="text-align: center;">
                <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/student/dashboard" class="cta-button">
                    View Dashboard
                </a>
            </div>
            
            <div class="footer">
                <p><strong>Best regards,</strong></p>
                <p style="font-size: 16px; color: #34495e; margin-top: 5px;">{company_name}</p>
                <p class="disclaimer">
                    This email was sent via SkillSync. Please do not reply to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_candidate_selection_email_text(
    candidate_name: str,
    company_name: str,
    internship_title: str,
    message: str
) -> str:
    """Generate plain text email for candidate selection notification"""
    
    text = f"""
CONGRATULATIONS - SELECTED FOR NEXT ROUND
{'=' * 60}

Dear {candidate_name},

We are pleased to inform you that you have been selected to proceed to the next round 
of the recruitment process for the following position:

INTERNSHIP: {internship_title}
COMPANY: {company_name}

MESSAGE FROM COMPANY:
{'-' * 60}
{message}
{'-' * 60}

Please log in to your SkillSync dashboard to view more details and next steps.

Dashboard: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/student/dashboard

Best regards,
{company_name}

{'=' * 60}
This email was sent via SkillSync. Please do not reply to this email.
"""
    
    return text
