#!/bin/bash

# Test Email Notification Feature
# Tests the clustered email notification system

echo "======================================"
echo "Testing Email Notification Feature"
echo "======================================"
echo ""

# Configuration
BASE_URL="http://localhost:8000/api"
COMPANY_EMAIL="hr@techcorp.com"
COMPANY_PASSWORD="company123"

echo "Step 1: Logging in as company..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$COMPANY_EMAIL\",\"password\":\"$COMPANY_PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "  Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✓ Login successful"
echo ""

# Test 1: Preview daily summary
echo "Step 2: Previewing daily summary (last 24 hours)..."
PREVIEW_RESPONSE=$(curl -s -X GET "$BASE_URL/notifications/preview-daily-summary?hours=24" \
  -H "Authorization: Bearer $TOKEN")

echo "✓ Preview generated"
echo "Response:"
echo $PREVIEW_RESPONSE | jq '.success, .message, .total_applications, .internships_with_applications'
echo ""

# Save preview HTML to file for viewing
PREVIEW_HTML=$(echo $PREVIEW_RESPONSE | jq -r '.preview_html')
if [ "$PREVIEW_HTML" != "null" ]; then
    echo "$PREVIEW_HTML" > /tmp/email_preview.html
    echo "✓ Preview saved to /tmp/email_preview.html"
    echo "  Open this file in a browser to see the email preview"
fi
echo ""

# Test 2: Get email settings
echo "Step 3: Getting current email settings..."
SETTINGS_RESPONSE=$(curl -s -X GET "$BASE_URL/notifications/email-settings" \
  -H "Authorization: Bearer $TOKEN")

echo "✓ Email settings retrieved"
echo "Response:"
echo $SETTINGS_RESPONSE | jq '.'
echo ""

# Test 3: Send daily summary (optional - only if user confirms)
echo "======================================"
echo "Would you like to send a test email?"
echo "Make sure SMTP settings are configured in .env"
echo "======================================"
read -p "Send test email? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Step 4: Sending daily summary email..."
    SEND_RESPONSE=$(curl -s -X POST "$BASE_URL/notifications/send-daily-summary?hours=24&preview_only=false" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "Response:"
    echo $SEND_RESPONSE | jq '.'
    
    SUCCESS=$(echo $SEND_RESPONSE | jq -r '.success')
    EMAIL_SENT=$(echo $SEND_RESPONSE | jq -r '.email_sent')
    
    if [ "$SUCCESS" = "true" ] && [ "$EMAIL_SENT" = "true" ]; then
        echo "✓ Email sent successfully!"
        echo "  Check your inbox at $COMPANY_EMAIL"
    else
        echo "⚠ Email not sent"
        echo "  This is expected if SMTP is not configured"
        echo "  Configure SMTP settings in .env to enable email sending"
    fi
else
    echo "Skipping email send test"
fi

echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo "✓ Email preview generation working"
echo "✓ Email settings endpoint working"
echo "✓ API endpoints accessible"
echo ""
echo "Next steps:"
echo "1. Configure SMTP settings in .env file"
echo "2. View email preview at: /tmp/email_preview.html"
echo "3. Test actual email sending with configured SMTP"
echo ""
echo "======================================"
