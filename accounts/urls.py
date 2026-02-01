"""URL configuration for the accounts app."""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import SignUpView

app_name = 'accounts'

urlpatterns = [
    # User profile
    path('profile/', views.profile_view, name='profile'),
    
    # Registration and authentication
    path('register/', SignUpView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Email verification
    path('verify-email/<str:key>/', 
         views.verify_email, 
         name='verify_email'),
    path('verify-email-required/', 
         views.verify_email_required, 
         name='verify_email_required'),
    path('resend-verification-email/', 
         views.resend_verification_email, 
         name='resend_verification_email'),
    
    # Account management
    path('settings/', views.account_settings, name='account_settings'),
    path('settings/email/', views.email_settings, name='email_settings'),
    path('settings/notifications/', 
         views.notification_settings, 
         name='notification_settings'),
    path('settings/security/', 
         views.security_settings, 
         name='security_settings'),
    
    # API tokens
    path('api-tokens/', 
         views.api_tokens, 
         name='api_tokens'),
    path('api-tokens/create/', 
         views.create_api_token, 
         name='create_api_token'),
    path('api-tokens/delete/<int:pk>/', 
         views.delete_api_token, 
         name='delete_api_token'),
]
