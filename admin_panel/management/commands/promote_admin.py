"""Assign or change an admin role for a user.

Usage:
    python manage.py promote_admin <username> <role> [--grant key1 key2 ...] [--revoke key3]

Roles: super_admin | admin | staff
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from admin_panel.models import AdminProfile, AdminPermission, AdminRole
from admin_panel.permissions import PERMISSIONS, seed_permissions


VALID_ROLES = {c[0] for c in AdminRole.choices}


class Command(BaseCommand):
    help = 'Promote/demote a user to an admin role and optionally grant ad-hoc permissions.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('role', help='super_admin | admin | staff')
        parser.add_argument('--grant', nargs='*', default=[], help='Permission keys to grant')
        parser.add_argument('--revoke', nargs='*', default=[], help='Permission keys to revoke')

    def handle(self, *args, **opts):
        username = opts['username']
        role = opts['role']
        if role not in VALID_ROLES:
            raise CommandError(f'Invalid role: {role}. Choose from {sorted(VALID_ROLES)}')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" not found.')

        seed_permissions()

        # Promote: also flip Django flags for compatibility with @staff_required.
        if role == AdminRole.SUPER_ADMIN:
            user.is_staff = True
            user.is_superuser = True
        elif role in (AdminRole.STANDARD_ADMIN, AdminRole.STAFF):
            user.is_staff = True
            user.is_superuser = False
        user.save(update_fields=['is_staff', 'is_superuser'])

        profile, _ = AdminProfile.objects.get_or_create(user=user)
        before_role = profile.role
        profile.role = role
        profile.save(update_fields=['role'])
        self.stdout.write(self.style.SUCCESS(
            f'{username}: {before_role} -> {role}'
        ))

        granted, missing = [], []
        for key in opts['grant']:
            if key not in PERMISSIONS:
                missing.append(key)
                continue
            perm = AdminPermission.objects.get(key=key)
            profile.permissions.add(perm)
            granted.append(key)
        if granted:
            self.stdout.write(self.style.SUCCESS(f'  granted: {", ".join(granted)}'))
        if missing:
            self.stdout.write(self.style.WARNING(f'  unknown (skipped): {", ".join(missing)}'))

        for key in opts['revoke']:
            try:
                perm = AdminPermission.objects.get(key=key)
                profile.permissions.remove(perm)
                self.stdout.write(self.style.SUCCESS(f'  revoked: {key}'))
            except AdminPermission.DoesNotExist:
                pass