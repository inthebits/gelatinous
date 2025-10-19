"""
Custom logout view that logs out of both Django/Evennia and Discourse.

This uses the Discourse API to log out the user server-side, then logs out
from Django and redirects home.

SETUP INSTRUCTIONS:
1. Configure in Django settings (server/conf/secret_settings.py):
   DISCOURSE_URL = "https://forum.gel.monster"
   DISCOURSE_API_KEY = "your_api_key"
   DISCOURSE_API_USERNAME = "system"

2. Override the default logout URL in your urls.py:
   path("auth/logout/", logout_with_discourse, name="logout"),

How it works:
- User clicks logout on Django
- Look up their Discourse user by external_id
- Call Discourse API to log them out server-side
- Log them out of Django
- Redirect home, logged out of both sites
"""

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect
from django.conf import settings
import requests


@require_http_methods(["GET", "POST"])
@login_required
def logout_with_discourse(request):
    """
    Log out the user from both Django/Evennia and Discourse.
    
    This view:
    1. Gets the user's Discourse user_id via external_id lookup
    2. Calls Discourse API to log them out (clears server-side session)
    3. Logs the user out of Django
    4. Redirects home
    
    Note: This only clears the server-side Discourse session. The browser
    cookies will be cleared on next page load when Discourse sees the 
    invalid session.
    
    Configuration:
        DISCOURSE_URL (required): Your Discourse forum URL
        DISCOURSE_API_KEY (required): Admin API key
        DISCOURSE_API_USERNAME (required): API username (usually "system")
    """
    user = request.user
    
    # Get Discourse configuration
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    api_key = getattr(settings, 'DISCOURSE_API_KEY', None)
    api_username = getattr(settings, 'DISCOURSE_API_USERNAME', 'system')
    
    # Try to log out from Discourse if API is configured
    if api_key and user.is_authenticated:
        try:
            # Use the user's ID as external_id to look up their Discourse account
            external_id = str(user.id)
            
            # Look up user by external_id
            lookup_url = f"{discourse_url}/users/by-external/{external_id}.json"
            headers = {
                "Api-Key": api_key,
                "Api-Username": api_username,
            }
            
            response = requests.get(lookup_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                user_data = response.json()
                discourse_user_id = user_data.get('user', {}).get('id')
                
                if discourse_user_id:
                    # Log out the Discourse user
                    logout_url = f"{discourse_url}/admin/users/{discourse_user_id}/log_out"
                    requests.post(logout_url, headers=headers, timeout=5)
        
        except Exception:
            # If Discourse logout fails, still log out from Django
            pass
    
    # Log out from Django
    logout(request)
    
    # Redirect to home page
    return redirect('/')
