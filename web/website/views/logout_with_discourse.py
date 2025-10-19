"""
Django logout view with Discourse logout synchronization using API.

Uses the official Discourse API endpoint to log out the user from Discourse.
The API invalidates the session in Discourse's database, which should cause
the browser's cookies to be treated as invalid on subsequent requests.

SETUP REQUIREMENTS:
1. DISCOURSE_URL in Django settings
2. DISCOURSE_API_KEY in Django settings (admin API key)
3. DISCOURSE_SSO_SECRET in Django settings (for SSO)

References:
- https://meta.discourse.org/t/logout-post-request/192601
- https://meta.discourse.org/t/discourseconnect-official-single-sign-on-for-discourse-sso/13045
"""

import requests
import hmac
import hashlib
import base64
from urllib.parse import urlencode, parse_qs
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect
from django.conf import settings


def get_discourse_user_id(user):
    """
    Get Discourse user ID for a Django user.
    For DiscourseConnect, this is the external_id which is the Django user ID.
    """
    from evennia.utils import logger
    
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    api_key = getattr(settings, 'DISCOURSE_API_KEY', None)
    
    logger.log_info(f"[DISCOURSE_LOGOUT] Attempting to get Discourse user ID for Django user {user.id}")
    logger.log_info(f"[DISCOURSE_LOGOUT] Discourse URL: {discourse_url}")
    logger.log_info(f"[DISCOURSE_LOGOUT] API key configured: {bool(api_key)}")
    
    if not api_key:
        logger.log_err("[DISCOURSE_LOGOUT] No API key configured!")
        return None
    
    # Use the by-external endpoint to find user by Django user ID
    url = f"{discourse_url}/users/by-external/{user.id}.json"
    headers = {
        'Api-Key': api_key,
        'Api-Username': 'system',
    }
    
    logger.log_info(f"[DISCOURSE_LOGOUT] Calling: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        logger.log_info(f"[DISCOURSE_LOGOUT] Response status: {response.status_code}")
        logger.log_info(f"[DISCOURSE_LOGOUT] Response body: {response.text[:200]}")
        
        if response.status_code == 200:
            user_data = response.json()
            discourse_user_id = user_data.get('user', {}).get('id')
            logger.log_info(f"[DISCOURSE_LOGOUT] Found Discourse user ID: {discourse_user_id}")
            return discourse_user_id
        else:
            logger.log_err(f"[DISCOURSE_LOGOUT] Failed to get user ID: {response.status_code} - {response.text}")
    except Exception as e:
        logger.log_trace(f"[DISCOURSE_LOGOUT] Exception fetching Discourse user ID: {e}")
    
    return None


def logout_discourse_user(discourse_user_id):
    """
    Log out a user from Discourse using the admin API.
    This invalidates their session in Discourse's database.
    """
    from evennia.utils import logger
    
    if not discourse_user_id:
        logger.log_warn("[DISCOURSE_LOGOUT] No discourse_user_id provided")
        return False
    
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    api_key = getattr(settings, 'DISCOURSE_API_KEY', None)
    
    if not api_key:
        logger.log_err("[DISCOURSE_LOGOUT] No API key configured for logout!")
        return False
    
    url = f"{discourse_url}/admin/users/{discourse_user_id}/log_out"
    headers = {
        'Api-Key': api_key,
        'Api-Username': 'system',
        'Content-Type': 'application/json',
    }
    
    logger.log_info(f"[DISCOURSE_LOGOUT] Calling logout API: {url}")
    
    try:
        response = requests.post(url, headers=headers, timeout=5)
        logger.log_info(f"[DISCOURSE_LOGOUT] Logout response status: {response.status_code}")
        logger.log_info(f"[DISCOURSE_LOGOUT] Logout response: {response.text[:200]}")
        
        success = response.status_code == 200
        if success:
            logger.log_info(f"[DISCOURSE_LOGOUT] Successfully logged out Discourse user {discourse_user_id}")
        else:
            logger.log_err(f"[DISCOURSE_LOGOUT] Failed to logout: {response.status_code} - {response.text}")
        return success
    except Exception as e:
        logger.log_trace(f"[DISCOURSE_LOGOUT] Exception logging out Discourse user: {e}")
        return False


@require_http_methods(["GET", "POST"])
@login_required
def logout_with_discourse(request):
    """
    Log out from both Django and Discourse.
    
    1. Look up Discourse user ID via external_id (Django user ID)
    2. Call Discourse API to invalidate their session
    3. Log out from Django
    4. Redirect to Django home page
    
    The API call invalidates the Discourse session in the database,
    so when the browser sends cookies on next request, they will be
    treated as invalid and the user will appear logged out.
    """
    from evennia.utils import logger
    
    user = request.user
    logger.log_info(f"[DISCOURSE_LOGOUT] User {user.username} (ID: {user.id}) initiating logout")
    
    # Try to logout from Discourse first
    discourse_user_id = get_discourse_user_id(user)
    if discourse_user_id:
        logger.log_info(f"[DISCOURSE_LOGOUT] Found Discourse user ID {discourse_user_id}, attempting logout")
        logout_discourse_user(discourse_user_id)
    else:
        logger.log_warn(f"[DISCOURSE_LOGOUT] Could not find Discourse user ID for Django user {user.id}")
    
    # Log out from Django
    logger.log_info(f"[DISCOURSE_LOGOUT] Logging out from Django")
    logout(request)
    
    # Redirect to home page
    logger.log_info(f"[DISCOURSE_LOGOUT] Redirecting to home page")
    return HttpResponseRedirect('/')
