#!/usr/bin/env python
"""
Create a test user and check if videos are visible
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from videos.models import Video, Tier

# Create test user
username = 'testuser'
password = 'test123'
email = 'test@example.com'

try:
    user = User.objects.get(username=username)
    print(f"✓ Test user '{username}' already exists")
except User.DoesNotExist:
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    print(f"✓ Created test user '{username}'")

# Get or create profile
profile, created = Profile.objects.get_or_create(user=user)
if created:
    print(f"✓ Created profile for {username}")
else:
    print(f"✓ Profile exists for {username}")

# Check current tier
print(f"\nUser Details:")
print(f"  - Username: {username}")
print(f"  - Password: {password}")
print(f"  - Current Tier: {profile.current_tier.name if profile.current_tier else 'None (Free)'}")
print(f"  - Balance: ${profile.balance}")

# Check what videos are available
bronze_tier = Tier.objects.filter(name='Bronze').first()
if bronze_tier and not profile.current_tier:
    # For testing, assign Bronze tier
    profile.current_tier = bronze_tier
    profile.save()
    print(f"\n✓ Assigned Bronze tier to test user for testing")

# Get available videos for this user
if profile.current_tier:
    available_videos = Video.objects.filter(
        is_active=True,
        min_tier__price__lte=profile.current_tier.price
    ).order_by('-created_at')
else:
    available_videos = Video.objects.filter(
        is_active=True,
        min_tier__isnull=True
    ).order_by('-created_at')

print(f"\n✓ Found {available_videos.count()} available videos for {username}:")
for video in available_videos:
    tier_prices = video.tier_prices.all()
    print(f"\n  Video: {video.title}")
    print(f"    - ID: {video.id}")
    print(f"    - URL: {video.url}")
    print(f"    - Duration: {video.duration_minutes} minutes ({video.duration_seconds} seconds)")
    print(f"    - Min Tier: {video.min_tier.name if video.min_tier else 'Free'}")
    print(f"    - Tier Rewards:")
    for tp in tier_prices:
        print(f"      - {tp.tier.name}: ${tp.reward}")

print(f"\n✅ Test complete! You can login at http://127.0.0.1:8000/accounts/login/")
print(f"   Username: {username}")
print(f"   Password: {password}")
