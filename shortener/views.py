"""Views for the shortener app."""

import csv
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import (
    HttpResponse, 
    HttpResponseRedirect, 
    HttpResponsePermanentRedirect,
    Http404,
    JsonResponse,
    FileResponse
)
from django.shortcuts import (
    render, 
    redirect, 
    get_object_or_404
)
from django.utils import timezone
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView
)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveAPIView,
    ListAPIView
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserActivity
from .models import URL, Click
from .forms import URLForm, EditURLForm
from .serializers import (
    URLSerializer, 
    ClickSerializer,
    URLDetailSerializer
)
from .utils import generate_qr_code

from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

# Regular Views

def home(request):
    """Home page view."""
    if request.user.is_authenticated:
        return redirect('shortener:dashboard')
    context = {
        'title': 'URL Shortener - Shorten Your Links',
        'description': 'Free URL Shortener for transforming long, ugly links into nice, memorable and trackable short URLs.',
    }
    return render(request, 'shortener/home.html', context)

def url_list(request):
    """View for listing all URLs for the current user."""
    if not request.user.is_authenticated:
        return redirect('account_login')
        
    # Get all URLs for the current user, ordered by most recent first
    urls = URL.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Get filter parameters
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    # Apply filters
    if search_query:
        urls = urls.filter(
            Q(original_url__icontains=search_query) |
            Q(short_code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if status_filter == 'active':
        urls = urls.filter(is_active=True)
    elif status_filter == 'inactive':
        urls = urls.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(urls, 10)  # Show 10 URLs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_urls': urls.count(),
        'active_urls': urls.filter(is_active=True).count(),
    }
    
    return render(request, 'shortener/url_list.html', context)

@login_required
def dashboard(request):
    """User dashboard view."""
    user = request.user
    
    # Get user's URLs
    urls = URL.objects.filter(created_by=user).order_by('-created_at')
    
    # Get recent clicks
    recent_clicks = Click.objects.filter(url__in=urls).select_related('url').order_by('-clicked_at')[:10]
    
    # Get stats
    total_urls = urls.count()
    total_clicks = sum(url.click_count for url in urls)
    
    context = {
        'title': 'Dashboard',
        'urls': urls[:5],  # Show only the 5 most recent URLs
        'recent_clicks': recent_clicks,
        'total_urls': total_urls,
        'total_clicks': total_clicks,
    }
    
    return render(request, 'shortener/dashboard.html', context)

@login_required
def create_short_url(request):
    """View for creating a new short URL."""
    if request.method == 'POST':
        form = URLForm(request.POST, user=request.user)
        if form.is_valid():
            url = form.save(commit=False)
            url.created_by = request.user
            url.save()
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='url_created',
                details={'url': url.original_url, 'short_code': url.short_code}
            )

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'short_url': url.get_absolute_url(),
                    'short_code': url.short_code,
                    'message': 'Short URL created successfully!'
                })
            else:
                messages.success(request, 'Short URL created successfully!')
                return redirect('shortener:url_analytics', short_code=url.short_code)
    else:
        form = URLForm(user=request.user)
    
    context = {
        'title': 'Create Short URL',
        'form': form,
    }
    return render(request, 'shortener/url_form.html', context)

@login_required
def edit_short_url(request, pk):
    """View for editing an existing short URL."""
    url = get_object_or_404(URL, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = EditURLForm(request.POST, instance=url)
        if form.is_valid():
            url = form.save()
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='url_updated',
                details={'url': url.original_url, 'short_code': url.short_code}
            )
            
            messages.success(request, 'URL updated successfully!')
            return redirect('shortener:url_analytics', short_code=url.short_code)
    else:
        form = EditURLForm(instance=url)
    
    context = {
        'title': 'Edit URL',
        'form': form,
        'url': url,
    }
    return render(request, 'shortener/url_edit.html', context)

