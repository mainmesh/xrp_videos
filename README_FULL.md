# XRPPrime-Style Watch-to-Earn Platform (Django)

A fully-featured Watch-to-Earn Django application with user registration, wallet, video rewards, referral tracking, Stripe payments, and withdrawal system.

## Features

✅ **User System**
- Registration with password protection and referral linking
- Profile dashboard with wallet balance, referral count, and withdrawal history
- Auto-generated unique referral links for each user

✅ **Video Categories & Tiers**
- Free tier: accessible without deposit
- Silver tier ($50): unlocked via Stripe deposit
- Gold tier ($100): unlocked via Stripe deposit
- Admin can assign videos to categories and tiers
- Self-hosted video support

✅ **Videos & Rewards**
- Time-based watch verification (client-side timer + server-side checks)
- Admin can set/change reward per video
- Reward credited immediately to wallet after verified watch
- Double-crediting prevention via verified flag

✅ **Wallet & Payments**
- Wallet tracks user balance
- **Stripe integration**: Create PaymentIntents, handle webhooks, mark deposits successful
- Withdrawal system with eligibility rules:
  - Must have ≥7 referrals
  - Max $50 per withdrawal
  - Admin approves manually; email notification placeholder

✅ **Referrals**
- Unique referral code per user
- Referral tracked via signup link (`/referrals/r/<code>/`)
- 10% bonus on referred users' earnings, credited immediately
- Referral bonus records tracked in database

✅ **UI/Dashboards**
- Public homepage with feature overview
- User dashboard: wallet, referrals, video categories, withdrawal request
- Admin dashboard: manage videos, approve withdrawals
- Tailwind CSS styling (CDN + responsive design)

## Quick Setup

### 1. Create & activate virtualenv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Migrations & admin user

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 3. Run dev server

```powershell
python manage.py runserver
```

Visit `http://localhost:8000/` to see the homepage.

## Configuration

### Stripe Setup (for real payments)

1. Get your Stripe API key from [stripe.com](https://stripe.com)
2. Set environment variables or edit `xrp_site/settings.py`:
   ```python
   STRIPE_API_KEY = 'sk_live_...'
   STRIPE_WEBHOOK_SECRET = 'whsec_...'
   ```

3. Create payment via the Deposit form:
   - User navigates to `/accounts/deposit/`
   - Creates PaymentIntent via `/accounts/deposit/intent/` (POST with amount)
   - Frontend uses Stripe.js to complete payment (TODO: add Stripe.js integration)
   - Webhook at `/stripe/webhook/` marks deposit successful and credits wallet

### Admin Panel

1. Visit `/admin/` (login with superuser)
2. Create tiers: **Free**, **Silver** ($50), **Gold** ($100)
3. Create categories: e.g., Tech, Finance, Entertainment
4. Add videos:
   - Title, URL (self-hosted or embed link)
   - Reward (e.g., $0.50)
   - Category, minimum tier
   - Duration in seconds
   - is_active flag

5. Manage withdrawals:
   - View pending requests from all users
   - Click "Approve selected withdrawals" action
   - Admin email notification placeholder (see `accounts/models.py`)

## Testing

### Run unit tests

```powershell
python manage.py test tests.test_watch_referral
```

Tests cover:
- Watch completion and reward crediting
- Referral bonus calculation (10%)
- Double-crediting prevention

### Manual testing flow

1. **Register two users**: Alice (referrer) and Bob (referee)
2. **Referral**: Copy Alice's link, open in incognito, register as Bob via referral link
3. **Add a video in admin**: Set reward=$1.00, duration=10s
4. **Watch video as Bob**: Visit video page, watch timer counts to 10s, auto-submit
5. **Verify credits**:
   - Bob's wallet: +$1.00
   - Alice's wallet: +$0.10 (10% bonus)
6. **Withdrawal**: Bob requests withdrawal (needs 7 referrals minimum)

## File Structure

```
xrp_clone_v2/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── README.md (this file)
├── xrp_site/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
├── core/
│   ├── views.py (home, about, tiers)
├── accounts/
│   ├── models.py (Profile, Deposit, WithdrawalRequest)
│   ├── views.py (dashboard, register, deposit, withdraw, Stripe webhook)
│   ├── urls.py
│   ├── admin.py
├── videos/
│   ├── models.py (Tier, Category, Video, WatchHistory)
│   ├── views.py (video_list, video_detail, watch_complete)
│   ├── urls.py
│   ├── admin.py
├── referrals/
│   ├── models.py (ReferralLink, ReferralBonus)
│   ├── views.py (signup_with_referral)
│   ├── urls.py
│   ├── admin.py
├── templates/
│   ├── base.html (header, footer, Tailwind CDN)
│   ├── home.html
│   ├── about.html
│   ├── tiers.html
│   ├── accounts/
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── withdrawal_form.html
│   │   ├── deposit_placeholder.html
│   ├── videos/
│   │   ├── list.html
│   │   ├── detail.html (with client-side watch timer)
├── tests/
│   ├── test_watch_referral.py
```

## Key Implementation Notes

### Watch Verification (Client + Server)
- **Client**: Timer increments every second; auto-submits form when duration reached
- **Server**: `watch_complete` checks WatchHistory.verified flag to prevent double-crediting
- **Security**: In production, use heartbeat + server timestamps to detect fraud

### Referral Flow
1. User registers; `ReferralLink` with unique code auto-created
2. Dashboard shows referral link; user shares it
3. New user visits `/referrals/r/<code>/` → code stored in session
4. New user registers; session code links them to referrer
5. Referrer's count increments; all future watch bonuses (10%) credited to referrer

### Withdrawal Rules
- Enforced in `request_withdrawal` view:
  - Check `profile.referrals_count >= 7`
  - Check `profile.balance >= amount`
  - Max $50 per request
- Admin approves via `/admin/` with action button
- Approval debits user's wallet and sets status="approved"

### Stripe Webhook
- Endpoint: `/stripe/webhook/`
- Expects `payment_intent.succeeded` event
- Marks `Deposit.success=True` and credits user's wallet
- **TODO for production**: Verify webhook signature using `settings.STRIPE_WEBHOOK_SECRET`

## Next Steps for Production

1. **Stripe.js integration**: Add client-side payment UI in deposit form
2. **Webhook signature verification**: Use `stripe.Webhook.construct_event()` with secret
3. **Email notifications**: Integrate SendGrid or AWS SES for withdrawal approvals
4. **Robust watch verification**: Add server-side heartbeat check + duration validation
5. **Rate limiting**: Prevent abuse of watch_complete endpoint (e.g., Django Ratelimit)
6. **Tailwind build**: Replace CDN with production Tailwind build
7. **Env variables**: Move secrets to `.env` or Docker compose
8. **Tests**: Add integration tests for withdrawal flow, Stripe webhooks
9. **Admin actions**: Add more admin actions (bulk video creation, deposit monitoring)

## Support

For issues or questions, see the code comments and admin panel help text.

Happy earning! 🚀
