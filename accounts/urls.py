from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit/', views.placeholder_deposit, name='deposit'),
    path('deposit/intent/', views.create_payment_intent, name='create_payment_intent'),
    path('withdraw/', views.request_withdrawal, name='withdraw'),
    path('register/', views.register, name='register'),
    path('notifications/', views.notifications, name='notifications'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('settings/update-profile/', views.update_profile, name='update_profile'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
]