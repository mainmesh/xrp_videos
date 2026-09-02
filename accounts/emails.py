"""Account-related email helpers. Keeps email templates and sending logic in
one place so views stay clean.
"""
from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone


def send_verification_email(user, request, new_email: str | None = None) -> str:
    """Send an email verification link. Returns the generated token.

    If `new_email` is supplied the user is changing their email; the link will
    confirm *both* the change and that the new address is reachable.
    """
    from .models import EmailVerification

    token = secrets.token_urlsafe(32)
    EmailVerification.objects.create(
        user=user,
        token=token,
        new_email=(new_email or '').strip().lower(),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    verify_path = f"/accounts/verify-email/{token}/"
    verify_url = request.build_absolute_uri(verify_path) if request else verify_path

    subject = 'Confirm your xrpvideos email'
    body = (
        f"Hi {user.username},\n\n"
        f"Please confirm your email address by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in 24 hours. If you didn't create an account, you can ignore this email.\n\n"
        f"— The xrpvideos Team\n"
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email or user.email],
        fail_silently=True,
    )
    return token


def send_password_reset_email(request, *args, **kwargs):
    """Wrapper used by Django's PasswordResetForm.send_mail that overrides
    branding/expiry copy and routes through our DEFAULT_FROM_EMAIL.
    """
    from .models import Profile  # noqa: F401  (ensures app is loaded)
    from django.contrib.auth.forms import PasswordResetForm

    form = PasswordResetForm()
    return form.save(
        *args,
        from_email=settings.DEFAULT_FROM_EMAIL,
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        request=request,
        use_https=request.is_secure(),
        **kwargs,
    )


def send_login_alert(user, request, ip: str, user_agent: str) -> None:
    """Send a 'new login on your account' email. Lightweight informational
    notice; it doesn't gate the login itself.
    """
    if not user.email:
        return
    subject = 'New sign-in to your xrpvideos account'
    body = (
        f"Hi {user.username},\n\n"
        f"We noticed a new sign-in to your account.\n\n"
        f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"IP: {ip}\n"
        f"Browser: {user_agent[:120]}\n\n"
        f"If this wasn't you, please reset your password immediately.\n\n"
        f"— The xrpvideos Team\n"
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )