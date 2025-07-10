"""
Combat Handler Module

Refactored combat handler that manages turn-based combat for all combatants
in one or more locations. This module contains the core CombatHandler script
and utility functions for combat management.

This is the central component that orchestrates combat encounters, handling:
- Combat initialization and cleanup
- Turn management and initiative
- Multi-room combat coordination
- Combatant state management
- Integration with proximity and grappling systems
"""

from evennia import DefaultScript, create_script, search_object
from random import randint
from evennia.utils.utils import delay
from world.combat.messages import get_combat_message
from evennia.comms.models import ChannelDB
import traceback

from .constants import (
    COMBAT_SCRIPT_KEY, SPLATTERCAST_CHANNEL,
    DB_COMBATANTS, DB_COMBAT_RUNNING, DB_MANAGED_ROOMS,
    DB_CHAR, DB_TARGET_DBREF, DB_GRAPPLING_DBREF, DB_GRAPPLED_BY_DBREF, DB_IS_YIELDING,
    NDB_COMBAT_HANDLER, NDB_PROXIMITY, NDB_SKIP_ROUND,
    DEBUG_PREFIX_HANDLER, DEBUG_SUCCESS, DEBUG_FAIL, DEBUG_ERROR, DEBUG_CLEANUP,
    MSG_GRAPPLE_AUTO_ESCAPE_VIOLENT, MSG_GRAPPLE_AUTO_YIELD
)
from .utils import (
    get_numeric_stat, log_combat_action, get_display_name_safe,
    roll_stat, opposed_roll, get_wielded_weapon
)
from .proximity import clear_all_proximity, establish_proximity, proximity_opposed_roll
from .grappling import break_grapple, establish_grapple


def get_or_create_combat(location):
    """
    Get an existing combat handler for a location or create a new one.
    
    This function ensures that each location has at most one active combat
    handler managing it, and handles the complex logic of multi-room combat
    coordination.
    
    Args:
        location: The room/location that needs combat management
        
    Returns:
        CombatHandler: The combat handler managing this location
    """
    splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
    
    # First, check if 'location' is already managed by ANY active CombatHandler
    # This requires iterating through all scripts, which can be slow.
    # A better way might be a global list of active combat handlers, but for now:
    from evennia.scripts.models import ScriptDB
    active_handlers = ScriptDB.objects.filter(db_key=COMBAT_SCRIPT_KEY, db_is_active=True)

    for handler_script in active_handlers:
        # Ensure it's our CombatHandler type and has managed_rooms
        if hasattr(handler_script, "db") and hasattr(handler_script.db, DB_MANAGED_ROOMS):
            if location in getattr(handler_script.db, DB_MANAGED_ROOMS, []):
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Location {location.key} is already managed by active handler {handler_script.key} (on {handler_script.obj.key}). Returning it.")
                return handler_script
    
    # If not managed by an existing handler, check for an inactive one on THIS location
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            # Found a handler on this specific location
            if script.is_active: # Should have been caught by the loop above if it managed this location
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Found active handler {script.key} directly on {location.key} (missed by global check or manages only self). Returning it.")
                # Ensure it knows it manages this location
                managed_rooms = getattr(script.db, DB_MANAGED_ROOMS, [])
                if location not in managed_rooms:
                    managed_rooms.append(location)
                    setattr(script.db, DB_MANAGED_ROOMS, managed_rooms)
                return script
            else:
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Found inactive handler {script.key} on {location.key}. Attempting cleanup.")
                # Only perform database operations if the handler has been saved to the database
                if hasattr(script, 'id') and script.id:
                    try:
                        script.stop() # Ensure it's fully stopped
                        script.save()
                        script.delete()
                        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Deleted inactive handler {script.key}.")
                    except Exception as e:
                        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Error cleaning up inactive handler {script.key}: {e}. Leaving as-is.")
                else:
                    splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Inactive handler {script.key} was not saved to database, skipping cleanup.")
                break # Only one handler script per location by key

    # If no suitable handler found, create a new one on this location
    new_script = create_script(
        "world.combat.handler.CombatHandler",
        key=COMBAT_SCRIPT_KEY,
        obj=location, # New handler is "hosted" by this location
        persistent=True,
    )
    splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Created new CombatHandler {new_script.key} on {location.key}.")
    return new_script


