from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users_list, name='users'),
    path('videos/', views.videos_list, name='videos'),
    path('withdrawals/', views.withdrawals_list, name='withdrawals'),
    path('withdrawals/<int:withdrawal_id>/approve/', views.approve_withdrawal, name='approve_withdrawal'),
    path('withdrawals/<int:withdrawal_id>/reject/', views.reject_withdrawal, name='reject_withdrawal'),
    path('deposits/', views.deposits_list, name='deposits'),
    path('referrals/', views.referrals_list, name='referrals'),
    path('tiers/', views.tiers_list, name='tiers'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_view, name='logout'),
]
