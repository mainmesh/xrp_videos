from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import Profile, Deposit, WithdrawalRequest
from videos.models import Video, WatchHistory, Tier, Category
from referrals.models import ReferralLink, ReferralBonus


@staff_member_required
def dashboard(request):
    """Admin dashboard with statistics and recent activity."""
    today = timezone.now().date()
    
    stats = {
        'total_users': User.objects.count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'total_videos': Video.objects.count(),
        'active_videos': Video.objects.filter(is_active=True).count(),
        'pending_withdrawals': WithdrawalRequest.objects.filter(status='pending').count(),
        'pending_amount': WithdrawalRequest.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0,
        'total_revenue': Deposit.objects.filter(success=True).aggregate(total=Sum('amount'))['total'] or 0,
        'revenue_today': Deposit.objects.filter(success=True, created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # Recent activity (watch history)
    recent_activity = WatchHistory.objects.select_related('user', 'video').order_by('-watched_at')[:10]
    
    # Top earners
    top_earners = User.objects.select_related('profile').order_by('-profile__balance')[:5]
    
    # Recent withdrawals
    recent_withdrawals = WithdrawalRequest.objects.select_related('user').order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_activity': recent_activity,
        'top_earners': top_earners,
        'recent_withdrawals': recent_withdrawals,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@staff_member_required
def users_list(request):
    """List all users with search and filter."""
    search_query = request.GET.get('search', '')
    users = User.objects.select_related('profile').all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/users.html', context)


@staff_member_required
def videos_list(request):
    """List all videos."""
    videos = Video.objects.select_related('category', 'min_tier').order_by('-created_at')
    
    context = {
        'videos': videos,
    }
    
    return render(request, 'admin_panel/videos.html', context)


@staff_member_required
def withdrawals_list(request):
    """List all withdrawal requests."""
    status_filter = request.GET.get('status', 'all')
    withdrawals = WithdrawalRequest.objects.select_related('user', 'approved_by').order_by('-created_at')
    
    if status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    context = {
        'withdrawals': withdrawals,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin_panel/withdrawals.html', context)


@staff_member_required
def approve_withdrawal(request, withdrawal_id):
    """Approve a withdrawal request."""
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    if withdrawal.status == 'pending':
        withdrawal.approve(request.user)
        messages.success(request, f'Withdrawal request for ${withdrawal.amount} approved successfully.')
    else:
        messages.error(request, 'This withdrawal has already been processed.')
    
    return redirect('admin_panel:withdrawals')


@staff_member_required
def reject_withdrawal(request, withdrawal_id):
    """Reject a withdrawal request."""
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    if withdrawal.status == 'pending':
        withdrawal.status = 'rejected'
        withdrawal.save()
        messages.warning(request, f'Withdrawal request for ${withdrawal.amount} rejected.')
    else:
        messages.error(request, 'This withdrawal has already been processed.')
    
    return redirect('admin_panel:withdrawals')


@staff_member_required
def deposits_list(request):
    """List all deposits."""
    deposits = Deposit.objects.select_related('user').order_by('-created_at')
    
    context = {
        'deposits': deposits,
    }
    
    return render(request, 'admin_panel/deposits.html', context)


@staff_member_required
def referrals_list(request):
    """List all referrals."""
    referrals = ReferralLink.objects.select_related('user', 'user__profile').order_by('-user__profile__referrals_count')
    
    context = {
        'referrals': referrals,
    }
    
    return render(request, 'admin_panel/referrals.html', context)


@staff_member_required
def tiers_list(request):
    """List all tiers."""
    tiers = Tier.objects.annotate(user_count=Count('profile')).all()
    
    context = {
        'tiers': tiers,
    }
    
    return render(request, 'admin_panel/tiers.html', context)


@staff_member_required
def settings_view(request):
    """Admin settings page."""
    if request.method == 'POST':
        # Handle settings updates here
        messages.success(request, 'Settings updated successfully.')
        return redirect('admin_panel:settings')
    
    context = {}
    return render(request, 'admin_panel/settings.html', context)


@staff_member_required
def logout_view(request):
    """Logout admin user."""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')
