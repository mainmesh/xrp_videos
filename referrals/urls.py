from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
	path('r/<str:code>/', views.signup_with_referral, name='signup'),
	path('stats/', views.referral_stats, name='stats'),
]
