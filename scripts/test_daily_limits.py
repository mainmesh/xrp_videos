"""E2E verification for tier-based rolling 24h daily watch limits.
Bronze=1/day, Silver=5/day, Gold=unlimited. Videos disappear after the
quota with a countdown; server blocks start/complete past the quota.
Run: venv\\Scripts\\python.exe scripts\\test_daily_limits.py
Uses the live dev database; cleans up test artifacts at the end.
"""
import os
import sys
import pathlib
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
import django
django.setup()
from datetime import timedelta
from django.utils import timezone
from django.test import Client
from django.contrib.auth.models import User
from videos.models import Video, VideoWatch, Tier
from videos.views import _daily_watch_state

H = {'HTTP_HOST': 'localhost', 'secure': True}
results = []


def check(name, ok, detail=''):
    results.append((name, ok, detail))


def credit_video(v, hours_ago=0):
    ts = timezone.now() - timedelta(hours=hours_ago)
    VideoWatch.objects.update_or_create(
        user=user, video=v,
        defaults={'client_id': f'test-{v.id}', 'credited': True,
                  'credited_at': ts, 'amount_credited': 1},
    )


# Pre-clean leftovers from any previous crashed run
User.objects.filter(username='limit_test_user').delete()
Video.objects.filter(title__startswith='LimitTest').delete()

user = User.objects.create_user(username='limit_test_user', password='x', email='lt@t.com')
videos = [
    Video.objects.create(title=f'LimitTest {i}', url='http://example.com', reward=1.0, duration_seconds=10)
    for i in range(1, 8)
]

c = Client()
c.force_login(user)

# --- Bronze (auto-assigned on first list view; limit=1) ---
r = c.get('/videos/', **H)
b = r.content.decode()
user.profile.refresh_from_db()
check('bronze auto-assigned', user.profile.current_tier is not None
      and user.profile.current_tier.name == 'Bronze', user.profile.current_tier)
check('bronze sees all videos initially', b.count('class="video-card') >= 7, b.count('class="video-card'))

credit_video(videos[0])
state = _daily_watch_state(user)
check('quota reached after 1 watch', state['reached'] and state['limit'] == 1, state)

r = c.get('/videos/', **H)
b = r.content.decode()
check('list hidden after 1 watch', 'LimitTest ' not in b, 'LimitTest ' in b)
check('countdown banner shown', 'limit-countdown' in b and "You&#x27;ve watched your 1 video" in b or "You've watched your 1 video" in b, '')
check('unlock_at in countdown script', 'new Date("' in b, '')
check('upgrade CTA for bronze', 'Upgrade for more daily videos' in b, '')

r = c.post(f'/videos/{videos[1].id}/watch/start/', {}, **H)
check('start blocked when quota spent', r.status_code == 400 and r.json().get('error') == 'daily_limit_reached', r.status_code)

r = c.post(f'/videos/{videos[1].id}/complete/', {'watched_seconds': 10}, **H)
check('legacy complete blocked', r.status_code == 400 and r.json().get('error') == 'daily_limit_reached', r.status_code)

# Rolling window: credit from 25h ago has expired -> user can watch again
VideoWatch.objects.filter(user=user).delete()
credit_video(videos[0], hours_ago=25)
r = c.get('/videos/', **H)
check('unlocked after 25h (rolling window)', 'LimitTest ' in r.content.decode(), '')
r = c.post(f'/videos/{videos[1].id}/watch/start/', {}, **H)
check('start allowed after window passed', r.status_code == 200 and r.json().get('ok'), r.status_code)

# --- Silver (limit=5) ---
silver = Tier.objects.get(name='Silver')
user.profile.current_tier = silver
user.profile.save()
VideoWatch.objects.filter(user=user).delete()

for v in videos[0:4]:
    credit_video(v)
state = _daily_watch_state(user)
check('silver at 4/5 not reached', not state['reached'] and state['limit'] == 5, state)
r = c.get('/videos/', **H)
check('silver still sees remaining videos at 4/5', 'LimitTest 5' in r.content.decode(), '')
r = c.post(f'/videos/{videos[4].id}/watch/start/', {}, **H)
check('silver start allowed at 4/5', r.status_code == 200, r.status_code)

credit_video(videos[4])
state = _daily_watch_state(user)
check('silver reached at 5/5', state['reached'], state)
r = c.get('/videos/', **H)
b = r.content.decode()
check('silver list hidden at 5/5', 'LimitTest ' not in b and 'You&#x27;ve watched your 5 videos' in b or "You've watched your 5 videos" in b, '')
r = c.post(f'/videos/{videos[5].id}/watch/start/', {}, **H)
check('silver start blocked at 5/5', r.status_code == 400 and r.json().get('error') == 'daily_limit_reached', r.status_code)
check('silver upgrade CTA shown (can go Gold for unlimited)', 'Upgrade for more daily videos' in b, '')

# --- Gold (unlimited) ---
gold = Tier.objects.get(name='Gold')
user.profile.current_tier = gold
user.profile.save()
VideoWatch.objects.filter(user=user).delete()
for v in videos[0:7]:
    credit_video(v)
state = _daily_watch_state(user)
check('gold never reached (limit=0)', not state['reached'] and state['limit'] == 0, state)
r = c.get('/videos/', **H)
check('gold sees all videos even after 7 credits', 'LimitTest 1' in r.content.decode(), '')
r = c.post(f'/videos/{videos[0].id}/watch/start/', {}, **H)
check('gold start allowed (unlimited)', r.status_code == 200 and r.json().get('ok'), r.status_code)

# --- Detail page banner ---
user.profile.current_tier = Tier.objects.get(name='Bronze')
user.profile.save()
VideoWatch.objects.filter(user=user).delete()
credit_video(videos[0])
r = c.get(f'/videos/{videos[1].id}/', **H)
b = r.content.decode()
check('detail page shows limit banner', 'Daily Limit Reached' in b and 'limit-countdown' in b, '')

# --- Cleanup ---
user.delete()
for v in videos:
    v.delete()

print('=' * 60)
all_ok = True
for name, ok, detail in results:
    mark = 'PASS' if ok else 'FAIL'
    if not ok:
        all_ok = False
    print(f'[{mark}] {name}: {detail}')
print('=' * 60)
print('ALL PASS' if all_ok else 'SOME FAILED')
sys.exit(0 if all_ok else 1)
