from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Profile, Deposit, WithdrawalRequest
from django.contrib.auth.models import User
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from referrals.models import ReferralLink
import stripe
from django.conf import settings
import uuid
import re
from .models import PaymentAttempt
from admin_panel.models import PaymentOption
from django.utils import timezone


stripe.api_key = settings.STRIPE_API_KEY


def placeholder_deposit(request):
    """Placeholder deposit view. In production, integrate Stripe payment flow."""
    from videos.models import Tier
    
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "login_required"}, status=401)
        
        amount = float(request.POST.get("amount", 0))
        deposit = Deposit.objects.create(user=request.user, amount=amount)
        
        # Determine tier based on deposit amount
        try:
            tier = Tier.objects.filter(price__lte=amount).order_by('-price').first()
            if tier:
                request.user.profile.current_tier = tier
                request.user.profile.credit(amount, reason="deposit")  # Add to wallet
                request.user.profile.save()
        except Exception:
            pass
        
        # Return success with tier info
        return JsonResponse({
            "status": "created",
            "deposit_id": deposit.id,
            "tier_upgraded": request.user.profile.current_tier.name if request.user.profile.current_tier else None
        })
    
    tiers = Tier.objects.all().order_by('price')
    return render(request, "accounts/deposit_placeholder.html", {"tiers": tiers})


def get_exchange_rates():
    """Fetch current exchange rates from API. Falls back to hardcoded rates if API fails."""
    import requests
    from django.core.cache import cache
    
    # Check cache first (cache for 1 hour)
    cached_rates = cache.get('exchange_rates')
    if cached_rates:
        return cached_rates
    
    # Hardcoded fallback rates
    fallback_rates = {
        'KES': 100,    # 1 USD = 100 KES
        'TZS': 2300,   # 1 USD = 2300 TZS
    }
    
    try:
        # Using exchangerate-api.com (free tier)
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if response.status_code == 200:
            data = response.json()
            rates = {
                'KES': data['rates'].get('KES', fallback_rates['KES']),
                'TZS': data['rates'].get('TZS', fallback_rates['TZS']),
            }
            # Cache for 1 hour
            cache.set('exchange_rates', rates, 3600)
            return rates
    except Exception:
        pass
    
    return fallback_rates


@login_required
def deposit_mpesa(request):
    """Allow users to submit MPesa/SMS payment messages for verification.

    Basic behavior:
    - User fills amount, selects country (KE/TZ), provides phone used and raw MPesa message.
    - Server attempts a simple parse/verification; if it finds a matching amount and transaction id, it marks verified and credits user.
    - Otherwise the attempt remains pending for manual review.
    """
    if request.method == 'POST':
        amount = request.POST.get('amount')
        country = request.POST.get('country')
        phone = request.POST.get('phone')
        message = request.POST.get('message', '')

        try:
            amount_val = float(amount)
        except Exception:
            messages.error(request, "Invalid amount")
            return redirect('accounts:deposit')

        pa = PaymentAttempt.objects.create(
            user=request.user,
            amount=amount_val,
            country=(country or '').upper(),
            phone=phone,
            raw_message=message,
        )

        # Attempt automatic verification via simple heuristics
        verified = False
        note = []

        # Get exchange rate to convert USD to local currency
        exchange_rates = get_exchange_rates()
        country_code = (country or '').upper()
        expected_local_amount = None
        
        if country_code == 'KE':
            expected_local_amount = amount_val * exchange_rates['KES']
        elif country_code == 'TZ':
            expected_local_amount = amount_val * exchange_rates['TZS']

        # Extract an amount from the message
        amt_match = re.search(r"(?:KES|TZS|UGX|USD|Ksh|TSh|TZS|KES)?\s*([0-9,.]+)", message, re.IGNORECASE)
        if amt_match:
            amt_str = amt_match.group(1).replace(',', '')
            try:
                parsed_amt = float(amt_str)
                
                # Compare with expected local currency amount if available
                if expected_local_amount:
                    # Allow 5% discrepancy for exchange rate fluctuations and fees
                    tolerance = max(100, expected_local_amount * 0.05)
                    if abs(parsed_amt - expected_local_amount) <= tolerance:
                        verified = True
                        note.append(f"Message amount {parsed_amt} matches expected {expected_local_amount:.2f} ({country_code})")
                    else:
                        note.append(f"Message amount {parsed_amt} differs from expected {expected_local_amount:.2f} ({country_code})")
                else:
                    # Fallback: compare with USD amount directly (for backwards compatibility)
                    if abs(parsed_amt - amount_val) <= max(1.0, 0.02 * amount_val):
                        verified = True
                        note.append(f"Message amount {parsed_amt} matches submitted {amount_val}")
                    else:
                        note.append(f"Message amount {parsed_amt} differs from submitted {amount_val}")
            except Exception:
                pass

        # Look for a transaction code token (alphanumeric, length 6-12)
        tx_match = re.search(r"([A-Z0-9]{6,12})", message)
        if tx_match:
            note.append(f"Found tx id {tx_match.group(1)}")

        # If heuristics pass, mark verified and credit
        if verified:
            pa.mark_verified(verifier_note='; '.join(note))
            
            # Auto-upgrade tier based on total balance
            try:
                from videos.models import Tier
                profile = request.user.profile
                profile.refresh_from_db()  # Get updated balance
                
                # Find highest tier user qualifies for based on balance
                tier = Tier.objects.filter(price__lte=profile.balance).order_by('-price').first()
                if tier and (not profile.current_tier or tier.price > profile.current_tier.price):
                    profile.current_tier = tier
                    profile.save()
                    messages.success(request, f"✅ Payment verified! ${amount_val:.2f} credited. Upgraded to {tier.name} tier!")
                else:
                    messages.success(request, f"✅ Payment verified! ${amount_val:.2f} credited to your wallet.")
            except Exception:
                messages.success(request, f"✅ Payment verified! ${amount_val:.2f} credited to your wallet.")
        else:
            pa.verifier_note = '; '.join(note)
            pa.save()
            messages.info(request, "📋 Payment submitted for verification. Our team will review it within 24 hours and you'll receive a notification once it's processed.")

        return redirect('accounts:dashboard')

    # GET -> show a small MPesa submission form with current exchange rates
    exchange_rates = get_exchange_rates()
    return render(request, 'accounts/deposit_mpesa.html', {
        'exchange_rates': exchange_rates
    })


