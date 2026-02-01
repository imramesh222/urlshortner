import os
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model that uses email as the unique identifier."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    email_verification_key = models.CharField(max_length=64, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()
        
    @property
    def email_confirmed(self):
        """Check if the user's email is confirmed."""
        return self.is_active and not self.email_verification_key
        
    def send_verification_email(self, request=None):
        """Send a verification email to the user."""
        from django.utils.crypto import get_random_string
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from django.urls import reverse
        
        # Generate a new verification key
        self.email_verification_key = get_random_string(64)
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_key', 'email_verification_sent_at'])
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', args=[self.email_verification_key])
        )
        
        # Prepare email
        subject = 'Verify your email address'
        context = {
            'user': self,
            'verification_url': verification_url,
        }
        
        # Render email templates
        html_message = render_to_string('accounts/emails/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True


class UserProfile(models.Model):
    """Extended user profile information."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user')
    )
    bio = models.TextField(_('biography'), blank=True)
    website = models.URLField(_('website'), blank=True)
    location = models.CharField(_('location'), max_length=255, blank=True)
    company = models.CharField(_('company'), max_length=255, blank=True)
    avatar = models.URLField(
        _('avatar URL'),
        blank=True,
        null=True,
        help_text=_('URL of the profile picture')
    )
    email_confirmed = models.BooleanField(_('email confirmed'), default=False)
    two_factor_enabled = models.BooleanField(_('two-factor authentication'), default=False)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    
    # Social media links
    twitter = models.CharField(_('Twitter username'), max_length=15, blank=True)
    github = models.CharField(_('GitHub username'), max_length=39, blank=True)
    linkedin = models.CharField(_('LinkedIn username'), max_length=100, blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    newsletter = models.BooleanField(_('subscribe to newsletter'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email}'s profile"
    
    @property
    def get_avatar_url(self):
        """Return the URL of the user's avatar or a default one."""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return f"https://www.gravatar.com/avatar/{hash(self.user.email)}?d=identicon&s=200"


class UserActivity(models.Model):
    """Track user activities on the platform."""
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        PROFILE_UPDATE = 'profile_update', _('Profile Update')
        URL_CREATED = 'url_created', _('URL Created')
        URL_DELETED = 'url_deleted', _('URL Deleted')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('user')
    )
    activity_type = models.CharField(
        _('activity type'),
        max_length=20,
        choices=ActivityType.choices
    )
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    details = models.JSONField(_('details'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('user activity')
        verbose_name_plural = _('user activities')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} at {self.timestamp}"
