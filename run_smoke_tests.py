"""End-to-end smoke test for xrpvideos core flows."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from accounts.models import Profile
from videos.models import Video, VideoWatch, WatchHistory
from admin_panel.models import AdminProfile, AdminRole
from accounts.ratelimit import make_math_captcha


def test_watch_credit_direct():
    print('\n=== Test: Watch + Credit (direct ORM) ===')
    user = User.objects.filter(username='directuser').first()
    if not user:
        user = User.objects.create_user('directuser', 'direct@example.com', 'TestPass123')
        Profile.objects.create(user=user)
    else:
        Profile.objects.get_or_create(user=user)
    Profile.objects.filter(user=user).update(balance=0)

    # Ensure user has Gold tier access for testing
    from videos.models import Tier
    gold = Tier.objects.filter(name='Gold').first()
    if not gold:
        gold = Tier.objects.create(name='Gold', price=100)
    user.profile.current_tier = gold
    user.profile.save()

    video = Video.objects.filter(is_active=True, min_tier__isnull=False).first()
    if not video:
        video = Video.objects.filter(is_active=True).first()
    assert video, 'No active video found'
    print(f'  Video: {video.title} | duration={video.duration_seconds}s | reward={video.effective_reward()}')

    VideoWatch.objects.filter(user=user, video=video).delete()
    WatchHistory.objects.filter(user=user, video=video).delete()

    client = Client()
    client.force_login(user)
    resp = client.post(f'/videos/{video.pk}/watch/start/', HTTP_HOST='localhost', secure=True)
    assert resp.status_code == 200, f'start failed: {resp.status_code}'
    data = resp.json()
    assert data['ok'], f'start not ok: {data}'
    client_id = data['client_id']

    watch = VideoWatch.objects.get(user=user, video=video, client_id=client_id)
    watch.started_at = timezone.now() - timedelta(seconds=video.duration_seconds + 5)
    watch.save()

    resp = client.post(f'/videos/{video.pk}/watch/complete/', {'client_id': client_id}, HTTP_HOST='localhost', secure=True)
    assert resp.status_code == 200, f'complete failed: {resp.status_code}'
    data = resp.json()
    assert data['ok'], f'complete not ok: {data}'
    amount = float(data.get('amount', 0))
    assert amount > 0, f'Reward should be > 0, got {amount}'

    watch.refresh_from_db()
    assert watch.credited, 'VideoWatch should be credited'

    profile = Profile.objects.get(user=user)
    assert profile.balance == amount, f'Balance mismatch: {profile.balance} vs {amount}'
    print(f'  Credited ${amount:.2f} | balance=${profile.balance:.2f} | credited={watch.credited}')

    # idempotent
    resp2 = client.post(f'/videos/{video.pk}/watch/complete/', {'client_id': client_id}, HTTP_HOST='localhost', secure=True)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2.get('already_credited') is True
    profile.refresh_from_db()
    assert profile.balance == amount
    print('  Idempotent re-call OK')


def test_admin_rbac():
    print('\n=== Test: Admin RBAC ===')
    from admin_panel.permissions import has_perm, is_admin, AdminRole

    su = User.objects.filter(username='superadmin').first()
    sa = User.objects.filter(username='stdadmin').first()
    st = User.objects.filter(username='staffonly').first()

    if not su:
        su = User.objects.create_superuser('superadmin', 'admin@xrpvideos.com', 'Admin@12345')
        AdminProfile.objects.create(user=su, role=AdminRole.SUPER_ADMIN)
    else:
        AdminProfile.objects.get_or_create(user=su, defaults={'role': AdminRole.SUPER_ADMIN})
    if not sa:
        sa = User.objects.create_user('stdadmin', 'std@xrpvideos.com', 'Admin@12345')
        sa.is_staff = True
        sa.save()
        AdminProfile.objects.create(user=sa, role=AdminRole.STANDARD_ADMIN)
    else:
        AdminProfile.objects.get_or_create(user=sa, defaults={'role': AdminRole.STANDARD_ADMIN})
    if not st:
        st = User.objects.create_user('staffonly', 'staff@xrpvideos.com', 'Admin@12345')
        st.is_staff = True
        st.save()
        AdminProfile.objects.create(user=st, role=AdminRole.STAFF)
    else:
        AdminProfile.objects.get_or_create(user=st, defaults={'role': AdminRole.STAFF})

    assert is_admin(su) and has_perm(su, 'manage_finance')
    assert is_admin(sa) and not has_perm(sa, 'manage_finance') and has_perm(sa, 'approve_payouts')
    assert is_admin(st) and not has_perm(st, 'manage_finance') and has_perm(st, 'view_dashboard')
    print('  RBAC matrix OK')


def test_password_reset_flow():
    print('\n=== Test: Password Reset Request ===')
    user = User.objects.filter(username='directuser').first()
    assert user, 'directuser must exist'

    c = Client()
    resp = c.get('/accounts/password-reset/', HTTP_HOST='localhost', secure=True, follow=True)
    assert resp.status_code == 200

    resp = c.post('/accounts/password-reset/', {'email': user.email}, HTTP_HOST='localhost', secure=True, follow=True)
    assert resp.status_code == 200
    print('  Password reset request OK')


def main():
    print('Starting smoke tests...')
    test_watch_credit_direct()
    test_admin_rbac()
    test_password_reset_flow()
    print('\nAll smoke tests passed.')


if __name__ == '__main__':
    main()