@require_http_methods(["POST"])
def mpesa_webhook(request):
    """Webhook endpoint for payment provider/aggregator to confirm transactions.

    Expected JSON body: {"tx_id": "ABC123", "amount": 50.0, "phone": "079...", "country": "KE"}
    A header `X-MPESA-WEBHOOK-SECRET` must match settings.MPESA_WEBHOOK_SECRET.
    If a matching pending PaymentAttempt exists (same amount, phone or tx id in raw_message), it will be marked verified.
    """
    import json
    from django.conf import settings

    secret = request.META.get('HTTP_X_MPESA_WEBHOOK_SECRET') or request.META.get('HTTP_X_MPESA_SECRET')
    expected = getattr(settings, 'MPESA_WEBHOOK_SECRET', None)
    if expected and (not secret or secret != expected):
        return JsonResponse({"error": "unauthorized"}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "invalid_json"}, status=400)

    tx_id = (payload.get('tx_id') or '').strip()
    amount = payload.get('amount')
    phone = (payload.get('phone') or '').strip()
    country = (payload.get('country') or '').strip().upper()

    # Find matching pending PaymentAttempt
    candidates = PaymentAttempt.objects.filter(status='pending')

    matched = None
    # match by tx id in raw_message
    if tx_id:
        candidates = candidates.filter(raw_message__icontains=tx_id)
        matched = candidates.first()

    # fallback: match by phone and approximate amount
    if not matched and phone:
        cand2 = PaymentAttempt.objects.filter(status='pending', phone__icontains=phone)
        for pa in cand2:
            try:
                if abs(float(pa.amount) - float(amount)) <= max(1.0, 0.02 * float(amount)):
                    matched = pa
                    break
            except Exception:
                continue

    if not matched and amount is not None:
        # try matching by amount alone (last recent)
        try:
            amt = float(amount)
            cand3 = PaymentAttempt.objects.filter(status='pending').order_by('-created_at')
            for pa in cand3:
                if abs(float(pa.amount) - amt) <= max(1.0, 0.02 * amt):
                    matched = pa
                    break
        except Exception:
            pass

    if not matched:
        return JsonResponse({"status": "no_match"}, status=200)

    # Mark verified
    matched.mark_verified(verifier_note=f"Webhook verified tx:{tx_id} phone:{phone}")
    return JsonResponse({"status": "verified", "payment_attempt_id": matched.id})


