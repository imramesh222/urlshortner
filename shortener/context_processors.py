"""
Context processors for the shortener app.
"""

def site_info(request):
    """Add site information to the template context."""
    return {
        'SITE_NAME': 'URL Shortener',
        'SITE_DESCRIPTION': 'A simple URL shortener service',
        'DEBUG': False  # This will be overridden by settings.DEBUG
    }
