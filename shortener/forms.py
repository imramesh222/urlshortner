"""Forms for the shortener app."""

import random
import string
from datetime import timedelta

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import URL


class URLForm(forms.ModelForm):
    """Form for creating a new short URL."""
    custom_short_code = forms.CharField(
        required=False,
        max_length=20,
        label=_('Custom Short Code (optional)'),
        help_text=_('Leave blank for auto-generation')
    )
    expiration_days = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=365,
        label=_('Expires after (days)'),
        help_text=_('Leave blank for no expiration'),
        widget=forms.NumberInput(attrs={'min': 1, 'max': 365})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=True),
        label=_('Password Protection (optional)'),
        help_text=_('Leave blank for no password protection')
    )

    class Meta:
        model = URL
        fields = ('original_url', 'title', 'custom_short_code', 'expiration_days', 'password')
        widgets = {
            'original_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com',
                'required': 'required',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('My Awesome Link'),
            }),
        }
        labels = {
            'original_url': _('Destination URL'),
            'title': _('Title (optional)'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set the user if provided
        if self.user and self.user.is_authenticated:
            self.fields['is_one_time'] = forms.BooleanField(
                required=False,
                label=_('One-time link'),
                help_text=_('Link will be deactivated after first use'),
            )

    def clean_custom_short_code(self):
        """Validate the custom short code."""
        short_code = self.cleaned_data.get('custom_short_code')
        
        if not short_code:
            return None
            
        # Check if the short code contains only alphanumeric characters and hyphens/underscores
        if not all(c.isalnum() or c in ('-', '_') for c in short_code):
            raise ValidationError(_(
                'Short code can only contain letters, numbers, hyphens, and underscores.'
            ))
            
        # Check if the short code is already in use
        if URL.objects.filter(short_code=short_code).exists():
            raise ValidationError(_('This short code is already in use. Please choose another one.'))
            
        return short_code

    def clean(self):
        """Clean and validate the form data."""
        cleaned_data = super().clean()
        
        # Set the short code
        short_code = cleaned_data.get('custom_short_code')
        if not short_code:
            # Generate a random short code if not provided
            short_code = self._generate_short_code()
            cleaned_data['short_code'] = short_code
        else:
            cleaned_data['short_code'] = short_code
            
        # Set the expiration date if provided
        expiration_days = cleaned_data.get('expiration_days')
        if expiration_days:
            cleaned_data['expires_at'] = timezone.now() + timedelta(days=expiration_days)
            
        # Set the created_by user if authenticated
        if self.user and self.user.is_authenticated:
            cleaned_data['created_by'] = self.user
            
        return cleaned_data
    
    def _generate_short_code(self, length=6):
        """Generate a random short code."""
        chars = string.ascii_letters + string.digits
        
        # Try to generate a unique code (max 10 attempts)
        for _ in range(10):
            code = ''.join(random.choices(chars, k=length))
            if not URL.objects.filter(short_code=code).exists():
                return code
                
        # If we couldn't find a unique code, try with a longer length
        return self._generate_short_code(length + 1)


class EditURLForm(forms.ModelForm):
    """Form for editing an existing short URL."""
    class Meta:
        model = URL
        fields = ('title', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('My Awesome Link'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'title': _('Title'),
            'is_active': _('Active'),
        }


class PasswordForm(forms.Form):
    """Form for password-protected URLs."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter password'),
            'required': 'required',
        }),
        label=_('Password')
    )
    
    def __init__(self, *args, **kwargs):
        self.url = kwargs.pop('url', None)
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """Validate the password."""
        password = self.cleaned_data.get('password')
        
        if self.url and self.url.password != password:
            raise ValidationError(_('Incorrect password. Please try again.'))
            
        return password
