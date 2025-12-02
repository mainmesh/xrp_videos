from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit/', views.placeholder_deposit, name='deposit'),
    path('deposit/intent/', views.create_payment_intent, name='create_payment_intent'),
    path('withdraw/', views.request_withdrawal, name='withdraw'),
    path('register/', views.register, name='register'),
]