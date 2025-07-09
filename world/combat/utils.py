"""
Combat System Utilities

Shared utility functions used throughout the combat system.
Extracted from repeated patterns in the codebase to improve
maintainability and consistency.

Functions:
- Dice rolling and stat validation
- Debug logging helpers
- Character attribute access
- NDB state management
- Proximity validation
- Message formatting
"""

from random import randint
from .constants import (
    DEFAULT_MOTORICS, MIN_DICE_VALUE, SPLATTERCAST_CHANNEL,
    DEBUG_TEMPLATE, NDB_PROXIMITY, COLOR_NORMAL
)


# ===================================================================
# DICE & STATS
# ===================================================================

def get_character_stat(character, stat_name, default=1):
    """
    Safely get a character's stat value with fallback to default.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat (e.g., 'motorics', 'grit')
        default (int): Default value if stat is missing or invalid
        
    Returns:
        int: The stat value, guaranteed to be a positive integer
    """
    stat_value = getattr(character, stat_name, default)
    
    # Ensure it's a valid number
    if not isinstance(stat_value, (int, float)) or stat_value < 1:
        return default
    
    return int(stat_value)


def roll_stat(character, stat_name, default=DEFAULT_MOTORICS):
    """
    Roll a die based on a character's stat value.
    
    Args:
        character: The character object
        stat_name (str): Name of the stat to roll against
        default (int): Default stat value if missing
        
    Returns:
        int: Random value from 1 to stat_value
    """
    stat_value = get_character_stat(character, stat_name, default)
    return randint(MIN_DICE_VALUE, max(MIN_DICE_VALUE, stat_value))


def opposed_roll(char1, char2, stat1="motorics", stat2="motorics"):
    """
    Perform an opposed roll between two characters.
    
    Args:
        char1: First character
        char2: Second character  
        stat1 (str): Stat name for first character
        stat2 (str): Stat name for second character
        
    Returns:
        tuple: (char1_roll, char2_roll, char1_wins)
    """
    roll1 = roll_stat(char1, stat1)
    roll2 = roll_stat(char2, stat2)
    
    return roll1, roll2, roll1 > roll2


# ===================================================================
# DEBUG LOGGING
# ===================================================================

def log_debug(prefix, action, message, character=None):
    """
    Send a standardized debug message to Splattercast.
    
    Args:
        prefix (str): Debug prefix (e.g., DEBUG_PREFIX_ATTACK)
        action (str): Action type (e.g., DEBUG_SUCCESS)
        message (str): The debug message
        character: Optional character for context
    """
    try:
        from evennia.comms.models import ChannelDB
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        if splattercast:
            char_context = f" ({character.key})" if character else ""
            full_message = f"{prefix}_{action}: {message}{char_context}"
            splattercast.msg(full_message)
    except Exception:
        # Fail silently if channel doesn't exist
        pass


def log_combat_action(character, action_type, target=None, success=True, details=""):
    """
    Log a combat action with standardized format.
    
    Args:
        character: The character performing the action
        action_type (str): Type of action (attack, flee, etc.)
        target: Optional target character
        success (bool): Whether the action succeeded
        details (str): Additional details
    """
    prefix = f"{action_type.upper()}_CMD"
    action = "SUCCESS" if success else "FAIL"
    
    target_info = f" on {target.key}" if target else ""
    details_info = f" - {details}" if details else ""
    
    message = f"{character.key}{target_info}{details_info}"
    log_debug(prefix, action, message)


# ===================================================================
# CHARACTER STATE MANAGEMENT
# ===================================================================

def initialize_proximity_ndb(character):
    """
    Initialize a character's proximity NDB if missing or invalid.
    
    Args:
        character: The character to initialize
        
    Returns:
        bool: True if initialization was needed
    """
    if not hasattr(character.ndb, NDB_PROXIMITY) or not isinstance(character.ndb.in_proximity_with, set):
        character.ndb.in_proximity_with = set()
        log_debug("PROXIMITY", "FAILSAFE", f"Initialized {NDB_PROXIMITY}", character)
        return True
    return False


def clear_character_proximity(character):
    """
    Clear all proximity relationships for a character.
    
    Args:
        character: The character to clear proximity for
    """
    if hasattr(character.ndb, NDB_PROXIMITY) and character.ndb.in_proximity_with:
        # Clear this character from others' proximity
        for other_char in list(character.ndb.in_proximity_with):
            if hasattr(other_char.ndb, NDB_PROXIMITY) and isinstance(other_char.ndb.in_proximity_with, set):
                other_char.ndb.in_proximity_with.discard(character)
        
        # Clear this character's proximity
        character.ndb.in_proximity_with.clear()
        log_debug("PROXIMITY", "CLEAR", f"Cleared all proximity", character)


