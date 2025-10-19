"""
Custom logout view that logs out of both Django/Evennia and Discourse.

This extends Django's logout to also log the user out of Discourse via the
admin API when they log out from the main site. This ensures Single Sign-Out
(SSO logout) works in both directions.

SETUP INSTRUCTIONS:
1. Configure DISCOURSE_URL and DISCOURSE_SSO_SECRET in Django settings
2. Create a Discourse API key with permission to log out users:
   - In Discourse admin: API > New API Key
   - User Level: All Users
   - Scopes: users#log_out
   - Add the key to settings as DISCOURSE_API_KEY

3. Override the default logout URL in your urls.py:
   path("auth/logout/", logout_with_discourse, name="logout"),
"""

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect
from django.conf import settings
import requests
import hmac
import hashlib
import base64
from urllib.parse import urlencode


@require_http_methods(["GET", "POST"])
@login_required
def logout_with_discourse(request):
    """
    Log out the user from both Django/Evennia and Discourse.
    
    This view:
    1. Finds the user's Discourse account via external_id (Django user.id)
    2. Logs them out of Discourse via the admin API
    3. Logs them out of Django
    4. Redirects to home page
    
    Configuration:
        DISCOURSE_URL (required): Your Discourse forum URL
        DISCOURSE_API_KEY (required): Discourse API key with users#log_out scope
        DISCOURSE_API_USERNAME (optional): Admin username for API calls, default: "system"
    """
    # Get configuration
    discourse_url = getattr(settings, 'DISCOURSE_URL', None)
    api_key = getattr(settings, 'DISCOURSE_API_KEY', None)
    api_username = getattr(settings, 'DISCOURSE_API_USERNAME', 'system')
    
    # If Discourse is configured, try to log out from there too
    if discourse_url and api_key:
        try:
            # Find the Discourse user by external_id (our Django user.id)
            user_url = f"{discourse_url}/users/by-external/{request.user.id}.json"
            headers = {
                'Api-Key': api_key,
                'Api-Username': api_username,
            }
            
            # Get the Discourse user
            response = requests.get(user_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                discourse_user = response.json().get('user', {})
                discourse_user_id = discourse_user.get('id')
                
                if discourse_user_id:
                    # Log out the Discourse user
                    logout_url = f"{discourse_url}/admin/users/{discourse_user_id}/log_out"
                    logout_response = requests.post(logout_url, headers=headers, timeout=5)
                    
                    if logout_response.status_code == 200:
                        pass  # Successfully logged out of Discourse
                    else:
                        # Log warning but continue with Django logout
                        try:
                            from evennia.utils import logger
                            logger.log_warn(
                                f"Failed to log out user {request.user.username} from Discourse: "
                                f"Status {logout_response.status_code}"
                            )
                        except ImportError:
                            pass
        except requests.exceptions.RequestException as e:
            # Log warning but continue with Django logout
            try:
                from evennia.utils import logger
                logger.log_warn(
                    f"Error logging out user {request.user.username} from Discourse: {e}"
                )
            except ImportError:
                pass
    
    # Log out from Django
    logout(request)
    
    # Redirect to home page
    return redirect('/')
