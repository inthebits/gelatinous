"""
Custom authentication backend for email-based login.

This allows users to log into the website using their email address
instead of their username, matching the telnet email-based login system.
"""

from django.contrib.auth.backends import ModelBackend
from evennia.accounts.models import AccountDB


class EmailAuthenticationBackend(ModelBackend):
    """
    Authenticate using email address instead of username.
    
    This backend allows the Django web login to accept email addresses,
    aligning with the telnet email-based login system.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by email address.
        
        Args:
            request: The HTTP request object
            username: Actually contains the email address from the login form
            password: User's password
            
        Returns:
            Account object if authentication succeeds, None otherwise
        """
        if username is None or password is None:
            return None
            
        try:
            # Try to find account by email (case-insensitive)
            account = AccountDB.objects.get(email__iexact=username)
            
            # Check password
            if account.check_password(password):
                # Set backend attribute required by Django
                account.backend = "web.utils.auth_backends.EmailAuthenticationBackend"
                return account
            else:
                return None
                
        except AccountDB.DoesNotExist:
            # Email not found - return None
            return None
        except AccountDB.MultipleObjectsReturned:
            # Multiple accounts with same email - shouldn't happen but handle it
            return None

    def get_user(self, user_id):
        """
        Get user by ID (required by ModelBackend).
        
        Args:
            user_id: The user's database ID
            
        Returns:
            Account object or None
        """
        try:
            return AccountDB.objects.get(pk=user_id)
        except AccountDB.DoesNotExist:
            return None
