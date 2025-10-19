"""
Custom logout view that logs out of both Django/Evennia and Discourse.

This extends Django's logout to redirect through Discourse's logout endpoint,
ensuring the user is logged out of both systems with proper cookie clearing.

SETUP INSTRUCTIONS:
1. Configure DISCOURSE_URL in Django settings (server/conf/secret_settings.py)
2. Set Discourse's logout_redirect setting to point back to this view
   (already configured: https://gel.monster/sso/discourse/logout/)

3. Override the default logout URL in your urls.py:
   path("auth/logout/", logout_with_discourse, name="logout"),

How it works:
- User clicks logout
- Django logs them out
- Redirects to Discourse /session/sso_logout
- Discourse clears its session cookies
- Discourse redirects back to /sso/discourse/logout/ (discourse_logout view)
- discourse_logout view confirms Django logout and redirects home
"""

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.conf import settings


@require_http_methods(["GET", "POST"])
@login_required
def logout_with_discourse(request):
    """
    Log out the user from both Django/Evennia and Discourse.
    
    This view:
    1. Logs the user out of Django
    2. Redirects to Discourse's logout endpoint
    3. Discourse clears its session cookies
    4. Discourse redirects back to our discourse_logout view
    5. User ends up at home page, logged out of both systems
    
    Configuration:
        DISCOURSE_URL (required): Your Discourse forum URL
    """
    # Log out from Django first
    logout(request)
    
    # Get Discourse URL
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    
    # Redirect to Discourse's logout endpoint
    # This will clear Discourse session cookies, then redirect to logout_redirect
    # which points to our discourse_logout view
    logout_url = f"{discourse_url}/session/sso_logout"
    
    return HttpResponseRedirect(logout_url)
