from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit/', views.placeholder_deposit, name='deposit'),
    path('deposit/mpesa/', views.deposit_mpesa, name='deposit_mpesa'),
    path('deposit/mpesa/webhook/', views.mpesa_webhook, name='mpesa_webhook'),
    path('deposit/intent/', views.create_payment_intent, name='create_payment_intent'),
    path('withdraw/', views.request_withdrawal, name='withdraw'),
    path('upgrade-tier/<int:tier_id>/', views.upgrade_tier, name='upgrade_tier'),
    path('register/', views.register, name='register'),
    path('notifications/', views.notifications, name='notifications'),
    path('transactions/', views.transaction_history, name='transactions'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('settings/update-profile/', views.update_profile, name='update_profile'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]