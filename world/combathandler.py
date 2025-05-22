from evennia import DefaultScript, create_script
from random import randint
from evennia.utils.utils import delay
from world.combat_messages import get_combat_message
from evennia.comms.models import ChannelDB

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    splattercast = ChannelDB.objects.get_channel("Splattercast")
    
    # First, check if 'location' is already managed by ANY active CombatHandler
    # This requires iterating through all scripts, which can be slow.
    # A better way might be a global list of active combat handlers, but for now:
    from evennia.scripts.models import ScriptDB
    active_handlers = ScriptDB.objects.filter(db_key=COMBAT_SCRIPT_KEY, db_is_active=True)

    for handler_script in active_handlers:
        # Ensure it's our CombatHandler type and has managed_rooms
        if hasattr(handler_script, "db") and hasattr(handler_script.db, "managed_rooms"):
            if location in handler_script.db.managed_rooms:
                splattercast.msg(f"GET_COMB: Location {location.key} is already managed by active handler {handler_script.key} (on {handler_script.obj.key}). Returning it.")
                return handler_script
    
    # If not managed by an existing handler, check for an inactive one on THIS location
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            # Found a handler on this specific location
            if script.is_active: # Should have been caught by the loop above if it managed this location
                splattercast.msg(f"GET_COMB: Found active handler {script.key} directly on {location.key} (missed by global check or manages only self). Returning it.")
                # Ensure it knows it manages this location
                if hasattr(script.db, "managed_rooms") and location not in script.db.managed_rooms:
                    script.db.managed_rooms.append(location) # Should already be there if self.obj
                return script
            else:
                splattercast.msg(f"GET_COMB: Found inactive handler {script.key} on {location.key}. Stopping and deleting it.")
                script.stop() # Ensure it's fully stopped
                script.delete()
                break # Only one handler script per location by key

    # If no suitable handler found, create a new one on this location
    new_script = create_script(
        "world.combathandler.CombatHandler",
        key=COMBAT_SCRIPT_KEY,
        obj=location, # New handler is "hosted" by this location
        persistent=True,
    )
    splattercast.msg(f"GET_COMB: Created new CombatHandler {new_script.key} on {location.key}.")
    return new_script

