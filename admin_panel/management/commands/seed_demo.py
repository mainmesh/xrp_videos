"""Seed demo data for xrpvideos: 3 tiers, 6 sample videos, and three admin
users (super, standard, staff). Idempotent — safe to run multiple times."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from admin_panel.models import AdminProfile, AdminPermission, AdminRole
from admin_panel.permissions import PERMISSIONS, ROLE_PERMS, seed_permissions
from videos.models import Tier as VideoTier, Video as VideoModel, Category


TIERS = [
    ('Bronze', 0),
    ('Silver', 50),
    ('Gold', 100),
]

VIDEOS = [
    # (title, url, duration_seconds, reward, tier_name)
    ('Crypto 101 — Intro to Bitcoin', 'https://www.youtube.com/embed/GCc0d1VQ8yE', 30, Decimal('0.50'), 'Bronze'),
    ('How XRP Ledger Works',         'https://www.youtube.com/embed/8_Hf2LHX_XY', 60, Decimal('1.00'), 'Silver'),
    ('Staking & Earning Strategies',  'https://www.youtube.com/embed/3pMH8LH8g2c', 60, Decimal('1.00'), 'Silver'),
    ('DeFi Yield Explained',         'https://www.youtube.com/embed/k9HZH0qVQgE', 90, Decimal('2.00'), 'Gold'),
    ('On-chain Analytics 101',       'https://www.youtube.com/embed/GW9F6nq1lgk', 90, Decimal('2.00'), 'Gold'),
    ('Quick Tips: Wallet Security',  'https://www.youtube.com/embed/c4bHlhJXp1I', 30, Decimal('0.50'), 'Bronze'),
]


class Command(BaseCommand):
    help = 'Seed demo tiers, videos, and admin users (idempotent).'

    def handle(self, *args, **options):
        seed_permissions()
        self.stdout.write(self.style.SUCCESS('[OK] Permissions seeded'))

        tier_by_name = {}
        for name, price in TIERS:
            t, _ = VideoTier.objects.get_or_create(name=name, defaults={'price': price})
            if t.price != price:
                t.price = price
                t.save(update_fields=['price'])
            tier_by_name[name] = t
            self.stdout.write(f'  - Tier {name} (${price})')

        cat, _ = Category.objects.get_or_create(name='Education')
        for title, url, dur, reward, tier_name in VIDEOS:
            v, created = VideoModel.objects.get_or_create(
                title=title,
                defaults={
                    'url': url, 'description': 'Demo video seeded by manage.py seed_demo',
                    'duration_seconds': dur, 'reward_amount': reward,
                    'reward': float(reward),
                    'min_tier': tier_by_name[tier_name],
                    'is_active': True,
                },
            )
            if not v.categories.filter(pk=cat.pk).exists():
                v.categories.add(cat)
            self.stdout.write(f"  - Video {title} ({'created' if created else 'exists'})")

        admins = [
            ('superadmin', 'admin@xrpvideos.com', 'Admin@12345', AdminRole.SUPER_ADMIN, True, True),
            ('stdadmin',   'std@xrpvideos.com',   'Admin@12345', AdminRole.STANDARD_ADMIN, True, False),
            ('staffonly',  'staff@xrpvideos.com', 'Admin@12345', AdminRole.STAFF, True, False),
        ]
        for username, email, pw, role, is_staff, is_super in admins:
            u, created = User.objects.get_or_create(
                username=username, defaults={'email': email, 'is_staff': is_staff, 'is_superuser': is_super},
            )
            u.is_staff = is_staff
            u.is_superuser = is_super
            if created:
                u.set_password(pw)
            u.save()
            Profile.objects.get_or_create(user=u)
            AdminProfile.objects.update_or_create(user=u, defaults={'role': role})
            self.stdout.write(f'  - Admin {username} ({role})')

        for username in ('alice', 'bob'):
            u, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
            if created:
                u.set_password('Test@12345')
                u.save()
            Profile.objects.get_or_create(user=u)
            self.stdout.write(f'  - User {username}')

        self.stdout.write(self.style.SUCCESS('\nDone. Sign in at /accounts/login/ or /admin/login/.'))