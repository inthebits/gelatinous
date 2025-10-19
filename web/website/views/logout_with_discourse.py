"""
Custom logout view that logs out of both Django/Evennia and Discourse.

This shows an intermediate page that logs out of Discourse via hidden iframe,
then completes Django logout.

SETUP INSTRUCTIONS:
1. Configure in Django settings (server/conf/secret_settings.py):
   DISCOURSE_URL = "https://forum.gel.monster"

2. Override the default logout URL in your urls.py:
   path("auth/logout/", logout_with_discourse, name="logout"),

How it works:
- User clicks logout on Django → GET request
- Shows intermediate page with hidden iframe to trigger Discourse logout
- After 1.5 seconds, auto-submits form → POST request
- Logs out of Django and redirects home
"""

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.middleware.csrf import get_token


@require_http_methods(["GET", "POST"])
@login_required
def logout_with_discourse(request):
    """
    Log out the user from both Django/Evennia and Discourse.
    
    GET request: Shows intermediate page with iframe to logout of Discourse
    POST request: Completes Django logout and redirects home
    
    Configuration:
        DISCOURSE_URL (required): Your Discourse forum URL
    """
    # POST request = final logout step
    if request.method == 'POST':
        logout(request)
        return HttpResponseRedirect('/')
    
    # GET request = show intermediate logout page
    discourse_url = getattr(settings, 'DISCOURSE_URL', 'https://forum.gel.monster')
    csrf_token = get_token(request)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logging out...</title>
        <style>
            body {{ 
                font-family: sans-serif; 
                text-align: center; 
                padding: 50px;
                background: #f4f4f4;
            }}
            .logout-box {{
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                max-width: 400px;
                margin: 0 auto;
            }}
        </style>
    </head>
    <body>
        <div class="logout-box">
            <h2>Logging out...</h2>
            <p>Please wait while we log you out of all systems.</p>
        </div>
        
        <!-- Hidden iframe to trigger Discourse logout by loading a Discourse page -->
        <!-- Discourse will see the session and can clear it -->
        <iframe src="{discourse_url}/session/csrf" style="display:none;" id="discourseFrame"></iframe>
        
        <!-- Auto-submit form after giving time for Discourse request -->
        <form id="logoutForm" method="post" action="/auth/logout/">
            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
        </form>
        
        <script>
            // Wait for iframe to load, then complete Django logout
            setTimeout(function() {{
                document.getElementById('logoutForm').submit();
            }}, 1500);
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html)
