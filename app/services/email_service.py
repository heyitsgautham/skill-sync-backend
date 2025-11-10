"""
Email Service - Handle email notifications for SkillSync
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    """
    Email service for sending notifications using SMTP
    Supports both Gmail SMTP and other SMTP providers
    """
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_username)
        self.sender_name = os.getenv("SENDER_NAME", "SkillSync")
        
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None
    ) -> bool:
        """
        Send an email using SMTP with optional attachments
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text fallback content
            attachments: List of tuples (filename, file_content, mime_type)
                        Example: [("report.csv", csv_bytes, "text/csv")]
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message - use "mixed" if attachments, "alternative" otherwise
            if attachments:
                message = MIMEMultipart("mixed")
            else:
                message = MIMEMultipart("alternative")
                
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            # Create alternative part for text and HTML
            if attachments:
                alternative_part = MIMEMultipart("alternative")
                if text_content:
                    text_part = MIMEText(text_content, "plain")
                    alternative_part.attach(text_part)
                html_part = MIMEText(html_content, "html")
                alternative_part.attach(html_part)
                message.attach(alternative_part)
            else:
                # Add text and HTML parts directly
                if text_content:
                    text_part = MIMEText(text_content, "plain")
                    message.attach(text_part)
                html_part = MIMEText(html_content, "html")
                message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for filename, file_content, mime_type in attachments:
                    # Create attachment part
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file_content)
                    
                    # Encode to base64
                    encoders.encode_base64(part)
                    
                    # Add header with filename
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}"
                    )
                    
                    message.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            return True
        except Exception as e:
            print(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def generate_daily_summary_html(
        self,
        company_name: str,
        internship_summaries: List[Dict],
        date: datetime
    ) -> str:
        """
        Generate HTML content for daily applicant summary email
        
        Args:
            company_name: Name of the company
            internship_summaries: List of internship summaries with applicants
            date: Date for the summary
            
        Returns:
            HTML string for the email
        """
        total_applications = sum(len(summary['applicants']) for summary in internship_summaries)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    border-bottom: 3px solid #1976d2;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #1976d2;
                    margin: 0 0 10px 0;
                    font-size: 28px;
                }}
                .header .date {{
                    color: #666;
                    font-size: 16px;
                }}
                .summary-box {{
                    background-color: #e3f2fd;
                    border-left: 4px solid #1976d2;
                    padding: 15px;
                    margin-bottom: 30px;
                    border-radius: 4px;
                }}
                .summary-box h2 {{
                    margin: 0 0 10px 0;
                    color: #1976d2;
                    font-size: 20px;
                }}
                .summary-box p {{
                    margin: 5px 0;
                    font-size: 16px;
                }}
                .internship-section {{
                    margin-bottom: 30px;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 20px;
                    background-color: #fafafa;
                }}
                .internship-section h3 {{
                    color: #424242;
                    margin: 0 0 15px 0;
                    font-size: 22px;
                }}
                .internship-meta {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 15px;
                }}
                .applicant-card {{
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 15px;
                    margin-bottom: 12px;
                }}
                .applicant-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }}
                .applicant-name {{
                    font-weight: 600;
                    font-size: 18px;
                    color: #212121;
                }}
                .match-score {{
                    background-color: #4caf50;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                .match-score.medium {{
                    background-color: #ff9800;
                }}
                .match-score.low {{
                    background-color: #f44336;
                }}
                .applicant-details {{
                    color: #666;
                    font-size: 14px;
                    line-height: 1.8;
                }}
                .applicant-details strong {{
                    color: #424242;
                }}
                .skills {{
                    margin-top: 10px;
                }}
                .skill-tag {{
                    display: inline-block;
                    background-color: #e8eaf6;
                    color: #3f51b5;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                    margin-right: 6px;
                    margin-top: 6px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }}
                .footer a {{
                    color: #1976d2;
                    text-decoration: none;
                }}
                .cta-button {{
                    display: inline-block;
                    background-color: #1976d2;
                    color: white !important;
                    padding: 12px 24px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 15px;
                }}
                .no-applicants {{
                    color: #999;
                    font-style: italic;
                    text-align: center;
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Applicant Summary</h1>
                    <div class="date">{date.strftime("%A, %B %d, %Y")}</div>
                </div>
                
                <div class="summary-box">
                    <h2>Hello, {company_name}!</h2>
                    <p>Here's your daily summary of new internship applications.</p>
                    <p><strong>{total_applications}</strong> new application(s) across <strong>{len(internship_summaries)}</strong> internship posting(s)</p>
                </div>
        """
        
        if total_applications == 0:
            html += """
                <div class="no-applicants">
                    <p>No new applications received in the last 24 hours.</p>
                </div>
            """
        else:
            for summary in internship_summaries:
                internship_title = summary['internship_title']
                applicants = summary['applicants']
                
                html += f"""
                <div class="internship-section">
                    <h3>{internship_title}</h3>
                    <div class="internship-meta">
                        {len(applicants)} new application(s)
                    </div>
                """
                
                for applicant in applicants:
                    match_score = applicant.get('match_score', 0)
                    match_class = 'low' if match_score < 60 else ('medium' if match_score < 80 else '')
                    
                    skills_html = ""
                    if applicant.get('top_skills'):
                        skills_html = '<div class="skills">'
                        for skill in applicant['top_skills'][:5]:  # Show top 5 skills
                            skills_html += f'<span class="skill-tag">{skill}</span>'
                        skills_html += '</div>'
                    
                    html += f"""
                    <div class="applicant-card">
                        <div class="applicant-header">
                            <div class="applicant-name">{applicant['name']}</div>
                            <div class="match-score {match_class}">{match_score}% Match</div>
                        </div>
                        <div class="applicant-details">
                            <div><strong>Email:</strong> {applicant['email']}</div>
                    """
                    
                    if applicant.get('phone'):
                        html += f"""<div><strong>Phone:</strong> {applicant['phone']}</div>"""
                    
                    if applicant.get('experience_years') is not None:
                        html += f"""<div><strong>Experience:</strong> {applicant['experience_years']} years</div>"""
                    
                    html += f"""
                            <div><strong>Applied:</strong> {applicant['applied_at']}</div>
                    """
                    
                    if applicant.get('key_strengths'):
                        html += f"""<div><strong>Key Strengths:</strong> {applicant['key_strengths']}</div>"""
                    
                    html += skills_html
                    html += """
                        </div>
                    </div>
                    """
                
                html += """
                </div>
                """
        
        html += f"""
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/company/dashboard" class="cta-button">
                        View All Applications in Dashboard
                    </a>
                </div>
                
                <div class="footer">
                    <p>This is an automated daily summary from SkillSync.</p>
                    <p>You're receiving this because you have active internship postings.</p>
                    <p><a href="#">Manage Email Preferences</a> | <a href="#">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_daily_summary_text(
        self,
        company_name: str,
        internship_summaries: List[Dict],
        date: datetime
    ) -> str:
        """
        Generate plain text content for daily applicant summary email
        
        Args:
            company_name: Name of the company
            internship_summaries: List of internship summaries with applicants
            date: Date for the summary
            
        Returns:
            Plain text string for the email
        """
        total_applications = sum(len(summary['applicants']) for summary in internship_summaries)
        
        text = f"""
SKILLSYNC - DAILY APPLICANT SUMMARY
{date.strftime("%A, %B %d, %Y")}
{'=' * 60}

Hello, {company_name}!

Here's your daily summary of new internship applications.

{total_applications} new application(s) across {len(internship_summaries)} internship posting(s)

"""
        
        if total_applications == 0:
            text += "No new applications received in the last 24 hours.\n"
        else:
            for summary in internship_summaries:
                internship_title = summary['internship_title']
                applicants = summary['applicants']
                
                text += f"\n{'-' * 60}\n"
                text += f"INTERNSHIP: {internship_title}\n"
                text += f"{len(applicants)} new application(s)\n"
                text += f"{'-' * 60}\n\n"
                
                for i, applicant in enumerate(applicants, 1):
                    text += f"{i}. {applicant['name']} - {applicant.get('match_score', 0)}% Match\n"
                    text += f"   Email: {applicant['email']}\n"
                    
                    if applicant.get('phone'):
                        text += f"   Phone: {applicant['phone']}\n"
                    
                    if applicant.get('experience_years') is not None:
                        text += f"   Experience: {applicant['experience_years']} years\n"
                    
                    text += f"   Applied: {applicant['applied_at']}\n"
                    
                    if applicant.get('top_skills'):
                        text += f"   Top Skills: {', '.join(applicant['top_skills'][:5])}\n"
                    
                    if applicant.get('key_strengths'):
                        text += f"   Key Strengths: {applicant['key_strengths']}\n"
                    
                    text += "\n"
        
        text += f"""
{'=' * 60}

View all applications in your dashboard:
{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/company/dashboard

This is an automated daily summary from SkillSync.
You're receiving this because you have active internship postings.

Manage Email Preferences | Unsubscribe
"""
        
        return text


# Global email service instance
email_service = EmailService()
