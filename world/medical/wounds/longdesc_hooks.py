"""
Longdesc Integration for Wound Descriptions

This module provides a simple hook into the existing longdesc system
to automatically append wound descriptions to body part descriptions.
"""

from .wound_descriptions import get_character_wounds, get_wound_description
from .constants import MAX_WOUND_DESCRIPTIONS


def append_wounds_to_longdesc(original_desc, character, location, looker=None):
    """
    Append wound descriptions to an existing longdesc for a body location.
    
    This function is designed to be called from the existing longdesc processing
    to seamlessly integrate wounds into body part descriptions.
    
    Args:
        original_desc (str): Original longdesc for this location
        character: Character object  
        location (str): Body location
        looker: Character looking (for future permission checks)
        
    Returns:
        str: Original description with wounds appended, or original if no wounds
    """
    # Get wounds visible at this location
    wounds = get_character_wounds(character)
    location_wounds = [w for w in wounds if w['location'] == location]
    
    if not location_wounds:
        return original_desc
    
    # Limit to most significant wounds to prevent spam
    significant_wounds = _prioritize_wounds_for_display(location_wounds)[:2]  # Max 2 per location
    
    # Generate wound descriptions
    wound_descriptions = []
    for wound in significant_wounds:
        wound_desc = get_wound_description(
            injury_type=wound['injury_type'],
            location=wound['location'],
            severity=wound['severity'], 
            stage=wound['stage'],
            organ=wound.get('organ'),
            character=character  # Pass character for skintone
        )
        wound_descriptions.append(wound_desc)
    
    # Append to original description
    if len(wound_descriptions) == 1:
        return f"{original_desc} {wound_descriptions[0]}."
    elif len(wound_descriptions) == 2:
        return f"{original_desc} {wound_descriptions[0]} and {wound_descriptions[1]}."
    
    return original_desc


def get_standalone_wound_locations(character):
    """
    Get locations that have wounds but no longdesc set.
    These wounds will need their own entries in the appearance.
    Uses character's actual anatomy from longdesc system.
    
    Args:
        character: Character object
        
    Returns:
        list: Locations with wounds but no longdesc
    """
    wounds = get_character_wounds(character)
    
    # Get character's actual anatomy locations
    if not hasattr(character, 'longdesc') or not character.longdesc:
        return []
    
    longdescs = character.longdesc
    
    wound_locations = set(w['location'] for w in wounds)
    
    # Only consider locations that exist in character's anatomy but have no description
    longdesc_locations = set(loc for loc, desc in longdescs.items() if desc is not None)
    
    # Locations with wounds but no longdesc
    standalone_locations = wound_locations - longdesc_locations
    
    return list(standalone_locations)


def get_standalone_wound_descriptions(character, looker=None):
    """
    Get wound descriptions for locations that don't have longdescs.
    
    Args:
        character: Character object
        looker: Character looking
        
    Returns:
        list: List of (location, description) tuples for standalone wounds
    """
    standalone_locations = get_standalone_wound_locations(character)
    if not standalone_locations:
        return []
    
    wounds = get_character_wounds(character)
    descriptions = []
    
    for location in standalone_locations:
        location_wounds = [w for w in wounds if w['location'] == location]
        if not location_wounds:
            continue
            
        # Prioritize wounds for this location
        significant_wounds = _prioritize_wounds_for_display(location_wounds)[:2]
        
        # Create location-based description
        if len(significant_wounds) == 1:
            wound = significant_wounds[0]
            wound_desc = get_wound_description(
                injury_type=wound['injury_type'],
                location=wound['location'],
                severity=wound['severity'],
                stage=wound['stage'],
                organ=wound.get('organ'),
                character=character  # Pass character for skintone
            )
            descriptions.append((location, wound_desc))
        else:
            # Multiple wounds at location without longdesc
            compound_desc = _create_compound_wound_description_for_location(location, significant_wounds, character)
            descriptions.append((location, compound_desc))
    
    return descriptions


def _prioritize_wounds_for_display(wounds):
    """Sort wounds by display priority."""
    severity_order = {"Critical": 4, "Severe": 3, "Moderate": 2, "Light": 1}
    stage_order = {"fresh": 4, "treated": 3, "healing": 2, "scarred": 1}
    
    def wound_priority(wound):
        severity_score = severity_order.get(wound['severity'], 0)
        stage_score = stage_order.get(wound['stage'], 0)
        return (severity_score, stage_score)
    
    return sorted(wounds, key=wound_priority, reverse=True)


def _create_compound_wound_description_for_location(location, wounds, character=None):
    """Create description for multiple wounds at a location without longdesc."""
    from .constants import get_location_display_name, INJURY_SEVERITY_MAP
    
    primary_wound = max(wounds, key=lambda w: ["Light", "Moderate", "Severe", "Critical"].index(w['severity']))
    
    fresh_count = len([w for w in wounds if w['stage'] == 'fresh'])
    location_display = get_location_display_name(location, character)
    severity_display = INJURY_SEVERITY_MAP.get(primary_wound['severity'], primary_wound['severity'].lower())
    
    # Determine if we need skintone coloring
    skintone_color = ""
    if character and fresh_count == 0:  # No fresh wounds, use skintone
        skintone = getattr(character.db, 'skintone', None)
        if skintone:
            try:
                from world.combat.constants import SKINTONE_PALETTE
                skintone_color = SKINTONE_PALETTE.get(skintone, "")
            except ImportError:
                # Skintone system not available
                skintone_color = ""
    
    if fresh_count > 1:
        return f"|RMultiple {severity_display} fresh wounds on the {location_display}|n"
    elif fresh_count == 1:
        return f"|RA {severity_display} fresh wound|n among other injuries on the {location_display}"
    else:
        return f"{skintone_color}Multiple {severity_display} wounds on the {location_display}|n"
