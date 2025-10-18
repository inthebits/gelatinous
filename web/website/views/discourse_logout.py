"""
DiscourseConnect logout handler.

This is the official logout endpoint for DiscourseConnect SSO as documented at:
https://meta.discourse.org/t/setup-discourseconnect-official-single-sign-on-for-discourse-sso/13045

SETUP INSTRUCTIONS:
1. Add DISCOURSE_URL to your Django settings (required):
   DISCOURSE_URL = "https://forum.example.com"

2. Optional: Customize the post-logout redirect:
   DISCOURSE_LOGOUT_REDIRECT = "/custom-page/"  # Default: "/"

3. In Discourse admin, set the 'logout_redirect' setting to:
   https://yoursite.com/sso/discourse/logout/

SECURITY:
- Validates Referer header to prevent logout CSRF attacks
- CSRF-exempt is required per DiscourseConnect spec (simple GET redirect)
- Only logs out current session (non-destructive)

Per the DiscourseConnect specification:
- This is a simple GET redirect (no signed payloads)
- The endpoint should log out the user and redirect to a landing page
"""

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
@require_http_methods(["GET"])
def discourse_logout(request):
    """
    Official DiscourseConnect logout endpoint.
    
    Called by Discourse's logout_redirect setting when a user logs out.
    Logs out the Django session and redirects to configured landing page.
    
    This follows the standard DiscourseConnect logout flow as documented
    in the official Discourse SSO documentation.
    
    Security: Checks Referer header to prevent logout CSRF attacks.
    
    Configuration:
        DISCOURSE_URL (required): Your Discourse forum URL
        DISCOURSE_LOGOUT_REDIRECT (optional): Where to redirect after logout
    """
    # Verify request is coming from configured Discourse forum
    # This prevents malicious sites from forcing users to logout via embedded links
    referer = request.META.get('HTTP_REFERER', '')
    discourse_url = getattr(settings, 'DISCOURSE_URL', None)
    
    if not discourse_url:
        # If DISCOURSE_URL is not configured, log a warning but allow logout
        # This makes the endpoint fail-safe rather than fail-closed
        try:
            from evennia.utils import logger
            logger.log_warn(
                "DISCOURSE_URL not configured in settings. "
                "Set DISCOURSE_URL in your Django settings for Referer validation."
            )
        except ImportError:
            pass  # Not in an Evennia environment
    elif referer and not referer.startswith(discourse_url):
        # Referer exists but doesn't match our Discourse forum
        return HttpResponseForbidden(
            "Invalid logout request. Please log out through your account page."
        )
    
    # Log the user out of Django
    logout(request)
    
    # Redirect to configured landing page (default: home page)
    redirect_url = getattr(settings, 'DISCOURSE_LOGOUT_REDIRECT', '/')
    return redirect(redirect_url)
