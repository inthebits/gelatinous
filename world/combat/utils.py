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


def roll_with_advantage(stat_value):
    """
    Roll with advantage: roll twice, take the higher result.
    
    Args:
        stat_value (int): The stat value to roll against
        
    Returns:
        tuple: (final_roll, roll1, roll2) for debugging
    """
    roll1 = randint(1, max(1, stat_value))
    roll2 = randint(1, max(1, stat_value))
    final_roll = max(roll1, roll2)
    return final_roll, roll1, roll2


def roll_with_disadvantage(stat_value):
    """
    Roll with disadvantage: roll twice, take the lower result.
    
    Args:
        stat_value (int): The stat value to roll against
        
    Returns:
        tuple: (final_roll, roll1, roll2) for debugging
    """
    roll1 = randint(1, max(1, stat_value))
    roll2 = randint(1, max(1, stat_value))
    final_roll = min(roll1, roll2)
    return final_roll, roll1, roll2


def standard_roll(stat_value):
    """
    Standard single roll.
    
    Args:
        stat_value (int): The stat value to roll against
        
    Returns:
        tuple: (final_roll, roll, roll) for consistent interface
    """
    roll = randint(1, max(1, stat_value))
    return roll, roll, roll


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


def is_wielding_ranged_weapon(character):
    """
    Check if a character is wielding a ranged weapon.
    
    Args:
        character: The character to check
        
    Returns:
        bool: True if wielding a ranged weapon, False otherwise
    """
    # Use the same hands detection logic as core_actions.py
    hands = getattr(character, "hands", {})
    for hand, weapon in hands.items():
        if weapon and hasattr(weapon, 'db') and getattr(weapon.db, 'is_ranged', False):
            return True
    
    return False


def get_wielded_weapons(character):
    """
    Get all weapons a character is currently wielding.
    
    Args:
        character: The character to check
        
    Returns:
        list: List of wielded weapon objects
    """
    weapons = []
    hands = getattr(character, "hands", {})
    
    for hand, weapon in hands.items():
        if weapon:
            weapons.append(weapon)
    
    return weapons


def get_weapon_damage(weapon, default=0):
    """
    Safely get weapon damage with fallback to default.
    
    Args:
        weapon: The weapon object
        default (int): Default damage if weapon has no damage or damage is None
        
    Returns:
        int: Weapon damage value, guaranteed to be a non-negative integer
    """
    if not weapon or not hasattr(weapon, 'db'):
        return default
    
    damage = getattr(weapon.db, "damage", default)
    
    # Handle None explicitly since some weapons might have damage=None
    if damage is None:
        return default
    
    # Ensure it's numeric and non-negative
    if not isinstance(damage, (int, float)) or damage < 0:
        return default
    
    return int(damage)


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


# ===================================================================
# AIM STATE MANAGEMENT HELPERS
# ===================================================================

def clear_aim_state(character):
    """
    Clear all aim-related state from a character.
    
    Args:
        character: The character to clear aim state from
    """
    # Clear aiming target
    if hasattr(character.ndb, "aiming_at"):
        del character.ndb.aiming_at
    
    # Clear aiming direction  
    if hasattr(character.ndb, "aiming_direction"):
        del character.ndb.aiming_direction
    
    # Clear being aimed at by others
    if hasattr(character.ndb, "aimed_at_by"):
        del character.ndb.aimed_at_by
    
    log_debug("AIM", "CLEAR", f"Cleared aim state", character)


def clear_mutual_aim(char1, char2):
    """
    Clear any mutual aiming relationships between two characters.
    
    Args:
        char1: First character
        char2: Second character
    """
    # Clear char1 aiming at char2
    if hasattr(char1.ndb, "aiming_at") and char1.ndb.aiming_at == char2:
        del char1.ndb.aiming_at
        if hasattr(char1.ndb, "aiming_direction"):
            del char1.ndb.aiming_direction
    
    # Clear char2 aiming at char1
    if hasattr(char2.ndb, "aiming_at") and char2.ndb.aiming_at == char1:
        del char2.ndb.aiming_at
        if hasattr(char2.ndb, "aiming_direction"):
            del char2.ndb.aiming_direction
    
    # Clear being aimed at relationships
    if hasattr(char1.ndb, "aimed_at_by") and char1.ndb.aimed_at_by == char2:
        del char1.ndb.aimed_at_by
    
    if hasattr(char2.ndb, "aimed_at_by") and char2.ndb.aimed_at_by == char1:
        del char2.ndb.aimed_at_by


