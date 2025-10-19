"""
DiscourseConnect Session Sync

This view automatically syncs a Django user's session with Discourse using the
/admin/users/sync_sso endpoint. This ensures that users logged into Django are
automatically logged into Discourse without needing to click a login button.

Setup:
1. Configure settings in server/conf/secret_settings.py:
   DISCOURSE_URL = 'https://forum.example.com'
   DISCOURSE_SSO_SECRET = 'your-sso-secret-here'
   DISCOURSE_API_KEY = 'your-api-key-here'
   DISCOURSE_API_USERNAME = 'system'

2. Add to your base template (or specific pages where you want auto-sync):
   {% if user.is_authenticated %}
   <script>
     // Trigger session sync when page loads
     fetch("{% url 'discourse-session-sync' %}", {
       method: 'POST',
       headers: {
         'X-CSRFToken': '{{ csrf_token }}'
       }
     });
   </script>
   {% endif %}

3. Or use middleware to sync on every request (see middleware example below)

How it works:
- When called, creates a signed SSO payload with user data
- Makes API call to Discourse /admin/users/sync_sso endpoint
- Discourse creates or updates user and establishes session
- User is now logged into both Django and Discourse simultaneously

Reference:
https://meta.discourse.org/t/sync-discourseconnect-user-data-with-the-sync-sso-route/84398
"""

import base64
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Try Evennia logger first, fall back to standard logging
try:
    from evennia.utils import logger
except ImportError:
    logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@login_required
def discourse_session_sync(request):
    """
    Sync logged-in Django user's session with Discourse.
    
    This endpoint should be called automatically for logged-in users to ensure
    they're also logged into Discourse. It uses the /admin/users/sync_sso
    endpoint which creates or updates the user on Discourse.
    
    Returns:
        JsonResponse: Success status and any relevant information
    """
    user = request.user
    
    # Get configuration
    discourse_url = getattr(settings, 'DISCOURSE_URL', None)
    sso_secret = getattr(settings, 'DISCOURSE_SSO_SECRET', None)
    api_key = getattr(settings, 'DISCOURSE_API_KEY', None)
    api_username = getattr(settings, 'DISCOURSE_API_USERNAME', 'system')
    
    # Validate configuration
    if not all([discourse_url, sso_secret, api_key]):
        logger.warning("DiscourseConnect session sync: Missing configuration")
        return JsonResponse({
            'success': False,
            'message': 'Discourse configuration incomplete'
        }, status=500)
    
    try:
        # Build SSO payload
        sso_params = {
            'external_id': str(user.id),
            'email': user.email,
            'username': user.username,
            'name': user.get_full_name() or user.username,
            # Include require_activation if email isn't verified
            # 'require_activation': 'true' if not user.email else 'false',
        }
        
        # Encode payload
        payload = base64.b64encode(urlencode(sso_params).encode('utf-8')).decode('utf-8')
        
        # Generate signature
        signature = hmac.new(
            sso_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Make API request to sync_sso endpoint
        sync_url = f"{discourse_url}/admin/users/sync_sso"
        headers = {
            'Api-Key': api_key,
            'Api-Username': api_username,
        }
        data = {
            'sso': payload,
            'sig': signature,
        }
        
        response = requests.post(sync_url, headers=headers, data=data, timeout=5)
        
        if response.status_code == 200:
            logger.info(f"DiscourseConnect session sync: Successfully synced user {user.username}")
            return JsonResponse({
                'success': True,
                'message': 'Session synced with Discourse'
            })
        else:
            logger.warning(
                f"DiscourseConnect session sync: Failed for user {user.username}. "
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return JsonResponse({
                'success': False,
                'message': f'Discourse sync failed: {response.status_code}'
            }, status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"DiscourseConnect session sync: Network error for user {user.username}: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Network error connecting to Discourse'
        }, status=503)
        
    except Exception as e:
        logger.error(f"DiscourseConnect session sync: Unexpected error for user {user.username}: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Unexpected error during sync'
        }, status=500)


# OPTIONAL: Middleware approach for automatic sync
"""
To use middleware approach instead of manual fetch, add this to your MIDDLEWARE in settings.py:

MIDDLEWARE = [
    ...
    'web.website.middleware.DiscourseSessionSyncMiddleware',
    ...
]

Then create web/website/middleware.py:

from django.conf import settings
from django.contrib.auth.decorators import login_required
import base64
import hmac
import hashlib
import requests
from urllib.parse import urlencode

class DiscourseSessionSyncMiddleware:
    '''
    Automatically sync logged-in users with Discourse on every request.
    
    Note: This adds overhead to every request. Consider using:
    - Caching to only sync once per session
    - Only syncing on specific URL patterns
    - Using the fetch approach in templates instead
    '''
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Only sync for authenticated users
        if request.user.is_authenticated:
            # Check if we've already synced this session
            if not request.session.get('discourse_synced'):
                self._sync_user_session(request.user)
                request.session['discourse_synced'] = True
        
        response = self.get_response(request)
        return response
    
    def _sync_user_session(self, user):
        '''Sync user session with Discourse'''
        discourse_url = getattr(settings, 'DISCOURSE_URL', None)
        sso_secret = getattr(settings, 'DISCOURSE_SSO_SECRET', None)
        api_key = getattr(settings, 'DISCOURSE_API_KEY', None)
        api_username = getattr(settings, 'DISCOURSE_API_USERNAME', 'system')
        
        if not all([discourse_url, sso_secret, api_key]):
            return
        
        try:
            sso_params = {
                'external_id': str(user.id),
                'email': user.email,
                'username': user.username,
                'name': user.get_full_name() or user.username,
            }
            
            payload = base64.b64encode(urlencode(sso_params).encode('utf-8')).decode('utf-8')
            signature = hmac.new(
                sso_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            sync_url = f"{discourse_url}/admin/users/sync_sso"
            headers = {
                'Api-Key': api_key,
                'Api-Username': api_username,
            }
            data = {
                'sso': payload,
                'sig': signature,
            }
            
            requests.post(sync_url, headers=headers, data=data, timeout=5)
        except Exception:
            # Silently fail - don't break the request if sync fails
            pass
"""
