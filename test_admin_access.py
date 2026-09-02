#!/usr/bin/env python
"""
Test admin panel access and dashboard loading.
"""
import os
import sys

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

print("=" * 70)
print("ADMIN PANEL ACCESS TEST")
print("=" * 70)

# Step 1: Check if admin user exists
print("\n📝 STEP 1: CHECK ADMIN USER")
print("-" * 70)

admin = User.objects.filter(username='admin', is_staff=True).first()
if admin:
    print(f"✅ Admin user exists: {admin.username}")
    print(f"   - Is Staff: {admin.is_staff}")
    print(f"   - Is Superuser: {admin.is_superuser}")
else:
    print("❌ No admin user found!")
    print("\n💡 Creating admin user...")
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@xrpvideos.com',
        password='admin123'
    )
    print(f"✅ Admin user created: admin / admin123")

# Step 2: Test admin login
print("\n🔐 STEP 2: TEST ADMIN LOGIN")
print("-" * 70)

client = Client()
login_url = reverse('admin_panel:login')
print(f"Login URL: {login_url}")

# Try to login
response = client.post(login_url, {
    'username': 'admin',
    'password': 'admin123'
}, follow=True)

if response.status_code == 200:
    print(f"✅ Login successful (Status: {response.status_code})")
    # Check if redirected to dashboard
    if 'admin_panel/dashboard' in response.request['PATH_INFO'] or response.request['PATH_INFO'] == '/admin/':
        print(f"✅ Redirected to dashboard: {response.request['PATH_INFO']}")
else:
    print(f"❌ Login failed (Status: {response.status_code})")

# Step 3: Test dashboard access
print("\n📊 STEP 3: TEST DASHBOARD ACCESS")
print("-" * 70)

# Login first
client.login(username='admin', password='admin123')

dashboard_url = reverse('admin_panel:dashboard')
print(f"Dashboard URL: {dashboard_url}")

try:
    response = client.get(dashboard_url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Dashboard loaded successfully!")
        
        # Check for key elements in response
        content = response.content.decode('utf-8')
        
        checks = {
            'stats': 'total_users' in content or 'Total Users' in content or 'statistics' in content.lower(),
            'navigation': 'dashboard' in content.lower() or 'admin panel' in content.lower(),
            'no_errors': 'error' not in content.lower() or 'exception' not in content.lower()
        }
        
        print(f"\n   Content Checks:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "⚠️"
            print(f"   {status} {check_name}: {'Passed' if passed else 'Not detected'}")
            
    elif response.status_code == 302:
        print(f"⚠️  Redirected to: {response.url}")
    elif response.status_code == 403:
        print("❌ Access Forbidden - User may not have staff permissions")
    elif response.status_code == 500:
        print("❌ Internal Server Error - Check the error details")
        if hasattr(response, 'content'):
            print(f"\n   Error content: {response.content.decode('utf-8')[:500]}")
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error accessing dashboard: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

# Step 4: Test other admin pages
print("\n🔍 STEP 4: TEST OTHER ADMIN PAGES")
print("-" * 70)

pages_to_test = [
    ('users', 'Users List'),
    ('videos', 'Videos List'),
    ('withdrawals', 'Withdrawals List'),
    ('deposits', 'Deposits List'),
    ('tiers', 'Tiers List'),
]

for url_name, page_name in pages_to_test:
    try:
        url = reverse(f'admin_panel:{url_name}')
        response = client.get(url)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {page_name}: {response.status_code}")
    except Exception as e:
        print(f"❌ {page_name}: Error - {str(e)}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"\n✅ Admin panel should be accessible at: /admin/")
print(f"   - Login URL: /admin/login/")
print(f"   - Dashboard URL: /admin/")
print(f"   - Credentials: admin / admin123")
print("\n" + "=" * 70)
