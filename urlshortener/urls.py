"""
URL configuration for urlshortener project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from shortener import views as shortener_views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Home page
    path('', shortener_views.home, name='home'),
    
    # Accounts and authentication
    path('accounts/', include('accounts.urls')),  # Custom accounts app
    path('accounts/', include('allauth.urls')),   # Allauth authentication
    
    # URL shortener app
    path('u/', include('shortener.urls')),
    
    # API endpoints
    path('api/', include('shortener.api.urls')),
    
    # Serve short URLs
    re_path(r'^(?P<short_code>[\w-]+)/?$', 
            shortener_views.redirect_short_url, 
            name='redirect_short_url'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
