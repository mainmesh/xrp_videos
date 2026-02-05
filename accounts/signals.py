from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """Send welcome email to newly registered users."""
    if created:
        try:
            subject = 'Welcome to XRPPrime - Start Earning Today!'
            
            # Create email content
            message = f"""
Hello {instance.username}!

Welcome to XRPPrime - Where Entertainment Meets Earnings! 🎉

We're thrilled to have you join our community. Your account has been successfully created and you're ready to start earning while watching amazing videos.

Here's what you can do now:
✅ Watch videos and earn rewards
✅ Refer friends and get bonuses
✅ Upgrade your tier for higher earnings
✅ Withdraw your earnings anytime

Get started now: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'xrpprime.com'}

If you have any questions or need assistance, feel free to reach out to our support team.

Happy watching and earning!

Best regards,
The XRPPrime Team

--
XRPPrime - Earn While You Watch
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True,  # Don't raise error if email fails
            )
        except Exception as e:
            # Log error but don't prevent user registration
            print(f"Failed to send welcome email to {instance.email}: {str(e)}")


# Import models here to avoid circular imports
def get_deposit_model():
    from .models import Deposit
    return Deposit


def get_withdrawal_model():
    from .models import WithdrawalRequest
    return WithdrawalRequest


@receiver(post_save, sender='accounts.Deposit')
def send_deposit_confirmation(sender, instance, **kwargs):
    """Send email when deposit is confirmed."""
    # Only send if deposit was just marked successful
    if instance.success and kwargs.get('update_fields') and 'success' in kwargs.get('update_fields', []):
        try:
            subject = 'Deposit Confirmed - XRPPrime'
            message = f"""
Hello {instance.user.username}!

Great news! Your deposit has been confirmed. 💰

Deposit Details:
• Amount: ${instance.amount}
• Transaction ID: {instance.id}
• Date: {instance.created_at.strftime('%B %d, %Y at %I:%M %p')}

Your new balance is now available for use. You can start watching videos or upgrade your tier for higher earnings.

Thank you for choosing XRPPrime!

Best regards,
The XRPPrime Team

--
XRPPrime - Earn While You Watch
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send deposit confirmation to {instance.user.email}: {str(e)}")


@receiver(post_save, sender='accounts.WithdrawalRequest')
def send_withdrawal_notification(sender, instance, created, **kwargs):
    """Send email when withdrawal request is created or processed."""
    try:
        if created:
            # Withdrawal request submitted
            subject = 'Withdrawal Request Received - XRPPrime'
            message = f"""
Hello {instance.user.username}!

We've received your withdrawal request. 📤

Withdrawal Details:
• Amount: ${instance.amount}
• Method: {instance.method}
• Status: Pending Review
• Request ID: {instance.id}
• Date: {instance.created_at.strftime('%B %d, %Y at %I:%M %p')}

Your request is being processed and will be reviewed shortly. We'll send you another email once it's completed.

Processing typically takes 1-3 business days.

Best regards,
The XRPPrime Team

--
XRPPrime - Earn While You Watch
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                fail_silently=True,
            )
        
        elif instance.status == 'completed':
            # Withdrawal completed
            subject = 'Withdrawal Completed - XRPPrime'
            message = f"""
Hello {instance.user.username}!

Great news! Your withdrawal has been processed successfully. ✅

Withdrawal Details:
• Amount: ${instance.amount}
• Method: {instance.method}
• Request ID: {instance.id}
• Completed: {instance.updated_at.strftime('%B %d, %Y at %I:%M %p')}

The funds should arrive in your account within the standard processing time for {instance.method}.

Thank you for being part of XRPPrime!

Best regards,
The XRPPrime Team

--
XRPPrime - Earn While You Watch
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                fail_silently=True,
            )
    except Exception as e:
        print(f"Failed to send withdrawal notification to {instance.user.email}: {str(e)}")

