"""
Django logout view with Discourse logout synchronization.

Uses the discourse-sso-logout pattern: redirect to Discourse with #logout hash,
which triggers a JavaScript snippet on Discourse that clears cookies.

SETUP INSTRUCTIONS:
1. Add this JavaScript to Discourse theme's </head> section:
   <script>
   if(window.location.hash=='#logout'){
       document.cookie = '_forum_session=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
       document.cookie = '_t=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
       document.location = 'https://gel.monster/';
   }
   </script>

2. Configure DISCOURSE_URL in Django settings

This approach is from: https://github.com/johnmap/discourse-sso-logout
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
    2. Redirect browser to Discourse with #logout hash
    3. JavaScript on Discourse detects hash and clears cookies
    4. JavaScript redirects back to Django home page
    
    This uses the discourse-sso-logout pattern since Discourse
    doesn't have a proper logout URL endpoint.
    """
    # Log out from Django first
    logout(request)
    
    # Get Discourse URL
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    
    # Redirect to Discourse with #logout hash
    # JavaScript on Discourse will detect this and clear cookies
    logout_url = f"{discourse_url}/#logout"
    
    return HttpResponseRedirect(logout_url)
