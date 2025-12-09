from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Message, ChatMessage, Announcement
import json
import uuid


def home(request):
    announcements = Announcement.objects.filter(is_active=True)[:3]
    return render(request, 'home.html', {'announcements': announcements})


def about(request):
    return render(request, 'about.html')


def tiers(request):
    return render(request, 'tiers.html')


@login_required
def inbox(request):
    """User inbox for messages."""
    messages = Message.objects.filter(receiver=request.user)
    unread_count = messages.filter(is_read=False).count()
    return render(request, 'core/inbox.html', {
        'messages': messages,
        'unread_count': unread_count
    })


@login_required
def view_message(request, message_id):
    """View a specific message."""
    message = Message.objects.get(id=message_id, receiver=request.user)
    message.is_read = True
    message.save()
    return render(request, 'core/message_detail.html', {'message': message})


@login_required
def compose_message(request):
    """Reply to admin message."""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        # Send to all staff users
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Message.objects.create(
                sender=request.user,
                receiver=admin,
                subject=subject,
                message=message_text
            )
        
        return redirect('inbox')
    
    return render(request, 'core/compose.html')


@csrf_exempt
def chatbot(request):
    """AI chatbot endpoint."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            # Get user context
            user_context = None
            if request.user.is_authenticated:
                profile = request.user.profile
                user_context = {
                    'balance': float(profile.balance),
                    'tier': profile.current_tier.name if profile.current_tier else 'Bronze',
                    'tier_price': float(profile.current_tier.price) if profile.current_tier else 0.0,
                    'username': request.user.username,
                    'videos_watched': WatchHistory.objects.filter(user=request.user).count(),
                    'referrals': request.user.referred_users.count() if hasattr(request.user, 'referred_users') else 0
                }
            
            # AI-powered response logic
            response = get_chatbot_response(user_message, user_context)
            
            # Save chat history
            chat = ChatMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                message=user_message,
                response=response
            )
            
            return JsonResponse({
                'response': response,
                'session_id': session_id,
                'timestamp': chat.created_at.isoformat(),
                'user_context': user_context
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_chatbot_response(message, user_context=None):
    """Generate chatbot response based on message with user context."""
    message_lower = message.lower().strip()
    
    # Command shortcuts
    if message_lower in ['/balance', '/bal', '/money']:
        if user_context:
            return f"💰 **Your Current Balance**\n\nBalance: **${user_context['balance']:.2f}**\nTier: **{user_context['tier']}**\nVideos Watched: **{user_context['videos_watched']}**\n\n[View Dashboard](/accounts/dashboard/)"
        return "💰 Please log in to check your balance. [Login here](/accounts/login/)"
    
    elif message_lower in ['/tiers', '/upgrade', '/tier']:
        tier_info = "🎯 **Membership Tiers**\n\n" \
                   "**Bronze** - FREE\n• Access to Bronze videos\n• Earn $0.50 per video\n\n" \
                   "**Silver** - $50\n• All Bronze benefits\n• Earn $1.00 per video\n• Premium videos\n\n" \
                   "**Gold** - $100\n• All Silver benefits\n• Earn $2.00 per video\n• Exclusive content\n• VIP support\n\n"
        if user_context:
            tier_info += f"Your current tier: **{user_context['tier']}**\n\n[Upgrade Now](/accounts/deposit/)"
        else:
            tier_info += "[View All Tiers](/tiers/) | [Sign Up](/accounts/register/)"
        return tier_info
    
    elif message_lower in ['/referrals', '/refer', '/invite']:
        if user_context:
            return f"👥 **Your Referral Stats**\n\nTotal Referrals: **{user_context['referrals']}**\n\nEarn **10%** of your referrals' earnings!\n\n[Get Referral Link](/referrals/stats/)"
        return "👥 **Referral Program**\n\nEarn 10% commission on all your referrals' earnings!\n\n[Sign up to get started](/accounts/register/)"
    
    elif message_lower in ['/help', '/commands', '/?']:
        return "🤖 **Available Commands**\n\n" \
               "• `/balance` - Check your balance\n" \
               "• `/tiers` - View membership tiers\n" \
               "• `/referrals` - Referral program info\n" \
               "• `/videos` - Browse videos\n" \
               "• `/support` - Contact support\n" \
               "• `/help` - Show this message\n\n" \
               "Or just ask me anything! 😊"
    
    elif message_lower in ['/videos', '/browse', '/watch']:
        if user_context:
            return f"📹 **Video Library**\n\nYou've watched **{user_context['videos_watched']}** videos so far!\n\nYour tier (**{user_context['tier']}**) gives you access to special content.\n\n[Browse Videos](/videos/)"
        return "📹 **Video Library**\n\nWatch videos and earn rewards!\n\n[Browse Videos](/videos/) | [Sign Up](/accounts/register/)"
    
    elif message_lower in ['/support', '/contact', '/admin']:
        return "💬 **Contact Support**\n\nNeed help? Our support team is here for you!\n\n[Send Message](/compose/) | [View Inbox](/inbox/)"
    
    # Natural language processing
    elif 'deposit' in message_lower or 'add money' in message_lower or 'fund' in message_lower:
        if user_context:
            return f"💳 **Deposit Funds**\n\nCurrent Balance: **${user_context['balance']:.2f}**\nCurrent Tier: **{user_context['tier']}**\n\nDeposit to upgrade your tier and unlock premium videos!\n\n**Upgrade Options:**\n• Silver Tier: $50\n• Gold Tier: $100\n\n[Make a Deposit](/accounts/deposit/)"
        return "💳 **Deposit Funds**\n\nDeposit to upgrade your tier and earn more!\n\n[Get Started](/accounts/register/) | [Learn About Tiers](/tiers/)"
    
    elif 'withdraw' in message_lower or 'cash out' in message_lower or 'payout' in message_lower:
        if user_context:
            return f"💵 **Withdrawal**\n\nYour Balance: **${user_context['balance']:.2f}**\n\n**Requirements:**\n• Minimum: $10\n• Processing: 24-48 hours\n• Fee: Small processing fee applies\n\n[Request Withdrawal](/accounts/withdrawal/)"
        return "💵 **Withdrawal Info**\n\n• Minimum withdrawal: $10\n• Processing time: 24-48 hours\n• Secure and reliable\n\n[Sign in to withdraw](/accounts/login/)"
    
    elif 'tier' in message_lower or 'upgrade' in message_lower or 'membership' in message_lower:
        if user_context:
            current = user_context['tier']
            suggestions = []
            if current == 'Bronze':
                suggestions = ['Upgrade to **Silver** ($50) to earn $1.00 per video!', 'Or jump to **Gold** ($100) and earn $2.00 per video!']
            elif current == 'Silver':
                suggestions = ['Upgrade to **Gold** ($100) to earn $2.00 per video and get VIP support!']
            else:
                suggestions = ["You're already at the highest tier! Enjoy exclusive content! 🌟"]
            
            response = f"🎯 **Tier Information**\n\nYour current tier: **{current}**\n\n"
            response += '\n'.join(suggestions)
            response += "\n\n[View All Tiers](/tiers/) | [Upgrade Now](/accounts/deposit/)"
            return response
        return "🎯 **Membership Tiers**\n\nWe have 3 tiers: **Bronze** (Free), **Silver** ($50), and **Gold** ($100).\n\nHigher tiers = More videos + Higher rewards!\n\n[Learn More](/tiers/) | [Sign Up](/accounts/register/)"
    
    elif 'video' in message_lower or 'watch' in message_lower or 'content' in message_lower:
        if user_context:
            return f"📹 **Videos & Rewards**\n\nVideos Watched: **{user_context['videos_watched']}**\nCurrent Tier: **{user_context['tier']}**\n\nEarn rewards by watching videos! Each video can be watched once per day.\n\n[Browse Videos](/videos/)"
        return "📹 **Watch & Earn**\n\nWatch videos and earn money! Rewards vary by tier.\n\n[Start Watching](/videos/) | [Create Account](/accounts/register/)"
    
    elif 'referral' in message_lower or 'refer' in message_lower or 'invite' in message_lower or 'friend' in message_lower:
        if user_context:
            return f"👥 **Referral Program**\n\nYour Referrals: **{user_context['referrals']}**\n\nEarn **10%** of what your referrals make! Share your unique link and grow your passive income.\n\n[Get Your Link](/referrals/stats/) | [View Dashboard](/accounts/dashboard/)"
        return "👥 **Invite & Earn**\n\nRefer friends and earn 10% of their earnings forever!\n\n[Sign Up to Get Link](/accounts/register/)"
    
    elif 'balance' in message_lower or 'earnings' in message_lower or 'money' in message_lower or 'wallet' in message_lower:
        if user_context:
            return f"💰 **Your Earnings**\n\nCurrent Balance: **${user_context['balance']:.2f}**\nVideos Watched: **{user_context['videos_watched']}**\nReferrals: **{user_context['referrals']}**\n\nKeep watching and referring to grow your balance!\n\n[Dashboard](/accounts/dashboard/) | [Withdraw](/accounts/withdrawal/)"
        return "💰 **Track Your Earnings**\n\nView your balance, earnings history, and more in your dashboard!\n\n[Sign In](/accounts/login/) | [Create Account](/accounts/register/)"
    
    elif 'support' in message_lower or 'help' in message_lower or 'contact' in message_lower or 'question' in message_lower:
        return "💬 **We're Here to Help!**\n\nNeed assistance? You can:\n\n• Send us a message through the inbox\n• Check the FAQ section\n• Use quick commands (type `/help`)\n\n[Contact Support](/compose/) | [View FAQ](/about/)"
    
    elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings', 'sup', 'yo']):
        greeting = f"Hello{', ' + user_context['username'] if user_context else ''}! 👋\n\n" if user_context else "Hello! 👋\n\n"
        greeting += "I'm your XRP Videos assistant! I can help you with:\n\n"
        greeting += "💰 Balance & Earnings\n🎯 Tier Upgrades\n📹 Watching Videos\n👥 Referrals\n💬 Support\n\n"
        greeting += "**Quick Commands:** Type `/help` to see all commands, or just ask me anything!"
        return greeting
    
    elif any(word in message_lower for word in ['thank', 'thanks', 'thx', 'appreciate']):
        return "You're very welcome! 😊\n\nIs there anything else I can help you with?\n\nType `/help` for quick commands or ask me anything!"
    
    elif any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'later', 'exit']):
        return "Goodbye! 👋 Feel free to come back anytime you need help.\n\nHappy earning! 💰"
    
    # Default response with personalization
    else:
        response = "🤖 **I'm Here to Help!**\n\n"
        if user_context:
            response += f"Hey **{user_context['username']}**! "
        response += "I can assist you with:\n\n"
        response += "💰 **Deposits & Withdrawals**\n"
        response += "🎯 **Tier Upgrades** (Bronze, Silver, Gold)\n"
        response += "📹 **Watching Videos** & Earning Rewards\n"
        response += "👥 **Referral Program** (Earn 10%!)\n"
        response += "💬 **General Support**\n\n"
        response += "**Quick Tips:**\n"
        response += "• Type `/help` for commands\n"
        response += "• Type `/balance` to check earnings\n"
        response += "• Type `/tiers` to see upgrades\n\n"
        response += "What would you like to know?"
        return response
