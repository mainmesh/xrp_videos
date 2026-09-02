"""Role-based access control for the admin panel.

Roles + their default permission sets live in `PERMISSIONS` and `ROLE_PERMS`.
Use `has_perm(user, 'permission_key')` for checks and `@permission_required('key')`
to guard views. `ensure_admin_profile` lazily creates an AdminProfile row when
a staff user first interacts with it.
"""
from __future__ import annotations

from functools import wraps
from typing import Iterable

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from .models import AdminPermission, AdminProfile, AdminRole


PERMISSIONS: dict[str, str] = {
    'view_dashboard':  'View admin dashboard & analytics',
    'manage_videos':   'Create / edit / delete videos',
    'manage_tiers':    'Create / edit / delete tiers and prices',
    'manage_finance':  'Edit global financial settings (payout caps, fees, default reward)',
    'approve_payouts': 'Approve or reject withdrawal requests',
    'manage_users':    'Edit user accounts (suspend, role changes, manual credit/debit)',
    'manage_admins':   'Create / promote / demote admins',
    'view_audit_log':  'View the audit log',
}

ROLE_PERMS: dict[str, set[str]] = {
    AdminRole.SUPER_ADMIN: set(PERMISSIONS.keys()),
    AdminRole.STANDARD_ADMIN: {
        'view_dashboard', 'manage_videos', 'manage_tiers',
        'approve_payouts', 'manage_users', 'view_audit_log',
    },
    AdminRole.STAFF: {'view_dashboard', 'view_audit_log'},
}


def seed_permissions() -> None:
    """Insert any missing permission rows. Safe to call repeatedly."""
    for key, label in PERMISSIONS.items():
        AdminPermission.objects.update_or_create(key=key, defaults={'label': label})


def ensure_admin_profile(user) -> AdminProfile:
    """Return the AdminProfile for `user`, creating one with the default
    'staff' role if missing. Idempotent."""
    if not user or not user.is_authenticated:
        raise ValueError('User must be authenticated')
    profile, _ = AdminProfile.objects.get_or_create(user=user, defaults={'role': AdminRole.STAFF})
    return profile


def is_admin(user) -> bool:
    """True if the user can reach the admin panel at all."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.is_staff:
        return True
    return AdminProfile.objects.filter(user=user).exists()


def has_perm(user, key: str) -> bool:
    """Return True if `user` has the named permission."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'admin_profile', None)
    if profile is None:
        return False
    if key in ROLE_PERMS.get(profile.role, set()):
        return True
    return profile.permissions.filter(key=key).exists()


def permission_required(key: str, *, login_url: str = 'admin_panel:login'):
    """Decorator that gates a view on a permission. Returns 403 if the user is
    authenticated but lacks the permission, or redirects to `login_url` if
    unauthenticated."""
    def deco(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect(login_url)
            if not is_admin(user):
                return HttpResponseForbidden('Admin access required.')
            if not has_perm(user, key):
                return HttpResponseForbidden(f'Missing permission: {key}')
            return view(request, *args, **kwargs)
        return wrapper
    return deco


def staff_or_permission_required(key: str, login_url: str = 'admin_panel:login'):
    """Like permission_required, but Django superusers / `is_staff` users
    always pass even if they don't have an AdminProfile (lets us keep working
    while admins transition to the new RBAC)."""
    return permission_required(key, login_url=login_url)


__all__ = [
    'PERMISSIONS', 'ROLE_PERMS', 'AdminRole', 'AdminPermission', 'AdminProfile',
    'seed_permissions', 'ensure_admin_profile', 'is_admin', 'has_perm',
    'permission_required',
]