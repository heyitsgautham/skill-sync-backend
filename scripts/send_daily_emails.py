"""
Daily Email Scheduler - Schedule daily summary emails for all companies
This script should be run as a cron job or scheduled task at midnight daily
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.connection import get_db
from app.models import User, Internship, Application, Resume, UserRole
from app.services.email_service import email_service


def send_daily_summaries_to_all_companies():
    """
    Send daily summary emails to all companies with active internships
    This function should be called once per day at midnight
    """
    print(f"\n{'='*60}")
    print(f"Starting Daily Email Summary Job")
    print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all companies with active internships
        companies = db.query(User).filter(
            User.role == UserRole.company,
            User.is_active == 1
        ).all()
        
        print(f"Found {len(companies)} active companies")
        
        if not companies:
            print("No companies found. Exiting.")
            return
        
        # Get cutoff time (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        print(f"Looking for applications since: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        
        emails_sent = 0
        emails_failed = 0
        companies_skipped = 0
        
        for company in companies:
            print(f"\nProcessing company: {company.full_name} ({company.email})")
            
            # Get all active internships for this company
            internships = db.query(Internship).filter(
                Internship.company_id == company.id,
                Internship.is_active == 1
            ).all()
            
            if not internships:
                print(f"  ⊘ No active internships. Skipping.")
                companies_skipped += 1
                continue
            
            print(f"  Found {len(internships)} active internship(s)")
            
            # Get all recent applications for these internships
            internship_ids = [i.id for i in internships]
            
            recent_applications = db.query(Application).filter(
                and_(
                    Application.internship_id.in_(internship_ids),
                    Application.created_at >= cutoff_time
                )
            ).order_by(Application.created_at.desc()).all()
            
            if not recent_applications:
                print(f"  ⊘ No new applications in the last 24 hours. Skipping.")
                companies_skipped += 1
                continue
            
            print(f"  Found {len(recent_applications)} new application(s)")
            
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
                    phone = None  # Placeholder for future implementation
                    
                    # Extract top skills from student profile
                    top_skills = student.skills[:5] if student.skills else []
                    
                    # Generate key strengths summary
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
            
            if not internship_summaries:
                print(f"  ⊘ No valid application data. Skipping.")
                companies_skipped += 1
                continue
            
            # Generate email content
            date = datetime.utcnow()
            html_content = email_service.generate_daily_summary_html(
                company_name=company.full_name,
                internship_summaries=internship_summaries,
                date=date
            )
            
            text_content = email_service.generate_daily_summary_text(
                company_name=company.full_name,
                internship_summaries=internship_summaries,
                date=date
            )
            
            # Send email
            print(f"  Sending email with {total_applications} application(s)...")
            email_sent = email_service.send_email(
                to_email=company.email,
                subject=f"SkillSync Daily Summary - {total_applications} New Application(s) - {date.strftime('%b %d, %Y')}",
                html_content=html_content,
                text_content=text_content
            )
            
            if email_sent:
                print(f"  ✓ Email sent successfully to {company.email}")
                emails_sent += 1
            else:
                print(f"  ✗ Failed to send email to {company.email}")
                emails_failed += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Daily Email Summary Job Complete")
        print(f"{'='*60}")
        print(f"Total companies processed: {len(companies)}")
        print(f"Emails sent successfully: {emails_sent}")
        print(f"Emails failed: {emails_failed}")
        print(f"Companies skipped (no applications): {companies_skipped}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ Error in daily email job: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    send_daily_summaries_to_all_companies()
