"""API URL configuration for the shortener app."""

from django.urls import path
from . import views

app_name = 'shortener_api'

urlpatterns = [
    # List and create URLs
    path('urls/', 
         views.URLListCreateView.as_view(), 
         name='url-list-create'),
         
    # Retrieve, update, or delete a URL
    path('urls/<str:short_code>/', 
         views.URLDetailView.as_view(), 
         name='url-retrieve-update-destroy'),
         
    # Get clicks for a URL
    path('urls/<str:short_code>/clicks/', 
         views.UrlClicksView.as_view(), 
         name='url-clicks'),
         
    # Generate QR code for a URL
    path('urls/<str:short_code>/qrcode/', 
         views.GenerateQRCodeView.as_view(), 
         name='url-qrcode'),
         
    # Get URL statistics
    path('urls/<str:short_code>/stats/', 
         views.url_stats, 
         name='url-stats'),
]
