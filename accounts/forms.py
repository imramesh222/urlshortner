from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, UserChangeForm as BaseUserChangeForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(UserCreationForm):
    """A form for creating new users. Includes all the required fields, plus a repeated password."""
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'}),
        help_text=_('Required. Enter a valid email address.')
    )
    
    class Meta:
        model = get_user_model()
        fields = ('email', 'password1', 'password2')
        field_classes = {}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CustomUserChangeForm(BaseUserChangeForm):
    """A form for updating users. Includes all the fields on the user,
    but replaces the password field with admin's password hash display field.
    """
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control'})
    )
    
    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields.get('password')
        if password:
            password.help_text = password.help_text.format(
                f'../../{self.instance.id}/password/'
            )
            password.widget.attrs['class'] = 'form-control'
