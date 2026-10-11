"""E2E verification for admin credit/debit/tier/suspend features.
Run: venv\\Scripts\\python.exe scripts/test_admin_user_manage.py
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
from django.test import Client
from django.contrib.auth.models import User
from videos.models import Tier
from accounts.models import Transaction
from admin_panel.models import AuditLog

H = {'HTTP_HOST': 'localhost', 'secure': True}
admin = User.objects.get(username='admin')

# Find a non-staff user (create one if none)
user = User.objects.filter(is_staff=False, is_superuser=False).exclude(username='admin').first()
created = False
if user is None:
    user = User.objects.create_user(username='admin_feature_test', password='x', email='t@t.com')
    created = True

start_balance = float(user.profile.balance)
results = []

c = Client()
c.force_login(admin)

# 1. Manage page renders
r = c.get(f'/admin/users/{user.id}/manage/', **H)
results.append(('manage page GET 200', r.status_code == 200, r.status_code))

# 2. Credit $5
r = c.post(f'/admin/users/{user.id}/credit/', {'amount': '5', 'reason': 'test bonus'}, **H)
user.profile.refresh_from_db()
ok = r.status_code == 302 and abs(float(user.profile.balance) - (start_balance + 5.0)) < 0.001
results.append(('credit +$5', ok, (r.status_code, float(user.profile.balance))))

# 3. Debit $2
r = c.post(f'/admin/users/{user.id}/debit/', {'amount': '2', 'reason': 'test correction'}, **H)
user.profile.refresh_from_db()
ok = r.status_code == 302 and abs(float(user.profile.balance) - (start_balance + 3.0)) < 0.001
results.append(('debit -$2', ok, (r.status_code, float(user.profile.balance))))

# 4. Overdraft blocked
bal_before = float(user.profile.balance)
r = c.post(f'/admin/users/{user.id}/debit/', {'amount': '999999', 'reason': 'x'}, **H)
user.profile.refresh_from_db()
ok = r.status_code == 302 and abs(float(user.profile.balance) - bal_before) < 0.001
results.append(('overdraft blocked', ok, float(user.profile.balance)))

# 5. Invalid amount rejected
r = c.post(f'/admin/users/{user.id}/credit/', {'amount': '0', 'reason': 'x'}, **H)
user.profile.refresh_from_db()
ok = r.status_code == 302 and abs(float(user.profile.balance) - bal_before) < 0.001
results.append(('zero amount rejected', ok, float(user.profile.balance)))

# 6. Set tier
tier = Tier.objects.order_by('-price').first()
r = c.post(f'/admin/users/{user.id}/set-tier/', {'tier_id': tier.id}, **H)
user.profile.refresh_from_db()
ok = r.status_code == 302 and user.profile.current_tier == tier
results.append((f'set tier -> {tier.name}', ok, user.profile.current_tier))

# 7. Clear tier
r = c.post(f'/admin/users/{user.id}/set-tier/', {'tier_id': ''}, **H)
user.profile.refresh_from_db()
ok = r.status_code == 302 and user.profile.current_tier is None
results.append(('clear tier', ok, user.profile.current_tier))

# 8. Suspend + re-activate (non-self, non-superuser target)
user.is_active = True
user.save()
r = c.post(f'/admin/users/{user.id}/toggle-active/', {}, **H)
user.refresh_from_db()
ok = r.status_code == 302 and not user.is_active
results.append(('suspend', ok, user.is_active))
r = c.post(f'/admin/users/{user.id}/toggle-active/', {}, **H)
user.refresh_from_db()
ok = r.status_code == 302 and user.is_active
results.append(('re-activate', ok, user.is_active))

# 9. Cannot suspend self
r = c.post(f'/admin/users/{admin.id}/toggle-active/', {}, **H)
admin.refresh_from_db()
ok = admin.is_active
results.append(('self-suspend blocked', ok, admin.is_active))

# 10. Users list page has quick actions + modals
r = c.get('/admin/users/', **H)
b = r.content.decode()
ok = r.status_code == 200 and 'credit-modal' in b and 'tier-modal' in b and f'/admin/users/{user.id}/manage/' in b
results.append(('users list actions+modals', ok, r.status_code))

# 11. Transactions recorded correctly
types = list(Transaction.objects.filter(user=user).order_by('-id').values_list('transaction_type', flat=True)[:2])
ok = types == ['admin_debit', 'admin_credit']
results.append(('transactions recorded', ok, types))

# 12. Audit log entries
actions = list(AuditLog.objects.order_by('-id').values_list('action', flat=True)[:10])
needed = {'user.credit', 'user.debit', 'user.tier_set', 'user.tier_remove', 'user.toggle_active'}
ok = needed.issubset(set(actions))
results.append(('audit entries', ok, actions[:5]))

# 13. User-side transactions page renders with new filters
uc = Client()
uc.force_login(user)
r = uc.get('/accounts/transactions/', **H)
b = r.content.decode() if r.status_code == 200 else ''
ok = r.status_code == 200 and 'admin_credit' in b
results.append(('user transactions page', ok, r.status_code))

# 14. User was actually notified (in-app inbox message delivered)
from core.models import Message
notified = Message.objects.filter(receiver=user, subject='Account Credited').order_by('-id').first()
ok = notified is not None and 'credited' in (notified.content + notified.message)
results.append(('credit notification delivered', ok, notified.subject if notified else None))
tier_notices = Message.objects.filter(receiver=user, subject='Membership Tier Updated').order_by('-id')
ok = tier_notices.filter(content__icontains='Enjoy your benefits').exists()
results.append(('tier notification delivered', ok, tier_notices.first().subject if tier_notices.exists() else None))

# Cleanup
tx_count = Transaction.objects.filter(user=user).count()
Message.objects.filter(receiver=user).delete()
if created:
    user.delete()
else:
    Transaction.objects.filter(user=user).delete()
    user.profile.balance = start_balance
    user.profile.current_tier = None
    user.profile.save()
    user.is_active = True
    user.save()

print('=' * 60)
all_ok = True
for name, ok, detail in results:
    mark = 'PASS' if ok else 'FAIL'
    if not ok:
        all_ok = False
    print(f'[{mark}] {name}: {detail}')
print('=' * 60)
print('ALL PASS' if all_ok else 'SOME FAILED')
