"""
Combat Grappling System

Handles all grappling-related logic for the combat system.
Extracted from combathandler.py and CmdCombat.py to improve
organization and maintainability.

Functions:
- Grapple establishment and breaking
- Grapple state validation
- Grapple relationship management
- Integration with proximity system
"""

from .constants import (
    DB_GRAPPLING_DBREF, DB_GRAPPLED_BY_DBREF, 
    MSG_CANNOT_WHILE_GRAPPLED, MSG_CANNOT_GRAPPLE_SELF, MSG_ALREADY_GRAPPLING,
    MSG_GRAPPLE_AUTO_YIELD
)
from .utils import log_debug, get_display_name_safe
from .proximity import establish_proximity, is_in_proximity


def get_character_by_dbref(dbref):
    """
    Helper to get character by dbref with error handling.
    
    Args:
        dbref: Database reference number
        
    Returns:
        Character or None
    """
    if not dbref:
        return None
    
    try:
        from evennia import search_object
        results = search_object(f"#{dbref}")
        return results[0] if results else None
    except (ValueError, TypeError, ImportError):
        return None


def get_grappling_target(combat_handler, combatant_entry):
    """
    Get the character that this combatant is grappling.
    
    Args:
        combat_handler: The combat handler script
        combatant_entry (dict): The combatant's entry in the handler
        
    Returns:
        Character or None: The grappled character
    """
    grappling_dbref = combatant_entry.get(DB_GRAPPLING_DBREF)
    return get_character_by_dbref(grappling_dbref)


def get_grappled_by(combat_handler, combatant_entry):
    """
    Get the character that is grappling this combatant.
    
    Args:
        combat_handler: The combat handler script
        combatant_entry (dict): The combatant's entry in the handler
        
    Returns:
        Character or None: The grappling character
    """
    grappled_by_dbref = combatant_entry.get(DB_GRAPPLED_BY_DBREF)
    return get_character_by_dbref(grappled_by_dbref)


def establish_grapple(combat_handler, grappler, victim):
    """
    Establish a grapple between two characters.
    
    Args:
        combat_handler: The combat handler script
        grappler: Character doing the grappling
        victim: Character being grappled
        
    Returns:
        tuple: (success, message)
    """
    if grappler == victim:
        return False, MSG_CANNOT_GRAPPLE_SELF
    
    # Get combatant entries
    grappler_entry = None
    victim_entry = None
    
    combatants_list = list(combat_handler.db.combatants)
    for entry in combatants_list:
        if entry.get("char") == grappler:
            grappler_entry = entry
        elif entry.get("char") == victim:
            victim_entry = entry
    
    if not grappler_entry or not victim_entry:
        return False, "Combat entries not found."
    
    # Check if grappler is already grappling someone
    if grappler_entry.get(DB_GRAPPLING_DBREF):
        current_target = get_grappling_target(combat_handler, grappler_entry)
        if current_target:
            return False, MSG_ALREADY_GRAPPLING.format(target=get_display_name_safe(current_target, grappler))
    
    # Check if victim is already being grappled
    if victim_entry.get(DB_GRAPPLED_BY_DBREF):
        current_grappler = get_grappled_by(combat_handler, victim_entry)
        if current_grappler:
            return False, f"{get_display_name_safe(victim, grappler)} is already being grappled by {get_display_name_safe(current_grappler, grappler)}."
    
    # Establish the grapple
    for i, entry in enumerate(combatants_list):
        if entry.get("char") == grappler:
            combatants_list[i][DB_GRAPPLING_DBREF] = victim.id
            # Grappler starts in restraint mode (yielding)
            combatants_list[i]["is_yielding"] = True
        elif entry.get("char") == victim:
            combatants_list[i][DB_GRAPPLED_BY_DBREF] = grappler.id
            # Victim automatically yields when grappled (restraint mode)
            combatants_list[i]["is_yielding"] = True
    
    # Save the updated list
    combat_handler.db.combatants = combatants_list
    
    # Ensure proximity (grappling requires proximity)
    establish_proximity(grappler, victim)
    
    # Notify victim they're auto-yielding
    victim.msg(MSG_GRAPPLE_AUTO_YIELD)
    
    log_debug("GRAPPLE", "ESTABLISH", f"{grappler.key} grapples {victim.key}")
    
    return True, f"You successfully grapple {get_display_name_safe(victim, grappler)}!"


