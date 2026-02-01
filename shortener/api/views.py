"""
API views for the URL shortener application.

This module provides REST API endpoints for managing URLs and their analytics.
"""

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q
from django.http import Http404

from shortener.models import URL, Click
from .serializers import URLSerializer, ClickSerializer, URLDetailSerializer

class URLListCreateView(generics.ListCreateAPIView):
    """
    API endpoint that allows URLs to be viewed or created.
    """
    serializer_class = URLSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return URLs for the current user."""
        return URL.objects.filter(created_by=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """Set the user when creating a new URL."""
        serializer.save(created_by=self.request.user)


class URLDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that allows a URL to be retrieved, updated, or deleted.
    """
    serializer_class = URLDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'short_code'
    lookup_url_kwarg = 'short_code'

    def get_queryset(self):
        """Return URLs for the current user."""
        return URL.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update the URL and log the activity."""
        instance = self.get_object()
        serializer.save()
        # Log the update activity
        instance.log_activity('updated', self.request)

    def perform_destroy(self, instance):
        """Delete the URL and log the activity."""
        instance.log_activity('deleted', self.request)
        instance.delete()


class UrlClicksView(generics.ListAPIView):
    """
    API endpoint that lists all clicks for a specific URL.
    """
    serializer_class = ClickSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return clicks for the URL owned by the current user."""
        short_code = self.kwargs['short_code']
        url = get_object_or_404(URL, short_code=short_code, created_by=self.request.user)
        return Click.objects.filter(url=url).order_by('-clicked_at')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def url_stats(request, short_code):
    """
    API endpoint that returns statistics for a specific URL.
    """
    url = get_object_or_404(URL, short_code=short_code, created_by=request.user)
    
    # Basic stats
    total_clicks = Click.objects.filter(url=url).count()
    unique_visitors = Click.objects.filter(url=url).values('ip_address').distinct().count()
    
    # Clicks by date
    clicks_by_date = (
        Click.objects
        .filter(url=url)
        .values('clicked_at__date')
        .annotate(count=Count('id'))
        .order_by('clicked_at__date')
    )
    
    # Referrers
    top_referrers = (
        Click.objects
        .filter(url=url, referrer__isnull=False)
        .exclude(referrer='')
        .values('referrer')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # User agents
    top_user_agents = (
        Click.objects
        .filter(url=url, user_agent__isnull=False)
        .exclude(user_agent='')
        .values('user_agent')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    return Response({
        'url': URLDetailSerializer(url).data,
        'total_clicks': total_clicks,
        'unique_visitors': unique_visitors,
        'clicks_by_date': list(clicks_by_date),
        'top_referrers': list(top_referrers),
        'top_user_agents': list(top_user_agents),
    })


class GenerateQRCodeView(APIView):
    """
    API view for generating a QR code for a URL.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return URLs for the current user."""
        return URL.objects.filter(created_by=self.request.user)

    def get(self, request, *args, **kwargs):
        """Return a QR code for the URL."""
        short_code = self.kwargs['short_code']
        url = get_object_or_404(URL, short_code=short_code, created_by=request.user)
        
        # Generate QR code (implementation depends on your QR code library)
        # This is a placeholder - replace with actual QR code generation
        qr_code = f"QR_CODE_FOR_{short_code}"
        
        return Response({
            'url': URLDetailSerializer(url).data,
            'qr_code': qr_code
        })