# ===================================================================
# COMBATANT MANAGEMENT (moved from handler.py)
# ===================================================================

def add_combatant(handler, char, target=None, initial_grappling=None, initial_grappled_by=None, initial_is_yielding=False):
    """
    Add a character to combat.
    
    Args:
        handler: The combat handler instance
        char: The character to add
        target: Optional initial target
        initial_grappling: Optional character being grappled initially
        initial_grappled_by: Optional character grappling this char initially
        initial_is_yielding: Whether the character starts yielding
    """
    from evennia.comms.models import ChannelDB
    from .constants import (
        SPLATTERCAST_CHANNEL, DB_COMBATANTS, DB_CHAR, DB_TARGET_DBREF,
        DB_GRAPPLING_DBREF, DB_GRAPPLED_BY_DBREF, DB_IS_YIELDING, 
        NDB_PROXIMITY, NDB_COMBAT_HANDLER, DB_COMBAT_RUNNING
    )
    from random import randint
    
    splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
    
    # Debug: Show what parameters were passed
    splattercast.msg(f"ADD_COMBATANT_PARAMS: char={char.key if char else None}, target={target.key if target else None}")
    
    # Prevent self-targeting
    if target and char == target:
        splattercast.msg(f"ADD_COMBATANT_ERROR: {char.key} cannot target themselves! Setting target to None.")
        target = None
    
    # Check if already in combat
    combatants = getattr(handler.db, DB_COMBATANTS, [])
    for entry in combatants:
        if entry.get(DB_CHAR) == char:
            splattercast.msg(f"ADD_COMB: {char.key} is already in combat.")
            return
    
    # Initialize proximity NDB if it doesn't exist or is not a set
    if not hasattr(char.ndb, NDB_PROXIMITY) or not isinstance(getattr(char.ndb, NDB_PROXIMITY), set):
        setattr(char.ndb, NDB_PROXIMITY, set())
        splattercast.msg(f"ADD_COMB: Initialized char.ndb.{NDB_PROXIMITY} as a new set for {char.key}.")
    
    # Create combat entry
    target_dbref = get_character_dbref(target)
    entry = {
        DB_CHAR: char,
        "initiative": randint(1, 20) + get_numeric_stat(char, "motorics", 0),
        DB_TARGET_DBREF: target_dbref,
        DB_GRAPPLING_DBREF: get_character_dbref(initial_grappling),
        DB_GRAPPLED_BY_DBREF: get_character_dbref(initial_grappled_by),
        DB_IS_YIELDING: initial_is_yielding,
        "combat_action": None
    }
    
    splattercast.msg(f"ADD_COMBATANT_ENTRY: {char.key} -> target_dbref={target_dbref}, initiative={entry['initiative']}")
    
    combatants.append(entry)
    setattr(handler.db, DB_COMBATANTS, combatants)
    
    # Set the character's handler reference
    setattr(char.ndb, NDB_COMBAT_HANDLER, handler)
    
    splattercast.msg(f"ADD_COMB: {char.key} added to combat in {handler.key} with initiative {entry['initiative']}.")
    char.msg("|rYou enter combat!|n")
    
    # Start combat if not already running
    if not getattr(handler.db, DB_COMBAT_RUNNING, False):
        handler.start()
    
    # Validate grapple state after adding new combatant
    from .grappling import validate_and_cleanup_grapple_state
    validate_and_cleanup_grapple_state(handler)