class CombatHandler(DefaultScript):
    """
    Script that manages turn-based combat for all combatants in a location.
    
    This is the central orchestrator of combat encounters, handling:
    - Combat state management and lifecycle
    - Turn-based initiative and action resolution
    - Multi-room combat coordination through handler merging
    - Integration with proximity and grappling systems
    - Cleanup and state consistency
    
    The handler uses a database-backed combatants list with entries containing:
    - char: The character object
    - target_dbref: DBREF of their current target
    - grappling_dbref: DBREF of who they're grappling
    - grappled_by_dbref: DBREF of who's grappling them
    - is_yielding: Whether they're actively attacking
    """

    def at_script_creation(self):
        """
        Initialize combat handler script attributes.
        
        Sets up the initial state for a new combat handler, including
        the combatants list, round counter, and room management.
        """
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6  # 6-second combat rounds
        self.persistent = True
        
        # Initialize database attributes using constants
        setattr(self.db, DB_COMBATANTS, [])
        setattr(self.db, "round", 0)
        setattr(self.db, DB_MANAGED_ROOMS, [self.obj])  # Initially manages only its host room
        setattr(self.db, DB_COMBAT_RUNNING, False)
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        managed_rooms = getattr(self.db, DB_MANAGED_ROOMS, [])
        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_CREATE: New handler {self.key} created on {self.obj.key}, initially managing: {[r.key for r in managed_rooms]}. Combat logic initially not running.")

    def start(self):
        """
        Start the combat handler's repeat timer if combat logic isn't already running
        or if the Evennia ticker isn't active.
        
        This method ensures the combat handler is properly running and handles
        cases where the internal state might be out of sync with Evennia's ticker.
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)

        # Use super().is_active to check Evennia's ticker status
        evennia_ticker_is_active = super().is_active
        combat_is_running = getattr(self.db, DB_COMBAT_RUNNING, False)

        if combat_is_running and evennia_ticker_is_active:
            splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_START: Handler {self.key} on {self.obj.key} - combat logic and Evennia ticker are already active. Skipping redundant start.")
            return

        managed_rooms = getattr(self.db, DB_MANAGED_ROOMS, [])
        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_START: Handler {self.key} on {self.obj.key} (managing {[r.key for r in managed_rooms]}) - ensuring combat logic is running and ticker is scheduled.")
        
        if not combat_is_running:
            splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_START_DETAIL: Setting {DB_COMBAT_RUNNING} = True for {self.key}.")
            setattr(self.db, DB_COMBAT_RUNNING, True)
        
        if not evennia_ticker_is_active:
            splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_START_DETAIL: Evennia ticker for {self.key} is not active (super().is_active=False). Calling force_repeat().")
            self.force_repeat()
        else:
            splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_START_DETAIL: Evennia ticker was already active, but combat logic flag was corrected.")

    def stop_combat_logic(self, cleanup_combatants=True):
        """
        Stop the combat logic while optionally cleaning up combatants.
        
        This method stops the internal combat logic flag and can optionally
        clean up all combatant state. The Evennia ticker may continue running
        but no combat processing will occur.
        
        Args:
            cleanup_combatants (bool): Whether to remove all combatants and clean state
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        combat_was_running = getattr(self.db, DB_COMBAT_RUNNING, False)
        setattr(self.db, DB_COMBAT_RUNNING, False)
        
        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Handler {self.key} stopping combat logic. Was running: {combat_was_running}, cleanup_combatants: {cleanup_combatants}")

        if cleanup_combatants:
            self._cleanup_all_combatants()
            
        # Reset round counter
        self.db.round = 0
        
        # Determine if we should delete the script
        combatants = getattr(self.db, DB_COMBATANTS, [])
        should_delete_script = False
        if not combatants and self.pk:
            splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Handler {self.key} is empty and persistent. Marking for deletion.")
            should_delete_script = True
        
        if should_delete_script:
            splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Preparing to delete handler script {self.key}.")
            # Only delete if the handler has been saved to the database
            if hasattr(self, 'id') and self.id:
                try:
                    # Ensure we're fully saved before attempting deletion
                    self.save()
                    self.delete()
                    splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Successfully deleted handler {self.key}.")
                except Exception as e:
                    splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Error deleting handler {self.key}: {e}. Trying stop().")
                    try:
                        self.stop()
                        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Successfully stopped handler {self.key}.")
                    except Exception as e2:
                        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Error stopping handler {self.key}: {e2}. Leaving as-is.")
            else:
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Handler {self.key} was not saved to database, skipping all database operations.")
        else:
            # Stop the ticker if the script is saved to the database
            if hasattr(self, 'id') and self.id:
                try:
                    splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Handler {self.key} is not being deleted. Calling self.stop() to halt ticker.")
                    self.stop()
                except Exception as e:
                    splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Error stopping handler {self.key}: {e}. Leaving as-is.")
            else:
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Handler {self.key} is not saved to database, skipping stop() call.")
        
        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: Combat logic stopped for {self.key}. Round reset to 0.")

    def _cleanup_all_combatants(self):
        """
        Clean up all combatant state and remove them from the handler.
        
        This method clears all proximity relationships, breaks grapples,
        and removes combat-related NDB attributes from all combatants.
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        combatants = getattr(self.db, DB_COMBATANTS, [])
        
        for entry in combatants:
            char = entry.get(DB_CHAR)
            if char:
                self._cleanup_combatant_state(char, entry)
        
        # Clear the combatants list
        setattr(self.db, DB_COMBATANTS, [])
        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_{DEBUG_CLEANUP}: All combatants cleaned up for {self.key}.")

    def at_stop(self):
        """
        Called when the script is stopped.
        
        Performs cleanup of all combatant state when the handler is stopped.
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_STOP: Handler {self.key} at_stop() called. Cleaning up combat state.")
        self.stop_combat_logic(cleanup_combatants=True)

    def enroll_room(self, room_to_add):
        """
        Add a room to be managed by this handler.
        
        Args:
            room_to_add: The room to add to managed rooms
        """
        managed_rooms = getattr(self.db, DB_MANAGED_ROOMS, [])
        if room_to_add not in managed_rooms:
            managed_rooms.append(room_to_add)
            setattr(self.db, DB_MANAGED_ROOMS, managed_rooms)

    def merge_handler(self, other_handler):
        """
        Merge another combat handler into this one.
        
        This method handles the complex logic of merging two combat handlers
        when characters move between rooms that are managed by different handlers.
        
        Args:
            other_handler: The CombatHandler to merge into this one
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Get combatants from both handlers
        our_combatants = getattr(self.db, DB_COMBATANTS, [])
        their_combatants = getattr(other_handler.db, DB_COMBATANTS, [])
        
        # Merge combatants lists
        for entry in their_combatants:
            char = entry.get(DB_CHAR)
            if char and char not in [e.get(DB_CHAR) for e in our_combatants]:
                our_combatants.append(entry)
                # Update the character's handler reference
                setattr(char.ndb, NDB_COMBAT_HANDLER, self)
        
        # Merge managed rooms
        our_rooms = getattr(self.db, DB_MANAGED_ROOMS, [])
        their_rooms = getattr(other_handler.db, DB_MANAGED_ROOMS, [])
        for room in their_rooms:
            if room not in our_rooms:
                our_rooms.append(room)
        
        # Update our state
        setattr(self.db, DB_COMBATANTS, our_combatants)
        setattr(self.db, DB_MANAGED_ROOMS, our_rooms)
        
        # Stop and clean up the other handler
        other_handler.stop_combat_logic(cleanup_combatants=False)
        
        # Only delete if the handler has been saved to the database
        if hasattr(other_handler, 'id') and other_handler.id:
            try:
                # Ensure the handler is properly saved before deletion
                other_handler.save()
                other_handler.delete()
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_MERGE: Deleted other handler {other_handler.key}.")
            except Exception as e:
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_MERGE: Error deleting other handler {other_handler.key}: {e}. Handler stopped but not deleted.")
        else:
            splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_MERGE: Other handler {other_handler.key} was not saved to database, skipping delete.")
        
        splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_MERGE: Merged {other_handler.key} into {self.key}. Now managing {len(our_rooms)} rooms with {len(our_combatants)} combatants.")

    def add_combatant(self, char, target=None, initial_grappling=None, initial_grappled_by=None, initial_is_yielding=False):
        """
        Add a character to combat.
        
        Args:
            char: The character to add
            target: Optional initial target
            initial_grappling: Optional character being grappled initially
            initial_grappled_by: Optional character grappling this char initially
            initial_is_yielding: Whether the character starts yielding
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Debug: Show what parameters were passed
        splattercast.msg(f"ADD_COMBATANT_PARAMS: char={char.key if char else None}, target={target.key if target else None}")
        
        # Prevent self-targeting
        if target and char == target:
            splattercast.msg(f"ADD_COMBATANT_ERROR: {char.key} cannot target themselves! Setting target to None.")
            target = None
        
        # Check if already in combat
        combatants = getattr(self.db, DB_COMBATANTS, [])
        for entry in combatants:
            if entry.get(DB_CHAR) == char:
                splattercast.msg(f"ADD_COMB: {char.key} is already in combat.")
                return
        
        # Initialize proximity NDB if it doesn't exist or is not a set
        if not hasattr(char.ndb, NDB_PROXIMITY) or not isinstance(getattr(char.ndb, NDB_PROXIMITY), set):
            setattr(char.ndb, NDB_PROXIMITY, set())
            splattercast.msg(f"ADD_COMB: Initialized char.ndb.{NDB_PROXIMITY} as a new set for {char.key}.")
        
        # Create combat entry
        target_dbref = self._get_dbref(target)
        entry = {
            DB_CHAR: char,
            "initiative": randint(1, 20) + get_numeric_stat(char, "motorics", 0),
            DB_TARGET_DBREF: target_dbref,
            DB_GRAPPLING_DBREF: self._get_dbref(initial_grappling),
            DB_GRAPPLED_BY_DBREF: self._get_dbref(initial_grappled_by),
            DB_IS_YIELDING: initial_is_yielding,
            "combat_action": None
        }
        
        splattercast.msg(f"ADD_COMBATANT_ENTRY: {char.key} -> target_dbref={target_dbref}, initiative={entry['initiative']}")
        
        combatants.append(entry)
        setattr(self.db, DB_COMBATANTS, combatants)
        
        # Set the character's handler reference
        setattr(char.ndb, NDB_COMBAT_HANDLER, self)
        
        splattercast.msg(f"ADD_COMB: {char.key} added to combat in {self.key} with initiative {entry['initiative']}.")
        char.msg("|rYou enter combat!|n")
        
        # Start combat if not already running
        if not getattr(self.db, DB_COMBAT_RUNNING, False):
            self.start()
        
        # Validate grapple state after adding new combatant
        self.validate_and_cleanup_grapple_state()

    def remove_combatant(self, char):
        """
        Remove a character from combat and clean up their state.
        
        Args:
            char: The character to remove from combat
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        combatants = getattr(self.db, DB_COMBATANTS, [])
        entry = next((e for e in combatants if e.get(DB_CHAR) == char), None)
        
        if not entry:
            splattercast.msg(f"RMV_COMB: {char.key} not found in combat.")
            return
        
        # Clean up the character's state
        self._cleanup_combatant_state(char, entry)
        
        # Remove references to this character from other combatants
        for other_entry in combatants:
            if other_entry.get(DB_TARGET_DBREF) == self._get_dbref(char):
                other_entry[DB_TARGET_DBREF] = None
                splattercast.msg(f"RMV_COMB: Cleared {other_entry[DB_CHAR].key}'s target_dbref (was {char.key})")
                # Inform the character that their target is gone
                if hasattr(other_entry[DB_CHAR], 'msg'):
                    other_entry[DB_CHAR].msg(f"|yYour target {char.get_display_name(other_entry[DB_CHAR]) if hasattr(char, 'get_display_name') else char.key} has left combat. Choose a new target if you wish to continue fighting.|n")
        
        # Remove from combatants list
        combatants = [e for e in combatants if e.get(DB_CHAR) != char]
        setattr(self.db, DB_COMBATANTS, combatants)
        
        # Remove handler reference
        if hasattr(char.ndb, NDB_COMBAT_HANDLER) and getattr(char.ndb, NDB_COMBAT_HANDLER) == self:
            delattr(char.ndb, NDB_COMBAT_HANDLER)
        
        splattercast.msg(f"{char.key} removed from combat.")
        char.msg("|gYou are no longer in combat.|n")
        
        # Stop combat if no combatants remain
        if len(combatants) == 0:
            splattercast.msg(f"RMV_COMB: No combatants remain in handler {self.key}. Stopping.")
            self.stop_combat_logic()

    def _cleanup_combatant_state(self, char, entry):
        """
        Clean up all combat-related state for a character.
        
        Args:
            char: The character to clean up
            entry: The character's combat entry
        """
        # Clear proximity relationships
        clear_all_proximity(char)
        
        # Break grapples
        grappling = self.get_grappling_obj(entry)
        grappled_by = self.get_grappled_by_obj(entry)
        
        if grappling:
            break_grapple(self, grappler=char, victim=grappling)
        if grappled_by:
            break_grapple(self, grappler=grappled_by, victim=char)
        
        # Clear NDB attributes
        ndb_attrs = [NDB_PROXIMITY, NDB_SKIP_ROUND, "charging_vulnerability_active", 
                    "charge_attack_bonus_active", "skip_combat_round"]
        for attr in ndb_attrs:
            if hasattr(char.ndb, attr):
                delattr(char.ndb, attr)

    def validate_and_cleanup_grapple_state(self):
        """
        Validate and clean up stale grapple references in the combat handler.
        
        This method checks for and fixes:
        - Stale DBREFs to characters no longer in the database
        - Invalid cross-references (A grappling B but B not grappled by A)
        - Self-grappling references
        - References to characters no longer in combat
        - Orphaned grapple states
        
        Called periodically during combat to maintain data integrity.
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        combatants_list = list(getattr(self.db, DB_COMBATANTS, []))
        cleanup_needed = False
        
        splattercast.msg(f"GRAPPLE_VALIDATE: Starting grapple state validation for handler {self.key}")
        
        # Get list of all valid character DBREFs in combat for reference checking
        valid_combat_dbrefs = set()
        valid_combat_chars = set()
        for entry in combatants_list:
            char = entry.get(DB_CHAR)
            if char:
                valid_combat_dbrefs.add(self._get_dbref(char))
                valid_combat_chars.add(char)
        
        for i, entry in enumerate(combatants_list):
            char = entry.get(DB_CHAR)
            if not char:
                continue
                
            grappling_dbref = entry.get(DB_GRAPPLING_DBREF)
            grappled_by_dbref = entry.get(DB_GRAPPLED_BY_DBREF)
            
            # Check grappling_dbref (who this character is grappling)
            if grappling_dbref is not None:
                # Try to resolve the grappling target
                grappling_target = self._get_char_by_dbref(grappling_dbref)
                
                if not grappling_target:
                    # Stale DBREF - character no longer exists
                    splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} has stale grappling_dbref {grappling_dbref} (character doesn't exist). Clearing.")
                    combatants_list[i] = dict(entry)
                    combatants_list[i][DB_GRAPPLING_DBREF] = None
                    cleanup_needed = True
                elif grappling_target == char:
                    # Self-grappling
                    splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} is grappling themselves! Clearing self-grapple.")
                    combatants_list[i] = dict(entry)
                    combatants_list[i][DB_GRAPPLING_DBREF] = None
                    cleanup_needed = True
                elif grappling_target not in valid_combat_chars:
                    # Target not in combat
                    splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} is grappling {grappling_target.key} who is not in combat. Clearing.")
                    combatants_list[i] = dict(entry)
                    combatants_list[i][DB_GRAPPLING_DBREF] = None
                    cleanup_needed = True
                else:
                    # Valid target - check cross-reference
                    target_entry = next((e for e in combatants_list if e.get(DB_CHAR) == grappling_target), None)
                    if target_entry:
                        target_grappled_by_dbref = target_entry.get(DB_GRAPPLED_BY_DBREF)
                        expected_dbref = self._get_dbref(char)
                        
                        if target_grappled_by_dbref != expected_dbref:
                            # Broken cross-reference
                            splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} claims to grapple {grappling_target.key}, but {grappling_target.key} doesn't have matching grappled_by reference. Fixing cross-reference.")
                            # Fix the target's grappled_by reference
                            target_index = next(j for j, e in enumerate(combatants_list) if e.get(DB_CHAR) == grappling_target)
                            combatants_list[target_index] = dict(combatants_list[target_index])
                            combatants_list[target_index][DB_GRAPPLED_BY_DBREF] = expected_dbref
                            cleanup_needed = True
            
            # Check grappled_by_dbref (who is grappling this character)
            if grappled_by_dbref is not None:
                # Try to resolve the grappler
                grappler = self._get_char_by_dbref(grappled_by_dbref)
                
                if not grappler:
                    # Stale DBREF - grappler no longer exists
                    splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} has stale grappled_by_dbref {grappled_by_dbref} (character doesn't exist). Clearing.")
                    combatants_list[i] = dict(entry)
                    combatants_list[i][DB_GRAPPLED_BY_DBREF] = None
                    cleanup_needed = True
                elif grappler == char:
                    # Self-grappling
                    splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} is grappled by themselves! Clearing self-grapple.")
                    combatants_list[i] = dict(entry)
                    combatants_list[i][DB_GRAPPLED_BY_DBREF] = None
                    cleanup_needed = True
                elif grappler not in valid_combat_chars:
                    # Grappler not in combat
                    splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} is grappled by {grappler.key} who is not in combat. Clearing.")
                    combatants_list[i] = dict(entry)
                    combatants_list[i][DB_GRAPPLED_BY_DBREF] = None
                    cleanup_needed = True
                else:
                    # Valid grappler - check cross-reference
                    grappler_entry = next((e for e in combatants_list if e.get(DB_CHAR) == grappler), None)
                    if grappler_entry:
                        grappler_grappling_dbref = grappler_entry.get(DB_GRAPPLING_DBREF)
                        expected_dbref = self._get_dbref(char)
                        
                        if grappler_grappling_dbref != expected_dbref:
                            # Broken cross-reference
                            splattercast.msg(f"GRAPPLE_CLEANUP: {char.key} claims to be grappled by {grappler.key}, but {grappler.key} doesn't have matching grappling reference. Fixing cross-reference.")
                            # Fix the grappler's grappling reference
                            grappler_index = next(j for j, e in enumerate(combatants_list) if e.get(DB_CHAR) == grappler)
                            combatants_list[grappler_index] = dict(combatants_list[grappler_index])
                            combatants_list[grappler_index][DB_GRAPPLING_DBREF] = expected_dbref
                            cleanup_needed = True
        
        # Save changes if any cleanup was needed
        if cleanup_needed:
            setattr(self.db, DB_COMBATANTS, combatants_list)
            splattercast.msg(f"GRAPPLE_CLEANUP: Grapple state cleanup completed for handler {self.key}. Changes saved.")
        else:
            splattercast.msg(f"GRAPPLE_VALIDATE: All grapple states valid for handler {self.key}.")

    # ...existing code...

    def at_repeat(self):
        """
        Main combat loop, processes each combatant's turn in initiative order.
        Handles attacks, misses, deaths, and round progression across managed rooms.
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        if not getattr(self.db, DB_COMBAT_RUNNING, False):
            splattercast.msg(f"AT_REPEAT: Handler {self.key} on {self.obj.key} combat logic is not running ({DB_COMBAT_RUNNING}=False). Returning.")
            return

        if not super().is_active:
             splattercast.msg(f"AT_REPEAT: Handler {self.key} on {self.obj.key} Evennia script.is_active=False. Marking {DB_COMBAT_RUNNING}=False and returning.")
             setattr(self.db, DB_COMBAT_RUNNING, False)
             return

        # Convert SaverList to regular list to avoid corruption during modifications
        combatants_list = []
        if getattr(self.db, DB_COMBATANTS, None):
            for entry in getattr(self.db, DB_COMBATANTS):
                # Convert each entry to a regular dict to avoid SaverList issues
                regular_entry = dict(entry)
                combatants_list.append(regular_entry)
        splattercast.msg(f"AT_REPEAT_DEBUG: Converted SaverList to regular list with {len(combatants_list)} entries")

        # Validate and clean up stale grapple references
        self.validate_and_cleanup_grapple_state()

        valid_combatants_entries = []
        managed_rooms = getattr(self.db, DB_MANAGED_ROOMS, [])
        for entry in combatants_list:
            char = entry.get(DB_CHAR)
            if not char:
                splattercast.msg(f"AT_REPEAT: Pruning missing character from handler {self.key}.")
                continue
            if not char.location:
                splattercast.msg(f"AT_REPEAT: Pruning {char.key} (no location) from handler {self.key}.")
                if hasattr(char, "ndb") and getattr(char.ndb, NDB_COMBAT_HANDLER) == self:
                    delattr(char.ndb, NDB_COMBAT_HANDLER)
                continue
            if char.location not in managed_rooms:
                splattercast.msg(f"AT_REPEAT: Pruning {char.key} (in unmanaged room {char.location.key}) from handler {self.key}.")
                if hasattr(char, "ndb") and getattr(char.ndb, NDB_COMBAT_HANDLER) == self:
                    delattr(char.ndb, NDB_COMBAT_HANDLER)
                continue
            valid_combatants_entries.append(entry)
        
        # Update the working list
        combatants_list = valid_combatants_entries

        if not combatants_list:
            splattercast.msg(f"AT_REPEAT: No valid combatants remain in managed rooms for handler {self.key}. Stopping.")
            self.stop_combat_logic()
            return

        if self.db.round == 0:
            if len(combatants_list) > 0:
                splattercast.msg(f"AT_REPEAT: Handler {self.key}. Combatants present. Starting combat in round 1.")
                self.db.round = 1
            else:
                splattercast.msg(f"AT_REPEAT: Handler {self.key}. Waiting for combatants to join...")
                # Save the list back before returning
                setattr(self.db, DB_COMBATANTS, combatants_list)
                return

        splattercast.msg(f"AT_REPEAT: Handler {self.key} (managing {[r.key for r in managed_rooms]}). Round {self.db.round} begins.")
        
        if len(combatants_list) <= 1:
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. Not enough combatants ({len(combatants_list)}) to continue. Ending combat.")
            self.stop_combat_logic()
            return

        # Check if all combatants are yielding - but only end combat if no active grapples exist
        all_yielding = all(entry.get(DB_IS_YIELDING, False) for entry in combatants_list)
        
        # Check for any active grapples (anyone grappling or being grappled)
        active_grapples = any(
            entry.get(DB_GRAPPLING_DBREF) is not None or entry.get(DB_GRAPPLED_BY_DBREF) is not None
            for entry in combatants_list
        )
        
        if all_yielding and not active_grapples:
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. All combatants are yielding and no active grapples. Ending combat peacefully.")
            # Send a message to all combatants about peaceful resolution
            for entry in combatants_list:
                char = entry.get(DB_CHAR)
                if char and char.location:
                    char.msg("|gWith all hostilities ceased, the confrontation comes to a peaceful end.|n")
            # Notify observers in all managed rooms
            for room in managed_rooms:
                if room:
                    room.msg_contents("|gThe confrontation ends peacefully as all participants stand down.|n", 
                                    exclude=[entry.get(DB_CHAR) for entry in combatants_list if entry.get(DB_CHAR)])
            self.stop_combat_logic()
            return
        elif all_yielding and active_grapples:
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. All combatants are yielding but active grapples exist. Combat continues.")
        elif active_grapples:
            grapple_pairs = []
            for entry in combatants_list:
                if entry.get(DB_GRAPPLING_DBREF):
                    grappler = entry.get(DB_CHAR)
                    victim = self._get_char_by_dbref(entry.get(DB_GRAPPLING_DBREF))
                    if grappler and victim:
                        grapple_pairs.append(f"{grappler.key}->{victim.key}")
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. Active grapples detected: {', '.join(grapple_pairs)}. Combat continues.")

        # Sort combatants by initiative for processing
        initiative_order = sorted(combatants_list, key=lambda e: e.get("initiative", 0), reverse=True)
        
        for combat_entry in initiative_order:
            char = combat_entry.get(DB_CHAR)
            splattercast.msg(f"DEBUG_LOOP_ITERATION: Starting processing for {char.key}, combat_entry: {combat_entry}")

            # Always get a fresh reference to ensure we have current data
            current_char_combat_entry = next((e for e in combatants_list if e.get(DB_CHAR) == char), None)
            if not current_char_combat_entry:
                splattercast.msg(f"AT_REPEAT: {char.key} no longer in combatants list. Skipping.")
                continue

            # Skip if character has skip_combat_round flag
            if hasattr(char.ndb, NDB_SKIP_ROUND) and getattr(char.ndb, NDB_SKIP_ROUND):
                delattr(char.ndb, NDB_SKIP_ROUND)
                splattercast.msg(f"AT_REPEAT: {char.key} skipping this round as requested.")
                char.msg("|yYou skip this combat round.|n")
                continue

            # START-OF-TURN NDB CLEANUP for charge flags
            if hasattr(char.ndb, "charging_vulnerability_active"):
                splattercast.msg(f"AT_REPEAT_START_TURN_CLEANUP: Clearing charging_vulnerability_active for {char.key} (was active from their own previous charge).")
                delattr(char.ndb, "charging_vulnerability_active")
            
            if hasattr(char.ndb, "charge_attack_bonus_active"):
                splattercast.msg(f"AT_REPEAT_START_TURN_CLEANUP: Clearing expired/unused charge_attack_bonus_active for {char.key}.")
                delattr(char.ndb, "charge_attack_bonus_active")

            # Get combat action for this character
            combat_action = current_char_combat_entry.get("combat_action")
            splattercast.msg(f"AT_REPEAT: {char.key} combat_action: {combat_action}")

            # Check if character is yielding first
            if current_char_combat_entry.get(DB_IS_YIELDING, False):
                # Exception: Allow release grapple actions even when yielding
                if combat_action == "release_grapple":
                    splattercast.msg(f"{char.key} is yielding but can still release their grapple.")
                    self._resolve_release_grapple(current_char_combat_entry, combatants_list)
                else:
                    # Check if this character is grappling someone (restraint mode)
                    grappling_target = self.get_grappling_obj(current_char_combat_entry)
                    if grappling_target:
                        # Grappler in restraint mode - maintain hold without violence
                        splattercast.msg(f"{char.key} is yielding but maintains restraining hold on {grappling_target.key}.")
                        char.msg(f"|gYou maintain a restraining hold on {grappling_target.key} without violence.|n")
                        grappling_target.msg(f"|g{char.key} maintains a gentle but firm restraining hold on you.|n")
                        char.location.msg_contents(f"|g{char.key} maintains a restraining hold on {grappling_target.key}.|n", exclude=[char, grappling_target])
                    else:
                        # Regular yielding behavior
                        splattercast.msg(f"{char.key} is yielding and takes no hostile action this turn.")
                        char.location.msg_contents(f"|y{char.key} holds their action, appearing non-hostile.|n", exclude=[char])
                        char.msg("|yYou hold your action, appearing non-hostile.|n")
                continue
                
            # Handle being grappled (auto resist unless yielding)
            grappler = self.get_grappled_by_obj(current_char_combat_entry)
            if grappler:
                # Safety check: prevent self-grappling and invalid grappler
                if grappler == char:
                    splattercast.msg(f"GRAPPLE_ERROR: {char.key} is grappled by themselves! Clearing invalid state.")
                    current_char_combat_entry[DB_GRAPPLED_BY_DBREF] = None
                    grappler = None
                elif not any(e[DB_CHAR] == grappler for e in combatants_list):
                    splattercast.msg(f"GRAPPLE_ERROR: {char.key} is grappled by {grappler.key} who is not in combat! Clearing invalid state.")
                    current_char_combat_entry[DB_GRAPPLED_BY_DBREF] = None
                    grappler = None
                    
            if grappler:
                # Check if the victim is yielding (restraint mode acceptance)
                if current_char_combat_entry.get(DB_IS_YIELDING, False):
                    # Victim is yielding/accepting restraint - no automatic escape attempt
                    splattercast.msg(f"{char.key} is being grappled by {grappler.key} but is yielding (accepting restraint).")
                    char.msg(f"|gYou remain still in {grappler.key}'s hold, not resisting.|n")
                    char.location.msg_contents(f"|g{char.key} does not resist {grappler.key}'s hold.|n", exclude=[char])
                    continue
                    
                # Victim is not yielding - automatically attempt to escape
                splattercast.msg(f"{char.key} is being grappled by {grappler.key} and automatically attempts to escape.")
                char.msg(f"|yYou struggle against {grappler.key}'s grip!|n")
                
                # Setup an escape attempt
                escaper_roll = randint(1, max(1, get_numeric_stat(char, "motorics", 1)))
                grappler_roll = randint(1, max(1, get_numeric_stat(grappler, "motorics", 1)))
                splattercast.msg(f"AUTO_ESCAPE_ATTEMPT: {char.key} (roll {escaper_roll}) vs {grappler.key} (roll {grappler_roll}).")

                if escaper_roll > grappler_roll:
                    # Success - clear grapple
                    current_char_combat_entry[DB_GRAPPLED_BY_DBREF] = None
                    grappler_entry = next((e for e in combatants_list if e[DB_CHAR] == grappler), None)
                    if grappler_entry:
                        grappler_entry[DB_GRAPPLING_DBREF] = None
                    
                    # Successful auto-escape switches victim to violent mode (fighting for their life)
                    was_yielding = current_char_combat_entry.get(DB_IS_YIELDING, False)
                    current_char_combat_entry[DB_IS_YIELDING] = False
                    
                    escape_messages = get_combat_message("grapple", "escape_hit", attacker=char, target=grappler)
                    char.msg(escape_messages.get("attacker_msg", f"You break free from {grappler.key}'s grasp!"))
                    grappler.msg(escape_messages.get("victim_msg", f"{char.key} breaks free from your grasp!"))
                    obs_msg = escape_messages.get("observer_msg", f"{char.key} breaks free from {grappler.key}'s grasp!")
                    char.location.msg_contents(obs_msg, exclude=[char, grappler])
                    
                    # Additional message if they switched from yielding to violent
                    if was_yielding:
                        char.msg(MSG_GRAPPLE_AUTO_ESCAPE_VIOLENT)
                    
                    splattercast.msg(f"AUTO_ESCAPE_SUCCESS: {char.key} escaped from {grappler.key}.")
                else:
                    # Failure
                    escape_messages = get_combat_message("grapple", "escape_miss", attacker=char, target=grappler)
                    char.msg(escape_messages.get("attacker_msg", f"You struggle but fail to break free from {grappler.key}'s grasp!"))
                    grappler.msg(escape_messages.get("victim_msg", f"{char.key} struggles but fails to break free from your grasp!"))
                    obs_msg = escape_messages.get("observer_msg", f"{char.key} struggles but fails to break free from {grappler.key}'s grasp!")
                    char.location.msg_contents(obs_msg, exclude=[char, grappler])
                    splattercast.msg(f"AUTO_ESCAPE_FAIL: {char.key} failed to escape {grappler.key}.")
                    
                # Either way, turn ends after escape attempt
                continue

            # Process combat action intent
            if combat_action:
                splattercast.msg(f"AT_REPEAT: {char.key} has action_intent: {combat_action}")
                
                if isinstance(combat_action, str):
                    if combat_action == "grapple_initiate":
                        self._resolve_grapple_initiate(current_char_combat_entry, combatants_list)
                        current_char_combat_entry["combat_action"] = None
                        continue
                    elif combat_action == "grapple_join":
                        self._resolve_grapple_join(current_char_combat_entry, combatants_list)
                        current_char_combat_entry["combat_action"] = None
                        continue
                    elif combat_action == "release_grapple":
                        self._resolve_release_grapple(current_char_combat_entry, combatants_list)
                        current_char_combat_entry["combat_action"] = None
                        continue
                elif isinstance(combat_action, dict):
                    intent_type = combat_action.get("type")
                    action_target_char = combat_action.get("target")
                    
                    # Validate target
                    is_action_target_valid = False
                    if action_target_char and any(e[DB_CHAR] == action_target_char for e in combatants_list):
                        if action_target_char.location and action_target_char.location in getattr(self.db, DB_MANAGED_ROOMS, []):
                            is_action_target_valid = True
                    
                    if not is_action_target_valid and action_target_char:
                        char.msg(f"The target of your planned action ({action_target_char.key}) is no longer valid.")
                        splattercast.msg(f"{char.key}'s action_intent target {action_target_char.key} is invalid. Intent cleared, falling through.")
                    elif intent_type == "grapple" and is_action_target_valid:
                        # Handle grapple intent
                        can_grapple_target = (char.location == action_target_char.location)
                        
                        if can_grapple_target:
                            # Proximity Check for Grapple
                            if not hasattr(char.ndb, NDB_PROXIMITY): 
                                setattr(char.ndb, NDB_PROXIMITY, set())
                            if action_target_char not in getattr(char.ndb, NDB_PROXIMITY):
                                char.msg(f"You need to be in melee proximity with {action_target_char.key} to grapple them. Try advancing or charging.")
                                splattercast.msg(f"GRAPPLE FAIL (PROXIMITY): {char.key} not in proximity with {action_target_char.key}.")
                                continue

                            attacker_roll = randint(1, max(1, get_numeric_stat(char, "motorics", 1)))
                            defender_roll = randint(1, max(1, get_numeric_stat(action_target_char, "motorics", 1)))
                            splattercast.msg(f"GRAPPLE ATTEMPT: {char.key} (roll {attacker_roll}) vs {action_target_char.key} (roll {defender_roll}).")

                            if attacker_roll > defender_roll:
                                # Store dbrefs for persistence
                                current_char_combat_entry[DB_GRAPPLING_DBREF] = self._get_dbref(action_target_char)
                                target_entry = next((e for e in combatants_list if e[DB_CHAR] == action_target_char), None)
                                if target_entry:
                                    target_entry[DB_GRAPPLED_BY_DBREF] = self._get_dbref(char)
                                
                                # Auto-yield both parties on successful grapple (restraint mode)
                                current_char_combat_entry[DB_IS_YIELDING] = True
                                if target_entry:
                                    target_entry[DB_IS_YIELDING] = True
                                
                                # Notify victim they're auto-yielding
                                action_target_char.msg(MSG_GRAPPLE_AUTO_YIELD)
                                
                                grapple_messages = get_combat_message("grapple", "hit", attacker=char, target=action_target_char)
                                char.msg(grapple_messages.get("attacker_msg"))
                                action_target_char.msg(grapple_messages.get("victim_msg"))
                                obs_msg = grapple_messages.get("observer_msg")
                                if char.location:
                                    char.location.msg_contents(obs_msg, exclude=[char, action_target_char])
                                splattercast.msg(f"GRAPPLE_SUCCESS: {char.key} grappled {action_target_char.key}.")
                            else:
                                # Grapple failed
                                grapple_messages = get_combat_message("grapple", "miss", attacker=char, target=action_target_char)
                                char.msg(grapple_messages.get("attacker_msg"))
                                action_target_char.msg(grapple_messages.get("victim_msg"))
                                obs_msg = grapple_messages.get("observer_msg")
                                if char.location:
                                    char.location.msg_contents(obs_msg, exclude=[char, action_target_char])
                                splattercast.msg(f"GRAPPLE_FAIL: {char.key} failed to grapple {action_target_char.key}.")
                        else:
                            char.msg(f"You can't reach {action_target_char.key} to grapple them from here.")
                            splattercast.msg(f"GRAPPLE FAIL (REACH): {char.key} cannot reach {action_target_char.key}.")
                        
                        continue
                    elif intent_type == "escape_grapple":
                        grappler = self.get_grappled_by_obj(current_char_combat_entry)
                        if grappler and any(e[DB_CHAR] == grappler for e in combatants_list):
                            escaper_roll = randint(1, max(1, get_numeric_stat(char, "motorics", 1)))
                            grappler_roll = randint(1, max(1, get_numeric_stat(grappler, "motorics", 1)))
                            splattercast.msg(f"ESCAPE ATTEMPT: {char.key} (roll {escaper_roll}) vs {grappler.key} (roll {grappler_roll}).")

                            if escaper_roll > grappler_roll:
                                current_char_combat_entry[DB_GRAPPLED_BY_DBREF] = None
                                grappler_entry = next((e for e in combatants_list if e[DB_CHAR] == grappler), None)
                                if grappler_entry:
                                    grappler_entry[DB_GRAPPLING_DBREF] = None
                                escape_messages = get_combat_message("grapple", "escape_hit", attacker=char, target=grappler)
                                char.msg(escape_messages.get("attacker_msg"))
                                grappler.msg(escape_messages.get("victim_msg"))
                                obs_msg = escape_messages.get("observer_msg")
                                char.location.msg_contents(obs_msg, exclude=[char, grappler])
                                splattercast.msg(f"ESCAPE SUCCESS: {char.key} escaped from {grappler.key}.")
                            else:
                                escape_messages = get_combat_message("grapple", "escape_miss", attacker=char, target=grappler)
                                char.msg(escape_messages.get("attacker_msg"))
                                grappler.msg(escape_messages.get("victim_msg"))
                                obs_msg = escape_messages.get("observer_msg")
                                char.location.msg_contents(obs_msg, exclude=[char, grappler])
                                splattercast.msg(f"ESCAPE FAIL: {char.key} failed to escape {grappler.key}.")
                        continue

            # Standard attack processing - get target and attack
            target = self.get_target(char)
            splattercast.msg(f"AT_REPEAT: After get_target(), {char.key} target is {target.key if target else None}")
            if target:
                splattercast.msg(f"AT_REPEAT: About to call _process_attack({char.key}, {target.key}, ...)")
                try:
                    self._process_attack(char, target, current_char_combat_entry, combatants_list)
                    splattercast.msg(f"AT_REPEAT: _process_attack completed for {char.key} -> {target.key}")
                except Exception as e:
                    splattercast.msg(f"AT_REPEAT: ERROR in _process_attack for {char.key} -> {target.key}: {e}")
                    import traceback
                    splattercast.msg(f"AT_REPEAT: Traceback: {traceback.format_exc()}")
            else:
                splattercast.msg(f"AT_REPEAT: {char.key} has no valid target for attack.")

            # Clear the combat action after processing
            current_char_combat_entry["combat_action"] = None

        # Save the modified combatants list back to the database
        setattr(self.db, DB_COMBATANTS, combatants_list)

        # Check if combat should continue
        remaining_combatants = getattr(self.db, DB_COMBATANTS, [])
        if not remaining_combatants:
            splattercast.msg(f"AT_REPEAT: No combatants remain in handler {self.key}. Stopping.")
            self.stop_combat_logic()
            return
        elif len(remaining_combatants) <= 1:
            splattercast.msg(f"AT_REPEAT: Only {len(remaining_combatants)} combatant(s) remain in handler {self.key}. Ending combat.")
            self.stop_combat_logic()
            return

        self.db.round += 1
        splattercast.msg(f"AT_REPEAT: Handler {self.key}. Round {self.db.round} scheduled for next interval.")

    def _process_attack(self, attacker, target, attacker_entry, combatants_list):
        """Process a standard attack between two characters."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        splattercast.msg(f"_PROCESS_ATTACK: Starting attack processing for {attacker.key} -> {target.key}")
        
        # Check if attacker is yielding
        if attacker_entry.get(DB_IS_YIELDING, False):
            splattercast.msg(f"AT_REPEAT: {attacker.key} is yielding, skipping attack.")
            return
        
        splattercast.msg(f"_PROCESS_ATTACK: {attacker.key} is not yielding, continuing...")
        
        # Find target's entry
        target_entry = next((e for e in combatants_list if e.get(DB_CHAR) == target), None)
        if not target_entry:
            splattercast.msg(f"AT_REPEAT: Target {target.key} not found in combatants.")
            return
        
        splattercast.msg(f"_PROCESS_ATTACK: Found target entry for {target.key}, proceeding to weapon detection...")
        
        # Get weapon and weapon type - using consistent approach with attack command
        hands = getattr(attacker, "hands", {})
        weapon = next((item for hand, item in hands.items() if item), None)
        
        # Safe weapon type detection
        weapon_type = "unarmed"
        is_ranged_weapon = False
        
        if weapon:
            # Check if weapon has db attribute and it's not None
            weapon_db = getattr(weapon, "db", None)
            if weapon_db:
                weapon_type = getattr(weapon_db, "weapon_type", "unarmed")
                is_ranged_weapon = getattr(weapon_db, "is_ranged", False)
            else:
                # Fallback if weapon.db is None
                splattercast.msg(f"WEAPON_WARNING: {weapon.key} has no db attribute or db is None, using unarmed")
                weapon_type = "unarmed"
                is_ranged_weapon = False
        
        # Debug weapon detection
        splattercast.msg(f"WEAPON_DEBUG: {attacker.key} weapon={weapon.key if weapon else 'None'}, "
                        f"weapon_type={weapon_type}, is_ranged={is_ranged_weapon}")
        if weapon:
            weapon_db = getattr(weapon, "db", None)
            if weapon_db:
                splattercast.msg(f"WEAPON_DEBUG: {weapon.key} db.is_ranged={getattr(weapon_db, 'is_ranged', 'MISSING')}, "
                                f"db.weapon_type={getattr(weapon_db, 'weapon_type', 'MISSING')}")
            else:
                splattercast.msg(f"WEAPON_DEBUG: {weapon.key} has no db or db is None")
        
        # Check proximity and weapon compatibility
        attack_has_disadvantage = False
        if attacker.location == target.location:
            # Same room - check proximity
            attacker_proximity = getattr(attacker.ndb, NDB_PROXIMITY, set())
            is_in_melee_proximity = target in attacker_proximity
            
            if is_in_melee_proximity and is_ranged_weapon:
                # Ranged weapon in melee - apply disadvantage
                attacker.msg(f"|yYou struggle to aim your {weapon.key if weapon else 'weapon'} effectively while locked in melee with {target.key}. You attack at disadvantage.|n")
                attack_has_disadvantage = True
                splattercast.msg(f"ATTACK_DISADVANTAGE: {attacker.key} using ranged weapon in melee vs {target.key}")
            elif not is_in_melee_proximity and not is_ranged_weapon:
                # Melee weapon at range - invalid
                attacker.msg(f"|rYou are too far away to hit {target.key} with your {weapon.key if weapon else 'fists'}. Try advancing or charging.|n")
                splattercast.msg(f"ATTACK_INVALID: {attacker.key} trying melee attack at range vs {target.key}")
                return
            # Note: Ranged weapon at range (not in proximity) is valid and continues below
        elif target.location not in getattr(self.db, DB_MANAGED_ROOMS, []):
            # Target not in managed rooms
            attacker.msg(f"|r{target.key} is not in the current combat zone.|n")
            return
        elif not is_ranged_weapon:
            # Different rooms but no ranged weapon
            attacker.msg(f"|rYou need a ranged weapon to attack {target.key} in {target.location.key}.|n")
            return
        
        # Calculate attack rolls (with disadvantage if applicable)
        attacker_grit = get_numeric_stat(attacker, "grit", 1)
        splattercast.msg(f"_PROCESS_ATTACK: Got attacker grit: {attacker_grit}")
        
        if attack_has_disadvantage:
            # Roll twice, take the lower
            roll1 = randint(1, max(1, attacker_grit))
            roll2 = randint(1, max(1, attacker_grit))
            attack_roll_base = min(roll1, roll2)
            splattercast.msg(f"ATTACK_DISADVANTAGE_ROLL: {attacker.key} rolls {roll1}, {roll2} -> {attack_roll_base} (disadvantage)")
        else:
            attack_roll_base = randint(1, max(1, attacker_grit))
        
        splattercast.msg(f"_PROCESS_ATTACK: Attack roll calculated: {attack_roll_base}")
        
        # Check for aiming bonus
        aiming_target = getattr(attacker.ndb, "aiming_at", None)
        if aiming_target == target and is_ranged_weapon:
            # Grant aiming bonus for ranged attacks against aimed target
            aiming_bonus = 2  # Flat bonus for aimed shots
            attack_roll_base += aiming_bonus
            splattercast.msg(f"AIMING_BONUS: {attacker.key} gets +{aiming_bonus} attack bonus for aiming at {target.key}")
            
            # Clear the aim after use
            delattr(attacker.ndb, "aiming_at")
            if hasattr(target.ndb, "aimed_at_by") and getattr(target.ndb, "aimed_at_by") == attacker:
                delattr(target.ndb, "aimed_at_by")
            
            attacker.msg("|gYour careful aim pays off! You attack with improved accuracy.|n")
            target.msg(f"|r{attacker.key}'s careful aim makes their attack more precise!|n")
        elif aiming_target == target and not is_ranged_weapon:
            # Small bonus even for melee attacks when aimed
            aiming_bonus = 1
            attack_roll_base += aiming_bonus
            splattercast.msg(f"AIMING_BONUS_MELEE: {attacker.key} gets +{aiming_bonus} small bonus for focusing on {target.key}")
            
            # Clear the aim after use
            delattr(attacker.ndb, "aiming_at")
            if hasattr(target.ndb, "aimed_at_by") and getattr(target.ndb, "aimed_at_by") == attacker:
                delattr(target.ndb, "aimed_at_by")
        
        # Check for direction aiming bonus (when attacking into another room)
        aiming_direction = getattr(attacker.ndb, "aiming_direction", None)
        if aiming_direction and attacker.location != target.location and is_ranged_weapon:
            # Grant aiming bonus for ranged attacks into aimed direction
            direction_bonus = 2  # Same bonus as target aiming
            attack_roll_base += direction_bonus
            splattercast.msg(f"DIRECTION_AIMING_BONUS: {attacker.key} gets +{direction_bonus} attack bonus for aiming {aiming_direction}")
            
            # Clear the direction aim after use
            delattr(attacker.ndb, "aiming_direction")
            
            attacker.msg(f"|gYour careful aim {aiming_direction} pays off! You attack with improved accuracy.|n")
                
        # Defense roll
        defense_roll = randint(1, max(1, get_numeric_stat(target, "motorics", 1)))
        
        splattercast.msg(f"ATTACK_ROLL: {attacker.key} (attack {attack_roll_base}) vs {target.key} (defense {defense_roll})")
        
        # Determine if grappling this target
        grappling_this_target = self.get_grappling_obj(attacker_entry) == target
        effective_weapon_type = "grapple" if grappling_this_target else weapon_type
        
        splattercast.msg(f"_PROCESS_ATTACK: About to determine hit/miss. Grappling={grappling_this_target}, effective_weapon_type={effective_weapon_type}")
        
        if attack_roll_base > defense_roll:
            splattercast.msg(f"_PROCESS_ATTACK: HIT DETECTED - {attacker.key} hit {target.key}")
            # Hit - calculate damage
            damage = max(1, get_numeric_stat(attacker, "grit", 1))
            
            # Check for body shield mechanics if target is grappling someone
            actual_target = target
            if target_entry:
                # Target is grappling someone - they might use them as a shield
                target_grappling = self.get_grappling_obj(target_entry)
                if target_grappling and target_grappling != attacker:
                    # Body shield check
                    target_positioning_roll = randint(1, max(1, get_numeric_stat(target, "motorics", 1)))
                    shield_evasion_roll = randint(1, max(1, get_numeric_stat(target_grappling, "motorics", 1)))
                    
                    if target_positioning_roll > shield_evasion_roll:
                        actual_target = target_grappling
                        shield_msg = f"|c{target.key} yanks {target_grappling.key} in the way! {target_grappling.key} takes the hit!|n"
                        attacker.location.msg_contents(shield_msg, exclude=[target, target_grappling])
                        splattercast.msg(f"BODY_SHIELD: {target.key} used {target_grappling.key} as shield successfully")
                    else:
                        shield_fail_msg = f"|y{target.key} tries to use {target_grappling.key} as a shield but fails!|n"
                        attacker.location.msg_contents(shield_fail_msg, exclude=[target, target_grappling])
            
            # Apply damage
            if hasattr(actual_target, "take_damage"):
                actual_target.take_damage(damage)
            else:
                # Fallback HP system
                current_hp = getattr(actual_target, "hp", 10)
                actual_target.hp = max(0, current_hp - damage)
            
            # Check if target died
            is_dead = False
            if hasattr(actual_target, "is_dead"):
                is_dead = actual_target.is_dead()
            else:
                is_dead = getattr(actual_target, "hp", 10) <= 0
            
            # Get and send appropriate messages
            if is_dead:
                splattercast.msg(f"_PROCESS_ATTACK: Target is dead, getting kill messages")
                try:
                    hit_messages = get_combat_message(effective_weapon_type, "kill", 
                                                      attacker=attacker, target=actual_target, item=weapon, damage=damage)
                    self._handle_death(actual_target, attacker, effective_weapon_type, weapon)
                    
                    # CRITICAL: Remove the dead character from the local combatants_list
                    # to prevent them from being re-added when the list is saved back to database
                    combatants_list[:] = [e for e in combatants_list if e.get(DB_CHAR) != actual_target]
                    splattercast.msg(f"DEATH_CLEANUP: Removed {actual_target.key} from local combatants_list to prevent resurrection")
                    
                except Exception as e:
                    splattercast.msg(f"_PROCESS_ATTACK: ERROR in death handling: {e}")
                    # Fallback death handling
                    attacker.msg(f"You kill {actual_target.key}!")
                    actual_target.msg(f"{attacker.key} kills you!")
                    self.remove_combatant(actual_target)
                    # Also remove from local list in fallback case
                    combatants_list[:] = [e for e in combatants_list if e.get(DB_CHAR) != actual_target]
            else:
                splattercast.msg(f"_PROCESS_ATTACK: Target survived, getting hit messages")
                try:
                    hit_messages = get_combat_message(effective_weapon_type, "hit", 
                                                      attacker=attacker, target=actual_target, item=weapon, damage=damage)
                    
                    attacker.msg(hit_messages.get("attacker_msg", f"You hit {actual_target.key}!"))
                    actual_target.msg(hit_messages.get("victim_msg", f"{attacker.key} hits you!"))
                    
                    # Send observer message to room
                    obs_msg = hit_messages.get("observer_msg", f"{attacker.key} hits {actual_target.key}!")
                    for location in {attacker.location, actual_target.location}:
                        if location:
                            location.msg_contents(obs_msg, exclude=[attacker, actual_target])
                    
                    splattercast.msg(f"HIT: {attacker.key} hits {actual_target.key} for {damage} damage (dead: {is_dead})")
                except Exception as e:
                    splattercast.msg(f"_PROCESS_ATTACK: ERROR in hit messaging: {e}")
                    # Fallback hit messages
                    attacker.msg(f"You hit {actual_target.key}!")
                    actual_target.msg(f"{attacker.key} hits you!")
                    splattercast.msg(f"HIT: {attacker.key} hits {actual_target.key} for {damage} damage (fallback)")
                
        else:
            splattercast.msg(f"_PROCESS_ATTACK: MISS DETECTED - {attacker.key} missed {target.key}")
            # Miss
            miss_phase = "grapple_damage_miss" if grappling_this_target else "miss"
            splattercast.msg(f"_PROCESS_ATTACK: About to get miss message with phase '{miss_phase}'")
            
            try:
                miss_messages = get_combat_message(effective_weapon_type, miss_phase, 
                                                   attacker=attacker, target=target, item=weapon)
                splattercast.msg(f"_PROCESS_ATTACK: Got miss messages successfully")
                attacker.msg(miss_messages.get("attacker_msg", f"You miss {target.key}!"))
                target.msg(miss_messages.get("victim_msg", f"{attacker.key} misses you!"))
                
                obs_msg = miss_messages.get("observer_msg", f"{attacker.key} misses {target.key}!")
                for location in {attacker.location, target.location}:
                    if location:
                        location.msg_contents(obs_msg, exclude=[attacker, target])
                
                splattercast.msg(f"MISS: {attacker.key} misses {target.key}")
            except Exception as e:
                splattercast.msg(f"_PROCESS_ATTACK: ERROR getting miss messages: {e}")
                # Fallback messages
                attacker.msg(f"You miss {target.key}!")
                target.msg(f"{attacker.key} misses you!")
                splattercast.msg(f"MISS: {attacker.key} misses {target.key} (fallback messages)")
    
    def _handle_death(self, victim, killer, weapon_type, weapon):
        """Handle character death."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Get and send death messages
        death_messages = get_combat_message(weapon_type, "kill", attacker=killer, target=victim, item=weapon)
        killer.msg(death_messages.get("attacker_msg", f"You kill {victim.key}!"))
        victim.msg(death_messages.get("victim_msg", f"{killer.key} kills you!"))
        
        obs_msg = death_messages.get("observer_msg", f"{killer.key} kills {victim.key}!")
        victim.location.msg_contents(obs_msg, exclude=[killer, victim])
        
        splattercast.msg(f"DEATH: {victim.key} killed by {killer.key}")
        
        # Handle death - call character's death method if it exists
        if hasattr(victim, "at_death"):
            victim.at_death(killer)
        
        # Remove from combat
        self.remove_combatant(victim)
        
        # Clear targeting references to the deceased (don't auto-retarget)
        combatants = getattr(self.db, DB_COMBATANTS, [])
        for entry in combatants:
            if self.get_target_obj(entry) == victim:
                # Clear the target instead of auto-retargeting to prevent unwanted hostility
                entry[DB_TARGET_DBREF] = None
                splattercast.msg(f"{entry[DB_CHAR].key} no longer targets slain {victim.key}. Must choose new target manually.")
                # Inform the character that their target is gone
                if hasattr(entry[DB_CHAR], 'msg'):
                    entry[DB_CHAR].msg(f"|yYour target {victim.get_display_name(entry[DB_CHAR]) if hasattr(victim, 'get_display_name') else victim.key} has been slain. Choose a new target if you wish to continue fighting.|n")

    def _resolve_grapple_attempt(self, attacker_entry, target_entry):
        """Performs the opposed roll for a grapple."""
        attacker = attacker_entry[DB_CHAR]
        target = target_entry[DB_CHAR]
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)

        attacker_roll = randint(1, max(1, get_numeric_stat(attacker, "motorics", 1)))
        defender_roll = randint(1, max(1, get_numeric_stat(target, "motorics", 1)))
        splattercast.msg(f"GRAPPLE_ROLL: {attacker.key} (roll {attacker_roll}) vs {target.key} (roll {defender_roll}).")
        
        return attacker_roll > defender_roll

    def _resolve_grapple_initiate(self, attacker_entry, combatants_list):
        """Resolves an all-or-nothing grapple that starts combat."""
        attacker = attacker_entry[DB_CHAR]
        target = self.get_target_obj(attacker_entry)
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not target:
            splattercast.msg(f"GRAPPLE_INITIATE: {attacker.key} has no target for grapple initiate.")
            attacker.msg("|rYou have no target to grapple!|n")
            return
            
        # Find target's combat entry
        target_entry = next((e for e in combatants_list if e[DB_CHAR] == target), None)
        if not target_entry:
            splattercast.msg(f"GRAPPLE_INITIATE: Target {target.key} not in combat.")
            return

        # Check proximity first, if not in proximity, need to advance
        in_proximity = target in getattr(attacker.ndb, NDB_PROXIMITY, set())
        advance_success = False
        
        if in_proximity:
            advance_success = True
            splattercast.msg(f"GRAPPLE_INITIATE: {attacker.key} already in proximity with {target.key}.")
        else:
            # Try to advance into proximity using opposed roll
            advance_success = opposed_roll(attacker, target, "motorics", "motorics")
            if advance_success:
                establish_proximity(attacker, target)
                splattercast.msg(f"GRAPPLE_INITIATE: {attacker.key} successfully advanced to {target.key}.")
            else:
                splattercast.msg(f"GRAPPLE_INITIATE: {attacker.key} failed to advance to {target.key}.")

        # If advance succeeded, attempt the grapple
        if advance_success and self._resolve_grapple_attempt(attacker_entry, target_entry):
            # Successful grapple
            attacker_entry[DB_GRAPPLING_DBREF] = self._get_dbref(target)
            target_entry[DB_GRAPPLED_BY_DBREF] = self._get_dbref(attacker)
            
            # Set both parties to yielding (peaceful restraint mode) by default
            # This is for grapple_initiate which starts new combat - always start peaceful
            attacker_entry[DB_IS_YIELDING] = True
            target_entry[DB_IS_YIELDING] = True
            
            grapple_messages = get_combat_message("grapple", "hit", attacker=attacker, target=target)
            attacker.msg(grapple_messages.get("attacker_msg", f"You grapple {target.key}!"))
            target.msg(grapple_messages.get("victim_msg", f"{attacker.key} grapples you!"))
            
            obs_msg = grapple_messages.get("observer_msg", f"{attacker.key} grapples {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"GRAPPLE_SUCCESS: {attacker.key} grapples {target.key}")
        else:
            # Failed grapple - target gets bonus attack
            fail_messages = get_combat_message("grapple", "miss", attacker=attacker, target=target)
            attacker.msg(fail_messages.get("attacker_msg", f"You fail to grapple {target.key}!"))
            target.msg(fail_messages.get("victim_msg", f"{attacker.key} fails to grapple you!"))
            
            obs_msg = fail_messages.get("observer_msg", f"{attacker.key} fails to grapple {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"GRAPPLE_FAIL: {attacker.key} fails to grapple {target.key}")
            self.resolve_bonus_attack(target, attacker)

    def _resolve_grapple_join(self, attacker_entry, combatants_list):
        """Resolves a grapple attempt within an ongoing combat."""
        attacker = attacker_entry[DB_CHAR]
        target = self.get_target_obj(attacker_entry)
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not target:
            splattercast.msg(f"GRAPPLE_JOIN: {attacker.key} has no target for grapple join.")
            attacker.msg("|rYou have no target to grapple!|n")
            return
            
        # Find target's combat entry
        target_entry = next((e for e in combatants_list if e[DB_CHAR] == target), None)
        if not target_entry:
            splattercast.msg(f"GRAPPLE_JOIN: Target {target.key} not in combat.")
            return

        # Check proximity first, if not in proximity, need to advance
        in_proximity = target in getattr(attacker.ndb, NDB_PROXIMITY, set())
        advance_success = False
        
        if in_proximity:
            advance_success = True
            splattercast.msg(f"GRAPPLE_JOIN: {attacker.key} already in proximity with {target.key}.")
        else:
            # Try to advance into proximity using opposed roll
            advance_success = opposed_roll(attacker, target, "motorics", "motorics")
            if advance_success:
                establish_proximity(attacker, target)
                splattercast.msg(f"GRAPPLE_JOIN: {attacker.key} successfully advanced to {target.key}.")
            else:
                splattercast.msg(f"GRAPPLE_JOIN: {attacker.key} failed to advance to {target.key}.")

        # If advance succeeded, attempt the grapple
        if advance_success and self._resolve_grapple_attempt(attacker_entry, target_entry):
            # Successful grapple
            attacker_entry[DB_GRAPPLING_DBREF] = self._get_dbref(target)
            target_entry[DB_GRAPPLED_BY_DBREF] = self._get_dbref(attacker)
            
            # For grapple_join (during ongoing combat), preserve existing violence state
            # Don't modify is_yielding - if they were fighting violently, keep it violent
            # If they were yielding, keep them yielding
            
            grapple_messages = get_combat_message("grapple", "hit", attacker=attacker, target=target)
            attacker.msg(grapple_messages.get("attacker_msg", f"You grapple {target.key}!"))
            target.msg(grapple_messages.get("victim_msg", f"{attacker.key} grapples you!"))
            
            obs_msg = grapple_messages.get("observer_msg", f"{attacker.key} grapples {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"GRAPPLE_SUCCESS: {attacker.key} grapples {target.key}")
        else:
            # Failed grapple - target gets bonus attack
            fail_messages = get_combat_message("grapple", "miss", attacker=attacker, target=target)
            attacker.msg(fail_messages.get("attacker_msg", f"You fail to grapple {target.key}!"))
            target.msg(fail_messages.get("victim_msg", f"{attacker.key} fails to grapple you!"))
            
            obs_msg = fail_messages.get("observer_msg", f"{attacker.key} fails to grapple {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"GRAPPLE_FAIL: {attacker.key} fails to grapple {target.key}")
            self.resolve_bonus_attack(target, attacker)

    def resolve_bonus_attack(self, attacker, victim):
        """Immediately resolves a single bonus attack."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"BONUS_ATTACK: Resolving from {attacker.key} against {victim.key}.")
        
        combatants = getattr(self.db, DB_COMBATANTS, [])
        attacker_entry = next((e for e in combatants if e[DB_CHAR] == attacker), None)
        victim_entry = next((e for e in combatants if e[DB_CHAR] == victim), None)
        
        if not attacker_entry or not victim_entry:
            splattercast.msg(f"BONUS_ATTACK: Could not find combat entries for {attacker.key} or {victim.key}.")
            return
            
        # This is a simplified attack resolution - we'll send some messages and deal damage
        attacker.msg(f"|gYou hit {victim.key} with a swift counter-attack!|n")
        victim.msg(f"|r{attacker.key} counters your failed move, striking you!|n")
        attacker.location.msg_contents(
            f"{attacker.key} counters {victim.key}'s failed move!",
            exclude=[attacker, victim]
        )
        
        # Apply damage - simple implementation
        damage = 1
        if hasattr(victim, "hp"):
            old_hp = victim.hp
            victim.hp = max(0, old_hp - damage)
            splattercast.msg(f"BONUS_ATTACK: {victim.key} takes {damage} damage. HP: {old_hp} -> {victim.hp}")
            
            if victim.hp <= 0:
                self._handle_death(victim, attacker, "unarmed", None)
    
    def _resolve_release_grapple(self, attacker_entry, combatants_list):
        """Resolves a release grapple action."""
        attacker = attacker_entry[DB_CHAR]
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Get the victim being grappled
        victim_char_being_grappled = self.get_grappling_obj(attacker_entry)
        
        if not victim_char_being_grappled:
            splattercast.msg(f"RELEASE_GRAPPLE: {attacker.key} is not grappling anyone.")
            attacker.msg("|rYou are not grappling anyone to release!|n")
            return False
        
        # Find victim's combat entry
        victim_entry = next((e for e in combatants_list if e[DB_CHAR] == victim_char_being_grappled), None)
        
        if not victim_entry:
            splattercast.msg(f"RELEASE_GRAPPLE: Victim {victim_char_being_grappled.key} not found in combat.")
            return False
        
        # Validate the victim is actually in the same location
        managed_rooms = getattr(self.db, DB_MANAGED_ROOMS, [])
        if not victim_char_being_grappled.location or victim_char_being_grappled.location not in managed_rooms:
            splattercast.msg(f"RELEASE_GRAPPLE: Victim {victim_char_being_grappled.key} not in managed rooms.")
            return False
        
        # Debug before release
        splattercast.msg(f"RELEASE GRAPPLE DEBUG: Before release - {attacker.key} grappling_dbref: {attacker_entry.get(DB_GRAPPLING_DBREF)}")
        splattercast.msg(f"RELEASE GRAPPLE DEBUG: Before release - {victim_char_being_grappled.key} grappled_by_dbref: {victim_entry.get(DB_GRAPPLED_BY_DBREF)}")
        
        # Check if grappler is yielding to determine victim's post-release state
        grappler_is_yielding = attacker_entry.get(DB_IS_YIELDING, False)
        
        # Clear the grapple relationship on both sides
        attacker_entry[DB_GRAPPLING_DBREF] = None
        victim_entry[DB_GRAPPLED_BY_DBREF] = None
        
        # Post-release victim state logic
        if grappler_is_yielding:
            victim_entry[DB_IS_YIELDING] = True
            splattercast.msg(f"RELEASE_GRAPPLE: Grappler {attacker.key} was yielding. Setting victim {victim_char_being_grappled.key} to yielding.")
        else:
            victim_entry[DB_IS_YIELDING] = False
            splattercast.msg(f"RELEASE_GRAPPLE: Grappler {attacker.key} was not yielding. Setting victim {victim_char_being_grappled.key} to not yielding.")
        
        # Debug after release
        splattercast.msg(f"RELEASE GRAPPLE DEBUG: After release - {attacker.key} grappling_dbref: {attacker_entry.get(DB_GRAPPLING_DBREF)}")
        splattercast.msg(f"RELEASE GRAPPLE DEBUG: After release - {victim_char_being_grappled.key} grappled_by_dbref: {victim_entry.get(DB_GRAPPLED_BY_DBREF)}")
        
        # Get and send messages
        release_messages = get_combat_message("grapple", "release", attacker=attacker, target=victim_char_being_grappled)
        attacker.msg(release_messages.get("attacker_msg", f"You release {victim_char_being_grappled.key}."))
        victim_char_being_grappled.msg(release_messages.get("victim_msg", f"{attacker.key} releases you."))
        obs_msg = release_messages.get("observer_msg", f"{attacker.key} releases {victim_char_being_grappled.key}.")
        for loc in {attacker.location, victim_char_being_grappled.location}:
            if loc:
                loc.msg_contents(obs_msg, exclude=[attacker, victim_char_being_grappled])
        
        splattercast.msg(f"RELEASE GRAPPLE: {attacker.key} released {victim_char_being_grappled.key}. Grapple state cleared for both.")
        return True

    # --- Utility Methods ---
    
    def _get_dbref(self, char):
        """Get DBREF from a character object."""
        if not char:
            return None
        return getattr(char, 'id', None) or getattr(char, 'dbref', None)
    
    def _get_char_by_dbref(self, dbref):
        """Resolve a DBREF to a character object."""
        if not dbref:
            return None
        try:
            results = search_object(f"#{dbref}")
            if results and len(results) == 1:
                return results[0]
        except Exception:
            pass
        return None
    
    def get_target_obj(self, combatant_entry):
        """Get the target object for a combatant entry."""
        target_dbref = combatant_entry.get(DB_TARGET_DBREF)
        return self._get_char_by_dbref(target_dbref)
    
    def get_grappling_obj(self, combatant_entry):
        """Get the character that this combatant is grappling."""
        grappling_dbref = combatant_entry.get(DB_GRAPPLING_DBREF)
        return self._get_char_by_dbref(grappling_dbref)
    
    def get_grappled_by_obj(self, combatant_entry):
        """Get the character that is grappling this combatant."""
        grappled_by_dbref = combatant_entry.get(DB_GRAPPLED_BY_DBREF)
        return self._get_char_by_dbref(grappled_by_dbref)
