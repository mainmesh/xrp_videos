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
            
            # AI-powered response logic (using simple FAQ for now)
            response = get_chatbot_response(user_message)
            
            # Save chat history
            chat = ChatMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                message=user_message,
                response=response
            )
            
            return JsonResponse({
                'response': response,
                'session_id': session_id
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_chatbot_response(message):
    """Generate chatbot response based on message."""
    message_lower = message.lower()
    
    # FAQ responses
    if 'deposit' in message_lower or 'add money' in message_lower:
        return "To deposit funds, go to your dashboard and click the 'Deposit' button. You can deposit via cryptocurrency or bank transfer."
    
    elif 'withdraw' in message_lower or 'cash out' in message_lower:
        return "To withdraw earnings, navigate to your dashboard and click 'Withdraw'. Minimum withdrawal is $10. Withdrawals are processed within 24-48 hours."
    
    elif 'tier' in message_lower or 'upgrade' in message_lower:
        return "We have 3 tiers: Bronze ($10), Silver ($50), and Gold ($100). Higher tiers unlock more videos and higher rewards per watch. Visit the Tiers page to learn more."
    
    elif 'video' in message_lower or 'watch' in message_lower:
        return "Watch videos from the Videos page. You earn rewards based on your tier level. Each video can be watched once per day for rewards."
    
    elif 'referral' in message_lower or 'refer' in message_lower:
        return "Share your unique referral link to earn 10% of your referrals' earnings! Find your referral link in the Referral Stats section of your dashboard."
    
    elif 'support' in message_lower or 'help' in message_lower or 'contact' in message_lower:
        return "Need help? Check your inbox for messages from admins, or compose a new message to contact support directly."
    
    elif 'hello' in message_lower or 'hi' in message_lower or 'hey' in message_lower:
        return "Hello! I'm here to help you with any questions about XRP Videos. Ask me about deposits, withdrawals, tiers, videos, or referrals!"
    
    elif 'balance' in message_lower or 'earnings' in message_lower:
        return "You can check your current balance and earnings history in your dashboard. Your balance updates automatically after watching videos."
    
    else:
        return "I'm here to help! You can ask me about: deposits, withdrawals, tiers, watching videos, referrals, or general support. What would you like to know?"
