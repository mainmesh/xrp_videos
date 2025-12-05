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
            # Auto-create referral link for new user
            code = str(uuid.uuid4())[:8].upper()
            ReferralLink.objects.create(user=user, code=code)
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
def notifications(request):
    """Display user notifications."""
    return render(request, "accounts/notifications.html")


@login_required
def settings(request):
    """Display account settings page."""
    return render(request, "accounts/settings.html")


@login_required
def update_profile(request):
    """Update user profile information."""
    if request.method == "POST":
        user = request.user
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
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
            messages.error(request, "Please correct the errors below.")
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

