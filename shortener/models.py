import random
import string
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class URL(models.Model):
    """Model to store original URLs and their shortened versions."""
    original_url = models.URLField(
        _('original URL'),
        max_length=2000,
        help_text=_('The original long URL')
    )
    short_code = models.CharField(
        _('short code'),
        max_length=20,
        unique=True,
        blank=True,
        help_text=_('Leave blank to generate a random code')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    expires_at = models.DateTimeField(
        _('expires at'),
        null=True,
        blank=True,
        help_text=_('Leave blank for URLs that never expire')
    )
    is_custom = models.BooleanField(
        _('is custom'),
        default=False,
        help_text=_('Whether this URL uses a custom short code')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='urls',
        verbose_name=_('created by'),
        null=True,
        blank=True
    )
    title = models.CharField(
        _('title'),
        max_length=200,
        blank=True,
        help_text=_('Optional title for the URL')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Optional description for the URL')
    )
    tags = models.CharField(
        _('tags'),
        max_length=500,
        blank=True,
        help_text=_('Comma-separated tags for the URL')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this URL is active')
    )
    password = models.CharField(
        _('password'),
        max_length=128,
        blank=True,
        help_text=_('Optional password to protect the URL')
    )
    click_count = models.PositiveIntegerField(_('click count'), default=0)
    last_clicked = models.DateTimeField(_('last clicked'), null=True, blank=True)

    class Meta:
        verbose_name = _('URL')
        verbose_name_plural = _('URLs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"

    def save(self, *args, **kwargs):
        """Generate a short code if one isn't provided."""
        if not self.short_code:
            self.short_code = self.generate_short_code()
            self.is_custom = False
        super().save(*args, **kwargs)

    def generate_short_code(self, length=6):
        """Generate a random short code of the specified length."""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not URL.objects.filter(short_code=code).exists():
                return code

    def get_absolute_url(self):
        """Return the full short URL for this object."""
        from django.conf import settings
        return f"{settings.BASE_URL}/{self.short_code}"

    def is_expired(self):
        """Check if the URL has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def increment_click_count(self):
        """Increment the click count and update the last_clicked timestamp."""
        self.click_count += 1
        self.last_clicked = timezone.now()
        self.save(update_fields=['click_count', 'last_clicked'])

    def get_analytics_url(self):
        """Return the URL to view analytics for this URL."""
        return reverse('url_analytics', args=[self.short_code])

    @classmethod
    def get_top_urls(cls, limit=10):
        """Get the most popular URLs by click count."""
        return cls.objects.filter(is_active=True).order_by('-click_count')[:limit]

    @classmethod
    def get_recent_urls(cls, days=7):
        """Get URLs created in the last N days."""
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(created_at__gte=cutoff_date, is_active=True)


class Click(models.Model):
    """Model to track individual clicks on shortened URLs."""
    url = models.ForeignKey(
        URL,
        on_delete=models.CASCADE,
        related_name='clicks',
        verbose_name=_('URL')
    )
    clicked_at = models.DateTimeField(_('clicked at'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    referrer = models.URLField(_('referrer'), blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    country = models.CharField(_('country'), max_length=100, blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    device_type = models.CharField(_('device type'), max_length=50, blank=True)
    browser = models.CharField(_('browser'), max_length=100, blank=True)
    os = models.CharField(_('operating system'), max_length=100, blank=True)

    class Meta:
        verbose_name = _('click')
        verbose_name_plural = _('clicks')
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['clicked_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        return f"{self.url.short_code} - {self.clicked_at}"

    @classmethod
    def create_from_request(cls, url, request):
        """Create a new click record from a request object."""
        from django.contrib.gis.geoip2 import GeoIP2

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Get location info
        country = ''
        city = ''
        try:
            g = GeoIP2()
            location = g.city(ip)
            country = location.get('country_name', '')
            city = location.get('city', '')
        except Exception:
            pass

        # Get device and browser info
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_type = 'Desktop'  # Default
        browser = ''
        os = ''

        # Simple user agent parsing (in a real app, use a library like user-agents)
        if 'Mobile' in user_agent:
            device_type = 'Mobile'
        elif 'Tablet' in user_agent or 'iPad' in user_agent:
            device_type = 'Tablet'

        # Create and return the click
        return cls.objects.create(
            url=url,
            ip_address=ip,
            referrer=request.META.get('HTTP_REFERER', ''),
            user_agent=user_agent,
            country=country,
            city=city,
            device_type=device_type,
            browser=browser,
            os=os
        )