@login_required
def delete_short_url(request, pk):
    """View for deleting a short URL."""
    url = get_object_or_404(URL, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        # Log the activity before deletion
        UserActivity.objects.create(
            user=request.user,
            activity_type='url_deleted',
            details={'url': url.original_url, 'short_code': url.short_code}
        )
        
        url.delete()
        messages.success(request, 'URL deleted successfully!')
        return redirect('shortener:dashboard')
    
    context = {
        'title': 'Delete URL',
        'url': url,
    }
    return render(request, 'shortener/url_confirm_delete.html', context)

def redirect_short_url(request, short_code):
    """View for redirecting a short URL to the original URL."""
    try:
        url = URL.objects.get(short_code=short_code, is_active=True)
        
        # Check if the URL has expired
        if url.expires_at and url.expires_at < timezone.now():
            return render(request, 'shortener/url_expired.html', {'url': url}, status=410)
        
        # Check if the URL is password protected
        if url.password and not request.session.get(f'url_{url.id}_authenticated', False):
            return redirect('shortener:url_password', short_code=url.short_code)
        
        # Create a click record
        click = Click.create_from_request(url, request)
        
        # Update the URL's click count
        url.increment_click_count()
        
        # If it's a one-time URL, deactivate it
        if url.is_one_time:
            url.is_active = False
            url.save()
        
        # Redirect to the original URL
        return HttpResponsePermanentRedirect(url.original_url)
    except URL.DoesNotExist:
        raise Http404("Short URL not found")

@login_required
def url_analytics(request, short_code):
    """View for displaying URL analytics."""
    url = get_object_or_404(URL, short_code=short_code, created_by=request.user)
    
    # Get click data for the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    clicks = Click.objects.filter(
        url=url, 
        clicked_at__gte=thirty_days_ago
    ).order_by('clicked_at')
    
    # Prepare data for the chart
    click_dates = {}
    for click in clicks:
        date = click.clicked_at.strftime('%Y-%m-%d')
        if date in click_dates:
            click_dates[date] += 1
        else:
            click_dates[date] = 1
    
    chart_labels = list(click_dates.keys())
    chart_data = list(click_dates.values())
    
    # Get referrers
    referrers = (
        Click.objects.filter(url=url, referrer__isnull=False)
        .values('referrer')
        .annotate(count=Count('referrer'))
        .order_by('-count')[:10]
    )
    
    # Get countries
    countries = (
        Click.objects.filter(url=url, country__isnull=False)
        .values('country')
        .annotate(count=Count('country'))
        .order_by('-count')[:10]
    )
    
    # Get devices
    devices = (
        Click.objects.filter(url=url, device_type__isnull=False)
        .values('device_type')
        .annotate(count=Count('device_type'))
        .order_by('-count')
    )
    
    context = {
        'title': f'Analytics for {url.short_code}',
        'url': url,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'referrers': referrers,
        'countries': countries,
        'devices': devices,
        'total_clicks': url.click_count,
        'unique_visitors': Click.objects.filter(url=url).values('ip_address').distinct().count(),
        'avg_clicks_per_day': url.click_count / max(1, (timezone.now() - url.created_at).days),
    }
    
    return render(request, 'shortener/analytics.html', context)

@login_required
def url_clicks(request, short_code):
    """View for displaying URL clicks."""
    url = get_object_or_404(URL, short_code=short_code, created_by=request.user)
    clicks = Click.objects.filter(url=url).order_by('-clicked_at')
    
    # Apply filters
    query = request.GET.get('q')
    if query:
        clicks = clicks.filter(
            Q(ip_address__icontains=query) |
            Q(referrer__icontains=query) |
            Q(country__icontains=query) |
            Q(city__icontains=query) |
            Q(device_type__icontains=query) |
            Q(browser__icontains=query) |
            Q(os__icontains=query)
        )
    
    context = {
        'title': f'Clicks for {url.short_code}',
        'url': url,
        'clicks': clicks,
        'query': query or '',
    }
    
    return render(request, 'shortener/clicks.html', context)

