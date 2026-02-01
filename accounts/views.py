from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.views.decorators.http import require_http_methods
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .forms import CustomUserCreationForm
from .tokens import account_activation_token

User = get_user_model()

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/signup.html'

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('shortener:dashboard')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


def verify_email(request, key):
    """Verify user's email using the verification key."""
    try:
        # Get user by the verification key
        user = User.objects.get(email_verification_key=key, is_active=False)
        user.is_active = True
        user.email_verification_key = ''
        user.save()
        
        # Log the user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        messages.success(request, 'Your email has been verified successfully! You are now logged in.')
        return redirect('shortener:dashboard')
    except (User.DoesNotExist, ValueError):
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('home')


def verify_email_required(request):
    """Show a page explaining that email verification is required."""
    if request.user.is_authenticated and not request.user.email_confirmed:
        return render(request, 'accounts/verify_email_required.html')
    return redirect('home')


@require_http_methods(["POST"])
def resend_verification_email(request):
    """Resend the verification email to the user."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.email_confirmed:
        messages.info(request, 'Your email is already verified.')
        return redirect('shortener:dashboard')
    
    # Generate a new verification key
    from django.utils.crypto import get_random_string
    verification_key = get_random_string(32)
    
    # Save the verification key to the user
    request.user.email_verification_key = verification_key
    request.user.save()
    
    # Send verification email
    subject = 'Verify your email address'
    verification_url = request.build_absolute_uri(
        reverse('accounts:verify_email', args=[verification_key])
    )
    
    context = {
        'user': request.user,
        'verification_url': verification_url,
    }
    
    html_message = render_to_string('accounts/emails/verification_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    messages.success(request, 'A new verification email has been sent to your email address.')
    return redirect('accounts:verify_email_required')


@login_required
def account_settings(request):
    """View for user account settings."""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account settings have been updated.')
            return redirect('accounts:account_settings')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'accounts/account_settings.html', {
        'form': form,
    })


@login_required
def email_settings(request):
    """View for user email preferences."""
    if request.method == 'POST':
        # In a real application, you would process email preferences here
        # For now, we'll just show a success message
        messages.success(request, 'Your email preferences have been updated.')
        return redirect('accounts:email_settings')
    
    return render(request, 'accounts/email_settings.html')


@login_required
def notification_settings(request):
    """View for user notification preferences."""
    if request.method == 'POST':
        # In a real application, you would process notification preferences here
        # For now, we'll just show a success message
        messages.success(request, 'Your notification preferences have been updated.')
        return redirect('accounts:notification_settings')
    
    return render(request, 'accounts/notification_settings.html')


@login_required
def security_settings(request):
    """View for user security settings."""
    if request.method == 'POST':
        # In a real application, you would process security settings here
        # For now, we'll just show a success message
        messages.success(request, 'Your security settings have been updated.')
        return redirect('accounts:security_settings')
    
    return render(request, 'accounts/security_settings.html')


@login_required
def api_tokens(request):
    """View for managing API tokens."""
    # In a real application, you would fetch the user's API tokens from the database
    # For now, we'll just use a placeholder list
    tokens = [
        {
            'id': 1,
            'name': 'Development Token',
            'key': 'token_dev_example1234567890abcdefghijklmnop',
            'last_used': '2023-10-15 14:30:22',
            'created': '2023-10-01 10:15:45',
            'expires': '2024-10-01 10:15:45',
        },
        {
            'id': 2,
            'name': 'Production Token',
            'key': 'token_prod_example0987654321zyxwvutsrqponmlk',
            'last_used': '2023-10-16 09:12:33',
            'created': '2023-09-15 16:45:12',
            'expires': '2023-12-31 23:59:59',
        },
    ]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        token_id = request.POST.get('token_id')
        
        if action == 'create':
            # In a real application, generate a new API token
            messages.success(request, 'New API token created successfully.')
            return redirect('accounts:api_tokens')
            
        elif action == 'delete' and token_id:
            # In a real application, delete the specified token
            messages.success(request, 'API token deleted successfully.')
            return redirect('accounts:api_tokens')
    
    return render(request, 'accounts/api_tokens.html', {
        'tokens': tokens,
    })


@login_required
def create_api_token(request):
    """View for creating a new API token."""
    if request.method == 'POST':
        token_name = request.POST.get('token_name')
        expires_in = request.POST.get('expires_in')
        
        # In a real application, generate a secure token and save it to the database
        # For now, we'll just show a success message
        messages.success(request, f'API token "{token_name}" created successfully.')
        return redirect('accounts:api_tokens')
    
    return redirect('accounts:api_tokens')


@login_required
def delete_api_token(request, token_id):
    """View for deleting an API token."""
    if request.method == 'POST':
        # In a real application, verify the token belongs to the user and delete it
        # For now, we'll just show a success message
        messages.success(request, 'API token deleted successfully.')
        return redirect('accounts:api_tokens')
    
    return redirect('accounts:api_tokens')
