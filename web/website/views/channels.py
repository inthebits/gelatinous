"""
Staff-only channel views for Gelatinous Monster.

Restricts channel list and detail pages to staff members only.
"""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from evennia.web.website.views.channels import (
    ChannelListView as EvenniaChannelListView,
    ChannelDetailView as EvenniaChannelDetailView
)


class StaffChannelListView(EvenniaChannelListView):
    """
    Staff-only channel list view.
    
    Restricts access to the channel list to staff members only.
    Regular players attempting to access this page will be redirected.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is staff before allowing access."""
        if not request.user.is_staff:
            messages.error(request, "You must be a staff member to access the channel list.")
            return HttpResponseRedirect(reverse_lazy("index"))
        return super().dispatch(request, *args, **kwargs)


class StaffChannelDetailView(EvenniaChannelDetailView):
    """
    Staff-only channel detail view.
    
    Restricts access to channel details to staff members only.
    Regular players attempting to access this page will be redirected.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is staff before allowing access."""
        if not request.user.is_staff:
            messages.error(request, "You must be a staff member to access channel details.")
            return HttpResponseRedirect(reverse_lazy("index"))
        return super().dispatch(request, *args, **kwargs)
