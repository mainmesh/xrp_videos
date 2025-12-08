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
from videos.models import Video, WatchHistory, Tier, Category, VideoTierPrice
from referrals.models import ReferralLink, ReferralBonus
from .models import SiteSettings
from core.models import Message, Announcement


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
@staff_required
def videos_list(request):
    """List all videos and handle add video."""
    if request.method == 'POST':
        try:
            # Create video
            video = Video.objects.create(
                title=request.POST.get('title'),
                url=request.POST.get('url', ''),
                thumbnail_url=request.POST.get('thumbnail', ''),
                category_id=request.POST.get('category'),
                duration_seconds=request.POST.get('duration', 0),
                is_active=request.POST.get('is_active') == 'on',
                created_by=request.user
            )
            
            # Handle tier-specific pricing
            tiers = Tier.objects.all()
            tier_added = False
            for tier in tiers:
                tier_checkbox = request.POST.get(f'tier_{tier.id}')
                if tier_checkbox:
                    reward = request.POST.get(f'reward_{tier.id}', 0)
                    VideoTierPrice.objects.create(
                        video=video,
                        tier=tier,
                        reward=float(reward) if reward else 0.0
                    )
                    tier_added = True
            
            # Set minimum tier to the lowest selected tier
            if tier_added:
                lowest_tier = VideoTierPrice.objects.filter(video=video).select_related('tier').order_by('tier__price').first()
                if lowest_tier:
                    video.min_tier = lowest_tier.tier
                    # Set default reward to first tier's reward
                    video.reward = lowest_tier.reward
                    video.save()
            
            messages.success(request, f'Video "{video.title}" added successfully with tier-specific pricing!')
        except Exception as e:
            messages.error(request, f'Error adding video: {str(e)}')
        return redirect('admin_panel:videos')
    
    videos = Video.objects.select_related('category', 'min_tier').prefetch_related('tier_prices__tier').order_by('-created_at')
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
    site_settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        settings_type = request.POST.get('settings_type', 'maintenance')
        
        if settings_type == 'platform':
            # Update all platform settings
            site_settings.site_name = request.POST.get('site_name', site_settings.site_name)
            site_settings.contact_email = request.POST.get('contact_email', site_settings.contact_email)
            site_settings.min_withdrawal_amount = request.POST.get('min_withdrawal_amount', site_settings.min_withdrawal_amount)
            site_settings.min_referrals_for_withdrawal = request.POST.get('min_referrals_for_withdrawal', site_settings.min_referrals_for_withdrawal)
            site_settings.withdrawal_fee_percentage = request.POST.get('withdrawal_fee_percentage', site_settings.withdrawal_fee_percentage)
            site_settings.referral_bonus_percentage = request.POST.get('referral_bonus_percentage', site_settings.referral_bonus_percentage)
            site_settings.default_video_reward = request.POST.get('default_video_reward', site_settings.default_video_reward)
            messages.success(request, 'Platform settings updated successfully.')
        else:
            # Update maintenance mode
            if 'maintenance_mode' in request.POST:
                site_settings.maintenance_mode = True
            else:
                site_settings.maintenance_mode = False
            
            # Update maintenance message if provided
            if 'maintenance_message' in request.POST:
                site_settings.maintenance_message = request.POST.get('maintenance_message')
            
            messages.success(request, 'Maintenance settings updated successfully.')
        
        site_settings.save()
        return redirect('admin_panel:settings')
    
    context = {
        'site_settings': site_settings,
    }
    return render(request, 'admin_panel/settings.html', context)


@staff_required
def logout_view(request):
    """Logout admin user."""
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@staff_required
def messages_list(request):
    """Admin messages inbox."""
    admin_messages = Message.objects.filter(receiver=request.user)
    unread_count = admin_messages.filter(is_read=False).count()
    
    context = {
        'messages': admin_messages,
        'unread_count': unread_count,
    }
    return render(request, 'admin_panel/messages.html', context)


@staff_required
def view_admin_message(request, message_id):
    """View a specific message."""
    message = get_object_or_404(Message, id=message_id, receiver=request.user)
    message.is_read = True
    message.save()
    
    return render(request, 'admin_panel/message_detail.html', {'message': message})


@staff_required
def send_message_to_user(request, user_id):
    """Send message to a specific user."""
    recipient = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        Message.objects.create(
            sender=request.user,
            receiver=recipient,
            subject=subject,
            message=message_text
        )
        
        messages.success(request, f'Message sent to {recipient.username} successfully.')
        return redirect('admin_panel:users')
    
    return render(request, 'admin_panel/send_message.html', {'recipient': recipient})


@staff_required
def announcements_list(request):
    """Manage site-wide announcements."""
    all_announcements = Announcement.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        message_text = request.POST.get('message')
        is_active = 'is_active' in request.POST
        
        Announcement.objects.create(
            title=title,
            message=message_text,
            is_active=is_active,
            created_by=request.user
        )
        
        messages.success(request, 'Announcement created successfully.')
        return redirect('admin_panel:announcements')
    
    context = {
        'announcements': all_announcements,
    }
    return render(request, 'admin_panel/announcements.html', context)


@staff_required
def toggle_announcement(request, announcement_id):
    """Toggle announcement active status."""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.is_active = not announcement.is_active
    announcement.save()
    
    status = 'activated' if announcement.is_active else 'deactivated'
    messages.success(request, f'Announcement {status} successfully.')
    return redirect('admin_panel:announcements')


@staff_required
def delete_announcement(request, announcement_id):
    """Delete an announcement."""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    
    messages.success(request, 'Announcement deleted successfully.')
    return redirect('admin_panel:announcements')