@login_required
def dashboard(request):
    profile = request.user.profile
    withdrawals = WithdrawalRequest.objects.filter(user=request.user).order_by("-created_at")[:10]
    referral_link = ReferralLink.objects.filter(user=request.user).first()
    context = {"profile": profile, "withdrawals": withdrawals, "referral_link": referral_link}
    return render(request, "accounts/dashboard.html", context)


@login_required
def request_withdrawal(request):
    profile = request.user.profile
    if request.method == "POST":
        amount = float(request.POST.get("amount", 0))
        # Check eligibility: 7 referrals minimum
        if profile.referrals_count < 7:
            return JsonResponse({"error": f"Need {7 - profile.referrals_count} more referrals"}, status=400)
        # Max $50 per withdrawal and balance check
        if amount <= 0 or amount > 50:
            return JsonResponse({"error": "invalid_amount"}, status=400)
        if profile.balance < amount:
            return JsonResponse({"error": "insufficient_balance"}, status=400)
        w = WithdrawalRequest.objects.create(user=request.user, amount=amount)
        return redirect("accounts:dashboard")
    return render(request, "accounts/withdrawal_form.html", {"profile": profile})


def register(request):
    """Simple registration view that links referral if present in session."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Note: Profile and ReferralLink are auto-created by signals
            
            # attach referral if exists
            ref_code = request.session.pop('referral_code', None)
            if ref_code:
                try:
                    rl = ReferralLink.objects.get(code=ref_code)
                    user.profile.referred_by = rl.user
                    user.profile.save()
                    # increment referrer's count
                    try:
                        ref_profile = rl.user.profile
                        ref_profile.referrals_count = (ref_profile.referrals_count or 0) + 1
                        ref_profile.save()
                    except Exception:
                        pass
                except ReferralLink.DoesNotExist:
                    pass
            login(request, user)
            return redirect('accounts:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def create_payment_intent(request):
    """Create a Stripe PaymentIntent for a deposit."""
    try:
        amount = int(float(request.POST.get("amount", 0)) * 100)  # cents
        if amount <= 0:
            return JsonResponse({"error": "invalid_amount"}, status=400)
        
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={"user_id": request.user.id}
        )
        
        # Record deposit in DB
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount / 100,
            stripe_payment_intent=intent['id']
        )
        
        return JsonResponse({"client_secret": intent['client_secret'], "deposit_id": deposit.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
def stripe_webhook(request):
    """Handle Stripe webhook to mark deposits as successful."""
    from videos.models import Tier
    import json
    try:
        event_json = json.loads(request.body)
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        # In production, verify signature:
        # event = stripe.Webhook.construct_event(request.body, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        # For now, just process it (NOT SECURE for production)
        event = event_json
        
        if event['type'] == 'payment_intent.succeeded':
            pi = event['data']['object']
            try:
                deposit = Deposit.objects.get(stripe_payment_intent=pi['id'])
                deposit.success = True
                deposit.save()
                # Credit user's wallet with deposit amount
                user = deposit.user
                user.profile.credit(deposit.amount, reason="deposit")
                
                # Upgrade tier based on deposit amount
                tier = Tier.objects.filter(price__lte=deposit.amount).order_by('-price').first()
                if tier:
                    user.profile.current_tier = tier
                    user.profile.save()
            except Deposit.DoesNotExist:
                pass
        
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
@login_required
def transaction_history(request):
    """Display user's transaction history."""
    from .models import Transaction
    from django.core.paginator import Paginator
    
    # Get all transactions for this user
    transactions = Transaction.objects.filter(user=request.user).select_related('tier', 'video')
    
    # Filter by type if requested
    transaction_type = request.GET.get('type')
    if transaction_type and transaction_type != 'all':
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Pagination
    paginator = Paginator(transactions, 20)  # 20 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get transaction type counts for filter buttons
    type_counts = {
        'all': Transaction.objects.filter(user=request.user).count(),
        'tier_upgrade': Transaction.objects.filter(user=request.user, transaction_type='tier_upgrade').count(),
        'video_reward': Transaction.objects.filter(user=request.user, transaction_type='video_reward').count(),
        'deposit': Transaction.objects.filter(user=request.user, transaction_type='deposit').count(),
        'withdrawal': Transaction.objects.filter(user=request.user, transaction_type='withdrawal').count(),
        'referral_bonus': Transaction.objects.filter(user=request.user, transaction_type='referral_bonus').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'current_type': transaction_type or 'all',
        'type_counts': type_counts,
        'profile': request.user.profile,
    }
    return render(request, "accounts/transactions.html", context)


