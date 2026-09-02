#!/usr/bin/env python
"""
Test video watch termination and time validation.
This test simulates the client-side video player behavior and validates:
1. Video must be watched for the full required duration
2. Heartbeats are sent periodically
3. Watch completion is validated before rewarding
4. Insufficient watch time is rejected
"""
import os
import sys

# Configure Django settings before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')

# Import Django and setup
import django
django.setup()

from decimal import Decimal
import time
from django.contrib.auth.models import User
from accounts.models import Profile, Transaction
from videos.models import Video, Tier, WatchHistory, WatchHeartbeat, Category
from django.utils import timezone
from django.test import Client
import json

class VideoWatchSimulator:
    """Simulates a user watching a video with realistic heartbeat tracking."""
    
    def __init__(self, user, video):
        self.user = user
        self.video = video
        self.current_time = 0
        self.heartbeats = []
        self.completed = False
        
    def send_heartbeat(self, seconds):
        """Simulate sending a heartbeat to the server."""
        heartbeat = WatchHeartbeat.objects.create(
            user=self.user,
            video=self.video,
            seconds=seconds
        )
        self.heartbeats.append(seconds)
        print(f"   📡 Heartbeat sent: {seconds}s")
        return heartbeat
    
    def watch(self, duration_seconds, heartbeat_interval=10):
        """
        Simulate watching a video for a specific duration.
        Sends heartbeats at regular intervals.
        """
        print(f"\n▶️  Starting video playback simulation:")
        print(f"   - Video: {self.video.title}")
        print(f"   - Required Duration: {self.video.duration_seconds}s")
        print(f"   - Watch Duration: {duration_seconds}s")
        print(f"   - Heartbeat Interval: {heartbeat_interval}s")
        
        # Clear previous heartbeats for this user/video
        WatchHeartbeat.objects.filter(user=self.user, video=self.video).delete()
        
        # Simulate playback with heartbeats
        elapsed = 0
        while elapsed < duration_seconds:
            elapsed += heartbeat_interval
            if elapsed > duration_seconds:
                elapsed = duration_seconds
            
            self.current_time = elapsed
            self.send_heartbeat(elapsed)
            
            # Small delay to simulate real-time (optional)
            # time.sleep(0.1)
        
        self.completed = True
        print(f"   ✅ Playback completed: {elapsed}s watched")
        return elapsed
    
    def attempt_completion(self, watched_seconds):
        """Attempt to complete the watch and earn reward."""
        print(f"\n🎯 Attempting to complete watch:")
        print(f"   - Watched: {watched_seconds}s")
        print(f"   - Required: {self.video.duration_seconds}s")
        
        # Validate watch time
        if watched_seconds < self.video.duration_seconds:
            print(f"   ❌ REJECTED: Insufficient watch time")
            print(f"      Need {self.video.duration_seconds - watched_seconds}s more")
            return False, "insufficient_watch_time"
        
        # Validate heartbeats
        recent_heartbeats = WatchHeartbeat.objects.filter(
            user=self.user, 
            video=self.video
        ).order_by('-created_at')[:10]
        
        if recent_heartbeats.count() < 3:
            print(f"   ❌ REJECTED: Insufficient heartbeats ({recent_heartbeats.count()}/3)")
            return False, "insufficient_heartbeats"
        
        # Check for duplicate watch
        existing = WatchHistory.objects.filter(
            user=self.user, 
            video=self.video, 
            verified=True
        ).first()
        
        if existing:
            print(f"   ❌ REJECTED: Already watched this video")
            return False, "already_watched"
        
        # Check one video per day limit
        today = timezone.now().date()
        watched_today = WatchHistory.objects.filter(
            user=self.user,
            verified=True,
            watched_at__date=today
        ).exists()
        
        if watched_today:
            print(f"   ❌ REJECTED: Already watched a video today")
            return False, "one_per_day"
        
        print(f"   ✅ VALIDATION PASSED")
        return True, "ok"

