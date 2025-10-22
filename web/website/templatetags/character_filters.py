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
    # Import here to avoid circular imports
    from commands.CmdCharacter import get_stat_descriptor
    
    # Handle None or invalid values
    if value is None:
        value = 0
    
    try:
        numeric_value = int(value)
    except (ValueError, TypeError):
        numeric_value = 0
    
    # Get the descriptor
    return get_stat_descriptor(stat_name, numeric_value)
