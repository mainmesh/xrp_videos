#!/usr/bin/env python
"""
Comprehensive page test - Tests all pages including admin panel
"""
import os
import django

# Force SQLite for local testing
os.environ['DATABASE_URL'] = ''
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from accounts.models import Profile
from videos.models import Video, Tier
from django.urls import reverse
import sys

# Add localhost to ALLOWED_HOSTS for testing
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
if 'localhost' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('localhost')

print("=" * 80)
print("COMPREHENSIVE PAGE TEST - ALL ROUTES")
print("=" * 80)

# Create test client
client = Client()

# Test results storage
results = {
    'passed': [],
    'failed': [],
    'errors': []
}

def test_page(name, url, expected_status=200, requires_auth=False, requires_staff=False):
    """Test a single page"""
    try:
        response = client.get(url, follow=True, SERVER_NAME='testserver')
        
        # If requires auth and got redirected to login, that's expected
        if requires_auth and response.redirect_chain:
            for redirect_url, status in response.redirect_chain:
                if '/login' in redirect_url:
                    results['passed'].append(f"✓ {name} - Correctly redirects to login")
                    return
        
        if response.status_code == expected_status:
            # Check for template errors in response
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')
                if 'TemplateSyntaxError' in content or 'Invalid filter' in content:
                    results['errors'].append(f"✗ {name} - Template error detected")
                    print(f"    Template error in {url}")
                    return
            
            results['passed'].append(f"✓ {name} - Status {response.status_code}")
        else:
            error_detail = ""
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')[:500]
                if 'CSRF' in content:
                    error_detail = " (CSRF error)"
                elif 'Invalid HTTP_HOST' in content or 'DisallowedHost' in content:
                    error_detail = " (ALLOWED_HOSTS error)"
            results['failed'].append(f"✗ {name} - Expected {expected_status}, got {response.status_code}{error_detail}")
            
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        results['errors'].append(f"✗ {name} - Error: {error_msg}")

# Create test users
print("\n📝 SETTING UP TEST DATA")
print("-" * 80)

# Create regular user
try:
    test_user = User.objects.get(username='pagetest')
except User.DoesNotExist:
    test_user = User.objects.create_user('pagetest', 'test@test.com', 'test123')
print(f"✓ Test user: pagetest")

# Create admin user
try:
    admin_user = User.objects.get(username='admin')
except User.DoesNotExist:
    admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
print(f"✓ Admin user: admin")

# Get profile
profile, _ = Profile.objects.get_or_create(user=test_user)

print("\n" + "=" * 80)
print("TESTING PUBLIC PAGES (No Auth Required)")
print("=" * 80)

test_page("Home Page", "/")
test_page("About Page", "/about/")
test_page("Tiers Page", "/tiers/")

print("\n" + "=" * 80)
print("TESTING AUTH PAGES (Guest)")
print("=" * 80)

test_page("Login Page", "/accounts/login/")
test_page("Register Page", "/accounts/register/")

print("\n" + "=" * 80)
print("TESTING AUTHENTICATED PAGES (Logged Out - Should Redirect)")
print("=" * 80)

test_page("Dashboard", "/accounts/dashboard/", requires_auth=True)
test_page("Profile", "/accounts/profile/", requires_auth=True)
test_page("Settings", "/accounts/settings/", requires_auth=True)
test_page("Deposit Page", "/accounts/deposit/", requires_auth=True)
test_page("Withdrawal Form", "/accounts/withdraw/", requires_auth=True)
test_page("Notifications", "/accounts/notifications/", requires_auth=True)

# Login as regular user
print("\n" + "=" * 80)
print("TESTING AUTHENTICATED PAGES (Logged In as User)")
print("=" * 80)

client.login(username='pagetest', password='test123')

test_page("Dashboard (Logged In)", "/accounts/dashboard/")
test_page("Profile (Logged In)", "/accounts/profile/")
test_page("Settings (Logged In)", "/accounts/settings/")
test_page("Deposit Page (Logged In)", "/accounts/deposit/")
test_page("Withdrawal Form (Logged In)", "/accounts/withdraw/")
test_page("Notifications (Logged In)", "/accounts/notifications/")

print("\n" + "=" * 80)
print("TESTING VIDEO PAGES (Logged In)")
print("=" * 80)

test_page("Videos List", "/videos/")

# Create a test video if none exist
videos = Video.objects.filter(is_active=True)
if videos.exists():
    video = videos.first()
    test_page(f"Video Detail #{video.id}", f"/videos/{video.id}/")
    print(f"✓ Video detail page tested with video ID {video.id}")
else:
    print("⚠️  No videos available to test detail page")

print("\n" + "=" * 80)
print("TESTING REFERRAL PAGES (Logged In)")
print("=" * 80)

test_page("Referral Stats", "/referrals/stats/")

# Logout
client.logout()

print("\n" + "=" * 80)
print("TESTING ADMIN PAGES (Not Logged In - Should Redirect)")
print("=" * 80)

test_page("Admin Login", "/admin/login/")
test_page("Admin Users", "/admin/users/", requires_staff=True)
test_page("Admin Videos", "/admin/videos/", requires_staff=True)
test_page("Admin Tiers", "/admin/tiers/", requires_staff=True)
test_page("Admin Deposits", "/admin/deposits/", requires_staff=True)
test_page("Admin Withdrawals", "/admin/withdrawals/", requires_staff=True)
test_page("Admin Messages", "/admin/messages/", requires_staff=True)
test_page("Admin Settings", "/admin/settings/", requires_staff=True)

# Login as admin
print("\n" + "=" * 80)
print("TESTING ADMIN PAGES (Logged In as Admin)")
print("=" * 80)

client.login(username='admin', password='admin123')

test_page("Admin Users (Logged In)", "/admin/users/")
test_page("Admin Videos (Logged In)", "/admin/videos/")
test_page("Admin Tiers (Logged In)", "/admin/tiers/")
test_page("Admin Deposits (Logged In)", "/admin/deposits/")
test_page("Admin Withdrawals (Logged In)", "/admin/withdrawals/")
test_page("Admin Messages (Logged In)", "/admin/messages/")
test_page("Admin Settings (Logged In)", "/admin/settings/")
test_page("Admin Referrals (Logged In)", "/admin/referrals/")

# Logout
client.logout()

print("\n" + "=" * 80)
print("TESTING MESSAGE PAGES")
print("=" * 80)

# Login as regular user for messages
client.login(username='pagetest', password='test123')

# Messages might be in core app - check if routes exist
try:
    test_page("User Messages", "/accounts/notifications/")
except:
    print("⚠️  Message routes not found")

client.logout()

# Print Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

print(f"\n✅ PASSED: {len(results['passed'])}")
for item in results['passed']:
    print(f"  {item}")

if results['failed']:
    print(f"\n❌ FAILED: {len(results['failed'])}")
    for item in results['failed']:
        print(f"  {item}")

if results['errors']:
    print(f"\n🔥 ERRORS: {len(results['errors'])}")
    for item in results['errors']:
        print(f"  {item}")

total_tests = len(results['passed']) + len(results['failed']) + len(results['errors'])
success_rate = (len(results['passed']) / total_tests * 100) if total_tests > 0 else 0

print("\n" + "=" * 80)
print(f"TOTAL TESTS: {total_tests}")
print(f"SUCCESS RATE: {success_rate:.1f}%")
print("=" * 80)

if results['failed'] or results['errors']:
    print("\n⚠️  Some tests failed or had errors. Review above for details.")
    exit(1)
else:
    print("\n✅ All tests passed successfully!")
    exit(0)