class CombatHandler(DefaultScript):
    """
    Script that manages turn-based combat for all combatants in a location.
    Handles initiative, targeting, combat rounds, and cleanup.
    """

    def at_script_creation(self):
        """
        Initialize combat handler script attributes.
        """
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6
        self.persistent = True
        self.db.combatants = []
        self.db.round = 0
        self.db.managed_rooms = [self.obj]  # Initially manages only its host room
        self.db.combat_is_running = False  # <<< ADD THIS
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"CH_CREATE: New handler {self.key} created on {self.obj.key}, initially managing: {[r.key for r in self.db.managed_rooms]}. Combat logic initially not running.")

    def start(self):
        """
        Start the combat handler's repeat timer if combat logic isn't already running
        or if the Evennia ticker isn't active.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        # Use super().is_active to check Evennia's ticker status
        evennia_ticker_is_active = super().is_active

        if self.db.combat_is_running and evennia_ticker_is_active:
            splattercast.msg(f"CH_START: Handler {self.key} on {self.obj.key} - combat logic and Evennia ticker are already active. Skipping redundant start.")
            return

        splattercast.msg(f"CH_START: Handler {self.key} on {self.obj.key} (managing {[r.key for r in self.db.managed_rooms]}) - ensuring combat logic is running and ticker is scheduled.")
        
        if not self.db.combat_is_running:
            splattercast.msg(f"CH_START_DETAIL: Setting self.db.combat_is_running = True for {self.key}.")
            self.db.combat_is_running = True
        
        if not evennia_ticker_is_active:
            splattercast.msg(f"CH_START_DETAIL: Evennia ticker for {self.key} is not active (super().is_active=False). Calling force_repeat().")
            self.force_repeat()
        else:
            # This case implies:
            # 1. self.db.combat_is_running was False (now True) AND evennia_ticker_is_active was True.
            #    (Our flag was out of sync with a running ticker - now corrected)
            # OR
            # 2. self.db.combat_is_running was True AND evennia_ticker_is_active was True.
            #    (This case is caught by the initial check and return, so shouldn't be common here unless logic changes)
            splattercast.msg(f"CH_START_DETAIL: self.db.combat_is_running is now True. Evennia ticker for {self.key} was already active. State synchronized.")
            
        # For debugging, log the final states
        splattercast.msg(f"CH_START_COMPLETE: Handler {self.key} - self.db.combat_is_running: {self.db.combat_is_running}, super().is_active after updates: {super().is_active}")

    def stop_combat_logic(self, cleanup_combatants=True):
        """Stops the combat rounds and optionally cleans up combatants."""
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} stopping combat rounds. Initial state - combat_is_running: {self.db.combat_is_running}, Evennia ticker active (super().is_active): {super().is_active}")
        
        # Check if the ticker was effectively running for our combat logic *before* we change flags
        ticker_was_active_for_combat = self.db.combat_is_running and super().is_active
        
        self.db.combat_is_running = False # Mark our combat logic as stopped

        if cleanup_combatants:
            splattercast.msg(f"STOP_COMBAT_LOGIC: Cleaning up combatants for handler {self.key}.")
            for entry in list(self.db.combatants): # Iterate copy
                char = entry["char"]
                if hasattr(char, "ndb") and char.ndb.combat_handler == self:
                    del char.ndb.combat_handler
            self.db.combatants = [] # Clear the list
            self.db.round = 0
            splattercast.msg(f"STOP_COMBAT_LOGIC: Combatants list cleared for handler {self.key}.")
        
        should_delete_script = False
        # Condition for deleting the script entirely
        if not self.db.combatants and len(self.db.managed_rooms) <=1 and self.obj in self.db.managed_rooms:
             if self.pk: # Check if script is saved (i.e., not already deleted)
                splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} is empty and only managing its host room ({self.obj.key}). Marking for deletion.")
                should_delete_script = True
        
        if not self.db.combatants and not should_delete_script:
            splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} has no combatants. Rounds stopped. Still managing rooms: {[r.key for r in self.db.managed_rooms]}.")

        if should_delete_script:
            splattercast.msg(f"STOP_COMBAT_LOGIC: Deleting handler script {self.key}.")
            self.delete() # This will call at_stop() and Evennia's underlying stop mechanism which includes unrepeat.
        elif ticker_was_active_for_combat:
            # If not deleting, but our combat logic was using an active ticker, explicitly stop the ticker.
            splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} is not being deleted. Combat was running with active ticker. Explicitly calling unrepeat().")
            self.unrepeat()
        else:
            # Not deleting, and ticker wasn't active for our combat (or combat wasn't running).
            splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} is not being deleted. Ticker was not active for combat or combat was not running. No explicit unrepeat() needed from here.")

    def at_stop(self):
        """
        Clean up when combat ends or script is stopped.
        This method is called by Evennia when script.stop() is used.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"AT_STOP (Evennia): Handler {self.key} on {self.obj.key} is being stopped by Evennia. Ensuring combat logic is marked as not running.")
        self.db.combat_is_running = False

    def enroll_room(self, room_to_add):
        """Adds a room to this handler's managed_rooms if not already present."""
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if room_to_add not in self.db.managed_rooms:
            self.db.managed_rooms.append(room_to_add)
            splattercast.msg(f"CH_ENROLL: Handler {self.key} (on {self.obj.key}) enrolled room {room_to_add.key}. Now managing: {[r.key for r in self.db.managed_rooms]}.")
        else:
            splattercast.msg(f"CH_ENROLL: Handler {self.key} (on {self.obj.key}) attempted to enroll {room_to_add.key}, but it's already managed.")

    def merge_handler(self, other_handler):
        """Merges another handler's rooms and combatants into this one."""
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"CH_MERGE: Handler {self.key} (on {self.obj.key}) is merging handler {other_handler.key} (on {other_handler.obj.key}).")

        for room in other_handler.db.managed_rooms:
            self.enroll_room(room)  # Use enroll_room to add them

        for combatant_entry in list(other_handler.db.combatants):  # Iterate copy
            char = combatant_entry["char"]
            if not any(e["char"] == char for e in self.db.combatants):
                self.db.combatants.append(combatant_entry)  # Add the whole entry
                char.ndb.combat_handler = self  # CRITICAL: Update NDB pointer
                splattercast.msg(f"CH_MERGE: Migrated {char.key} from handler {other_handler.key} to {self.key}. NDB updated.")
            else:
                splattercast.msg(f"CH_MERGE: {char.key} was already in handler {self.key} during merge with {other_handler.key}. Skipping duplicate add.")

        splattercast.msg(f"CH_MERGE: Stopping and deleting other handler {other_handler.key}.")
        other_handler.is_active = False  # Prevent further at_repeats
        for entry in list(other_handler.db.combatants):
            if hasattr(entry["char"], "ndb") and entry["char"].ndb.combat_handler == other_handler:
                del entry["char"].ndb.combat_handler
        other_handler.db.combatants = []  # Clear its list
        other_handler.delete()

        splattercast.msg(f"CH_MERGE: Merge complete. Handler {self.key} now manages: {[r.key for r in self.db.managed_rooms]} with {len(self.db.combatants)} combatants.")
        if not self.db.combat_is_running and len(self.db.combatants) > 0: # Use your custom flag
            self.start()

    def add_combatant(self, char, target=None, initial_grappling=None, initial_grappled_by=None, initial_is_yielding=False):
        """
        Add a character to combat, assigning initiative and an optional target.
        Logs if joining an already-running combat.
        Initializes grapple status and combat_action.
        Can accept initial grapple/yielding states.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if char.location not in self.db.managed_rooms:
            splattercast.msg(f"ADD_COMB: {char.key} is in {char.location.key}, which is not yet managed by handler {self.key} (on {self.obj.key}). Enrolling room.")
            self.enroll_room(char.location)

        if any(entry["char"] == char for entry in self.db.combatants):
            splattercast.msg(f"ADD_COMB: {char.key} already in combatants list. Assuming update or re-add. Verifying combat state.")
            # Even if re-adding, ensure combat starts/restarts if necessary
            if len(self.db.combatants) > 0: # Should always be true if they are in the list
                 self.start()
            return

        initiative = randint(1, max(1, char.db.motorics or 1))
        self.db.combatants.append({
            "char": char,
            "initiative": initiative,
            "target": target,
            "grappling": initial_grappling,
            "grappled_by": initial_grappled_by,
            "combat_action": None, 
            "is_yielding": initial_is_yielding,
        })
        char.ndb.combat_handler = self
        splattercast.msg(f"{char.key} joins combat (handler {self.key}) with initiative {initiative} (Yielding: {initial_is_yielding}, Grappling: {initial_grappling.key if initial_grappling else 'None'}).")
        splattercast.msg(f"{char.key} added to combat (handler {self.key}). Total combatants: {len(self.db.combatants)}.")
        
        if self.db.round == 0: # This is just a status message
            splattercast.msg(f"Combat (handler {self.key}) is in setup phase (round 0).")

        # If there are any combatants, ensure the combat handler's logic and ticker are started.
        if len(self.db.combatants) > 0:
            splattercast.msg(f"ADD_COMB: Combatants present in handler {self.key}. Calling start() to ensure combat is active.")
            self.start()

    def remove_combatant(self, char):
        """
        Remove a character from combat and clean up their handler reference.
        If only one or zero combatants remain, end combat.
        Also handles releasing any grapples involving this character.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"RMV_COMB: Attempted to remove {char.key} from handler {self.key}...")

        if not self.pk or not self.db or not hasattr(self.db, 'combatants') or self.db.combatants is None:
            splattercast.msg(f"RMV_COMB: Attempted to remove {char.key} from handler {self.key}, but handler/combatants list is gone (handler likely already deleted/stopped).")
            if hasattr(char, "ndb") and char.ndb.combat_handler == self:
                splattercast.msg(f"RMV_COMB: Cleaning ndb.combat_handler for {char.key} as a fallback for defunct handler {self.key}.")
                del char.ndb.combat_handler
            return

        char_combat_entry = next((e for e in self.db.combatants if e["char"] == char), None)
        if char_combat_entry and char_combat_entry.get("grappling"):
            grappled_victim = char_combat_entry["grappling"]
            victim_entry = next((e for e in self.db.combatants if e["char"] == grappled_victim), None)
            if victim_entry:
                victim_entry["grappled_by"] = None
                splattercast.msg(f"{char.key} was grappling {grappled_victim.key}. {grappled_victim.key} is now free.")

        for entry in self.db.combatants:
            if entry.get("grappling") == char:
                entry["grappling"] = None
                splattercast.msg(f"{entry['char'].key} was grappling {char.key} (now removed). {entry['char'].key} is no longer grappling.")
            if entry.get("char") == char and entry.get("grappled_by"):
                grappler = entry["grappled_by"]
                grappler_entry = next((e for e in self.db.combatants if e["char"] == grappler), None)
                if grappler_entry:
                    grappler_entry["grappling"] = None

        self.db.combatants = [entry for entry in self.db.combatants if entry["char"] != char]
        if char.ndb.combat_handler:
            del char.ndb.combat_handler
        splattercast.msg(f"{char.key} removed from combat.")
        if len(self.db.combatants) == 0:
            splattercast.msg(f"RMV_COMB: No combatants remain in handler {self.key}. Stopping.")
            self.stop_combat_logic()

    def get_target(self, char):
        """
        Determine the current valid target for a combatant.
        If their target is invalid, retargets or removes them from combat.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        entry = next((e for e in self.db.combatants if e["char"] == char), None)
        if not entry:
            splattercast.msg(f"No combat entry found for {char.key}.")
            return None
        target = entry.get("target")
        valid_chars = [e["char"] for e in self.db.combatants]
        if not target or target not in valid_chars:
            splattercast.msg(
                f"{char.key} has no valid target or their target is not in combat."
            )
            attackers = [
                e["char"] for e in self.db.combatants 
                if e.get("target") == char and e["char"] != char
            ]
            splattercast.msg(f"Attackers targeting {char.key}: {[a.key for a in attackers]}.")

            if not attackers:
                splattercast.msg(f"{char.key} has no offensive target and is not being targeted by anyone for an attack. Potential for disengagement.")
                return None
            else:
                target = attackers[0]
        else:
            splattercast.msg(
                f"{char.key} keeps current target {target.key}."
            )
        return target

    def set_target(self, char, target):
        """
        Set a new target for a combatant.
        """
        for entry in self.db.combatants:
            if entry["char"] == char:
                entry["target"] = target

    def get_initiative_order(self):
        """
        Return combatants sorted by initiative, highest first.
        """
        return sorted(self.db.combatants, key=lambda e: e["initiative"], reverse=True)

    def at_repeat(self):
        """
        Main combat loop, processes each combatant's turn in initiative order.
        Handles attacks, misses, deaths, and round progression across managed rooms.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if not self.db.combat_is_running: # Check your custom flag FIRST
            splattercast.msg(f"AT_REPEAT: Handler {self.key} on {self.obj.key} combat logic is not running (self.db.combat_is_running=False). Returning.")
            return

        # Optional: Also check Evennia's underlying script active state for robustness
        if not super().is_active: # Or self.is_active if not overridden
             splattercast.msg(f"AT_REPEAT: Handler {self.key} on {self.obj.key} Evennia script.is_active=False. Marking combat_is_running=False and returning.")
             self.db.combat_is_running = False # Sync our flag
             return

        # Prune combatants: Ensure they exist and are in a managed room.
        valid_combatants_entries = []
        for entry in list(self.db.combatants): # Iterate a copy for safe removal
            char = entry.get("char")
            if not char: # Character object is gone
                splattercast.msg(f"AT_REPEAT: Pruning missing character from handler {self.key}.")
                continue # Skip this entry
            if not char.location: # Character has no location (e.g., destroyed, in limbo)
                splattercast.msg(f"AT_REPEAT: Pruning {char.key} (no location) from handler {self.key}.")
                if hasattr(char, "ndb") and char.ndb.combat_handler == self:
                    del char.ndb.combat_handler
                continue
            if char.location not in self.db.managed_rooms:
                splattercast.msg(f"AT_REPEAT: Pruning {char.key} (in unmanaged room {char.location.key}) from handler {self.key}.")
                if hasattr(char, "ndb") and char.ndb.combat_handler == self:
                    del char.ndb.combat_handler # Clean NDB if they left the zone
                continue
            valid_combatants_entries.append(entry)
        
        self.db.combatants = valid_combatants_entries

        if not self.db.combatants:
            splattercast.msg(f"AT_REPEAT: No valid combatants remain in managed rooms for handler {self.key}. Stopping.")
            self.stop_combat_logic()
            return

        if self.db.round == 0:
            if len(self.db.combatants) > 0: # Any combatant can start the round
                splattercast.msg(f"AT_REPEAT: Handler {self.key}. Combatants present. Starting combat in round 1.")
                self.db.round = 1
            else:
                # This case should be rare due to the check above, but good for safety
                splattercast.msg(f"AT_REPEAT: Handler {self.key}. Waiting for combatants to join...")
                return

        splattercast.msg(f"AT_REPEAT: Handler {self.key} (managing {[r.key for r in self.db.managed_rooms]}). Round {self.db.round} begins.")
        
        # Check if combat should end due to too few participants
        # Consider only active, non-yielding combatants for "active participants" count if desired
        if len(self.db.combatants) <= 1: # If only one or zero combatants are left
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. Not enough combatants ({len(self.db.combatants)}) to continue. Ending combat.")
            self.stop_combat_logic()
            return

        for combat_entry in list(self.get_initiative_order()): # Iterate copy in case of mid-turn removals
            char = combat_entry.get("char")

            # Re-validate char and their presence in self.db.combatants, as they might have been removed by a previous turn's action
            if not char or not any(e["char"] == char for e in self.db.combatants):
                splattercast.msg(f"AT_REPEAT: Skipping turn for {char.key if char else 'UnknownChar'} as they are no longer in combat list.")
                continue
            
            # Ensure char is still in a managed room (could have been moved by a non-combat effect mid-round)
            if not char.location or char.location not in self.db.managed_rooms:
                splattercast.msg(f"AT_REPEAT: {char.key} moved out of managed zone mid-round to {char.location.key if char.location else 'None'}. Removing.")
                self.remove_combatant(char) # This will also clean NDB
                continue

            current_char_combat_entry = next((e for e in self.db.combatants if e["char"] == char), None)
            if not current_char_combat_entry: # Should be redundant due to above check, but safety first
                splattercast.msg(f"Error: Could not find combat entry for {char.key} mid-turn (second check).")
                continue

            splattercast.msg(f"--- Turn: {char.key} (Loc: {char.location.key}, Init: {current_char_combat_entry['initiative']}) ---")

            action_intent = current_char_combat_entry.get("combat_action")
            if action_intent:
                splattercast.msg(f"AT_REPEAT: {char.key} has action_intent: {action_intent}")
                current_char_combat_entry["combat_action"] = None # Consume the intent

            # --- Handle Grapple States and Grapple-Related Actions ---
            # (This extensive grapple logic from your provided code seems mostly self-contained for messaging to char.location)
            # Ensure any msg_contents calls are to char.location or target.location as appropriate.
            # ... (Your existing grapple, escape, release grapple logic) ...
            # Example adjustment for a message within grapple logic:
            # msg = f"{char.key} automatically breaks free from {grappler.key}'s grapple!"
            # char.location.msg_contents(f"|G{msg}|n") # This is good, it's local to the event

            # --- Handle Yielding ---
            if current_char_combat_entry.get("is_yielding"):
                # Check if they were grappled and escaped, if so, they might not be yielding anymore
                # For now, if they are yielding at this point, they do nothing offensively.
                splattercast.msg(f"{char.key} is yielding and takes no hostile action this turn.")
                char.location.msg_contents(f"|y{char.key} holds their action, appearing non-hostile.|n", exclude=[char])
                char.msg("|yYou hold your action, appearing non-hostile.|n")
                continue # Skip to next combatant

            # --- Determine Target for Standard Attack ---
            target = None
            if current_char_combat_entry.get("grappling"): # If grappling, default target is the one grappled
                target = current_char_combat_entry["grappling"]
                # Validate grappled target is still in combat
                if not any(e["char"] == target for e in self.db.combatants):
                    splattercast.msg(f"{char.key} was grappling {target.key if target else 'Unknown'}, but they are no longer in combat. Clearing grapple.")
                    current_char_combat_entry["grappling"] = None
                    target = None # No longer a valid target
                else:
                     splattercast.msg(f"{char.key} is grappling {target.key}, and defaults to attacking them this turn.")
            
            if not target: # If not grappling or grappled target invalid, get general target
                target = self.get_target(char)

            if not target:
                # Check if still in an active grapple (e.g. being grappled) even if no offensive target
                is_in_active_grapple = current_char_combat_entry.get("grappled_by") and \
                                       any(e["char"] == current_char_combat_entry.get("grappled_by") for e in self.db.combatants)
                if not is_in_active_grapple:
                    splattercast.msg(f"{char.key} has no offensive target and is not in an active grapple. Removing from combat.")
                    self.remove_combatant(char)
                else:
                    splattercast.msg(f"{char.key} has no offensive target but is being grappled. Turn passes for offensive action.")
                continue # Skip to next combatant

            # --- Validate Target Location and Reachability for Attack ---
            can_attack_target = False
            if char.location == target.location:
                can_attack_target = True
                splattercast.msg(f"AT_REPEAT: {char.key} attacking {target.key} in same room: {char.location.key}.")
            elif target.location in self.db.managed_rooms:
                # Check for direct connection via an exit for inter-room attack
                is_adjacent = any(ex.destination == target.location for ex in char.location.exits)
                if is_adjacent:
                    can_attack_target = True
                    splattercast.msg(f"AT_REPEAT: {char.key} (in {char.location.key}) attacking {target.key} (in {target.location.key}) - rooms are adjacent and managed.")
                else:
                    char.msg(f"You can't reach {target.key} in {target.location.key} from here; they are not in an adjacent part of the combat zone.")
                    splattercast.msg(f"AT_REPEAT: {char.key} cannot attack {target.key}, rooms {char.location.key} and {target.location.key} not adjacent.")
            else:
                # Target is in a room not managed by this combat (should be rare if get_target is robust and pruning works)
                char.msg(f"{target.key} is not in the current combat zone.")
                splattercast.msg(f"AT_REPEAT: {char.key}'s target {target.key} is in {target.location.key}, which is not managed by {self.key}.")

            if not can_attack_target:
                # If cannot attack, clear their current target to avoid repeated failed attempts if target doesn't move
                current_char_combat_entry["target"] = None 
                splattercast.msg(f"AT_REPEAT: {char.key} could not attack target {target.key}. Target cleared for next round decision.")
                continue # Skip to next combatant's turn

            # --- Resolve Attack ---
            atk_roll = randint(1, max(1, getattr(char, "grit", 1)))
            def_roll = randint(1, max(1, getattr(target, "motorics", 1)))
            
            hands = getattr(char, "hands", {})
            weapon = next((item for hand, item in hands.items() if item), None)
            weapon_type = "unarmed"
            if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type:
                weapon_type = str(weapon.db.weapon_type).lower()

            grappling_this_target = current_char_combat_entry.get("grappling") == target
            effective_message_weapon_type = "grapple" if grappling_this_target else weapon_type

            splattercast.msg(f"{char.key} (using {effective_message_weapon_type}) attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")

            if atk_roll > def_roll:
                damage = getattr(char, "grit", 1) or 1
                actual_damage_recipient = target # Default
                
                # --- Body Shield Logic (ensure messages are room-aware) ---
                target_combat_entry = next((e for e in self.db.combatants if e["char"] == target), None)
                if target_combat_entry and target_combat_entry.get("grappling"):
                    shield_char = target_combat_entry.get("grappling")
                    # Ensure shield_char is a valid combatant and in a managed room
                    shield_char_entry = next((e for e in self.db.combatants if e["char"] == shield_char), None)

                    if shield_char_entry and shield_char.location in self.db.managed_rooms: 
                        splattercast.msg(f"BODY SHIELD CHECK: {target.key} is grappling {shield_char.key}. Performing body shield roll.")
                        
                        # --- THIS IS THE FIX: DEFINE THE ROLLS HERE ---
                        target_motorics = getattr(target, "motorics", 1)  # Or relevant stat for positioning
                        shield_char_motorics = getattr(shield_char, "motorics", 1) # Or relevant stat for evading
                        
                        target_positioning_roll = randint(1, max(1, target_motorics))
                        shield_evasion_roll = randint(1, max(1, shield_char_motorics))
                        # --- END OF THE FIX ---

                        splattercast.msg(f"BODY SHIELD ROLL: {target.key} (target trying to use shield) rolls {target_positioning_roll} vs {shield_char.key} (shield trying to evade) rolls {shield_evasion_roll} (motorics).")

                        if target_positioning_roll > shield_evasion_roll: 
                            actual_damage_recipient = shield_char
                            # Room-aware messages for body shield:
                            msg_shield_event = f"|c{target.key} yanks {shield_char.key} in the way! {shield_char.key} takes the hit!|n"
                            target.location.msg_contents(msg_shield_event, exclude=[target, shield_char]) # Announce in target's original room
                            if shield_char.location != target.location: 
                                shield_char.location.msg_contents(msg_shield_event, exclude=[target, shield_char])
                            splattercast.msg(f"BODY SHIELD SUCCESS: {target.key} uses {shield_char.key}. {shield_char.key} takes hit.")
                        else:
                            msg_shield_fail = f"|y{target.key} tries to use {shield_char.key} as a shield but fails!|n"
                            target.location.msg_contents(msg_shield_fail, exclude=[target, shield_char])
                            splattercast.msg(f"BODY SHIELD FAIL: {target.key} fails to use {shield_char.key}.")
                # --- End Body Shield ---

                hit_msg_observer = get_combat_message(
                    effective_message_weapon_type, "hit", 
                    attacker=char, target=actual_damage_recipient, item=weapon, damage=damage
                )
                splattercast.msg(f"get_combat_message (hit observer) returned: {hit_msg_observer!r}")

                # Send to attacker's room
                char.location.msg_contents(f"|R{hit_msg_observer}|n", exclude=[char, actual_damage_recipient])
                # Send to recipient's room if different from attacker's
                if actual_damage_recipient.location != char.location:
                    actual_damage_recipient.location.msg_contents(f"|R{hit_msg_observer}|n", exclude=[char, actual_damage_recipient])

                # Direct messages
                char.msg(f"|gYour attack hits {actual_damage_recipient.key}!|n")
                actual_damage_recipient.msg(f"|r{char.key}'s attack hits you!|n")
                
                splattercast.msg(f"{char.key}'s attack damages {actual_damage_recipient.key} for {damage}.")
                if hasattr(actual_damage_recipient, "take_damage"):
                    actual_damage_recipient.take_damage(damage)
                
                if hasattr(actual_damage_recipient, "is_dead") and actual_damage_recipient.is_dead():
                    kill_msg_observer = get_combat_message(
                        effective_message_weapon_type, "kill",
                        attacker=char, target=actual_damage_recipient, item=weapon, damage=damage
                    )
                    splattercast.msg(f"get_combat_message (kill observer) returned: {kill_msg_observer!r}")

                    # Send to attacker's room
                    char.location.msg_contents(f"|R{kill_msg_observer}|n", exclude=[char, actual_damage_recipient])
                    # Send to recipient's room if different
                    if actual_damage_recipient.location != char.location:
                        actual_damage_recipient.location.msg_contents(f"|R{kill_msg_observer}|n", exclude=[char, actual_damage_recipient])
                    
                    char.msg(f"|gYou have slain {actual_damage_recipient.key}!|n")
                    # Target's death message usually handled by their own death system/take_damage

                    splattercast.msg(f"{actual_damage_recipient.key} has been defeated.")
                    self.remove_combatant(actual_damage_recipient) # This also clears NDB
                    
                    # Retarget anyone who was targeting the slain combatant
                    for entry in list(self.db.combatants):
                        if entry.get("target") == actual_damage_recipient:
                            entry["target"] = self.get_target(entry["char"]) # Get new target
                            splattercast.msg(f"{entry['char'].key} was targeting slain {actual_damage_recipient.key}, now targets {entry['target'].key if entry['target'] else 'None'}.")
                    continue # Attacker's turn ends if they killed someone
            else: # Attack missed
                miss_msg_observer = get_combat_message(
                    effective_message_weapon_type, "miss", 
                    attacker=char, target=target, item=weapon # Original target for miss message
                )
                splattercast.msg(f"get_combat_message (miss observer) returned: {miss_msg_observer!r}")

                # Send to attacker's room
                char.location.msg_contents(f"|[X{miss_msg_observer}|n", exclude=[char, target])
                # Send to original target's room if different
                if target.location != char.location:
                    target.location.msg_contents(f"|[X{miss_msg_observer}|n", exclude=[char, target])
                
                char.msg(f"|yYour attack on {target.key} misses.|n")
                target.msg(f"|g{char.key}'s attack on you misses.|n")

        # --- End of Round ---
        if not self.db.combatants: # Check if all combatants were removed during the round
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. No combatants left after round processing. Stopping.")
            self.stop_combat_logic()
            return

        self.db.round += 1
        splattercast.msg(f"AT_REPEAT: Handler {self.key}. Round {self.db.round} scheduled for next interval.")
