"""Custom template filters for the shortener app."""

from django import template

register = template.Library()


@register.filter(name='abs')
def absolute_value(value):
    """Return the absolute value of a number."""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value
