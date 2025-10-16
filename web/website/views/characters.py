"""
Character creation views for Gelatinous Monster.

Extends Evennia's default character creation system with GRIM stats
and flash cloning support. Uses a smart single-page approach that
automatically detects respawn vs. first-time creation.
"""

from django.contrib import messages
from django.shortcuts import redirect
from evennia.web.website.views.characters import (
    CharacterCreateView as EvenniaCharacterCreateView
)

# Import our extended form
from web.website import forms

# Import telnet character creation functions for code reuse
from commands.charcreate import generate_random_template, create_flash_clone


class CharacterCreateView(EvenniaCharacterCreateView):
    """
    Smart character creation view that handles both:
    1. First-time character creation with custom GRIM stats
    2. Flash clone respawn after character death
    
    The view automatically detects if the account has archived (dead)
    characters and adapts the interface accordingly. This provides a
    unified experience at /characters/create/ regardless of whether
    the player is creating their first character or respawning.
    """
    
    # Use our extended form with GRIM fields
    form_class = forms.CharacterForm
    
    def get_context_data(self, **kwargs):
        """
        Add respawn context if account has archived characters.
        
        If archived characters exist, provides:
        - is_respawn: Flag indicating this is a respawn scenario
        - last_character: Most recent archived character (for flash clone)
        - random_templates: 3 alternative templates to choose from
        
        Otherwise provides standard character creation context.
        """
        context = super().get_context_data(**kwargs)
        
        # Check if this account has any archived (dead) characters
        account = self.request.user
        archived_chars = account.db_characters_all.filter(
            db_archived=True
        ).order_by('-db_date_created')
        
        if archived_chars.exists():
            # Respawn scenario - provide flash clone + templates
            context['is_respawn'] = True
            context['last_character'] = archived_chars.first()
            context['random_templates'] = [
                generate_random_template() for _ in range(3)
            ]
        else:
            # First-time creation - standard form
            context['is_respawn'] = False
        
        return context
    
    def form_valid(self, form):
        """
        Handle character creation with three possible paths:
        1. Flash clone: Copy stats from most recent archived character
        2. Template: Use one of the randomly generated templates
        3. Custom: Use the form data submitted by player
        
        The path is determined by the 'respawn_choice' POST parameter,
        which is only present when is_respawn=True in the template.
        """
        account = self.request.user
        respawn_choice = self.request.POST.get('respawn_choice')
        
        # PATH 1: Flash Clone (exact copy of last character)
        if respawn_choice == 'flash_clone':
            archived_chars = account.db_characters_all.filter(
                db_archived=True
            ).order_by('-db_date_created')
            
            if archived_chars.exists():
                last_character = archived_chars.first()
                new_character = create_flash_clone(account, last_character)
                
                messages.success(
                    self.request,
                    f"Flash clone '{new_character.name}' created from Stack backup. "
                    f"Consciousness restored with original GRIM configuration."
                )
                return redirect('character-detail', pk=new_character.id)
        
        # PATH 2: Template Selection (use generated template)
        elif respawn_choice and respawn_choice.startswith('template_'):
            # Extract template index from choice (e.g., 'template_0' -> 0)
            try:
                template_index = int(respawn_choice.split('_')[1])
                # Re-generate templates to match the ones shown
                # (Note: In production, might want to store in session)
                templates = [generate_random_template() for _ in range(3)]
                
                if template_index < len(templates):
                    template = templates[template_index]
                    
                    # Create character using parent's logic first
                    response = super().form_valid(form)
                    character = self.object
                    
                    if character:
                        # Override with template stats
                        character.db.grit = template['grit']
                        character.db.resonance = template['resonance']
                        character.db.intellect = template['intellect']
                        character.db.motorics = template['motorics']
                        character.db.stack_name_first = template['name_first']
                        character.db.stack_name_last = template['name_last']
                        character.db.stack_sex = template['sex']
                        character.db.stack_skintone = template['skintone']
                        character.db.death_count = 0
                        
                        messages.success(
                            self.request,
                            f"Character '{character.name}' created from template Sleeve."
                        )
                    
                    return response
            except (ValueError, IndexError):
                # Invalid template index, fall through to custom creation
                pass
        
        # PATH 3: Custom Character (standard form submission)
        # This is also the fallback if anything goes wrong above
        response = super().form_valid(form)
        character = self.object
        
        if character:
            # Set GRIM stats from form
            character.db.grit = form.cleaned_data['grit']
            character.db.resonance = form.cleaned_data['resonance']
            character.db.intellect = form.cleaned_data['intellect']
            character.db.motorics = form.cleaned_data['motorics']
            
            # Initialize Stack attributes for flash cloning
            char_name = form.cleaned_data.get('db_key', character.key)
            name_parts = char_name.split(maxsplit=1)
            character.db.stack_name_first = name_parts[0]
            character.db.stack_name_last = name_parts[1] if len(name_parts) > 1 else ""
            character.db.stack_sex = "ambiguous"  # Default, can be enhanced later
            character.db.stack_skintone = "fair"   # Default, can be enhanced later
            
            # Initialize death tracking
            if not hasattr(character.db, 'death_count'):
                character.db.death_count = 0
            
            messages.success(
                self.request,
                f"Character '{character.name}' created with GRIM stats: "
                f"Grit {character.db.grit}, Resonance {character.db.resonance}, "
                f"Intellect {character.db.intellect}, Motorics {character.db.motorics}"
            )
        
        return response
