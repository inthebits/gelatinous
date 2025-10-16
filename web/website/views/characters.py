"""
Django views for Gelatinous Monster character creation.

Extends Evennia's default CharacterCreateView to add GRIM stats and archiving.
"""

import time
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import View
from evennia.web.website.views.objects import ObjectCreateView, ObjectDetailView
from evennia.web.website.views.characters import (
    CharacterCreateView as EvenniaCharacterCreateView,
    CharacterMixin
)

# Import forms module (Evennia pattern)
from web.website import forms


class CharacterCreateView(EvenniaCharacterCreateView):
    """
    Extended character creation view with GRIM stats and name structure.
    
    Matches the telnet character creation in commands/charcreate.py:
    - Collects first name and last name separately
    - Collects sex (male/female/ambiguous)
    - Collects GRIM stat distribution (300 points total)
    - Sets all appropriate character attributes
    """
    
    # Use our extended form with GRIM fields (Evennia pattern: forms.ClassName)
    form_class = forms.CharacterForm
    
    def form_valid(self, form):
        """
        Handle character creation with GRIM stats and name structure.
        
        Follows Evennia's pattern: extract form data, call typeclass.create(),
        set additional attributes, return HttpResponseRedirect.
        """
        account = self.request.user
        
        # Extract name components and build full name
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        charname = f"{first_name} {last_name}"
        
        # Extract other form data
        description = form.cleaned_data.get('desc', '')
        sex = form.cleaned_data['sex']
        
        # Create character using typeclass.create() - returns (character, errors)
        character, errors = self.typeclass.create(charname, account, description=description)
        
        if errors:
            # Echo error messages to the user
            [messages.error(self.request, x) for x in errors]
            return self.form_invalid(form)
        
        if character:
            # Set GRIM stats (using AttributeProperty) - ensure integers
            character.grit = int(form.cleaned_data['grit'])
            character.resonance = int(form.cleaned_data['resonance'])
            character.intellect = int(form.cleaned_data['intellect'])
            character.motorics = int(form.cleaned_data['motorics'])
            
            # Set sex (using AttributeProperty)
            character.sex = sex
            
            # Set Stack/clone tracking (matching telnet charcreate.py)
            import uuid
            import time
            character.db.stack_id = str(uuid.uuid4())
            character.db.original_creation = time.time()
            character.db.current_sleeve_birth = time.time()
            character.db.archived = False
            # death_count defaults to 1 via AttributeProperty in Character class
            
            messages.success(
                self.request,
                f"Character '{character.name}' decanted successfully! "
                f"GRIM: Grit {character.grit}, Resonance {character.resonance}, "
                f"Intellect {character.intellect}, Motorics {character.motorics}"
            )
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(self.request, "Character creation failed.")
            return self.form_invalid(form)


class CharacterArchiveView(LoginRequiredMixin, ObjectDetailView, View):
    """
    Archive a character instead of deleting it.
    
    Sets character.db.archived = True rather than deleting from database.
    This preserves Stack tracking and death history.
    """
    
    # -- Django constructs --
    template_name = "website/character_confirm_archive.html"
    success_url = reverse_lazy("character-manage")
    
    # -- Evennia constructs --
    access_type = "delete"  # Use delete permission (user must own character)
    
    def get_queryset(self):
        """Override to only return characters owned by this account."""
        account = self.request.user
        ids = [getattr(x, "id") for x in account.characters if x]
        from typeclasses.characters import Character
        return Character.objects.filter(id__in=ids)
    
    def post(self, request, *args, **kwargs):
        """Handle the archive action."""
        # Get the character object (with permission check)
        character = self.get_object()
        
        # Archive instead of delete
        character.db.archived = True
        
        # Success message using character terminology
        messages.success(
            request,
            f"Sleeve '{character.name}' has been archived. "
            f"Stack ID preserved for future respawn."
        )
        
        # Redirect to character management page
        return HttpResponseRedirect(self.success_url)
