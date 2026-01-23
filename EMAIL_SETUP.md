# Email Features Setup Guide

This project includes automated email functionality for:
- Password reset requests
- Welcome emails for new users
- (Extensible for other notifications)

## Configuration

### Development Setup (Console Backend)

By default, emails are printed to the console during development. No additional setup needed.

In your `.env` file:
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production Setup (SMTP)

#### Option 1: Gmail

1. Create a Google Account or use an existing one
2. Enable 2-Step Verification in your Google Account
3. Generate an App Password:
   - Go to Google Account → Security → 2-Step Verification → App Passwords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password

4. Update your `.env` file:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=XRPPrime <noreply@xrpprime.com>
```

#### Option 2: SendGrid

1. Sign up at https://sendgrid.com (free tier available)
2. Create an API key from Settings → API Keys
3. Update your `.env` file:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=XRPPrime <noreply@yourdomain.com>
```

#### Option 3: Other SMTP Services

You can use any SMTP service (Mailgun, AWS SES, Postmark, etc.):
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-host
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-username
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=YourApp <noreply@yourdomain.com>
```

## Features

### 1. Password Reset

Users can reset their password via the login page:
- Click "Forgot password?" link
- Enter email address
- Receive reset link via email
- Set new password

URLs:
- `/accounts/password-reset/` - Request reset
- `/accounts/password-reset/done/` - Confirmation page
- `/accounts/password-reset-confirm/<uidb64>/<token>/` - Set new password
- `/accounts/password-reset-complete/` - Success page

### 2. Welcome Emails

Automatically sent when a new user registers:
- Personalized greeting
- Quick start guide
- Platform features overview

This is handled by Django signals in `accounts/signals.py`.

## Testing

### Test Password Reset (Console Backend)

1. Make sure `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` in your `.env`
2. Run the development server
3. Go to `/accounts/password-reset/`
4. Enter a user's email
5. Check the console/terminal for the email output with the reset link

### Test Welcome Email (Console Backend)

1. Register a new user at `/accounts/register/`
2. Check the console/terminal for the welcome email output

### Test with Real Email (SMTP)

1. Configure SMTP settings as described above
2. Register a new user or request password reset
3. Check the recipient's email inbox (and spam folder)

## Troubleshooting

### Emails not sending

1. Check your `.env` file has correct email settings
2. Verify SMTP credentials are correct
3. Check if your email provider requires app passwords
4. Look for error messages in the console/logs
5. For Gmail, ensure 2-Step Verification and App Password are set up

### Password reset link not working

1. Ensure your `ALLOWED_HOSTS` in settings includes your domain
2. Check the link hasn't expired (24 hours validity)
3. Verify the email template is using correct URL patterns

### Welcome email not triggering

1. Ensure `accounts.apps.AccountsConfig` is in `INSTALLED_APPS`
2. Check that `accounts/signals.py` is being imported in `accounts/apps.py`
3. Verify the user has a valid email address

## Customization

### Customize Email Templates

Edit these files to customize email content:
- `templates/registration/password_reset_email.html` - Password reset email body
- `templates/registration/password_reset_subject.txt` - Password reset subject
- `accounts/signals.py` - Welcome email content

### Add More Automated Emails

1. Create a new signal handler in `accounts/signals.py`
2. Define the trigger event (e.g., deposit confirmed, withdrawal processed)
3. Compose the email content
4. Send using `send_mail()` or `send_mass_mail()`

Example:
```python
@receiver(post_save, sender=Deposit)
def send_deposit_confirmation(sender, instance, created, **kwargs):
    if created and instance.status == 'verified':
        send_mail(
            subject='Deposit Confirmed',
            message=f'Your deposit of ${instance.amount} has been confirmed.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=True,
        )
```

## Security Notes

- Never commit `.env` file to version control
- Use app passwords, not regular passwords
- Enable TLS/SSL for production
- Consider using a dedicated email service for better deliverability
- Monitor email sending limits (Gmail: 500/day, SendGrid free: 100/day)
