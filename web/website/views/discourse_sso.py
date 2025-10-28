"""
Discourse SSO (DiscourseConnect) Provider

Handles SSO authentication requests from Discourse forum.
Users authenticate via Django/Evennia and are automatically logged into Discourse.

SSO Flow:
1. User clicks "Login" on Discourse
2. Discourse redirects to this endpoint with payload and signature
3. Django verifies signature, checks if user is logged in
4. Django generates response with user info
5. Redirects back to Discourse with signed payload
6. Discourse logs user in automatically

References:
- https://meta.discourse.org/t/discourseconnect-official-single-sign-on-for-discourse-sso/13045
"""

import base64
import hmac
import hashlib
from urllib.parse import parse_qs, urlencode, unquote, urlparse, urlunparse
from django.utils.http import url_has_allowed_host_and_scheme

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.http import require_http_methods

import logging
logger = logging.getLogger(__name__)

def get_discourse_sso_secret():
    """Get the SSO secret from settings."""
    return getattr(settings, 'DISCOURSE_SSO_SECRET', None)


def verify_payload(payload, signature):
    """
    Verify that the payload signature is valid.
    
    Args:
        payload: Base64 encoded SSO payload from Discourse
        signature: HMAC-SHA256 signature of the payload
        
    Returns:
        bool: True if signature is valid
    """
    secret = get_discourse_sso_secret()
    if not secret:
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


def sign_payload(payload):
    """
    Sign a payload with HMAC-SHA256.
    
    Args:
        payload: String to sign
        
    Returns:
        str: Hexadecimal signature
    """
    secret = get_discourse_sso_secret()
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


@require_http_methods(["GET"])
@login_required
def discourse_sso(request):
    """
    Handle SSO authentication request from Discourse.
    
    Query Parameters:
        sso: Base64 encoded payload from Discourse containing nonce and return_sso_url
        sig: HMAC-SHA256 signature of the sso parameter
        
    Returns:
        HttpResponseRedirect: Redirects back to Discourse with signed user data
        HttpResponseBadRequest: If parameters are invalid or signature doesn't match
    """
    # Check if SSO is configured
    if not get_discourse_sso_secret():
        return HttpResponseBadRequest("SSO is not configured")
    
    # Get SSO parameters from request
    payload = request.GET.get('sso')
    signature = request.GET.get('sig')
    
    if not payload or not signature:
        return HttpResponseBadRequest("Missing SSO parameters")
    
    # Verify the payload signature
    if not verify_payload(payload, signature):
        return HttpResponseBadRequest("Invalid signature")
    
    # Decode the payload
    try:
        decoded_payload = base64.b64decode(payload).decode('utf-8')
        params = parse_qs(decoded_payload)
    except Exception as e:
        logger.exception("Failed to decode or parse SSO payload")
        return HttpResponseBadRequest("Invalid payload")
    
    # Extract nonce (required by Discourse)
    nonce = params.get('nonce', [None])[0]
    if not nonce:
        return HttpResponseBadRequest("Missing nonce in payload")
    
    # Get authenticated user
    user = request.user
    
    # Build response payload with user information
    response_params = {
        'nonce': nonce,
        'email': user.email,
        'external_id': str(user.id),  # User's Django ID
        'username': user.username,
        'name': user.get_full_name() or user.username,  # Full name or username fallback
    }
    
    # Optional: Add avatar URL if available
    # if hasattr(user, 'avatar_url'):
    #     response_params['avatar_url'] = user.avatar_url
    
    # Optional: Make user admin in Discourse
    # if user.is_superuser:
    #     response_params['admin'] = 'true'
    
    # Optional: Make user moderator in Discourse
    # if user.is_staff:
    #     response_params['moderator'] = 'true'
    
    # Encode response payload
    response_payload = base64.b64encode(urlencode(response_params).encode('utf-8')).decode('utf-8')
    
    # Sign the response payload
    response_signature = sign_payload(response_payload)
    
    # Get return URL from original payload
    return_sso_url = params.get('return_sso_url', [None])[0]
    if not return_sso_url:
        return HttpResponseBadRequest("Missing return_sso_url in payload")

    # Sanitize return_sso_url - remove backslashes to prevent bypass attacks
    sanitized_url = return_sso_url.replace('\\', '')
    
    # Validate the return URL to prevent open redirect attacks
    discourse_url = getattr(settings, 'DISCOURSE_URL', '')
    if not discourse_url:
        logger.error("DISCOURSE_URL not configured - SSO redirect blocked for security")
        return HttpResponseBadRequest("SSO not properly configured")
    
    parsed_discourse = urlparse(discourse_url)
    if not parsed_discourse.hostname:
        logger.error("Invalid DISCOURSE_URL configuration - SSO redirect blocked")
        return HttpResponseBadRequest("SSO not properly configured")
    
    allowed_hosts = [parsed_discourse.hostname]
    
    # Validate URL against allowlist - Django's recommended approach for preventing open redirects
    if not url_has_allowed_host_and_scheme(sanitized_url, allowed_hosts=allowed_hosts, require_https=False):
        logger.warning("SSO redirect to unauthorized host blocked: %s", sanitized_url)
        return HttpResponseBadRequest("Invalid return URL")

    # Parse and reconstruct the validated URL to break taint flow
    parsed_return_url = urlparse(sanitized_url)
    
    # Rebuild URL from validated components only
    safe_base_url = urlunparse((
        parsed_return_url.scheme,
        parsed_return_url.netloc,
        parsed_return_url.path,
        parsed_return_url.params,
        parsed_return_url.query,
        parsed_return_url.fragment
    ))
    
    # Build redirect URL with SSO response parameters
    separator = '&' if '?' in safe_base_url else '?'
    redirect_params = urlencode({'sso': response_payload, 'sig': response_signature})
    final_redirect_url = f"{safe_base_url}{separator}{redirect_params}"
    
    return HttpResponseRedirect(final_redirect_url)