@login_required
def export_clicks(request, short_code):
    """View for exporting URL clicks as CSV."""
    url = get_object_or_404(URL, short_code=short_code, created_by=request.user)
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{url.short_code}-clicks.csv"'},
    )
    
    # Create a CSV writer
    writer = csv.writer(response)
    
    # Write the header row
    writer.writerow([
        'Date', 'Time', 'IP Address', 'Referrer', 'Country', 'City', 
        'Device Type', 'Browser', 'Operating System'
    ])
    
    # Write data rows
    for click in Click.objects.filter(url=url).order_by('-clicked_at'):
        writer.writerow([
            click.clicked_at.strftime('%Y-%m-%d'),
            click.clicked_at.strftime('%H:%M:%S'),
            click.ip_address or '',
            click.referrer or '',
            click.country or '',
            click.city or '',
            click.device_type or '',
            click.browser or '',
            click.os or '',
        ])
    
    return response

def generate_qr_code_view(request, short_code):
    """View for generating a QR code for a short URL."""
    url = get_object_or_404(URL, short_code=short_code)
    
    # Check if the user is the owner of the URL
    if not request.user.is_authenticated or url.created_by != request.user:
        raise PermissionDenied
    
    # Generate QR code
    qr_code = generate_qr_code(url.get_absolute_url())
    
    # Return the QR code as an image response
    response = HttpResponse(content_type='image/png')
    qr_code.save(response, 'PNG')
    return response

# API Views

class UrlListCreateView(ListCreateAPIView):
    """API view for listing and creating URLs."""
    serializer_class = URLSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return URLs for the current user."""
        return URL.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user when creating a new URL."""
        serializer.save(created_by=self.request.user)
        
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='url_created',
            details={
                'url': serializer.validated_data.get('original_url'),
                'short_code': serializer.validated_data.get('short_code', 'auto')
            }
        )

class UrlRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating, and deleting a URL."""
    serializer_class = URLDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'short_code'
    lookup_url_kwarg = 'short_code'
    
    def get_queryset(self):
        """Return URLs for the current user."""
        return URL.objects.filter(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Log the update activity."""
        instance = self.get_object()
        serializer.save()
        
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='url_updated',
            details={
                'url': instance.original_url,
                'short_code': instance.short_code
            }
        )
    
    def perform_destroy(self, instance):
        """Log the delete activity."""
        # Log the activity before deletion
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='url_deleted',
            details={
                'url': instance.original_url,
                'short_code': instance.short_code
            }
        )
        instance.delete()

class UrlClicksView(RetrieveAPIView):
    """API view for retrieving URL clicks."""
    serializer_class = ClickSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return clicks for the URL owned by the current user."""
        return Click.objects.filter(
            url__short_code=self.kwargs['short_code'],
            url__created_by=self.request.user
        )
    
    def get(self, request, *args, **kwargs):
        """Return a list of clicks for the URL."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Add some metadata
        data = {
            'count': queryset.count(),
            'results': serializer.data,
            'url': request.build_absolute_uri(
                reverse_lazy('shortener:redirect_short_url', 
                           kwargs={'short_code': self.kwargs['short_code']})
            )
        }
        
        return Response(data)

class GenerateQRCodeView(RetrieveAPIView):
    """API view for generating a QR code for a URL."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return URLs for the current user."""
        return URL.objects.filter(created_by=self.request.user)
    
    def get(self, request, *args, **kwargs):
        """Return a QR code for the URL."""
        url = self.get_object()
        qr_code = generate_qr_code(url.get_absolute_url())
        
        # Return the QR code as a base64-encoded string
        import base64
        from io import BytesIO
        
        buffer = BytesIO()
        qr_code.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return Response({
            'url': url.get_absolute_url(),
            'short_code': url.short_code,
            'qr_code': f'data:image/png;base64,{qr_code_base64}'
        })