@login_required
def profile(request):
    """User profile page (redirect target after login)."""
    profile = request.user.profile
    referral_link = None
    try:
        from referrals.models import ReferralLink
        referral_link = ReferralLink.objects.filter(user=request.user).first()
    except Exception:
        referral_link = None
    context = {
        'user': request.user,
        'profile': profile,
        'referral_link': referral_link,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def settings(request):
    """Display account settings page."""
    password_form = PasswordChangeForm(request.user)
    context = {
        'password_form': password_form,
        'user': request.user,
    }
    return render(request, "accounts/settings.html", context)


@login_required
def update_profile(request):
    """Update user profile information."""
    if request.method == "POST":
        user = request.user
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        
        # Validation
        if not username or not email:
            messages.error(request, "Username and email are required.")
            return redirect("accounts:settings")
        
        # Check if username is taken by another user
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Username already taken.")
            return redirect("accounts:settings")
        
        # Check if email is taken by another user
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already in use.")
            return redirect("accounts:settings")
        
        user.username = username
        user.email = email
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("accounts:settings")
    return redirect("accounts:settings")


@login_required
def change_password(request):
    """Change user password."""
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect("accounts:settings")
        else:
            # Display specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect("accounts:settings")
    return redirect("accounts:settings")


@login_required
def delete_account(request):
    """Delete user account."""
    if request.method == "POST":
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect("home")
    return redirect("accounts:settings")


@login_required
def upgrade_tier(request, tier_id):
    """Upgrade user's tier using account balance."""
    from videos.models import Tier
    from core.models import Message
    
    tier = get_object_or_404(Tier, id=tier_id)
    profile = request.user.profile
    
    if request.method == "POST":
        # Check if user already has this tier or higher
        if profile.current_tier and profile.current_tier.price >= tier.price:
            messages.warning(request, f"⚠️ You already have {profile.current_tier.name} tier or higher! You can't downgrade or re-purchase the same tier.")
            Message.objects.create(
                receiver=request.user,
                message_type="message",
                content=f"Tier upgrade failed: You already have {profile.current_tier.name} tier (${profile.current_tier.price:.2f}) which is equal or higher than {tier.name} (${tier.price:.2f})."
            )
            return redirect("accounts:dashboard")
        
        # Check if user has sufficient balance
        if profile.balance < tier.price:
            shortfall = tier.price - profile.balance
            messages.error(request, f"💳 Insufficient balance. You need ${tier.price:.2f} but have ${profile.balance:.2f}. Please deposit ${shortfall:.2f} more.")
            Message.objects.create(
                receiver=request.user,
                message_type="message",
                content=f"Tier upgrade failed: Insufficient balance. You need ${tier.price:.2f} for {tier.name} tier but your current balance is ${profile.balance:.2f}. Please deposit ${shortfall:.2f} to proceed."
            )
            return redirect("accounts:deposit")
        
        # Deduct balance and upgrade tier
        if profile.debit(tier.price, reason=f"Upgrade to {tier.name} tier", transaction_type="tier_upgrade", tier=tier):
            old_tier = profile.current_tier.name if profile.current_tier else "No Tier"
            profile.current_tier = tier
            profile.save()
            
            # Success messages and notification
            messages.success(request, f"🎉 Successfully upgraded from {old_tier} to {tier.name} tier! ${tier.price:.2f} has been deducted from your account.")
            Message.objects.create(
                receiver=request.user,
                message_type="reward",
                content=f"🎉 Tier Upgrade Successful! You've been upgraded from {old_tier} to {tier.name} tier. ${tier.price:.2f} was deducted from your account. New balance: ${profile.balance:.2f}"
            )
            return redirect("accounts:dashboard")
        else:
            messages.error(request, "❌ Failed to process upgrade. Transaction error occurred. Please contact support if this persists.")
            Message.objects.create(
                receiver=request.user,
                message_type="message",
                content=f"Tier upgrade transaction failed for {tier.name} tier. Please contact support if you continue experiencing issues."
            )
            return redirect("accounts:dashboard")
    
    # GET request - show confirmation page
    from videos.models import Tier
    all_tiers = Tier.objects.all().order_by('price')
    
    context = {
        'tier': tier,
        'profile': profile,
        'all_tiers': all_tiers,
        'has_sufficient_balance': profile.balance >= tier.price,
    }
    return render(request, "accounts/upgrade_tier.html", context)