def run_tests():
    """Run comprehensive video watch termination tests."""
    print("=" * 70)
    print("VIDEO WATCH TERMINATION & TIME VALIDATION TESTS")
    print("=" * 70)
    
    # Setup
    print("\n🔧 SETUP")
    print("-" * 70)
    
    # Create tiers
    bronze_tier, _ = Tier.objects.get_or_create(
        name='Bronze',
        defaults={'price': 0.0}
    )
    silver_tier, _ = Tier.objects.get_or_create(
        name='Silver',
        defaults={'price': 10.0}
    )
    
    # Create test user
    username = 'watchtest_user'
    User.objects.filter(username=username).delete()
    user = User.objects.create_user(
        username=username,
        email='watchtest@test.com',
        password='test123'
    )
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.current_tier = silver_tier
    profile.balance = 0.0
    profile.save()
    
    print(f"✅ User created: {username}")
    print(f"   - Tier: {profile.current_tier.name}")
    print(f"   - Balance: ${profile.balance:.2f}")
    
    # Create test videos with different durations
    videos = []
    
    video1, _ = Video.objects.get_or_create(
        title='Short Video (30s)',
        defaults={
            'url': 'https://www.youtube.com/embed/short',
            'reward': 0.25,
            'duration_seconds': 30,
            'min_tier': bronze_tier,
            'is_active': True
        }
    )
    video1.duration_seconds = 30
    video1.reward = 0.25
    video1.save()
    videos.append(video1)
    
    video2, _ = Video.objects.get_or_create(
        title='Medium Video (2min)',
        defaults={
            'url': 'https://www.youtube.com/embed/medium',
            'reward': 1.00,
            'duration_seconds': 120,
            'min_tier': silver_tier,
            'is_active': True
        }
    )
    video2.duration_seconds = 120
    video2.reward = 1.00
    video2.save()
    videos.append(video2)
    
    video3, _ = Video.objects.get_or_create(
        title='Long Video (5min)',
        defaults={
            'url': 'https://www.youtube.com/embed/long',
            'reward': 2.50,
            'duration_seconds': 300,
            'min_tier': silver_tier,
            'is_active': True
        }
    )
    video3.duration_seconds = 300
    video3.reward = 2.50
    video3.save()
    videos.append(video3)
    
    print(f"\n✅ Created {len(videos)} test videos:")
    for v in videos:
        print(f"   - {v.title}: {v.duration_seconds}s, ${v.reward} reward")
    
    # TEST 1: Insufficient watch time
    print("\n" + "=" * 70)
    print("TEST 1: INSUFFICIENT WATCH TIME (Should Reject)")
    print("=" * 70)
    
    simulator = VideoWatchSimulator(user, video2)  # 120s required
    watched = simulator.watch(duration_seconds=60, heartbeat_interval=10)  # Only watch 60s
    
    valid, reason = simulator.attempt_completion(watched)
    
    if not valid and reason == "insufficient_watch_time":
        print(f"\n✅ TEST PASSED: Correctly rejected insufficient watch time")
    else:
        print(f"\n❌ TEST FAILED: Should have rejected watch time")
    
    # TEST 2: Exact required watch time
    print("\n" + "=" * 70)
    print("TEST 2: EXACT REQUIRED WATCH TIME (Should Accept)")
    print("=" * 70)
    
    WatchHistory.objects.filter(user=user).delete()  # Clear history
    
    simulator = VideoWatchSimulator(user, video1)  # 30s required
    watched = simulator.watch(duration_seconds=30, heartbeat_interval=5)  # Watch exactly 30s
    
    valid, reason = simulator.attempt_completion(watched)
    
    if valid:
        print(f"\n✅ TEST PASSED: Accepted exact watch time")
        
        # Credit the reward
        balance_before = profile.balance
        wh, _ = WatchHistory.objects.get_or_create(user=user, video=video1)
        wh.watched_seconds = watched
        wh.verified = True
        wh.save()
        
        profile.credit(
            video1.reward,
            reason=f"Watched: {video1.title}",
            transaction_type="video_reward",
            video=video1
        )
        profile.refresh_from_db()
        
        print(f"   💰 Reward credited:")
        print(f"      Before: ${balance_before:.2f}")
        print(f"      Reward: ${video1.reward:.2f}")
        print(f"      After: ${profile.balance:.2f}")
    else:
        print(f"\n❌ TEST FAILED: Should have accepted exact watch time")
    
    # TEST 3: Excess watch time (more than required)
    print("\n" + "=" * 70)
    print("TEST 3: EXCESS WATCH TIME (Should Accept)")
    print("=" * 70)
    
    WatchHistory.objects.filter(user=user, verified=True).delete()  # Clear for new day
    
    simulator = VideoWatchSimulator(user, video3)  # 300s required
    watched = simulator.watch(duration_seconds=350, heartbeat_interval=15)  # Watch 350s
    
    valid, reason = simulator.attempt_completion(watched)
    
    if valid:
        print(f"\n✅ TEST PASSED: Accepted excess watch time")
        
        # Credit the reward
        balance_before = profile.balance
        wh, _ = WatchHistory.objects.get_or_create(user=user, video=video3)
        wh.watched_seconds = watched
        wh.verified = True
        wh.save()
        
        profile.credit(
            video3.reward,
            reason=f"Watched: {video3.title}",
            transaction_type="video_reward",
            video=video3
        )
        profile.refresh_from_db()
        
        print(f"   💰 Reward credited:")
        print(f"      Before: ${balance_before:.2f}")
        print(f"      Reward: ${video3.reward:.2f}")
        print(f"      After: ${profile.balance:.2f}")
    else:
        print(f"\n❌ TEST FAILED: Should have accepted excess watch time")
        print(f"   Reason: {reason}")
    
    # TEST 4: Insufficient heartbeats
    print("\n" + "=" * 70)
    print("TEST 4: INSUFFICIENT HEARTBEATS (Should Reject)")
    print("=" * 70)
    
    WatchHistory.objects.filter(user=user, verified=True).delete()
    
    # Create a new video for this test
    video4, _ = Video.objects.get_or_create(
        title='Test Video - Heartbeat Check',
        defaults={
            'url': 'https://www.youtube.com/embed/heartbeat',
            'reward': 1.50,
            'duration_seconds': 90,
            'min_tier': silver_tier,
            'is_active': True
        }
    )
    video4.duration_seconds = 90
    video4.save()
    
    # Clear heartbeats
    WatchHeartbeat.objects.filter(user=user, video=video4).delete()
    
    # Send only 2 heartbeats (less than required 3)
    WatchHeartbeat.objects.create(user=user, video=video4, seconds=30)
    WatchHeartbeat.objects.create(user=user, video=video4, seconds=60)
    
    print(f"   📡 Sent only 2 heartbeats (3 required)")
    
    simulator = VideoWatchSimulator(user, video4)
    simulator.current_time = 90
    
    valid, reason = simulator.attempt_completion(90)
    
    if not valid and reason == "insufficient_heartbeats":
        print(f"\n✅ TEST PASSED: Correctly rejected due to insufficient heartbeats")
    else:
        print(f"\n❌ TEST FAILED: Should have rejected due to insufficient heartbeats")
    
    # TEST 5: One video per day limit
    print("\n" + "=" * 70)
    print("TEST 5: ONE VIDEO PER DAY LIMIT (Should Reject Second Video)")
    print("=" * 70)
    
    # User has already watched video3 today (from TEST 3)
    today = timezone.now().date()
    watched_today = WatchHistory.objects.filter(
        user=user,
        verified=True,
        watched_at__date=today
    ).count()
    
    print(f"   Videos already watched today: {watched_today}")
    
    if watched_today > 0:
        # Try to watch another video
        video5, _ = Video.objects.get_or_create(
            title='Second Video Today',
            defaults={
                'url': 'https://www.youtube.com/embed/second',
                'reward': 1.00,
                'duration_seconds': 60,
                'min_tier': bronze_tier,
                'is_active': True
            }
        )
        video5.duration_seconds = 60
        video5.save()
        
        simulator = VideoWatchSimulator(user, video5)
        watched = simulator.watch(duration_seconds=60, heartbeat_interval=10)
        
        valid, reason = simulator.attempt_completion(watched)
        
        if not valid and reason == "one_per_day":
            print(f"\n✅ TEST PASSED: Correctly enforced one video per day limit")
        else:
            print(f"\n❌ TEST FAILED: Should have enforced one video per day limit")
    
    # FINAL SUMMARY
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    profile.refresh_from_db()
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')
    watched_videos = WatchHistory.objects.filter(user=user, verified=True)
    
    print(f"\n👤 User: {user.username}")
    print(f"   - Final Balance: ${profile.balance:.2f}")
    print(f"   - Videos Watched: {watched_videos.count()}")
    print(f"   - Total Transactions: {transactions.count()}")
    
    print(f"\n🎥 Watch History:")
    for wh in watched_videos:
        print(f"   - {wh.video.title}:")
        print(f"      Watched: {wh.watched_seconds}s / {wh.video.duration_seconds}s")
        print(f"      Reward: ${wh.video.reward:.2f}")
        print(f"      Verified: {wh.verified}")
    
    print(f"\n💰 Earnings Breakdown:")
    total_earned = 0
    for txn in transactions.filter(transaction_type='video_reward'):
        total_earned += float(txn.amount)
        print(f"   - {txn.description}: ${txn.amount}")
    
    print(f"\n   Total Earned: ${total_earned:.2f}")
    print(f"   Current Balance: ${profile.balance:.2f}")
    
    print("\n✅ ALL TESTS COMPLETED!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
