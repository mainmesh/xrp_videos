#!/usr/bin/env python
"""
Simple script to create admin user. 
Run this on Render: python create_admin_simple.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
password = 'admin123'
email = 'admin@xrpvideos.com'

try:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.email = email
    user.save()
    print(f'✓ Admin user "{username}" updated successfully!')
except User.DoesNotExist:
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f'✓ Admin user "{username}" created successfully!')

print(f'Username: {username}')
print(f'Password: {password}')
print(f'Staff: {user.is_staff}')
print(f'Superuser: {user.is_superuser}')
print(f'Active: {user.is_active}')
print('\nYou can now login at: /admin/login/')
