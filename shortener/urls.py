"""URL configuration for the shortener app."""

from django.urls import path
from . import views

app_name = 'shortener'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # URL management
    path('create/', views.create_short_url, name='create_short_url'),
    path('edit/<int:pk>/', views.edit_short_url, name='edit_short_url'),
    path('delete/<int:pk>/', views.delete_short_url, name='delete_short_url'),
    path('list/', views.url_list, name='url_list'),
    
    # Analytics
    path('analytics/<str:short_code>/', 
         views.url_analytics, 
         name='url_analytics'),
    path('clicks/<str:short_code>/', 
         views.url_clicks, 
         name='url_clicks'),
    path('clicks/<str:short_code>/export/', 
         views.export_clicks, 
         name='export_clicks'),
    
    # QR Code
    path('qrcode/<str:short_code>/', 
         views.generate_qr_code, 
         name='generate_qr_code'),
    
    # API endpoints
    path('api/urls/', 
         views.UrlListCreateView.as_view(), 
         name='api_url_list_create'),
    path('api/urls/<str:short_code>/', 
         views.UrlRetrieveUpdateDestroyView.as_view(), 
         name='api_url_retrieve_update_destroy'),
    path('api/urls/<str:short_code>/clicks/', 
         views.UrlClicksView.as_view(), 
         name='api_url_clicks'),
]
