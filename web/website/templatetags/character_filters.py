"""
Custom template filters for character display.
"""
from django import template

register = template.Library()


@register.filter(name='stat_descriptor')
def stat_descriptor(value, stat_name):
    """
    Convert numeric stat value to descriptive adjective.
    
    Usage in template:
        {{ object.grit|stat_descriptor:"grit" }}
        {{ object.resonance|stat_descriptor:"resonance" }}
    
    Args:
        value: Numeric stat value
        stat_name: Name of the stat (grit, resonance, intellect, motorics)
        
    Returns:
        str: Descriptive adjective for the stat tier
    """
    # Import constants
    from world.combat.constants import STAT_DESCRIPTORS, STAT_TIER_RANGES
    
    # Handle None or invalid values
    if value is None:
        value = 0
    
    try:
        numeric_value = int(value)
    except (ValueError, TypeError):
        numeric_value = 0
    
    # Validate stat name
    if stat_name not in STAT_DESCRIPTORS:
        return "Unknown"
    
    # Ensure numeric value is valid
    if numeric_value < 0:
        numeric_value = 0
    
    # Handle values over 150
    if numeric_value > 150:
        numeric_value = 150
    
    # Find the appropriate tier
    for min_val, max_val in STAT_TIER_RANGES:
        if min_val <= numeric_value <= max_val:
            # Find the descriptor key for this range
            descriptor_key = max_val
            return STAT_DESCRIPTORS[stat_name].get(descriptor_key, "Unknown")
    
    # Fallback
    return "Unknown"
