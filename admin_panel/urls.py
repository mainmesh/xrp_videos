from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('setup/', views.setup_admin, name='setup'),  # One-time setup URL
    path('login/', views.admin_login, name='login'),
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users_list, name='users'),
    path('videos/', views.videos_list, name='videos'),
    path('withdrawals/', views.withdrawals_list, name='withdrawals'),
    path('withdrawals/<int:withdrawal_id>/approve/', views.approve_withdrawal, name='approve_withdrawal'),
    path('withdrawals/<int:withdrawal_id>/reject/', views.reject_withdrawal, name='reject_withdrawal'),
    path('deposits/', views.deposits_list, name='deposits'),
    path('referrals/', views.referrals_list, name='referrals'),
    path('tiers/', views.tiers_list, name='tiers'),
    path('api/tiers/', views.api_tiers, name='api_tiers'),
    path('settings/', views.settings_view, name='settings'),
    # Messaging
    path('messages/', views.messages_list, name='messages'),
    path('messages/<int:message_id>/', views.view_admin_message, name='view_admin_message'),
    path('send-message/<int:user_id>/', views.send_message_to_user, name='send_message'),
    # Announcements
    path('announcements/', views.announcements_list, name='announcements'),
    path('announcements/<int:announcement_id>/toggle/', views.toggle_announcement, name='toggle_announcement'),
    path('announcements/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('logout/', views.logout_view, name='logout'),
]
