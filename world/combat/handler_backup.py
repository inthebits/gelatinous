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
    DEBUG_PREFIX_HANDLER, DEBUG_SUCCESS, DEBUG_FAIL, DEBUG_ERROR, DEBUG_CLEANUP
)
from .utils import (
    get_numeric_stat, log_combat_action, get_display_name_safe,
    roll_stat, opposed_roll
)
from .proximity import clear_all_proximity, establish_proximity
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
                splattercast.msg(f"{DEBUG_PREFIX_HANDLER}_GET: Found inactive handler {script.key} on {location.key}. Stopping and deleting it.")
                script.stop() # Ensure it's fully stopped
                script.delete()
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
        other_handler.stop()
        other_handler.delete()
        
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
        
        # Check if already in combat
        combatants = getattr(self.db, DB_COMBATANTS, [])
        for entry in combatants:
            if entry.get(DB_CHAR) == char:
                splattercast.msg(f"ADD_COMB: {char.key} is already in combat.")
                return
        
        # Create combat entry
        entry = {
            DB_CHAR: char,
            "initiative": randint(1, 20) + get_numeric_stat(char, "motorics", 0),
            DB_TARGET_DBREF: self._get_dbref(target),
            DB_GRAPPLING_DBREF: self._get_dbref(initial_grappling),
            DB_GRAPPLED_BY_DBREF: self._get_dbref(initial_grappled_by),
            DB_IS_YIELDING: initial_is_yielding,
            "combat_action": None
        }
        
        combatants.append(entry)
        setattr(self.db, DB_COMBATANTS, combatants)
        
        # Set the character's handler reference
        setattr(char.ndb, NDB_COMBAT_HANDLER, self)
        
        splattercast.msg(f"ADD_COMB: {char.key} added to combat in {self.key} with initiative {entry['initiative']}.")
        char.msg("|rYou enter combat!|n")
        
        # Start combat if not already running
        if not getattr(self.db, DB_COMBAT_RUNNING, False):
            self.start()

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
            break_grapple(char, grappling, handler=self)
        if grappled_by:
            break_grapple(grappled_by, char, handler=self)
        
        # Clear NDB attributes
        ndb_attrs = [NDB_PROXIMITY, NDB_SKIP_ROUND, "charging_vulnerability_active", 
                    "charge_attack_bonus_active", "skip_combat_round"]
        for attr in ndb_attrs:
            if hasattr(char.ndb, attr):
                delattr(char.ndb, attr)

    def get_target_obj(self, combatant_entry):
        """
        Get the target object from a combatant entry.
        
        Args:
            combatant_entry: The combatant's entry dict
            
        Returns:
            Character object or None
        """
        target_dbref = combatant_entry.get(DB_TARGET_DBREF)
        return self._get_char_by_dbref(target_dbref)
    
    def get_grappling_obj(self, combatant_entry):
        """
        Get the character being grappled by this combatant.
        
        Args:
            combatant_entry: The combatant's entry dict
            
        Returns:
            Character object or None
        """
        grappling_dbref = combatant_entry.get(DB_GRAPPLING_DBREF)
        return self._get_char_by_dbref(grappling_dbref)
    
    def get_grappled_by_obj(self, combatant_entry):
        """
        Get the character grappling this combatant.
        
        Args:
            combatant_entry: The combatant's entry dict
            
        Returns:
            Character object or None
        """
        grappled_by_dbref = combatant_entry.get(DB_GRAPPLED_BY_DBREF)
        return self._get_char_by_dbref(grappled_by_dbref)

    def set_target(self, char, target):
        """
        Set a new target for a combatant.
        
        Args:
            char: The character setting a target
            target: The target character (or None to clear)
        """
        combatants = getattr(self.db, DB_COMBATANTS, [])
        for entry in combatants:
            if entry.get(DB_CHAR) == char:
                entry[DB_TARGET_DBREF] = self._get_dbref(target)
                setattr(self.db, DB_COMBATANTS, combatants)
                break

    def get_target(self, char):
        """
        Determine the current valid target for a combatant.
        
        Args:
            char: The character to get target for
            
        Returns:
            Character object or None
        """
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        combatants = getattr(self.db, DB_COMBATANTS, [])
        entry = next((e for e in combatants if e.get(DB_CHAR) == char), None)
        
        if not entry:
            splattercast.msg(f"No combat entry found for {char.key}.")
            return None
            
        # Get target using dbref
        target = self.get_target_obj(entry)
        
        valid_chars = [e.get(DB_CHAR) for e in combatants]
        if not target or target not in valid_chars:
            splattercast.msg(f"{char.key} has no valid target or their target is not in combat.")
            attackers = [
                e.get(DB_CHAR) for e in combatants 
                if self.get_target_obj(e) == char and e.get(DB_CHAR) != char
            ]
            splattercast.msg(f"Attackers targeting {char.key}: {[a.key for a in attackers]}.")

            if not attackers:
                splattercast.msg(f"{char.key} has no offensive target and is not being targeted by anyone for an attack. Potential for disengagement.")
                return None
            else:
                target = attackers[0]
                splattercast.msg(f"{char.key} retargeting to {target.key}.")
                self.set_target(char, target)
        else:
            splattercast.msg(f"{char.key} keeps current target {target.key}.")
        return target

    def get_initiative_order(self):
        """
        Return combatants sorted by initiative, highest first.
        
        Returns:
            List of combat entries sorted by initiative
        """
        combatants = getattr(self.db, DB_COMBATANTS, [])
        return sorted(combatants, key=lambda e: e.get("initiative", 0), reverse=True)

    def _get_char_by_dbref(self, dbref):
        """
        Get a character object by dbref.
        
        Args:
            dbref: The dbref string to search for
            
        Returns:
            Character object or None if not found
        """
        if not dbref:
            return None
        
        # Search by dbref (adding # if not present)
        if not str(dbref).startswith("#"):
            dbref = f"#{dbref}"
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"DBREF_LOOKUP_DEBUG: Searching for dbref '{dbref}'")
        
        results = search_object(dbref)
        if results:
            splattercast.msg(f"DBREF_LOOKUP_DEBUG: Found {results[0].key} (dbref {results[0].dbref})")
            return results[0]
        else:
            splattercast.msg(f"DBREF_LOOKUP_DEBUG: No results found for dbref '{dbref}'")
        return None
    
    def _get_dbref(self, obj):
        """
        Get the dbref string from an object.
        
        Args:
            obj: The object to get dbref from
            
        Returns:
            str: The dbref without leading # or None if obj is None
        """
        if not obj:
            return None
        
        # Get the dbref and remove leading #
        dbref = obj.dbref
        if dbref and dbref.startswith("#"):
            dbref = dbref[1:]
        return dbref

    @property
    def is_active(self):
        """
        Check if combat is currently active.
        
        Returns:
            bool: True if combat logic is running
        """
        return getattr(self.db, DB_COMBAT_RUNNING, False) and super().is_active

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
        # All modifications will be done on this list, then saved back at the end
        # Use deep copy to ensure nested dictionaries are also converted from SaverList
        combatants_list = []
        if getattr(self.db, DB_COMBATANTS, None):
            for entry in getattr(self.db, DB_COMBATANTS):
                # Convert each entry to a regular dict to avoid SaverList issues
                regular_entry = dict(entry)
                combatants_list.append(regular_entry)
        splattercast.msg(f"AT_REPEAT_DEBUG: Converted SaverList to regular list with {len(combatants_list)} entries")

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

        # Check if all combatants are yielding - if so, end combat peacefully
        all_yielding = all(entry.get(DB_IS_YIELDING, False) for entry in combatants_list)
        if all_yielding:
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. All combatants are yielding. Ending combat peacefully.")
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

            # Get combat action for this character
            combat_action = current_char_combat_entry.get("combat_action")
            splattercast.msg(f"AT_REPEAT: {char.key} combat_action: {combat_action}")

            # Process the combat action
            if combat_action == "grapple_initiate":
                self._resolve_grapple_initiate(current_char_combat_entry, combatants_list)
            elif combat_action == "grapple_join":
                self._resolve_grapple_join(current_char_combat_entry, combatants_list)
            elif combat_action == "release_grapple":
                self._resolve_release_grapple(current_char_combat_entry, combatants_list)
            else:
                # Standard attack processing
                target = self.get_target(char)
                if target:
                    self._process_attack(char, target, current_char_combat_entry, combatants_list)
                else:
                    splattercast.msg(f"AT_REPEAT: {char.key} has no valid target for attack.")

            # Clear the combat action after processing
            current_char_combat_entry["combat_action"] = None

        # Save the modified combatants list back to the database
        setattr(self.db, DB_COMBATANTS, combatants_list)

        # Check if combat should continue
        if not getattr(self.db, DB_COMBATANTS, []):
            splattercast.msg(f"AT_REPEAT: No combatants remain in handler {self.key}. Stopping.")
            self.stop_combat_logic()
            return

        self.db.round += 1
        splattercast.msg(f"AT_REPEAT: Handler {self.key}. Round {self.db.round} scheduled for next interval.")
            
            # Diagnostic Log:
            current_target = self.get_target_obj(current_char_combat_entry)
            splattercast.msg(f"AT_REPEAT_DEBUG_TURN_START: For {char.key}'s turn, handler ID {self.id}, current target in entry: {current_target.key if current_target else 'None'}. Full entry: {current_char_combat_entry}")

            splattercast.msg(f"--- Turn: {char.key} (Loc: {char.location.key}, Init: {current_char_combat_entry.get('initiative', 0)}) ---")

            # --- Check for string-based grapple actions first ---
            action = current_char_combat_entry.get("combat_action")

            if isinstance(action, str):
                if action == "grapple_initiate":
                    splattercast.msg(f"AT_REPEAT: {char.key} attempting grapple_initiate.")
                    self._resolve_grapple_initiate(current_char_combat_entry, combatants_list)
                    current_char_combat_entry["combat_action"] = None
                    # Save combatants list before ending turn
                    setattr(self.db, DB_COMBATANTS, combatants_list)
                    continue  # End turn for this combatant

                elif action == "grapple_join":
                    splattercast.msg(f"AT_REPEAT: {char.key} attempting grapple_join.")
                    self._resolve_grapple_join(current_char_combat_entry, combatants_list)
                    current_char_combat_entry["combat_action"] = None
                    # Save combatants list before ending turn
                    setattr(self.db, DB_COMBATANTS, combatants_list)
                    continue  # End turn for this combatant

                elif action == "release_grapple":
                    splattercast.msg(f"AT_REPEAT: {char.key} attempting release_grapple.")
                    self._resolve_release_grapple(current_char_combat_entry, combatants_list)
                    current_char_combat_entry["combat_action"] = None
                    # Save combatants list before ending turn
                    setattr(self.db, DB_COMBATANTS, combatants_list)
                    continue  # End turn for this combatant

            # --- Initialize attack condition flags for this turn ---
            attack_has_disadvantage = False # NEW FLAG

            # --- START-OF-TURN NDB CLEANUP for char (Charge Flags) ---
            if hasattr(char.ndb, "charging_vulnerability_active"):
                splattercast.msg(f"AT_REPEAT_START_TURN_CLEANUP: Clearing charging_vulnerability_active for {char.key} (was active from their own previous charge).")
                delattr(char.ndb, "charging_vulnerability_active")
            
            if hasattr(char.ndb, "charge_attack_bonus_active"): # Bonus from *previous* turn expired if not used
                splattercast.msg(f"AT_REPEAT_START_TURN_CLEANUP: Clearing expired/unused charge_attack_bonus_active for {char.key}.")
                delattr(char.ndb, "charge_attack_bonus_active")

            # --- TURN SKIP CHECK (e.g. from failed charge/flee) ---
            if hasattr(char.ndb, NDB_SKIP_ROUND) and getattr(char.ndb, NDB_SKIP_ROUND):
                char.msg("|yYou are recovering or off-balance and cannot act this turn.|n")
                splattercast.msg(f"AT_REPEAT_SKIP_TURN: {char.key} is skipping turn due to ndb.{NDB_SKIP_ROUND}.")
                delattr(char.ndb, NDB_SKIP_ROUND) # Consume the flag
                # Save combatants list before ending turn
                setattr(self.db, DB_COMBATANTS, combatants_list)
                continue # Skip to next combatant

            # --- CHECK FOR YIELDING ---
            if current_char_combat_entry.get(DB_IS_YIELDING):
                # Exception: Allow release grapple actions even when yielding
                action_intent = current_char_combat_entry.get("combat_action")
                if action_intent and isinstance(action_intent, dict) and action_intent.get("type") == "release_grapple":
                    splattercast.msg(f"{char.key} is yielding but can still release their grapple.")
                else:
                    splattercast.msg(f"{char.key} is yielding and takes no hostile action this turn.")
                    char.location.msg_contents(f"|y{char.key} holds their action, appearing non-hostile.|n", exclude=[char])
                    char.msg("|yYou hold your action, appearing non-hostile.|n")
                    # Save combatants list before ending turn
                    setattr(self.db, DB_COMBATANTS, combatants_list)
                    continue
            
            # --- Handle being grappled (auto resist unless yielding) ---
            # Use the helper method to get the grappler
            grappler = self.get_grappled_by_obj(current_char_combat_entry)
            splattercast.msg(f"GRAPPLE_DEBUG: {char.key} grapple check - grappler={grappler.key if grappler else 'None'}, {DB_GRAPPLED_BY_DBREF}={current_char_combat_entry.get(DB_GRAPPLED_BY_DBREF)}")
            splattercast.msg(f"GRAPPLE_DEBUG_CHAR_DBREF: {char.key} has dbref={char.dbref}")
            
            # Safety check: prevent self-grappling and invalid grappler
            if grappler:
                if grappler == char:
                    splattercast.msg(f"GRAPPLE_ERROR: {char.key} is grappled by themselves! Clearing invalid state.")
                    splattercast.msg(f"GRAPPLE_CLEAR_DEBUG: Clearing {char.key}'s {DB_GRAPPLED_BY_DBREF} due to self-grappling")
                    current_char_combat_entry[DB_GRAPPLED_BY_DBREF] = None
                    grappler = None
                elif not any(e.get(DB_CHAR) == grappler for e in combatants_list):
                    splattercast.msg(f"GRAPPLE_ERROR: {char.key} is grappled by {grappler.key} who is not in combat! Clearing invalid state.")
                    splattercast.msg(f"GRAPPLE_CLEAR_DEBUG: Clearing {char.key}'s {DB_GRAPPLED_BY_DBREF} due to invalid grappler")
                    current_char_combat_entry[DB_GRAPPLED_BY_DBREF] = None
                    grappler = None
            
            if grappler:
                splattercast.msg(f"DEBUG_GRAPPLED_CHECK: {char.key} has grappled_by={grappler.key}")
                try:
                    is_yielding = current_char_combat_entry.get(DB_IS_YIELDING)
                    splattercast.msg(f"DEBUG_YIELDING_CHECK: {char.key} {DB_IS_YIELDING}={is_yielding}")
                    
                    # Check if character is actively yielding (which now also means accepting the grapple)
                    splattercast.msg(f"DEBUG_ESCAPE_CONDITION: {char.key} not {DB_IS_YIELDING} = {not is_yielding}")
                    if not is_yielding:
                        splattercast.msg(f"DEBUG_ENTERING_ESCAPE_BLOCK: {char.key} entering escape attempt block")
                        # Automatically attempt to escape
                        splattercast.msg(f"{char.key} is being grappled by {grappler.key} and automatically attempts to escape.")
                        char.msg(f"|yYou struggle against {grappler.get_display_name(char)}'s grip!|n")
                        
                        # Setup an escape attempt
                        escaper_roll = randint(1, max(1, get_numeric_stat(char, "motorics", 1)))
                        grappler_roll = randint(1, max(1, get_numeric_stat(grappler, "motorics", 1)))
                        splattercast.msg(f"AUTO_ESCAPE_ATTEMPT: {char.key} (roll {escaper_roll}) vs {grappler.key} (roll {grappler_roll}).")

                        if escaper_roll > grappler_roll:
                            # Success - update to use dbrefs
                            splattercast.msg(f"GRAPPLE_CLEAR_DEBUG: {char.key} successfully escaped, clearing grapple state")
                            current_char_combat_entry[DB_GRAPPLED_BY_DBREF] = None
                            grappler_entry = next((e for e in combatants_list if e.get(DB_CHAR) == grappler), None)
                            if grappler_entry:
                                grappler_entry[DB_GRAPPLING_DBREF] = None
                                
                            escape_messages = get_combat_message("grapple", "escape_hit", attacker=char, target=grappler)
                            char.msg(escape_messages.get("attacker_msg", f"You break free from {grappler.get_display_name(char)}'s grasp!"))
                            grappler.msg(escape_messages.get("victim_msg", f"{char.get_display_name(grappler)} breaks free from your grasp!"))
                            obs_msg = escape_messages.get("observer_msg", f"{char.get_display_name(char.location)} breaks free from {grappler.get_display_name(grappler.location)}'s grasp!")
                            for loc in {char.location, grappler.location}: 
                                if loc: loc.msg_contents(obs_msg, exclude=[char, grappler])
                            splattercast.msg(f"AUTO_ESCAPE_SUCCESS: {char.key} escaped from {grappler.key}.")
                        else:
                            # Failure
                            escape_messages = get_combat_message("grapple", "escape_miss", attacker=char, target=grappler)
                            char.msg(escape_messages.get("attacker_msg", f"You struggle but fail to break free from {grappler.get_display_name(char)}'s grasp!"))
                            grappler.msg(escape_messages.get("victim_msg", f"{char.get_display_name(grappler)} struggles but fails to break free from your grasp!"))
                            obs_msg = escape_messages.get("observer_msg", f"{char.get_display_name(char.location)} struggles but fails to break free from {grappler.get_display_name(grappler.location)}'s grasp!")
                            for loc in {char.location, grappler.location}:
                                if loc: loc.msg_contents(obs_msg, exclude=[char, grappler])
                            splattercast.msg(f"AUTO_ESCAPE_FAIL: {char.key} failed to escape {grappler.key}.")
                    else:
                        # Character is yielding, which means accepting the grapple
                        char.msg(f"|cYou remain in {grappler.get_display_name(char)}'s grip without struggling.|n")
                        splattercast.msg(f"{char.key} is accepting being grappled by {grappler.key} and takes no action.")
                    
                    # Either way, turn ends after escape attempt or accepting
                    splattercast.msg(f"DEBUG_CONTINUE_ATTEMPT: {char.key} about to continue (end turn) after grapple handling")
                    # Save combatants list before ending turn
                    setattr(self.db, DB_COMBATANTS, combatants_list)
                    continue
                    
                except Exception as e:
                    splattercast.msg(f"GRAPPLE_HANDLING_ERROR: Exception in grapple handling for {char.key}: {e}")
                    traceback.print_exc()
                    # Fall through to normal combat processing

            # Not grappled or escaped successfully, proceed with normal turn

            # --- Determine Target ---
            target = self.get_target(char)
            if not target:
                char.msg("You have no valid target.")
                splattercast.msg(f"{char.key} has no valid target and takes no action this turn.")
                # Save combatants list before ending turn
                setattr(self.db, DB_COMBATANTS, combatants_list)
                continue

            splattercast.msg(f"{char.key} targets {target.key}.")

            # [REST OF COMBAT LOGIC WOULD GO HERE - attacks, damage, etc.]
            # For now, just log the action
            splattercast.msg(f"COMBAT_ACTION: {char.key} would attack {target.key} (full combat logic to be implemented)")

            # Save combatants list at end of turn
            setattr(self.db, DB_COMBATANTS, combatants_list)

        # Increment round counter
        self.db.round += 1
        
        # Save the final state
        setattr(self.db, DB_COMBATANTS, combatants_list)

    def _process_attack(self, attacker, target, attacker_entry, combatants_list):
        """Process a standard attack between two characters."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Check if attacker is yielding
        if attacker_entry.get(DB_IS_YIELDING, False):
            splattercast.msg(f"AT_REPEAT: {attacker.key} is yielding, skipping attack.")
            return
        
        # Find target's entry
        target_entry = next((e for e in combatants_list if e.get(DB_CHAR) == target), None)
        if not target_entry:
            splattercast.msg(f"AT_REPEAT: Target {target.key} not found in combatants.")
            return
        
        # Get weapon and weapon type
        from world.combat.utils import get_wielded_weapon
        weapon = get_wielded_weapon(attacker)
        weapon_type = getattr(weapon, "db", {}).get("weapon_type", "unarmed") if weapon else "unarmed"
        
        # Calculate attack and defense rolls
        attack_roll = randint(1, 20) + get_numeric_stat(attacker, "motorics", 0)
        defense_roll = randint(1, 20) + get_numeric_stat(target, "motorics", 0)
        
        splattercast.msg(f"ATTACK_ROLL: {attacker.key} rolls {attack_roll} vs {target.key} defense {defense_roll}")
        
        if attack_roll > defense_roll:
            # Hit - calculate damage
            damage = 1 + max(0, get_numeric_stat(attacker, "grit", 1) - 1)
            if weapon:
                damage += getattr(weapon.db, "damage", 0)
            
            # Apply damage
            target_hp = getattr(target, "hp", 10)
            new_hp = max(0, target_hp - damage)
            target.hp = new_hp
            
            # Get and send hit messages
            hit_messages = get_combat_message(weapon_type, "hit", attacker=attacker, target=target, item=weapon, damage=damage)
            attacker.msg(hit_messages.get("attacker_msg", f"You hit {target.key}!"))
            target.msg(hit_messages.get("victim_msg", f"{attacker.key} hits you!"))
            
            # Send observer message to room
            obs_msg = hit_messages.get("observer_msg", f"{attacker.key} hits {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"HIT: {attacker.key} hits {target.key} for {damage} damage. {target.key} HP: {new_hp}")
            
            # Check for death
            if new_hp <= 0:
                self._handle_death(target, attacker, weapon_type, weapon)
                
        else:
            # Miss
            miss_messages = get_combat_message(weapon_type, "miss", attacker=attacker, target=target, item=weapon)
            attacker.msg(miss_messages.get("attacker_msg", f"You miss {target.key}!"))
            target.msg(miss_messages.get("victim_msg", f"{attacker.key} misses you!"))
            
            obs_msg = miss_messages.get("observer_msg", f"{attacker.key} misses {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"MISS: {attacker.key} misses {target.key}")
    
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
            # Try to advance into proximity
            from world.combat.proximity import proximity_opposed_roll
            advance_success = proximity_opposed_roll(attacker, target)
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
            
            grapple_messages = get_combat_message("grapple", "initiate", attacker=attacker, target=target)
            attacker.msg(grapple_messages.get("attacker_msg", f"You grapple {target.key}!"))
            target.msg(grapple_messages.get("victim_msg", f"{attacker.key} grapples you!"))
            
            obs_msg = grapple_messages.get("observer_msg", f"{attacker.key} grapples {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"GRAPPLE_SUCCESS: {attacker.key} grapples {target.key}")
        else:
            # Failed grapple - target gets bonus attack
            fail_messages = get_combat_message("grapple", "fail", attacker=attacker, target=target)
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
            # Try to advance into proximity
            from world.combat.proximity import proximity_opposed_roll
            advance_success = proximity_opposed_roll(attacker, target)
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
            
            grapple_messages = get_combat_message("grapple", "join", attacker=attacker, target=target)
            attacker.msg(grapple_messages.get("attacker_msg", f"You grapple {target.key}!"))
            target.msg(grapple_messages.get("victim_msg", f"{attacker.key} grapples you!"))
            
            obs_msg = grapple_messages.get("observer_msg", f"{attacker.key} grapples {target.key}!")
            attacker.location.msg_contents(obs_msg, exclude=[attacker, target])
            
            splattercast.msg(f"GRAPPLE_SUCCESS: {attacker.key} grapples {target.key}")
        else:
            # Failed grapple - target gets bonus attack
            fail_messages = get_combat_message("grapple", "fail", attacker=attacker, target=target)
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
