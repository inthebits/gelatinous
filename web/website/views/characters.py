"""
Django views for Gelatinous Monster character creation.

Extends Evennia's default CharacterCreateView to add GRIM stats and archiving.
"""

import time
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.text import slugify
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
        
        # Check character slot availability (excluding archived characters)
        # Characters with db.archived == True should not count toward the limit
        active_characters = []
        for char in account.characters:
            # Check if archived attribute exists and is True
            if not char.attributes.get('archived', default=False):
                active_characters.append(char)
        
        from django.conf import settings
        max_chars = settings.MAX_NR_CHARACTERS
        
        if max_chars is not None and len(active_characters) >= max_chars:
            from evennia.utils.ansi import strip_ansi
            error_msg = strip_ansi(f"You may only have a maximum of {max_chars} active character(s). Archive an existing sleeve to create a new one.")
            messages.error(self.request, error_msg)
            return self.form_invalid(form)
        
        # Extract name components and build full name
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        charname = f"{first_name} {last_name}"
        
        # Extract other form data
        description = form.cleaned_data.get('desc', '')
        sex = form.cleaned_data['sex']
        
        # Get START_LOCATION for character spawn point
        from django.conf import settings
        from evennia.objects.models import ObjectDB
        start_location = ObjectDB.objects.get_id(settings.START_LOCATION)
        
        # Create character using typeclass.create() - returns (character, errors)
        character, errors = self.typeclass.create(
            charname, account, description=description, location=start_location, home=start_location
        )
        
        if errors:
            # Strip Evennia color codes from error messages before displaying on web
            from evennia.utils.ansi import strip_ansi
            clean_errors = [strip_ansi(str(err)) for err in errors]
            [messages.error(self.request, err) for err in clean_errors]
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


class CharacterArchiveView(LoginRequiredMixin, CharacterMixin, View):
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
    
    def get(self, request, *args, **kwargs):
        """Display the archive confirmation page."""
        # Get the character using pk from URL
        pk = kwargs.get('pk')
        slug_param = kwargs.get('slug')
        
        # Get character from database
        try:
            character = self.typeclass.objects.get(pk=pk)
            
            # Verify slug matches
            if slugify(character.name) != slug_param:
                raise Http404("Character not found")
            
            # Verify ownership (user must be in character's account's characters)
            if character not in request.user.characters:
                raise PermissionDenied("You don't have permission to archive this character")
                
        except self.typeclass.DoesNotExist:
            raise Http404("Character not found")
        
        # Render confirmation template
        return render(request, self.template_name, {'object': character})
    
    def post(self, request, *args, **kwargs):
        """Handle the archive action."""
        # Get the character using pk from URL
        pk = kwargs.get('pk')
        slug_param = kwargs.get('slug')
        
        # Get character (same validation as GET)
        try:
            character = self.typeclass.objects.get(pk=pk)
            
            # Verify slug matches
            if slugify(character.name) != slug_param:
                raise Http404("Character not found")
            
            # Verify ownership
            if character not in request.user.characters:
                raise PermissionDenied("You don't have permission to archive this character")
                
        except self.typeclass.DoesNotExist:
            raise Http404("Character not found")
        
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
