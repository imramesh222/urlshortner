"""Utility functions for the shortener app."""

import hashlib
import logging
import qrcode
import qrcode.image.svg
from urllib.parse import urljoin

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_short_code(url, length=6):
    """
    Generate a short code for a URL.
    
    Args:
        url (str): The original URL to generate a short code for.
        length (int): The desired length of the short code.
        
    Returns:
        str: A short code.
    """
    # Use MD5 hash of the URL + timestamp to ensure uniqueness
    hash_input = f"{url}{timezone.now().timestamp()}"
    hash_digest = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    # Take the first 'length' characters of the hash
    return hash_digest[:length]


def generate_qr_code(url, size=10, border=4):
    """
    Generate a QR code for a URL.
    
    Args:
        url (str): The URL to encode in the QR code.
        size (int): The size of the QR code (1-40, where 1 is 21x21 modules).
        border (int): The border size around the QR code.
        
    Returns:
        PIL.Image: A QR code image.
    """
    qr = qrcode.QRCode(
        version=size,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=border,
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    return qr.make_image(fill_color="black", back_color="white")


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        str: The client's IP address, or None if not found.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_geolocation_data(ip_address):
    """
    Get geolocation data for an IP address using GeoIP2.
    
    Args:
        ip_address (str): The IP address to look up.
        
    Returns:
        dict: A dictionary containing geolocation data, or None if not available.
    """
    if not ip_address or ip_address == '127.0.0.1':
        return None
    
    try:
        import geoip2.database
        import os
        
        # Path to the GeoIP2 database
        geoip_db_path = os.path.join(settings.GEOIP_PATH, 'GeoLite2-City.mmdb')
        
        if not os.path.exists(geoip_db_path):
            logger.warning(f"GeoIP2 database not found at {geoip_db_path}")
            return None
            
        with geoip2.database.Reader(geoip_db_path) as reader:
            try:
                response = reader.city(ip_address)
                return {
                    'country': response.country.name,
                    'country_code': response.country.iso_code,
                    'city': response.city.name,
                    'postal_code': response.postal.code,
                    'latitude': response.location.latitude,
                    'longitude': response.location.longitude,
                    'time_zone': response.location.time_zone,
                }
            except (geoip2.errors.AddressNotFoundError, AttributeError):
                logger.warning(f"Could not find geolocation data for IP: {ip_address}")
                return None
    except ImportError:
        logger.warning("GeoIP2 is not installed. Install with: pip install geoip2")
        return None
    except Exception as e:
        logger.error(f"Error getting geolocation data: {str(e)}")
        return None


def get_user_agent_info(user_agent_string):
    """
    Parse user agent string to extract device, browser, and OS information.
    
    Args:
        user_agent_string (str): The user agent string from the request.
        
    Returns:
        dict: A dictionary containing device, browser, and OS information.
    """
    if not user_agent_string:
        return {
            'device_type': None,
            'browser': None,
            'os': None,
        }
    
    # Simple parsing (for a more robust solution, consider using a library like user-agents)
    user_agent = user_agent_string.lower()
    
    # Detect device type
    device_type = 'desktop'  # default
    if 'mobile' in user_agent:
        device_type = 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        device_type = 'tablet'
    
    # Detect browser
    browser = None
    if 'chrome' in user_agent:
        browser = 'Chrome'
    elif 'firefox' in user_agent:
        browser = 'Firefox'
    elif 'safari' in user_agent:
        browser = 'Safari'
    elif 'edge' in user_agent:
        browser = 'Edge'
    elif 'opera' in user_agent:
        browser = 'Opera'
    elif 'msie' in user_agent or 'trident' in user_agent:
        browser = 'Internet Explorer'
    
    # Detect OS
    os_info = None
    if 'windows' in user_agent:
        os_info = 'Windows'
    elif 'mac os' in user_agent:
        os_info = 'macOS'
    elif 'linux' in user_agent and 'android' not in user_agent:
        os_info = 'Linux'
    elif 'android' in user_agent:
        os_info = 'Android'
    elif 'iphone' in user_agent or 'ipad' in user_agent or 'ipod' in user_agent:
        os_info = 'iOS'
    
    return {
        'device_type': device_type,
        'browser': browser,
        'os': os_info,
    }


def get_absolute_url(path=''):
    """
    Get the absolute URL for a given path.
    
    Args:
        path (str): The path to append to the base URL.
        
    Returns:
        str: The absolute URL.
    """
    return urljoin(settings.BASE_URL, path.lstrip('/'))


def format_short_url(short_code):
    """
    Format a short code as a full short URL.
    
    Args:
        short_code (str): The short code.
        
    Returns:
        str: The full short URL.
    """
    return urljoin(settings.BASE_URL, short_code)