def remove_combatant(handler, char):
    """
    Remove a character from combat and clean up their state.
    
    Args:
        handler: The combat handler instance
        char: The character to remove from combat
    """
    from evennia.comms.models import ChannelDB
    from .constants import (
        SPLATTERCAST_CHANNEL, DB_COMBATANTS, DB_CHAR, DB_TARGET_DBREF, 
        NDB_COMBAT_HANDLER
    )
    
    splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
    
    combatants = getattr(handler.db, DB_COMBATANTS, [])
    entry = next((e for e in combatants if e.get(DB_CHAR) == char), None)
    
    if not entry:
        splattercast.msg(f"RMV_COMB: {char.key} not found in combat.")
        return
    
    # Clean up the character's state
    cleanup_combatant_state(char, entry, handler)
    
    # Remove references to this character from other combatants
    for other_entry in combatants:
        if other_entry.get(DB_TARGET_DBREF) == get_character_dbref(char):
            other_entry[DB_TARGET_DBREF] = None
            splattercast.msg(f"RMV_COMB: Cleared {other_entry[DB_CHAR].key}'s target_dbref (was {char.key})")
            # Inform the character that their target is gone
            if hasattr(other_entry[DB_CHAR], 'msg'):
                other_entry[DB_CHAR].msg(f"|yYour target {char.get_display_name(other_entry[DB_CHAR]) if hasattr(char, 'get_display_name') else char.key} has left combat. Choose a new target if you wish to continue fighting.|n")
    
    # Remove from combatants list
    combatants = [e for e in combatants if e.get(DB_CHAR) != char]
    setattr(handler.db, DB_COMBATANTS, combatants)
    
    # Remove handler reference
    if hasattr(char.ndb, NDB_COMBAT_HANDLER) and getattr(char.ndb, NDB_COMBAT_HANDLER) == handler:
        delattr(char.ndb, NDB_COMBAT_HANDLER)
    
    splattercast.msg(f"{char.key} removed from combat.")
    char.msg("|gYou are no longer in combat.|n")
    
    # Stop combat if no combatants remain
    if len(combatants) == 0:
        splattercast.msg(f"RMV_COMB: No combatants remain in handler {handler.key}. Stopping.")
        handler.stop_combat_logic()


def cleanup_combatant_state(char, entry, handler):
    """
    Clean up all combat-related state for a character.
    
    Args:
        char: The character to clean up
        entry: The character's combat entry
        handler: The combat handler instance
    """
    from .proximity import clear_all_proximity
    from .grappling import break_grapple
    from .constants import NDB_PROXIMITY, NDB_SKIP_ROUND
    
    # Clear proximity relationships
    clear_all_proximity(char)
    
    # Break grapples
    grappling = get_combatant_grappling_target(entry, handler)
    grappled_by = get_combatant_grappled_by(entry, handler)
    
    if grappling:
        break_grapple(handler, grappler=char, victim=grappling)
    if grappled_by:
        break_grapple(handler, grappler=grappled_by, victim=char)
    
    # Clear NDB attributes
    ndb_attrs = [NDB_PROXIMITY, NDB_SKIP_ROUND, "charging_vulnerability_active", 
                "charge_attack_bonus_active", "skip_combat_round"]
    for attr in ndb_attrs:
        if hasattr(char.ndb, attr):
            delattr(char.ndb, attr)
    
    # Force clear charge bonus flag with explicit setting to False as fallback
    char.ndb.charge_attack_bonus_active = False
    char.ndb.charging_vulnerability_active = False


def cleanup_all_combatants(handler):
    """
    Clean up all combatant state and remove them from the handler.
    
    This function clears all proximity relationships, breaks grapples,
    and removes combat-related NDB attributes from all combatants.
    
    Args:
        handler: The combat handler instance
    """
    from evennia.comms.models import ChannelDB
    from .constants import SPLATTERCAST_CHANNEL, DB_COMBATANTS, DB_CHAR, DEBUG_PREFIX_HANDLER, DEBUG_CLEANUP
    
    splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
    combatants = getattr(handler.db, DB_COMBATANTS, [])
    
    for entry in combatants:
        char = entry.get(DB_CHAR)
        if char:
            cleanup_combatant_state(char, entry, handler)
    
    # Clear the combatants list
    setattr(handler.db, DB_COMBATANTS, [])
    splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: All combatants cleaned up for {handler.key}.")


# ===================================================================
# COMBATANT UTILITY FUNCTIONS
# ===================================================================

def get_combatant_target(entry, handler):
    """Get the target object for a combatant entry."""
    target_dbref = entry.get("target_dbref")
    return get_character_by_dbref(target_dbref)


def get_combatant_grappling_target(entry, handler):
    """Get the character that this combatant is grappling."""
    grappling_dbref = entry.get("grappling_dbref")
    return get_character_by_dbref(grappling_dbref)


def get_combatant_grappled_by(entry, handler):
    """Get the character that is grappling this combatant."""
    grappled_by_dbref = entry.get("grappled_by_dbref")
    return get_character_by_dbref(grappled_by_dbref)


def get_character_dbref(char):
    """
    Get DBREF for a character object.
    
    Args:
        char: The character object
        
    Returns:
        int or None: The character's DBREF
    """
    return char.id if char else None


def get_character_by_dbref(dbref):
    """
    Get character object by DBREF.
    
    Args:
        dbref: The database reference number
        
    Returns:
        Character object or None
    """
    if dbref is None:
        return None
    try:
        from evennia import search_object
        return search_object(f"#{dbref}")[0]
    except (IndexError, ValueError):
        return None
