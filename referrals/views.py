from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import ReferralLink, ReferralBonus
from accounts.models import Profile


def signup_with_referral(request, code):
    # This is a lightweight placeholder.
    try:
        rl = ReferralLink.objects.get(code=code)
        # store referral code in session to use during registration
        request.session['referral_code'] = code
    except ReferralLink.DoesNotExist:
        pass
    return redirect('accounts:register')


@login_required
def referral_stats(request):
    """Display user's referral stats and earnings."""
    try:
        profile = request.user.profile
        referral_link = ReferralLink.objects.get(user=request.user)
    except (Profile.DoesNotExist, ReferralLink.DoesNotExist):
        referral_link = None
    
    # Get all referral bonuses earned
    bonuses = ReferralBonus.objects.filter(to_user=request.user).order_by('-created_at')
    total_referral_earnings = sum(b.amount for b in bonuses)
    
    # Get referrals (users who signed up with this code)
    referrals = User.objects.filter(profile__referred_by=request.user).select_related('profile')
    
    context = {
        'profile': profile,
        'referral_link': referral_link,
        'referrals': referrals,
        'bonuses': bonuses[:20],  # Last 20 bonuses
        'total_referral_earnings': total_referral_earnings,
        'referrals_count': profile.referrals_count,
    }
    return render(request, 'referrals/stats.html', context)
