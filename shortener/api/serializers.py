"""
Serializers for the URL shortener API.

This module provides serializers for the URL and Click models,
which are used to convert model instances to JSON and vice versa.
"""

from rest_framework import serializers
from shortener.models import URL, Click

class ClickSerializer(serializers.ModelSerializer):
    """Serializer for the Click model."""
    
    class Meta:
        model = Click
        fields = [
            'id',
            'url',
            'clicked_at',
            'ip_address',
            'referrer',
            'user_agent',
            'country',
            'city',
            'device_type',
            'browser',
            'os',
        ]
        read_only_fields = ['url']


class URLSerializer(serializers.ModelSerializer):
    """Serializer for the URL model (basic fields)."""
    
    short_url = serializers.SerializerMethodField()
    click_count = serializers.SerializerMethodField()
    
    class Meta:
        model = URL
        fields = [
            'id',
            'original_url',
            'short_code',
            'short_url',
            'title',
            'description',
            'is_active',
            'expires_at',
            'created_at',
            'updated_at',
            'click_count',
        ]
        read_only_fields = ['short_code', 'created_at', 'updated_at', 'click_count']
    
    def get_short_url(self, obj):
        """
        Get the full short URL for the given URL object.
        
        Args:
            obj: The URL instance.
            
        Returns:
            str: The full short URL.
        """
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(f'/{obj.short_code}')
        return f'/{obj.short_code}'
    
    def get_click_count(self, obj):
        """
        Get the number of clicks for the URL.
        
        Args:
            obj: The URL instance.
            
        Returns:
            int: The number of clicks.
        """
        return obj.clicks.count()


class URLDetailSerializer(URLSerializer):
    """
    Extended URL serializer that includes related clicks.
    
    This serializer includes a nested representation of the most recent clicks.
    """
    
    recent_clicks = serializers.SerializerMethodField()
    
    class Meta(URLSerializer.Meta):
        fields = URLSerializer.Meta.fields + ['recent_clicks']
    
    def get_recent_clicks(self, obj):
        """
        Get the 10 most recent clicks for the URL.
        
        Args:
            obj: The URL instance.
            
        Returns:
            list: A list of serialized click data.
        """
        clicks = obj.clicks.all().order_by('-clicked_at')[:10]
        return ClickSerializer(clicks, many=True).data
