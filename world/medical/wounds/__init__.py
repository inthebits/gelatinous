"""
Wound Description System

Phase 2.4 implementation for wound descriptions and longdesc integration.
Provides automatic wound descriptions that change based on healing stage,
respect clothing concealment, and integrate with character longdesc.

Key Features:
- Multiple description variants per injury type and healing stage
- Red color coding for fresh wounds (|R....|n)
- Clothing/armor concealment system
- Grammatically correct compound descriptions
- Integration with medical system and longdesc

Usage:
    from world.medical.wounds import get_character_wound_display
    
    # Get formatted wound descriptions for longdesc
    wound_text = get_character_wound_display(character)
    
    # Update character's longdesc with current wounds
    update_character_longdesc_with_wounds(character)
"""

from .wound_descriptions import (
    get_wound_description,
    get_character_wounds,
    update_character_wounds
)

from .longdesc_hooks import (
    append_wounds_to_longdesc,
    get_standalone_wound_descriptions
)

from .constants import (
    WOUND_STAGES,
    INJURY_SEVERITY_MAP,
    get_location_display_name,
    MAX_WOUND_DESCRIPTIONS,
    MEDICAL_COLORS
)

# Main exports for easy import
__all__ = [
    # Core wound functions
    'get_wound_description',
    'get_character_wounds', 
    'update_character_wounds',
    
    # Longdesc integration hooks
    'append_wounds_to_longdesc',
    'get_standalone_wound_descriptions',
    
    # Constants
    'WOUND_STAGES',
    'INJURY_SEVERITY_MAP',
    'get_location_display_name',
    'MAX_WOUND_DESCRIPTIONS',
    'MEDICAL_COLORS'
]
