"""
Custom account views for Gelatinous Monster.

Extends Evennia's AccountCreateView with Cloudflare Turnstile verification.
"""

import requests
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from evennia.web.website.views.accounts import (
    AccountCreateView as EvenniaAccountCreateView
)
from web.website.forms import TurnstileAccountForm


class TurnstileAccountCreateView(EvenniaAccountCreateView):
    """
    Account creation view with Cloudflare Turnstile verification.
    
    Extends Evennia's default account creation to include CAPTCHA verification
    using Cloudflare Turnstile (free, privacy-friendly alternative to reCAPTCHA).
    """
    
    # -- Django constructs --
    template_name = "website/registration/register.html"
    success_url = reverse_lazy("login")
    form_class = TurnstileAccountForm
    
    def get_context_data(self, **kwargs):
        """Add Turnstile site key to template context."""
        context = super().get_context_data(**kwargs)
        context['turnstile_site_key'] = getattr(settings, 'TURNSTILE_SITE_KEY', '')
        return context
    
    def form_valid(self, form):
        """
        Validate form including Turnstile verification and duplicate checking.
        
        This extends the parent form_valid() to first verify the Cloudflare
        Turnstile response and ensure Django's form validation (including our
        custom clean_email() and clean_username() methods) has run before
        proceeding with account creation.
        
        Note: Evennia's AccountCreateView.form_valid() bypasses Django's
        standard form validation, so we must ensure it happens here.
        """
        from evennia.accounts.models import AccountDB
        from evennia.comms.models import ChannelDB
        
        # Get Turnstile response token from form
        turnstile_response = form.cleaned_data.get('cf_turnstile_response')
        
        # Verify Turnstile token with Cloudflare
        if not self.verify_turnstile(turnstile_response):
            form.add_error(None, "CAPTCHA verification failed. Please try again.")
            return self.form_invalid(form)
        
        # Django's form.is_valid() should have already been called by the framework,
        # which would have run our clean_email() and clean_username() validators.
        # However, Evennia's parent class bypasses this, so we need to verify
        # the form validation actually happened.
        
        # The cleaned_data existing means is_valid() was called, but let's be extra safe
        # and check that our custom validation methods would pass
        email = form.cleaned_data.get('email', '').strip()
        username = form.cleaned_data.get('username', '').strip()
        
        # Debug logging to Splattercast
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"REGISTRATION_DEBUG: Attempting registration - username='{username}', email='{email}'")
        except:
            pass
        
        # Double-check email uniqueness (shouldn't be needed if form validation ran)
        if email and AccountDB.objects.filter(email__iexact=email).exists():
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"REGISTRATION_BLOCKED: Duplicate email '{email}' detected")
            except:
                pass
            form.add_error('email', "An account with this email address already exists.")
            return self.form_invalid(form)
            
        # Double-check username uniqueness (shouldn't be needed if form validation ran)  
        if username and AccountDB.objects.filter(username__iexact=username).exists():
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"REGISTRATION_BLOCKED: Duplicate username '{username}' detected")
            except:
                pass
            form.add_error('username', "An account with this username already exists.")
            return self.form_invalid(form)
        
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"REGISTRATION_SUCCESS: Validation passed, creating account")
        except:
            pass
        
        # All validations passed - proceed with account creation
        return super().form_valid(form)
    
    def verify_turnstile(self, token):
        """
        Verify Cloudflare Turnstile response token.
        
        Args:
            token (str): The cf-turnstile-response token from the form
            
        Returns:
            bool: True if verification successful, False otherwise
        """
        # Get secret key from settings
        secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', None)
        
        if not secret_key:
            # If no secret key configured, log error and fail verification
            print("ERROR: TURNSTILE_SECRET_KEY not configured in settings")
            return False
        
        # Cloudflare Turnstile verification endpoint
        verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        
        # Prepare verification data
        data = {
            'secret': secret_key,
            'response': token,
            'remoteip': self.get_client_ip(),  # Optional but recommended
        }
        
        try:
            # Send verification request to Cloudflare
            response = requests.post(verify_url, data=data, timeout=10)
            result = response.json()
            
            # Check if verification was successful
            return result.get('success', False)
            
        except Exception as e:
            # Log error and fail verification
            print(f"Turnstile verification error: {e}")
            return False
    
    def get_client_ip(self):
        """
        Get the client's IP address from the request.
        
        Returns:
            str: Client IP address
        """
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

