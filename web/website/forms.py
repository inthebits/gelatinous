"""
Django forms for Gelatinous Monster character creation and account registration.

Extends Evennia's default forms to add GRIM stat system, name structure,
and Cloudflare Turnstile verification.
"""

from django import forms
from evennia.web.website.forms import (
    CharacterForm as EvenniaCharacterForm,
    AccountForm as EvenniaAccountForm
)


# Constants from telnet character creation
GRIM_TOTAL_POINTS = 300
GRIM_MIN = 1
GRIM_MAX = 150

SEX_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('ambiguous', 'Ambiguous'),
]


class CharacterForm(EvenniaCharacterForm):
    """
    Extends Evennia's default CharacterForm with GRIM stats and name structure.
    
    GRIM System:
    - Grit: Physical power and endurance
    - Resonance: Psychic affinity and willpower
    - Intellect: Logic, memory, and reasoning
    - Motorics: Dexterity, reflexes, and coordination
    
    Total points must equal 300.
    """
    
    # Name fields (split from db_key)
    first_name = forms.CharField(
        max_length=30,
        min_length=2,
        label="First Name",
        help_text="Your character's first name (2-30 characters)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        min_length=2,
        label="Last Name",
        help_text="Your character's last name (2-30 characters)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    
    # Sex/Gender
    sex = forms.ChoiceField(
        choices=SEX_CHOICES,
        initial='ambiguous',
        label="Sex",
        help_text="Biological sex presentation",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # GRIM Stats
    grit = forms.IntegerField(
        min_value=GRIM_MIN,
        max_value=GRIM_MAX,
        initial=75,
        label="Grit",
        help_text="Physical power and endurance (1-150)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control grim-stat',
            'data-stat': 'grit',
            'value': '75'
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
            'data-stat': 'resonance',
            'value': '75'
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
            'data-stat': 'intellect',
            'value': '75'
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
            'data-stat': 'motorics',
            'value': '75'
        })
    )
    
    class Meta(EvenniaCharacterForm.Meta):
        # Extend parent's fields with our custom fields
        fields = ('first_name', 'last_name', 'sex', 'desc', 'grit', 'resonance', 'intellect', 'motorics')
    
    def clean_first_name(self):
        """Validate first name format."""
        import re
        name = self.cleaned_data.get('first_name', '').strip()
        
        if not re.match(r"^[a-zA-Z][a-zA-Z\-']*[a-zA-Z]$", name):
            raise forms.ValidationError(
                "Name must start and end with a letter, and contain only letters, hyphens, and apostrophes."
            )
        
        return name
    
    def clean_last_name(self):
        """Validate last name format."""
        import re
        name = self.cleaned_data.get('last_name', '').strip()
        
        if not re.match(r"^[a-zA-Z][a-zA-Z\-']*[a-zA-Z]$", name):
            raise forms.ValidationError(
                "Name must start and end with a letter, and contain only letters, hyphens, and apostrophes."
            )
        
        return name
    
    def clean(self):
        """
        Validate that GRIM stats total exactly 300 points.
        
        IntegerField automatically converts values to int during field cleaning,
        so by the time we get here, values should already be integers.
        """
        cleaned_data = super().clean()
        
        # IntegerField should have already converted these to int
        # If a field failed validation, it won't be in cleaned_data
        grit = cleaned_data.get('grit', 0)
        resonance = cleaned_data.get('resonance', 0)
        intellect = cleaned_data.get('intellect', 0)
        motorics = cleaned_data.get('motorics', 0)
        
        # Sanity check: ensure they're actually integers
        if not all(isinstance(v, int) for v in [grit, resonance, intellect, motorics]):
            # Force conversion if needed (shouldn't happen with IntegerField)
            grit = int(grit) if grit else 0
            resonance = int(resonance) if resonance else 0
            intellect = int(intellect) if intellect else 0
            motorics = int(motorics) if motorics else 0
        
        total = grit + resonance + intellect + motorics
        
        if total != GRIM_TOTAL_POINTS:
            raise forms.ValidationError(
                f"GRIM stats must total exactly {GRIM_TOTAL_POINTS} points. "
                f"Current total: {total} points."
            )
        
        return cleaned_data


class TurnstileAccountForm(EvenniaAccountForm):
    """
    Extends Evennia's AccountForm with Cloudflare Turnstile verification.
    
    Adds a hidden field to capture the Turnstile response token,
    which is validated server-side in the view.
    
    Overrides email field to make it required (critical for password resets).
    """
    
    # Hidden field to store Turnstile response token
    # This is populated by the Turnstile JavaScript widget
    cf_turnstile_response = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
        error_messages={
            'required': 'CAPTCHA verification is required. Please complete the verification.'
        }
    )
    
    def __init__(self, *args, **kwargs):
        """Override email field to make it required."""
        super().__init__(*args, **kwargs)
        # Make email required and update help text
        self.fields['email'].required = True
        self.fields['email'].help_text = "A valid email address. Required for password resets."
        self.fields['email'].error_messages = {
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    
    class Meta(EvenniaAccountForm.Meta):
        # Extend parent's fields with Turnstile response
        fields = EvenniaAccountForm.Meta.fields + ('cf_turnstile_response',)

