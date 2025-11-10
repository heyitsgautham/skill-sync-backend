"""
Simple SMTP Credentials Test
Sends a test email to verify SMTP configuration
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.email_service import email_service

def test_smtp_credentials():
    """Send a test email to verify SMTP credentials"""
    
    print("\n" + "="*60)
    print("SMTP Credentials Test")
    print("="*60 + "\n")
    
    # Check if SMTP is configured
    print(f"SMTP Host: {email_service.smtp_host}")
    print(f"SMTP Port: {email_service.smtp_port}")
    print(f"SMTP Username: {email_service.smtp_username}")
    print(f"Sender Email: {email_service.sender_email}")
    print(f"Sender Name: {email_service.sender_name}")
    print()
    
    if not email_service.smtp_username or not email_service.smtp_password:
        print("  SMTP credentials not configured in .env file")
        print("\nPlease add these to your .env file:")
        print("SMTP_USERNAME=your-email@gmail.com")
        print("SMTP_PASSWORD=your-app-password")
        return False
    
    # Test email content
    recipient = "heyitsgautham@gmail.com"
    subject = "SkillSync SMTP Test - Feature 4"
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background-color: #1976d2;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }
            .content {
                background-color: #f5f5f5;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }
            .success {
                background-color: #4caf50;
                color: white;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                text-align: center;
                font-weight: bold;
            }
            .info {
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border-left: 4px solid #1976d2;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 SMTP Test Successful!</h1>
        </div>
        <div class="content">
            <div class="success">
                ✅ Your SMTP credentials are working correctly!
            </div>
            
            <p>Hello from SkillSync!</p>
            
            <p>This is a test email to verify that your SMTP configuration is working properly.</p>
            
            <div class="info">
                <strong>📧 Email Configuration Details:</strong><br>
                SMTP Host: """ + email_service.smtp_host + """<br>
                SMTP Port: """ + str(email_service.smtp_port) + """<br>
                Sender: """ + email_service.sender_name + """ &lt;""" + email_service.sender_email + """&gt;
            </div>
            
            <p><strong>What this means:</strong></p>
            <ul>
                <li>✅ SMTP server connection successful</li>
                <li>✅ Authentication working</li>
                <li>✅ Email delivery functional</li>
                <li>✅ Feature 4: Clustered Email Notifications is ready!</li>
            </ul>
            
            <p>You can now use the daily summary email feature to send professional notifications to companies.</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            
            <p style="font-size: 12px; color: #666; text-align: center;">
                This is an automated test email from SkillSync<br>
                Feature 4: Clustered Email Notifications Implementation<br>
                Date: November 6, 2025
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = """
    SKILLSYNC - SMTP TEST SUCCESSFUL!
    ==================================
    
    Hello from SkillSync!
    
    This is a test email to verify that your SMTP configuration is working properly.
    
    Email Configuration Details:
    - SMTP Host: {host}
    - SMTP Port: {port}
    - Sender: {name} <{email}>
    
    What this means:
    ✓ SMTP server connection successful
    ✓ Authentication working
    ✓ Email delivery functional
    ✓ Feature 4: Clustered Email Notifications is ready!
    
    You can now use the daily summary email feature to send professional notifications to companies.
    
    ---
    This is an automated test email from SkillSync
    Feature 4: Clustered Email Notifications Implementation
    Date: November 6, 2025
    """.format(
        host=email_service.smtp_host,
        port=email_service.smtp_port,
        name=email_service.sender_name,
        email=email_service.sender_email
    )
    
    print(f"Sending test email to: {recipient}")
    print("Please wait...\n")
    
    try:
        success = email_service.send_email(
            to_email=recipient,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if success:
            print("=" * 60)
            print("✅ SUCCESS! Test email sent successfully!")
            print("=" * 60)
            print(f"\nEmail sent to: {recipient}")
            print(f"Subject: {subject}")
            print("\nPlease check the inbox at heyitsgautham@gmail.com")
            print("(Check spam folder if not in inbox)")
            print("\n🎉 Your SMTP credentials are configured correctly!")
            print("\nYou can now use Feature 4: Clustered Email Notifications")
            print("=" * 60 + "\n")
            return True
        else:
            print("=" * 60)
            print("  FAILED to send email")
            print("=" * 60)
            print("\nPossible issues:")
            print("1. Invalid SMTP credentials")
            print("2. Gmail app password incorrect")
            print("3. Network connectivity issues")
            print("4. SMTP server blocking connection")
            print("\nPlease verify:")
            print("- SMTP_USERNAME is your full Gmail address")
            print("- SMTP_PASSWORD is your 16-character app password")
            print("- Get app password from: https://myaccount.google.com/apppasswords")
            print("=" * 60 + "\n")
            return False
            
    except Exception as e:
        print("=" * 60)
        print("  ERROR sending email")
        print("=" * 60)
        print(f"\nError details: {str(e)}")
        print("\nCommon issues:")
        print("1. SMTP_PASSWORD should be app password, not regular Gmail password")
        print("2. Verify credentials in .env file")
        print("3. Check that 2-factor authentication is enabled on Gmail")
        print("4. Generate new app password at: https://myaccount.google.com/apppasswords")
        print("=" * 60 + "\n")
        return False


if __name__ == "__main__":
    test_smtp_credentials()
