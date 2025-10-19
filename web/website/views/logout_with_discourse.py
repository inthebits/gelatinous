"""
Django logout view with Discourse logout synchronization.

When a user logs out from Django, we redirect their browser to Discourse's
logout endpoint. Discourse will clear its cookies and then redirect back to
Django via the 'logout_redirect' setting, which points to discourse_logout view.

This creates a logout flow:
Django logout → Discourse /logout → Django discourse_logout → Home page
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
    Initiate logout from both Django and Discourse.
    
    1. Log out from Django first (clear Django session)
    2. Redirect browser to Discourse's logout page
    3. Discourse clears its cookies
    4. Discourse redirects to logout_redirect setting (Django discourse_logout)
    5. discourse_logout confirms and redirects to home
    """
    # Log out from Django first
    logout(request)
    
    # Get Discourse URL
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    
    # Redirect to Discourse's logout page
    # Discourse will handle its logout and redirect via logout_redirect setting
    logout_url = f"{discourse_url}/logout"
    
    return HttpResponseRedirect(logout_url)
