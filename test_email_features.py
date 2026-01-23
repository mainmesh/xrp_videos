"""
Test script for email functionality
Run this with: python manage.py shell < test_email_features.py
"""

from django.core.mail import send_mail
from django.conf import settings

print("\n" + "="*60)
print("Testing Email Configuration")
print("="*60)

# Test 1: Check email settings
print("\n1. Current Email Settings:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test 2: Send a test email
print("\n2. Sending Test Email...")
try:
    send_mail(
        subject='XRPPrime - Test Email',
        message='This is a test email from your XRPPrime application. If you see this, email is configured correctly!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['test@example.com'],
        fail_silently=False,
    )
    print("   ✅ Test email sent successfully!")
    print("   Check your console output above for the email content.")
except Exception as e:
    print(f"   ❌ Error sending email: {str(e)}")

# Test 3: Check if signals are loaded
print("\n3. Checking if welcome email signal is registered...")
from django.db.models.signals import post_save
from django.contrib.auth.models import User

receivers = post_save.receivers
user_receivers = [r for r in receivers if r[0][1] == User]
if user_receivers:
    print(f"   ✅ Found {len(user_receivers)} signal(s) for User model")
    print("   Welcome email should be sent on user registration")
else:
    print("   ⚠️  No signals found for User model")

print("\n" + "="*60)
print("Email Configuration Test Complete")
print("="*60)
print("\nNext Steps:")
print("1. To test in development: Emails will appear in console")
print("2. To test in production: Configure SMTP in .env file")
print("3. Register a new user to test welcome email")
print("4. Try password reset from login page")
print("\nSee EMAIL_SETUP.md for detailed configuration instructions")
print("="*60 + "\n")
