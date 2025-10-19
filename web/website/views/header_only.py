"""
Header-only view for iframe embedding in Discourse.

This view renders just the navigation header without the full page layout,
allowing it to be embedded in an iframe on the Discourse forum while
maintaining visual consistency.
"""

from django.shortcuts import render


def header_only(request):
    """
    Render just the navbar for iframe embedding in Discourse.
    
    This minimal view provides the Django header with full functionality
    (authentication state, dropdowns, etc.) without page chrome.
    
    The header detects it's in an iframe context and adjusts link behavior
    to prevent double-header issues when navigating to Discourse.
    """
    context = {
        'game_name': 'Gelatinous Monster',
        'game_slogan': 'An abomination to behold',
        'account': request.user if request.user.is_authenticated else None,
        'webclient_enabled': True,
        'register_enabled': True,
        'rest_api_enabled': request.user.is_staff if request.user.is_authenticated else False,
        'is_iframe': True,  # Signal to template that this is iframe context
    }
    
    return render(request, 'website/header_only.html', context)