def break_grapple(combat_handler, grappler=None, victim=None):
    """
    Break a grapple relationship.
    
    Args:
        combat_handler: The combat handler script
        grappler: Character doing the grappling (optional if victim provided)
        victim: Character being grappled (optional if grappler provided)
        
    Returns:
        tuple: (success, message)
    """
    if not grappler and not victim:
        return False, "Must specify either grappler or victim."
    
    combatants_list = list(combat_handler.db.combatants)
    grapple_broken = False
    
    # Find and break the grapple
    for i, entry in enumerate(combatants_list):
        char = entry.get("char")
        
        if grappler and char == grappler:
            if entry.get(DB_GRAPPLING_DBREF):
                combatants_list[i][DB_GRAPPLING_DBREF] = None
                grapple_broken = True
        
        if victim and char == victim:
            if entry.get(DB_GRAPPLED_BY_DBREF):
                combatants_list[i][DB_GRAPPLED_BY_DBREF] = None
                grapple_broken = True
    
    if grapple_broken:
        # Save the updated list
        combat_handler.db.combatants = combatants_list
        
        grappler_name = get_display_name_safe(grappler) if grappler else "someone"
        victim_name = get_display_name_safe(victim) if victim else "someone"
        
        log_debug("GRAPPLE", "BREAK", f"{grappler_name} -> {victim_name}")
        
        return True, "Grapple broken."
    
    return False, "No grapple found to break."


def is_grappling(combat_handler, character):
    """
    Check if a character is grappling someone.
    
    Args:
        combat_handler: The combat handler script
        character: Character to check
        
    Returns:
        bool: True if character is grappling someone
    """
    for entry in combat_handler.db.combatants:
        if entry.get("char") == character:
            return bool(entry.get(DB_GRAPPLING_DBREF))
    return False


def is_grappled(combat_handler, character):
    """
    Check if a character is being grappled.
    
    Args:
        combat_handler: The combat handler script
        character: Character to check
        
    Returns:
        bool: True if character is being grappled
    """
    for entry in combat_handler.db.combatants:
        if entry.get("char") == character:
            return bool(entry.get(DB_GRAPPLED_BY_DBREF))
    return False


def validate_grapple_action(combat_handler, character, action_name):
    """
    Validate if a character can perform an action while grappled/grappling.
    
    Args:
        combat_handler: The combat handler script
        character: Character attempting the action
        action_name (str): Name of the action being attempted
        
    Returns:
        tuple: (can_perform, error_message)
    """
    # Check if being grappled
    for entry in combat_handler.db.combatants:
        if entry.get("char") == character:
            grappled_by_dbref = entry.get(DB_GRAPPLED_BY_DBREF)
            if grappled_by_dbref:
                grappler = get_grappled_by(combat_handler, entry)
                if grappler:
                    grappler_name = get_display_name_safe(grappler, character)
                    message = MSG_CANNOT_WHILE_GRAPPLED.format(
                        action=action_name,
                        grappler=grappler_name
                    )
                    return False, message
    
    return True, ""


def cleanup_invalid_grapples(combat_handler):
    """
    Clean up grapple relationships with invalid characters.
    
    Args:
        combat_handler: The combat handler script
    """
    combatants_list = list(combat_handler.db.combatants)
    cleaned = False
    
    for i, entry in enumerate(combatants_list):
        char = entry.get("char")
        if not char:
            continue
        
        # Check grappling target
        grappling_dbref = entry.get(DB_GRAPPLING_DBREF)
        if grappling_dbref:
            target = get_grappling_target(combat_handler, entry)
            if not target or not hasattr(target, 'location') or target.location != char.location:
                combatants_list[i][DB_GRAPPLING_DBREF] = None
                cleaned = True
                log_debug("GRAPPLE", "CLEANUP", f"Removed invalid grappling target from {char.key}")
        
        # Check grappled by
        grappled_by_dbref = entry.get(DB_GRAPPLED_BY_DBREF)
        if grappled_by_dbref:
            grappler = get_grappled_by(combat_handler, entry)
            if not grappler or not hasattr(grappler, 'location') or grappler.location != char.location:
                combatants_list[i][DB_GRAPPLED_BY_DBREF] = None
                cleaned = True
                log_debug("GRAPPLE", "CLEANUP", f"Removed invalid grappler from {char.key}")
    
    if cleaned:
        combat_handler.db.combatants = combatants_list
