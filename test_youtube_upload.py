#!/usr/bin/env python
"""
Test script to upload a YouTube video via admin panel
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from videos.models import Video, Tier, VideoTierPrice
from django.utils import timezone

# YouTube video details
youtube_url = "https://www.youtube.com/embed/I-QfPUz1es8"
video_title = "Test YouTube Video"
duration_minutes = 3.5  # 3 minutes 30 seconds

# Convert minutes to seconds
duration_seconds = int(duration_minutes * 60)

print(f"Creating video: {video_title}")
print(f"URL: {youtube_url}")
print(f"Duration: {duration_minutes} minutes ({duration_seconds} seconds)")

# Get admin user
try:
    admin_user = User.objects.get(username='admin')
    print(f"✓ Found admin user: {admin_user.username}")
except User.DoesNotExist:
    print("✗ Admin user not found. Please create admin user first.")
    exit(1)

# Get all tiers
tiers = Tier.objects.all().order_by('price')
print(f"\n✓ Found {tiers.count()} tiers:")
for tier in tiers:
    print(f"  - {tier.name}: ${tier.price}")

if tiers.count() == 0:
    print("✗ No tiers found. Please create tiers first.")
    exit(1)

# Create video
try:
    video = Video.objects.create(
        title=video_title,
        url=youtube_url,
        thumbnail_url="",
        reward=0.0,
        duration_seconds=duration_seconds,
        is_active=True,
        created_by=admin_user
    )
    print(f"\n✓ Video created with ID: {video.id}")
    
    # Add tier pricing - Bronze tier gets $0.10, Silver $0.15, Gold $0.20
    rewards = {
        'Bronze': 0.10,
        'Silver': 0.15,
        'Gold': 0.20
    }
    
    lowest_tier = None
    for tier in tiers:
        reward_amount = rewards.get(tier.name, 0.10)
        VideoTierPrice.objects.create(
            video=video,
            tier=tier,
            reward=reward_amount
        )
        print(f"  ✓ Added {tier.name} tier with reward ${reward_amount}")
        
        if lowest_tier is None or tier.price < lowest_tier.price:
            lowest_tier = tier
    
    # Set minimum tier
    if lowest_tier:
        video.min_tier = lowest_tier
        video.save()
        print(f"\n✓ Set minimum tier to: {lowest_tier.name}")
    
    print(f"\n✅ SUCCESS! Video uploaded successfully!")
    print(f"   - Video ID: {video.id}")
    print(f"   - Title: {video.title}")
    print(f"   - Duration: {video.duration_seconds} seconds ({video.duration_minutes} minutes)")
    print(f"   - URL: {video.url}")
    print(f"   - Active: {video.is_active}")
    
    # Check if video can be retrieved
    check_video = Video.objects.get(id=video.id)
    print(f"\n✓ Video can be retrieved from database")
    print(f"   - Tier prices: {check_video.tier_prices.count()}")
    
except Exception as e:
    print(f"\n✗ ERROR creating video: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