def establish_proximity(char1, char2):
    """
    Establish bidirectional proximity between two characters.
    
    Args:
        char1: First character
        char2: Second character
    """
    # Initialize if needed
    initialize_proximity_ndb(char1)
    initialize_proximity_ndb(char2)
    
    # Establish bidirectional proximity
    char1.ndb.in_proximity_with.add(char2)
    char2.ndb.in_proximity_with.add(char1)
    
    log_debug("PROXIMITY", "ESTABLISH", f"{char1.key} <-> {char2.key}")


# ===================================================================
# WEAPON & ITEM HELPERS
# ===================================================================

def get_wielded_weapon(character):
    """
    Get the first weapon found in character's hands.
    
    Args:
        character: The character to check
        
    Returns:
        The weapon object, or None if no weapon is wielded
    """
    hands = getattr(character, "hands", {})
    return next((item for hand, item in hands.items() if item), None)


# ===================================================================
# MESSAGE FORMATTING
# ===================================================================

def format_combat_message(template, **kwargs):
    """
    Format a combat message template with color codes preserved.
    
    Args:
        template (str): Message template with {placeholders}
        **kwargs: Values to substitute
        
    Returns:
        str: Formatted message with proper color code termination
    """
    message = template.format(**kwargs)
    
    # Ensure message ends with color normal if it contains color codes
    if "|" in message and not message.endswith(COLOR_NORMAL):
        message += COLOR_NORMAL
    
    return message


def get_display_name_safe(character, observer=None):
    """
    Safely get a character's display name with fallback.
    
    Args:
        character: The character object
        observer: Optional observer for context
        
    Returns:
        str: Character's display name or fallback
    """
    if not character:
        return "someone"
    
    try:
        if observer and hasattr(character, "get_display_name"):
            return character.get_display_name(observer)
        return character.key if hasattr(character, "key") else str(character)
    except Exception:
        return "someone"


# ===================================================================
# VALIDATION HELPERS
# ===================================================================

def validate_combat_target(caller, target, allow_self=False):
    """
    Validate a combat target is appropriate.
    
    Args:
        caller: The character initiating combat
        target: The target character
        allow_self (bool): Whether self-targeting is allowed
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not target:
        return False, "Target not found."
    
    if not allow_self and target == caller:
        return False, "You can't target yourself."
    
    if not hasattr(target, "location") or not target.location:
        return False, "Target is not in a valid location."
    
    return True, ""


def validate_in_same_room(char1, char2):
    """
    Check if two characters are in the same room.
    
    Args:
        char1: First character
        char2: Second character
        
    Returns:
        bool: True if in same room
    """
    return (hasattr(char1, "location") and hasattr(char2, "location") and 
            char1.location and char2.location and 
            char1.location == char2.location)


# ===================================================================
# STAT MANAGEMENT HELPERS
# ===================================================================

def get_highest_opponent_stat(opponents, stat_name="motorics", default=1):
    """
    Get the highest stat value among a list of opponents.
    
    Args:
        opponents (list): List of character objects
        stat_name (str): Name of the stat to check
        default (int): Default value if stat is missing or invalid
        
    Returns:
        tuple: (highest_value, character_with_highest_value)
    """
    if not opponents:
        return default, None
        
    highest_value = default
    highest_char = None
    
    for opponent in opponents:
        if not opponent or not hasattr(opponent, stat_name):
            continue
            
        stat_value = getattr(opponent, stat_name, default)
        numeric_value = stat_value if isinstance(stat_value, (int, float)) else default
        
        if numeric_value > highest_value:
            highest_value = numeric_value
            highest_char = opponent
            
    return highest_value, highest_char


def get_numeric_stat(character, stat_name, default=1):
    """
    Get a numeric stat value from a character, with fallback to default.
    
    Args:
        character: Character object
        stat_name (str): Name of the stat to retrieve
        default (int): Default value if stat is missing or invalid
        
    Returns:
        int: Numeric stat value
    """
    if not character or not hasattr(character, stat_name):
        return default
        
    stat_value = getattr(character, stat_name, default)
    return stat_value if isinstance(stat_value, (int, float)) else default


def filter_valid_opponents(opponents):
    """
    Filter a list to only include valid opponent characters.
    
    Args:
        opponents (list): List of potential opponent objects
        
    Returns:
        list: Filtered list of valid characters
    """
    return [
        opp for opp in opponents 
        if opp and hasattr(opp, "motorics")  # Basic character validation
    ]
