"""
Custom logout view that logs out of both Django/Evennia and Discourse.

This extends Django's logout to redirect through Discourse's logout endpoint,
ensuring the user is logged out of both systems with proper cookie clearing.

SETUP INSTRUCTIONS:
1. Configure DISCOURSE_URL in Django settings (server/conf/secret_settings.py)
2. Set Discourse's logout_redirect setting to point back to Django logout handler
   (already configured: https://gel.monster/sso/discourse/logout/)

3. Override the default logout URL in your urls.py:
   path("auth/logout/", logout_with_discourse, name="logout"),

How it works:
- User clicks logout on Django
- Django logs them out
- Redirects to Discourse's main logout page
- Discourse clears its session cookies
- Discourse redirects back to /sso/discourse/logout/ (discourse_logout view)
- User arrives at home page, logged out of both sites
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
    2. Redirects to Discourse's logout page
    3. Discourse clears its session cookies and redirects via logout_redirect
    4. discourse_logout view confirms Django logout and redirects home
    5. User ends up at home page, logged out of both systems
    
    Configuration:
        DISCOURSE_URL (required): Your Discourse forum URL
    """
    # Log out from Django first
    logout(request)
    
    # Get Discourse URL
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    
    # Redirect to Discourse's standard logout endpoint
    # Discourse will clear cookies and redirect to logout_redirect setting
    logout_url = f"{discourse_url}/logout"
    
    return HttpResponseRedirect(logout_url)
