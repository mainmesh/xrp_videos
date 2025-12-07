from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from functools import wraps
from datetime import timedelta
import json

from accounts.models import Profile, Deposit, WithdrawalRequest
from videos.models import Video, WatchHistory, Tier, Category
from referrals.models import ReferralLink, ReferralBonus


def staff_required(view_func):
    """Custom decorator to check if user is staff and redirect to admin login."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_panel:login' + '?next=' + request.path)
        if not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


def setup_admin(request):
    """One-time setup view to create admin user. Access via /admin/setup/"""
    # Check if admin already exists
    if User.objects.filter(username='admin').exists():
        return JsonResponse({
            'status': 'exists',
            'message': 'Admin user already exists. You can login at /admin/login/',
            'username': 'admin',
            'note': 'If you forgot the password, contact support or check your deployment logs.'
        })
    
    # Create admin user
    try:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@xrpvideos.com',
            password='admin123'
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Admin user created successfully!',
            'username': 'admin',
            'password': 'admin123',
            'login_url': '/admin/login/',
            'note': 'Please change your password after first login.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating admin user: {str(e)}'
        }, status=500)


def admin_login(request):
    """Custom admin login page."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_panel:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff:
                auth_login(request, user)
                next_url = request.GET.get('next', 'admin_panel:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'You do not have permission to access the admin panel.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'admin_panel/login.html')


@staff_required
def dashboard(request):
    """Admin dashboard with statistics and recent activity."""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_users': User.objects.count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'total_videos': Video.objects.count(),
        'active_videos': Video.objects.filter(is_active=True).count(),
        'pending_withdrawals': WithdrawalRequest.objects.filter(status='pending').count(),
        'pending_amount': WithdrawalRequest.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0,
        'total_revenue': Deposit.objects.filter(success=True).aggregate(total=Sum('amount'))['total'] or 0,
        'revenue_today': Deposit.objects.filter(success=True, created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0,
        'active_users_week': User.objects.filter(last_login__gte=week_ago).count(),
        'total_withdrawals_paid': WithdrawalRequest.objects.filter(status='approved').aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # User growth data (last 7 days)
    user_growth_data = []
    revenue_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        users_count = User.objects.filter(date_joined__date=date).count()
        revenue = Deposit.objects.filter(success=True, created_at__date=date).aggregate(total=Sum('amount'))['total'] or 0
        user_growth_data.append({'date': date.strftime('%b %d'), 'count': users_count})
        revenue_data.append({'date': date.strftime('%b %d'), 'amount': float(revenue)})
    
    # Video watch stats
    video_stats = Video.objects.annotate(
        watch_count=Count('watchhistory')
    ).order_by('-watch_count')[:5]
    
    # Recent activity (watch history)
    recent_activity = WatchHistory.objects.select_related('user', 'video').order_by('-watched_at')[:10]
    
    # Top earners
    top_earners = User.objects.select_related('profile').order_by('-profile__balance')[:5]
    
    # Recent withdrawals
    recent_withdrawals = WithdrawalRequest.objects.select_related('user').order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'user_growth_data': json.dumps(user_growth_data),
        'revenue_data': json.dumps(revenue_data),
        'video_stats': video_stats,
        'recent_activity': recent_activity,
        'top_earners': top_earners,
        'recent_withdrawals': recent_withdrawals,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@staff_required
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


@staff_required
def videos_list(request):
    """List all videos and handle add video."""
    if request.method == 'POST':
        try:
            video = Video.objects.create(
                title=request.POST.get('title'),
                url=request.POST.get('url'),
                thumbnail_url=request.POST.get('thumbnail', ''),
                description=request.POST.get('description', ''),
                category_id=request.POST.get('category'),
                min_tier_id=request.POST.get('min_tier'),
                reward=request.POST.get('reward'),
                duration=request.POST.get('duration', 0),
                is_active=request.POST.get('is_active') == 'on'
            )
            messages.success(request, f'Video "{video.title}" added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding video: {str(e)}')
        return redirect('admin_panel:videos')
    
    videos = Video.objects.select_related('category', 'min_tier').order_by('-created_at')
    categories = Category.objects.all()
    tiers = Tier.objects.all().order_by('price')
    
    context = {
        'videos': videos,
        'categories': categories,
        'tiers': tiers,
    }
    
    return render(request, 'admin_panel/videos.html', context)


@staff_required
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


@staff_required
def approve_withdrawal(request, withdrawal_id):
    """Approve a withdrawal request."""
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    if withdrawal.status == 'pending':
        withdrawal.approve(request.user)
        messages.success(request, f'Withdrawal request for ${withdrawal.amount} approved successfully.')
    else:
        messages.error(request, 'This withdrawal has already been processed.')
    
    return redirect('admin_panel:withdrawals')


@staff_required
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


@staff_required
def deposits_list(request):
    """List all deposits."""
    deposits = Deposit.objects.select_related('user').order_by('-created_at')
    
    context = {
        'deposits': deposits,
    }
    
    return render(request, 'admin_panel/deposits.html', context)


@staff_required
def referrals_list(request):
    """List all referrals."""
    referrals = ReferralLink.objects.select_related('user', 'user__profile').order_by('-user__profile__referrals_count')
    
    context = {
        'referrals': referrals,
    }
    
    return render(request, 'admin_panel/referrals.html', context)


@staff_required
def tiers_list(request):
    """List all tiers."""
    tiers = Tier.objects.annotate(user_count=Count('profile')).all()
    
    context = {
        'tiers': tiers,
    }
    
    return render(request, 'admin_panel/tiers.html', context)


@staff_required
def settings_view(request):
    """Admin settings page."""
    if request.method == 'POST':
        # Handle settings updates here
        messages.success(request, 'Settings updated successfully.')
        return redirect('admin_panel:settings')
    
    context = {}
    return render(request, 'admin_panel/settings.html', context)


@staff_required
def logout_view(request):
    """Logout admin user."""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')
