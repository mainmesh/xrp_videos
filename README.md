# XRPPrime-Style Watch-to-Earn (Django)

This is a minimal Watch-to-Earn Django starter app inspired by the user's requirements. It includes:

- User profiles with wallet balances
- Video categories, tiers, and self-hosted videos
- Watch verification endpoint that credits rewards and referral bonuses
- Referral link placeholder and referral bonus model
- Deposit and withdrawal models (Stripe integration placeholder)
- Simple Tailwind-styled templates

Quick setup

1. Create and activate a Python virtualenv

```powershell
# on Windows (PowerShell)
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run migrations and create a superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

3. Admin

Visit `/admin/` to add `Tier`, `Category`, and `Video` entries and manage withdrawals.

Notes / next steps

- The deposit flow uses a placeholder view. Integrate Stripe PaymentIntents and webhooks for production.
- Email notifications are placeholders; integrate `django.core.mail` or a transactional email provider.
- For robust watch verification use client-side heartbeat + server-side timestamp checks.
- For production, build Tailwind properly instead of CDN, and secure settings/keys via environment variables.