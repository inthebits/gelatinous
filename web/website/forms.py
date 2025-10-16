"""
Django forms for Gelatinous Monster character creation.

Extends Evennia's default CharacterForm to add GRIM stat system.
"""

from django import forms
from evennia.web.website.forms import CharacterForm as EvenniaCharacterForm


# Constants from telnet character creation
GRIM_TOTAL_POINTS = 300
GRIM_MIN = 1
GRIM_MAX = 150


class CharacterForm(EvenniaCharacterForm):
    """
    Extends Evennia's default CharacterForm with GRIM stats.
    
    GRIM System:
    - Grit: Physical power and endurance
    - Resonance: Psychic affinity and willpower
    - Intellect: Logic, memory, and reasoning
    - Motorics: Dexterity, reflexes, and coordination
    
    Total points must equal 300.
    """
    
    grit = forms.IntegerField(
        min_value=GRIM_MIN,
        max_value=GRIM_MAX,
        initial=75,
        label="Grit",
        help_text="Physical power and endurance (1-150)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control grim-stat',
            'placeholder': '75'
        })
    )
    
    resonance = forms.IntegerField(
        min_value=GRIM_MIN,
        max_value=GRIM_MAX,
        initial=75,
        label="Resonance",
        help_text="Psychic affinity and willpower (1-150)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control grim-stat',
            'placeholder': '75'
        })
    )
    
    intellect = forms.IntegerField(
        min_value=GRIM_MIN,
        max_value=GRIM_MAX,
        initial=75,
        label="Intellect",
        help_text="Logic, memory, and reasoning (1-150)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control grim-stat',
            'placeholder': '75'
        })
    )
    
    motorics = forms.IntegerField(
        min_value=GRIM_MIN,
        max_value=GRIM_MAX,
        initial=75,
        label="Motorics",
        help_text="Dexterity, reflexes, and coordination (1-150)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control grim-stat',
            'placeholder': '75'
        })
    )
    
    class Meta(EvenniaCharacterForm.Meta):
        # Extend parent's fields with GRIM stats
        fields = EvenniaCharacterForm.Meta.fields + ('grit', 'resonance', 'intellect', 'motorics')
    
    def clean(self):
        """
        Validate that GRIM stats total exactly 300 points.
        """
        cleaned_data = super().clean()
        
        grit = cleaned_data.get('grit', 0)
        resonance = cleaned_data.get('resonance', 0)
        intellect = cleaned_data.get('intellect', 0)
        motorics = cleaned_data.get('motorics', 0)
        
        total = grit + resonance + intellect + motorics
        
        if total != GRIM_TOTAL_POINTS:
            raise forms.ValidationError(
                f"GRIM stats must total exactly {GRIM_TOTAL_POINTS} points. "
                f"Current total: {total} points."
            )
        
        return cleaned_data
