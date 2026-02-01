"""Serializers for the shortener app."""

from rest_framework import serializers
from django.urls import reverse

from .models import URL, Click


class ClickSerializer(serializers.ModelSerializer):
    """Serializer for Click model."""
    class Meta:
        model = Click
        fields = [
            'id', 'clicked_at', 'ip_address', 'referrer', 'user_agent',
            'country', 'city', 'device_type', 'browser', 'os'
        ]
        read_only_fields = fields


class URLSerializer(serializers.ModelSerializer):
    """Serializer for URL model."""
    short_url = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    clicks_count = serializers.IntegerField(source='click_count', read_only=True)
    
    class Meta:
        model = URL
        fields = [
            'id', 'original_url', 'short_code', 'short_url', 'title', 
            'created_at', 'expires_at', 'is_active', 'click_count',
            'clicks_count', 'qr_code_url', 'is_one_time', 'password_protected'
        ]
        read_only_fields = ['id', 'created_at', 'click_count', 'clicks_count', 'qr_code_url']
        extra_kwargs = {
            'short_code': {'required': False, 'allow_blank': True},
            'password': {'write_only': True, 'required': False, 'allow_blank': True},
        }
    
    def get_short_url(self, obj):
        """Get the full short URL."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/{obj.short_code}')
        return f'/{obj.short_code}'
    
    def get_qr_code_url(self, obj):
        """Get the QR code URL."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/urls/{obj.short_code}/qrcode/')
        return f'/api/urls/{obj.short_code}/qrcode/'
    
    def validate_short_code(self, value):
        """Validate the short code."""
        if value and not value.isalnum() and not all(c in ('-', '_') for c in value):
            raise serializers.ValidationError(
                'Short code can only contain letters, numbers, hyphens, and underscores.'
            )
        return value
    
    def create(self, validated_data):
        """Create a new URL."""
        # If no short code is provided, generate one
        if not validated_data.get('short_code'):
            validated_data['short_code'] = self._generate_short_code()
        
        # Set the created_by user if not set
        if 'created_by' not in validated_data and 'request' in self.context:
            validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)
    
    def _generate_short_code(self, length=6):
        """Generate a random short code."""
        import random
        import string
        
        chars = string.ascii_letters + string.digits
        
        # Try to generate a unique code (max 10 attempts)
        for _ in range(10):
            code = ''.join(random.choices(chars, k=length))
            if not URL.objects.filter(short_code=code).exists():
                return code
                
        # If we couldn't find a unique code, try with a longer length
        return self._generate_short_code(length + 1)


class URLDetailSerializer(URLSerializer):
    """Detailed serializer for URL model, including clicks."""
    clicks = ClickSerializer(many=True, read_only=True)
    
    class Meta(URLSerializer.Meta):
        fields = URLSerializer.Meta.fields + ['clicks']
        read_only_fields = URLSerializer.Meta.read_only_fields + ['clicks']


class URLCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating URLs via API."""
    short_code = serializers.CharField(
        required=False, 
        allow_blank=True, 
        max_length=20,
        help_text='Custom short code (leave blank for auto-generation)'
    )
    expiration_days = serializers.IntegerField(
        required=False, 
        min_value=1, 
        max_value=365,
        help_text='Number of days until the URL expires (optional)'
    )
    password = serializers.CharField(
        required=False, 
        allow_blank=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Password protection (optional)'
    )
    
    class Meta:
        model = URL
        fields = [
            'original_url', 'title', 'short_code', 'expiration_days',
            'is_one_time', 'password'
        ]
    
    def create(self, validated_data):
        """Create a new URL with optional expiration and password."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Handle expiration
        expiration_days = validated_data.pop('expiration_days', None)
        if expiration_days:
            validated_data['expires_at'] = timezone.now() + timedelta(days=expiration_days)
        
        # Handle password
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = password
        
        # Set the created_by user if not set
        if 'created_by' not in validated_data and 'request' in self.context:
            validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)
