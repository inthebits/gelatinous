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
        # New condition: Delete if no combatants and script is persistent (saved in DB)
        if not self.db.combatants and self.pk:
            splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} is empty and persistent. Marking for deletion.")
            should_delete_script = True
        
        if not self.db.combatants and not should_delete_script:
            # This log will now only appear if self.pk is False (e.g., script not yet saved, which is rare for persistent scripts)
            # or if some other logic prevents deletion.
            managed_room_keys = [f"{r.key}(#{r.id})" for r in self.db.managed_rooms if r and hasattr(r, 'id')]
            splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} has no combatants but is not being deleted (e.g. not persistent or other logic). Rounds stopped. Still managing rooms: {managed_room_keys}.")

        if should_delete_script:
            splattercast.msg(f"STOP_COMBAT_LOGIC: Deleting handler script {self.key}.")
            self.delete() # This will call at_stop() and Evennia's underlying stop mechanism.
        else:
            # If not deleting, but combat logic is stopping, we should stop the script's ticker
            # and mark it as inactive. self.stop() handles this.
            splattercast.msg(f"STOP_COMBAT_LOGIC: Handler {self.key} is not being deleted. Calling self.stop() to halt ticker and mark script inactive.")
            self.stop() # This calls self.unrepeat() and sets self.db_is_active = False.
            # self.at_stop() will be called by self.stop() if not already stopped.
            # Our at_stop() also sets self.db.combat_is_running = False.

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
        Initializes grapple status, combat_action, and proximity NDB.
        Can accept initial grapple/yielding states.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if char.location not in self.db.managed_rooms:
            splattercast.msg(f"ADD_COMB: {char.key} is in {char.location.key}, which is not yet managed by handler {self.key} (on {self.obj.key}). Enrolling room.")
            self.enroll_room(char.location)

        # Initialize proximity NDB if it doesn't exist or is not a set
        if not hasattr(char.ndb, "in_proximity_with") or not isinstance(char.ndb.in_proximity_with, set):
            char.ndb.in_proximity_with = set()
            splattercast.msg(f"ADD_COMB: Initialized char.ndb.in_proximity_with as a new set for {char.key}.")

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
        Also handles releasing any grapples involving this character and clears proximity.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"RMV_COMB: Attempted to remove {char.key} from handler {self.key}...")

        if not self.pk or not self.db or not hasattr(self.db, 'combatants') or self.db.combatants is None:
            splattercast.msg(f"RMV_COMB: Attempted to remove {char.key} from handler {self.key}, but handler/combatants list is gone (handler likely already deleted/stopped).")
            if hasattr(char, "ndb") and hasattr(char.ndb, "combat_handler") and char.ndb.combat_handler == self:
                splattercast.msg(f"RMV_COMB: Cleaning ndb.combat_handler for {char.key} as a fallback for defunct handler {self.key}.")
                del char.ndb.combat_handler
            # Fallback proximity cleanup if handler is gone
            if hasattr(char.ndb, "in_proximity_with") and isinstance(char.ndb.in_proximity_with, set):
                splattercast.msg(f"RMV_COMB_FALLBACK: Cleaning proximity for {char.key} (defunct handler). Was with: {[o.key for o in char.ndb.in_proximity_with]}.")
                for other_char in list(char.ndb.in_proximity_with): # Iterate a copy
                    if hasattr(other_char.ndb, "in_proximity_with") and isinstance(other_char.ndb.in_proximity_with, set):
                        other_char.ndb.in_proximity_with.discard(char)
                char.ndb.in_proximity_with.clear()
            return

        # --- Proximity Cleanup ---
        if hasattr(char.ndb, "in_proximity_with") and isinstance(char.ndb.in_proximity_with, set):
            splattercast.msg(f"RMV_COMB: Clearing proximity for {char.key}. They were in proximity with: {[o.key for o in char.ndb.in_proximity_with]}.")
            for other_char in list(char.ndb.in_proximity_with): # Iterate a copy
                if hasattr(other_char.ndb, "in_proximity_with") and isinstance(other_char.ndb.in_proximity_with, set):
                    other_char.ndb.in_proximity_with.discard(char)
                    splattercast.msg(f"RMV_COMB: Removed {char.key} from {other_char.key}'s proximity list.")
            char.ndb.in_proximity_with.clear()
        # Optionally: if you want to remove the attribute entirely when not in combat:
        # if hasattr(char.ndb, "in_proximity_with"):
        #     del char.ndb.in_proximity_with
        #     splattercast.msg(f"RMV_COMB: Deleted char.ndb.in_proximity_with for {char.key}.")

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
        if hasattr(char.ndb, "combat_handler") and char.ndb.combat_handler == self: # Check if attribute exists before deleting
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
        if not self.db.combat_is_running:
            splattercast.msg(f"AT_REPEAT: Handler {self.key} on {self.obj.key} combat logic is not running (self.db.combat_is_running=False). Returning.")
            return

        if not super().is_active:
             splattercast.msg(f"AT_REPEAT: Handler {self.key} on {self.obj.key} Evennia script.is_active=False. Marking combat_is_running=False and returning.")
             self.db.combat_is_running = False
             return

        valid_combatants_entries = []
        for entry in list(self.db.combatants):
            char = entry.get("char")
            if not char:
                splattercast.msg(f"AT_REPEAT: Pruning missing character from handler {self.key}.")
                continue
            if not char.location:
                splattercast.msg(f"AT_REPEAT: Pruning {char.key} (no location) from handler {self.key}.")
                if hasattr(char, "ndb") and char.ndb.combat_handler == self:
                    del char.ndb.combat_handler
                continue
            if char.location not in self.db.managed_rooms:
                splattercast.msg(f"AT_REPEAT: Pruning {char.key} (in unmanaged room {char.location.key}) from handler {self.key}.")
                if hasattr(char, "ndb") and char.ndb.combat_handler == self:
                    del char.ndb.combat_handler
                continue
            valid_combatants_entries.append(entry)
        
        self.db.combatants = valid_combatants_entries

        if not self.db.combatants:
            splattercast.msg(f"AT_REPEAT: No valid combatants remain in managed rooms for handler {self.key}. Stopping.")
            self.stop_combat_logic()
            return

        if self.db.round == 0:
            if len(self.db.combatants) > 0:
                splattercast.msg(f"AT_REPEAT: Handler {self.key}. Combatants present. Starting combat in round 1.")
                self.db.round = 1
            else:
                splattercast.msg(f"AT_REPEAT: Handler {self.key}. Waiting for combatants to join...")
                return

        splattercast.msg(f"AT_REPEAT: Handler {self.key} (managing {[r.key for r in self.db.managed_rooms]}). Round {self.db.round} begins.")
        
        if len(self.db.combatants) <= 1:
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. Not enough combatants ({len(self.db.combatants)}) to continue. Ending combat.")
            self.stop_combat_logic()
            return

        for combat_entry in list(self.get_initiative_order()): # combat_entry is a snapshot
            char = combat_entry.get("char")

            # ... (pruning logic for char, location) ...

            current_char_combat_entry = next((e for e in self.db.combatants if e["char"] == char), None)
            if not current_char_combat_entry:
                splattercast.msg(f"Error: Could not find combat entry for {char.key} mid-turn (second check).")
                continue
            
            # Diagnostic Log:
            splattercast.msg(f"AT_REPEAT_DEBUG_TURN_START: For {char.key}'s turn, handler ID {self.id}, current target in entry: {current_char_combat_entry.get('target').key if current_char_combat_entry.get('target') else 'None'}. Full entry: {current_char_combat_entry}")

            splattercast.msg(f"--- Turn: {char.key} (Loc: {char.location.key}, Init: {current_char_combat_entry['initiative']}) ---")

            # --- Check for string-based grapple actions first ---
            action = current_char_combat_entry.get("combat_action")

            if isinstance(action, str):
                if action == "grapple_initiate":
                    splattercast.msg(f"AT_REPEAT: {char.key} attempting grapple_initiate.")
                    self._resolve_grapple_initiate(current_char_combat_entry)
                    current_char_combat_entry["combat_action"] = None
                    continue  # End turn for this combatant

                elif action == "grapple_join":
                    splattercast.msg(f"AT_REPEAT: {char.key} attempting grapple_join.")
                    self._resolve_grapple_join(current_char_combat_entry)
                    current_char_combat_entry["combat_action"] = None
                    continue  # End turn for this combatant

            # --- Initialize attack condition flags for this turn ---
            attack_has_disadvantage = False # NEW FLAG

            # --- START-OF-TURN NDB CLEANUP for char (Charge Flags) ---
            if hasattr(char.ndb, "charging_vulnerability_active"):
                splattercast.msg(f"AT_REPEAT_START_TURN_CLEANUP: Clearing charging_vulnerability_active for {char.key} (was active from their own previous charge).")
                del char.ndb.charging_vulnerability_active
            
            if hasattr(char.ndb, "charge_attack_bonus_active"): # Bonus from *previous* turn expired if not used
                splattercast.msg(f"AT_REPEAT_START_TURN_CLEANUP: Clearing expired/unused charge_attack_bonus_active for {char.key}.")
                del char.ndb.charge_attack_bonus_active

            # --- TURN SKIP CHECK (e.g. from failed charge/flee) ---
            if hasattr(char.ndb, "skip_combat_round") and char.ndb.skip_combat_round:
                char.msg("|yYou are recovering or off-balance and cannot act this turn.|n")
                splattercast.msg(f"AT_REPEAT_SKIP_TURN: {char.key} is skipping turn due to ndb.skip_combat_round.")
                del char.ndb.skip_combat_round # Consume the flag
                continue # Skip to next combatant

            # --- CHECK FOR YIELDING ---
            if current_char_combat_entry.get("is_yielding"):
                splattercast.msg(f"{char.key} is yielding and takes no hostile action this turn.")
                char.location.msg_contents(f"|y{char.key} holds their action, appearing non-hostile.|n", exclude=[char])
                char.msg("|yYou hold your action, appearing non-hostile.|n")
                continue

            # --- PROCESS COMBAT ACTION INTENT ---
            action_intent_this_turn = current_char_combat_entry.get("combat_action")
            if action_intent_this_turn:
                splattercast.msg(f"AT_REPEAT: {char.key} has action_intent: {action_intent_this_turn}")
                current_char_combat_entry["combat_action"] = None 

                intent_type = action_intent_this_turn.get("type")
                action_target_char = action_intent_this_turn.get("target") 

                is_action_target_valid = False
                if action_target_char and any(e["char"] == action_target_char for e in self.db.combatants):
                    if action_target_char.location and action_target_char.location in self.db.managed_rooms:
                        is_action_target_valid = True
                
                if not is_action_target_valid and action_target_char:
                    char.msg(f"The target of your planned action ({action_target_char.key}) is no longer valid.")
                    splattercast.msg(f"{char.key}'s action_intent target {action_target_char.key} is invalid. Intent cleared, falling through.")
                
                # === YOUR EXISTING GRAPPLE INTENT LOGIC STARTS HERE ===
                elif intent_type == "grapple" and is_action_target_valid:
                    splattercast.msg(f"AT_REPEAT: {char.key} attempting to grapple {action_target_char.key} based on intent.")
                    
                    can_grapple_target = (char.location == action_target_char.location) # Must be in the same room
                    
                    if can_grapple_target:
                        # Proximity Check for Grapple (NEW)
                        if not hasattr(char.ndb, "in_proximity_with"): char.ndb.in_proximity_with = set()
                        if action_target_char not in char.ndb.in_proximity_with:
                            char.msg(f"You need to be in melee proximity with {action_target_char.get_display_name(char)} to grapple them. Try advancing or charging.")
                            splattercast.msg(f"GRAPPLE FAIL (PROXIMITY): {char.key} not in proximity with {action_target_char.key}.")
                            # Do not 'continue' here, let it fall through if you want default attack
                            # Or 'continue' if grapple attempt (even if proximity failed) consumes the turn.
                            # For now, let's assume it consumes the turn if intent was grapple.
                            continue


                        attacker_roll = randint(1, max(1, getattr(char, "motorics", 1)))
                        defender_roll = randint(1, max(1, getattr(action_target_char, "motorics", 1)))
                        splattercast.msg(f"GRAPPLE ATTEMPT: {char.key} (roll {attacker_roll}) vs {action_target_char.key} (roll {defender_roll}).")

                        if attacker_roll > defender_roll:
                            current_char_combat_entry["grappling"] = action_target_char
                            target_entry = next((e for e in self.db.combatants if e["char"] == action_target_char), None)
                            if target_entry:
                                target_entry["grappled_by"] = char
                            
                            grapple_messages = get_combat_message("grapple", "hit", attacker=char, target=action_target_char)
                            char.msg(grapple_messages.get("attacker_msg"))
                            action_target_char.msg(grapple_messages.get("victim_msg"))
                            obs_msg = grapple_messages.get("observer_msg")
                            if char.location:
                                char.location.msg_contents(obs_msg, exclude=[char, action_target_char])
                            splattercast.msg(f"GRAPPLE SUCCESS: {char.key} grappled {action_target_char.key}.")
                        else: # Grapple failed
                            grapple_messages = get_combat_message("grapple", "miss", attacker=char, target=action_target_char)
                            char.msg(grapple_messages.get("attacker_msg"))
                            action_target_char.msg(grapple_messages.get("victim_msg"))
                            obs_msg = grapple_messages.get("observer_msg")
                            if char.location:
                                char.location.msg_contents(obs_msg, exclude=[char, action_target_char])
                            splattercast.msg(f"GRAPPLE FAIL: {char.key} failed to grapple {action_target_char.key}.")
                    else: # Cannot reach (different rooms)
                        char.msg(f"You can't reach {action_target_char.key} to grapple them from here.")
                        splattercast.msg(f"GRAPPLE FAIL (REACH): {char.key} cannot reach {action_target_char.key}.")
                    
                    splattercast.msg(f"AT_REPEAT: {char.key}'s turn concluded by 'grapple' intent processing.")
                    continue 
                
                elif intent_type == "escape_grapple":
                    grappler = current_char_combat_entry.get("grappled_by")
                    is_grappler_valid = False
                    if grappler and any(e["char"] == grappler for e in self.db.combatants):
                        if grappler.location and grappler.location in self.db.managed_rooms:
                             is_grappler_valid = True
                    
                    if is_grappler_valid:
                        escaper_roll = randint(1, max(1, getattr(char, "motorics", 1)))
                        grappler_roll = randint(1, max(1, getattr(grappler, "motorics", 1)))
                        splattercast.msg(f"ESCAPE ATTEMPT: {char.key} (roll {escaper_roll}) vs {grappler.key} (roll {grappler_roll}).")

                        if escaper_roll > grappler_roll:
                            current_char_combat_entry["grappled_by"] = None
                            grappler_entry = next((e for e in self.db.combatants if e["char"] == grappler), None)
                            if grappler_entry:
                                grappler_entry["grappling"] = None
                            escape_messages = get_combat_message("grapple", "escape_hit", attacker=char, target=grappler)
                            char.msg(escape_messages.get("attacker_msg"))
                            grappler.msg(escape_messages.get("victim_msg"))
                            obs_msg = escape_messages.get("observer_msg")
                            for loc in {char.location, grappler.location}: 
                                if loc: loc.msg_contents(obs_msg, exclude=[char, grappler])
                            splattercast.msg(f"ESCAPE SUCCESS: {char.key} escaped from {grappler.key}.")
                        else: # Escape failed
                            escape_messages = get_combat_message("grapple", "escape_miss", attacker=char, target=grappler)
                            char.msg(escape_messages.get("attacker_msg"))
                            grappler.msg(escape_messages.get("victim_msg"))
                            obs_msg = escape_messages.get("observer_msg")
                            for loc in {char.location, grappler.location}:
                                if loc: loc.msg_contents(obs_msg, exclude=[char, grappler])
                            splattercast.msg(f"ESCAPE FAIL: {char.key} failed to escape {grappler.key}.")
                    else: 
                        char.msg("You are not currently grappled by a valid opponent to escape from.")
                        if current_char_combat_entry.get("grappled_by"): 
                            current_char_combat_entry["grappled_by"] = None
                            splattercast.msg(f"CLEANUP: {char.key} was grappled_by an invalid char. Cleared.")
                    
                    splattercast.msg(f"AT_REPEAT: {char.key}'s turn concluded by 'escape_grapple' intent processing.")
                    continue 

                elif intent_type == "release_grapple":
                    victim_char_being_grappled = current_char_combat_entry.get("grappling")
                    is_victim_valid = False
                    if victim_char_being_grappled and any(e["char"] == victim_char_being_grappled for e in self.db.combatants):
                        if victim_char_being_grappled.location and victim_char_being_grappled.location in self.db.managed_rooms:
                            is_victim_valid = True
                    
                    if is_victim_valid:
                        current_char_combat_entry["grappling"] = None
                        victim_entry = next((e for e in self.db.combatants if e["char"] == victim_char_being_grappled), None)
                        if victim_entry:
                            victim_entry["grappled_by"] = None
                        release_messages = get_combat_message("grapple", "release", attacker=char, target=victim_char_being_grappled)
                        char.msg(release_messages.get("attacker_msg"))
                        victim_char_being_grappled.msg(release_messages.get("victim_msg"))
                        obs_msg = release_messages.get("observer_msg")
                        for loc in {char.location, victim_char_being_grappled.location}:
                             if loc: loc.msg_contents(obs_msg, exclude=[char, victim_char_being_grappled])
                        splattercast.msg(f"RELEASE GRAPPLE: {char.key} released {victim_char_being_grappled.key}.")
                    else: 
                        char.msg("You are not grappling a valid opponent to release.")
                        if current_char_combat_entry.get("grappling"): 
                            current_char_combat_entry["grappling"] = None
                            splattercast.msg(f"CLEANUP: {char.key} was grappling an invalid char. Cleared.")

                    splattercast.msg(f"AT_REPEAT: {char.key}'s turn concluded by 'release_grapple' intent processing.")
                    continue 
                # === YOUR EXISTING GRAPPLE INTENT LOGIC ENDS HERE ===
                
                else: 
                    char.msg(f"You briefly consider your plan to '{intent_type}' but it doesn't seem applicable right now, or it's an unknown action.")
                    splattercast.msg(f"AT_REPEAT: {char.key}'s intent '{intent_type}' not fully processed or doesn't end turn. Falling through.")
            
            # --- Handle Yielding (if no intent consumed turn) ---
            if current_char_combat_entry.get("is_yielding"):
                splattercast.msg(f"{char.key} is yielding and takes no hostile action this turn.")
                char.location.msg_contents(f"|y{char.key} holds their action, appearing non-hostile.|n", exclude=[char])
                char.msg("|yYou hold your action, appearing non-hostile.|n")
                continue

            # --- Handle being grappled (auto resist unless yielding) ---
            elif current_char_combat_entry.get("grappled_by"):
                grappler = current_char_combat_entry.get("grappled_by")
                # Check if character is actively yielding (which now also means accepting the grapple)
                if not current_char_combat_entry.get("is_yielding"):
                    # Automatically attempt to escape
                    splattercast.msg(f"{char.key} is being grappled by {grappler.key} and automatically attempts to escape.")
                    char.msg(f"|yYou struggle against {grappler.get_display_name(char)}'s grip!|n")
                    
                    # Setup an escape attempt
                    escaper_roll = randint(1, max(1, getattr(char, "motorics", 1)))
                    grappler_roll = randint(1, max(1, getattr(grappler, "motorics", 1)))
                    splattercast.msg(f"AUTO_ESCAPE_ATTEMPT: {char.key} (roll {escaper_roll}) vs {grappler.key} (roll {grappler_roll}).")

                    if escaper_roll > grappler_roll:
                        # Success
                        current_char_combat_entry["grappled_by"] = None
                        grappler_entry = next((e for e in self.db.combatants if e["char"] == grappler), None)
                        if grappler_entry:
                            grappler_entry["grappling"] = None
                            
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
                continue

            # --- Determine Target for Standard Attack (if no intent consumed turn and not yielding) ---
            target = None
            if current_char_combat_entry.get("grappling"):
                target = current_char_combat_entry["grappling"]
                if not any(e["char"] == target for e in self.db.combatants):
                    splattercast.msg(f"{char.key} was grappling {target.key if target else 'Unknown'}, but they are no longer in combat. Clearing grapple.")
                    current_char_combat_entry["grappling"] = None
                    target = None 
                else:
                     splattercast.msg(f"{char.key} is grappling {target.key}, and defaults to attacking them this turn.")
            
            if not target: 
                target = self.get_target(char)

            if not target:
                is_in_active_grapple = current_char_combat_entry.get("grappled_by") and \
                                       any(e["char"] == current_char_combat_entry.get("grappled_by") for e in self.db.combatants)
                if not is_in_active_grapple:
                    splattercast.msg(f"{char.key} has no offensive target and is not in an active grapple. Removing from combat.")
                    self.remove_combatant(char)
                else:
                    splattercast.msg(f"{char.key} has no offensive target but is being grappled. Turn passes for offensive action.")
                continue 

            # --- WEAPON IDENTIFICATION for current attacker char ---
            hands = getattr(char, "hands", {})
            weapon_obj = next((item for hand, item in hands.items() if item), None)
            is_ranged_weapon = weapon_obj and hasattr(weapon_obj.db, "is_ranged") and weapon_obj.db.is_ranged
            weapon_name_for_msg = weapon_obj.key if weapon_obj else "their fists"
            # --- END WEAPON IDENTIFICATION ---

            # --- PROXIMITY AND WEAPON VALIDATION FOR HANDLER-DRIVEN STANDARD ATTACK ---
            can_attack_target_based_on_proximity_and_weapon = False
            if char.location == target.location: # SAME ROOM
                if not hasattr(char.ndb, "in_proximity_with"): char.ndb.in_proximity_with = set() 
                if not hasattr(target.ndb, "in_proximity_with"): target.ndb.in_proximity_with = set()
                
                is_in_melee_proximity = target in char.ndb.in_proximity_with

                if is_in_melee_proximity: 
                    if is_ranged_weapon:
                        # MODIFIED BLOCK FOR RANGED IN MELEE
                        char.msg(f"|yYou struggle to aim your {weapon_name_for_msg} effectively while locked in melee with {target.get_display_name(char)}. You attack at disadvantage.|n")
                        splattercast.msg(f"AT_REPEAT_ATTACK_CONDITION: {char.key} attacking with ranged '{weapon_name_for_msg}' vs {target.key} in melee. Applying disadvantage.")
                        attack_has_disadvantage = True
                        can_attack_target_based_on_proximity_and_weapon = True 
                    else: 
                        can_attack_target_based_on_proximity_and_weapon = True
                        splattercast.msg(f"AT_REPEAT_PROXIMITY_VALID: {char.key} (melee/unarmed) vs {target.key} (in proximity).")
                else: # Not in melee proximity (at range in same room)
                    if not is_ranged_weapon: # Trying non-ranged attack at someone not in proximity
                        char.msg(f"|rYou are too far away to hit {target.get_display_name(char)} with your {weapon_name_for_msg}. Try advancing or charging.|n")
                        splattercast.msg(f"AT_REPEAT_INVALID_ATTACK: {char.key} tried to use non-ranged '{weapon_name_for_msg}' on {target.key} (not in prox). Attack fails.")
                        continue # Attack still fails and turn ends for this attack
                    else: 
                        can_attack_target_based_on_proximity_and_weapon = True
                        splattercast.msg(f"AT_REPEAT_PROXIMITY_VALID: {char.key} (ranged) vs {target.key} (not in proximity, same room).")
            
            elif target.location in self.db.managed_rooms: # DIFFERENT MANAGED ROOMS
                is_adjacent = any(ex.destination == target.location for ex in char.location.exits)
                if not is_adjacent: 
                    char.msg(f"|rYou can't reach {target.key} in {target.location.key}; they are not in an adjacent part of the combat zone.|n")
                    splattercast.msg(f"AT_REPEAT_INVALID_ATTACK: {char.key} vs {target.key}, rooms not adjacent ({char.location.key} -> {target.location.key}). Attack fails.")
                    current_char_combat_entry["target"] = None
                    continue
                if not is_ranged_weapon:
                    char.msg(f"|rYou need a ranged weapon to attack {target.get_display_name(char)} in {target.location.get_display_name(char)}.|n")
                    splattercast.msg(f"AT_REPEAT_INVALID_ATTACK: {char.key} tried to attack {target.key} in different room without ranged. Attack fails.")
                    current_char_combat_entry["target"] = None
                    continue
                else: 
                    can_attack_target_based_on_proximity_and_weapon = True
                    splattercast.msg(f"AT_REPEAT_PROXIMITY_VALID: {char.key} (ranged) vs {target.key} (different room).")
            else: 
                char.msg(f"|r{target.key} is not in the current combat zone or is unreachable.|n")
                splattercast.msg(f"AT_REPEAT_INVALID_ATTACK: Target {target.key} in unmanaged/unreachable room {target.location.key if target.location else 'None'}. Attack fails.")
                current_char_combat_entry["target"] = None
                continue

            if not can_attack_target_based_on_proximity_and_weapon:
                splattercast.msg(f"AT_REPEAT_ERROR: Attack validation failed for {char.key} vs {target.key} but did not 'continue'. Stopping attack explicitly.")
                continue
            # --- END PROXIMITY AND WEAPON VALIDATION ---

            # --- Resolve Standard Attack ---
            # Robust stat fetching for attack roll
            char_grit_val = getattr(char, "grit", 1)
            char_grit_val_numeric = char_grit_val if isinstance(char_grit_val, (int, float)) else 1
            
            # MODIFIED ATTACK ROLL CALCULATION
            if attack_has_disadvantage:
                roll1 = randint(1, max(1, char_grit_val_numeric))
                roll2 = randint(1, max(1, char_grit_val_numeric))
                atk_roll_base = min(roll1, roll2)
                splattercast.msg(f"AT_REPEAT_ATTACK_ROLL: {char.key} attacking with disadvantage. Rolls: {roll1}, {roll2}. Base attack: {atk_roll_base}.")
            else:
                atk_roll_base = randint(1, max(1, char_grit_val_numeric))
                # Optional: Add a log for normal rolls if desired for consistency
                # splattercast.msg(f"AT_REPEAT_ATTACK_ROLL: {char.key} attacking normally. Base attack: {atk_roll_base}.")

            # Robust stat fetching for defense roll
            target_motorics_val = getattr(target, "motorics", 1)
            # Ensure the value is numeric before using in max(), default to 1 if not
            def_roll_base = randint(1, max(1, target_motorics_val if isinstance(target_motorics_val, (int, float)) else 1))
            
            atk_roll_final = atk_roll_base
            def_roll_final = def_roll_base

            # Apply CHARGE ATTACK BONUS for attacker (char)
            if hasattr(char.ndb, "charge_attack_bonus_active") and char.ndb.charge_attack_bonus_active:
                splattercast.msg(f"AT_REPEAT_CHARGE_BONUS_PENDING: {char.key} had charge_attack_bonus_active (effects temporarily disabled).")
                del char.ndb.charge_attack_bonus_active

            # Apply CHARGING VULNERABILITY for defender (target)
            if hasattr(target.ndb, "charging_vulnerability_active") and target.ndb.charging_vulnerability_active:
                splattercast.msg(f"AT_REPEAT_VULNERABILITY_PENDING: {target.key} had charging_vulnerability_active (effects temporarily disabled).")

            # Safely determine weapon_type_stat
            weapon_type_stat = "unarmed"
            if weapon_obj:  # Check if weapon_obj exists
                if hasattr(weapon_obj, "db"):  # Then check if it has a .db attribute
                    if hasattr(weapon_obj.db, "weapon_type") and weapon_obj.db.weapon_type:
                        weapon_type_stat = str(weapon_obj.db.weapon_type).lower()
                # else: # Optional: Log if weapon_obj exists but has no .db (for deeper debugging if needed)
                #     splattercast.msg(f"DEBUG_WEAPON_INFO: {char.key}'s weapon_obj '{weapon_obj.key}' has no .db attribute.")
            # else: # Optional: Log if no weapon_obj
                # splattercast.msg(f"DEBUG_WEAPON_INFO: {char.key} has no weapon_obj for this attack.")

            # Determine effective_message_weapon_type (assuming current_char_combat_entry is valid)
            grappling_this_target = current_char_combat_entry.get("grappling") == target
            effective_message_weapon_type = "grapple" if grappling_this_target else weapon_type_stat
            
            # This is the splattercast message that was not appearing
            splattercast.msg(f"{char.key} (using {effective_message_weapon_type}, base atk {atk_roll_base}, final {atk_roll_final}) attacks {target.key} (base def {def_roll_base}, final {def_roll_final})")

            if atk_roll_final > def_roll_final:
                splattercast.msg(f"HIT_DEBUG: Attack by {char.key} on {target.key} is a HIT. Processing...")
                # Robust damage calculation
                char_damage_grit_val = getattr(char, "grit", 1)
                damage = (char_damage_grit_val if isinstance(char_damage_grit_val, (int, float)) else 1)
                damage = max(1, damage) # Ensure damage is at least 1
                
                actual_damage_recipient = target 

                target_combat_entry = next((e for e in self.db.combatants if e["char"] == target), None)
                if target_combat_entry and target_combat_entry.get("grappling"):
                    shield_char = target_combat_entry.get("grappling")
                    shield_char_entry = next((e for e in self.db.combatants if e["char"] == shield_char), None)

                    if shield_char_entry and shield_char.location in self.db.managed_rooms: 
                        splattercast.msg(f"HIT_DEBUG: Body shield check. Target {target.key} grappling {shield_char.key}.")
                        target_motorics = getattr(target, "motorics", 1)
                        shield_char_motorics = getattr(shield_char, "motorics", 1)
                        target_positioning_roll = randint(1, max(1, target_motorics))
                        shield_evasion_roll = randint(1, max(1, shield_char_motorics))
                        splattercast.msg(f"HIT_DEBUG: Body shield roll: {target.key} ({target_positioning_roll}) vs {shield_char.key} ({shield_evasion_roll}).")

                        if target_positioning_roll > shield_evasion_roll: 
                            actual_damage_recipient = shield_char
                            msg_shield_event = f"|c{target.key} yanks {shield_char.key} in the way! {shield_char.key} takes the hit!|n"
                            relevant_shield_locations = {target.location, shield_char.location}
                            for loc in relevant_shield_locations:
                                if loc: loc.msg_contents(msg_shield_event, exclude=[target, shield_char])
                            splattercast.msg(f"HIT_DEBUG: Body shield SUCCESS. New recipient: {actual_damage_recipient.key}.")
                        else:
                            msg_shield_fail = f"|y{target.key} tries to use {shield_char.key} as a shield but fails!|n"
                            if target.location: target.location.msg_contents(msg_shield_fail, exclude=[target, shield_char])
                            splattercast.msg(f"HIT_DEBUG: Body shield FAIL. Recipient remains {actual_damage_recipient.key}.")
                splattercast.msg(f"HIT_DEBUG: After body shield, final recipient: {actual_damage_recipient.key}.")

                is_lethal_blow_predicted = False 
                if hasattr(actual_damage_recipient, "db") and hasattr(actual_damage_recipient.db, "hp") and actual_damage_recipient.db.hp is not None:
                    try:
                        hp_val = float(actual_damage_recipient.db.hp) 
                        if hp_val <= damage:
                            is_lethal_blow_predicted = True
                        splattercast.msg(f"HIT_DEBUG: Lethality PREDICTED using db.hp (value: {hp_val} <= damage: {damage}). Predicted lethal: {is_lethal_blow_predicted}.")
                    except (ValueError, TypeError):
                        splattercast.msg(f"HIT_DEBUG: db.hp for {actual_damage_recipient.key} is not a valid number ('{actual_damage_recipient.db.hp}'). Cannot PREDICT lethality via HP.")
                        is_lethal_blow_predicted = False 
                elif hasattr(actual_damage_recipient, "is_dead"):
                    splattercast.msg(f"HIT_DEBUG: db.hp not found or None for {actual_damage_recipient.key}. Cannot reliably PREDICT lethality via HP. Will rely on post-damage check.")
                else:
                    splattercast.msg(f"HIT_DEBUG: No db.hp or is_dead method for {actual_damage_recipient.key} for lethality PRE-check.")

                initial_message_phase = ""
                if is_lethal_blow_predicted:
                    initial_message_phase = "grapple_damage_kill" if grappling_this_target else "kill"
                else:
                    initial_message_phase = "grapple_damage_hit" if grappling_this_target else "hit"
                splattercast.msg(f"HIT_DEBUG: Phase for initial message: '{initial_message_phase}'.")

                initial_combat_messages = {}
                try:
                    initial_combat_messages = get_combat_message(
                        effective_message_weapon_type, initial_message_phase, 
                        attacker=char, target=actual_damage_recipient, item=weapon_obj, damage=damage # Use weapon_obj
                    )
                    splattercast.msg(f"HIT_DEBUG: get_combat_message for initial message returned: {str(initial_combat_messages)[:200]}...")
                except Exception as e_get_msg:
                    splattercast.msg(f"HIT_DEBUG: ERROR during get_combat_message for initial message: {e_get_msg}")
                    initial_combat_messages = {} 

                attacker_msg = initial_combat_messages.get("attacker_msg", f"You {initial_message_phase} {actual_damage_recipient.key} (default msg).")
                victim_msg = initial_combat_messages.get("victim_msg", f"{char.key} {initial_message_phase}s you (default msg).")
                observer_msg = initial_combat_messages.get("observer_msg", f"{char.key} {initial_message_phase}s {actual_damage_recipient.key} (default msg).")
                splattercast.msg(f"HIT_DEBUG: Initial messages retrieved/defaulted. Attacker: '{attacker_msg[:100]}...'")

                try:
                    char.msg(attacker_msg)
                    if actual_damage_recipient != char:
                        actual_damage_recipient.msg(victim_msg)
                    
                    observer_locations = {char.location, actual_damage_recipient.location}
                    observer_locations.discard(None)
                    for loc in observer_locations:
                        exclude_list = [char]
                        if actual_damage_recipient != char:
                            exclude_list.append(actual_damage_recipient)
                        loc.msg_contents(observer_msg, exclude=exclude_list)
                    splattercast.msg(f"HIT_DEBUG: Player-facing initial messages sent for phase '{initial_message_phase}'.")
                except Exception as e_send_msg:
                    splattercast.msg(f"HIT_DEBUG: ERROR sending player-facing initial messages: {e_send_msg}")
                
                splattercast.msg(f"{char.key}'s attack (initial phase: {initial_message_phase}) will attempt to deal {damage} to {actual_damage_recipient.key}.")
                
                if hasattr(actual_damage_recipient, "take_damage"):
                    actual_damage_recipient.take_damage(damage) 
                
                actually_dead = hasattr(actual_damage_recipient, "is_dead") and actual_damage_recipient.is_dead()

                if actually_dead:
                    splattercast.msg(f"HIT_DEBUG: Confirmed ACTUAL death of {actual_damage_recipient.key}.")
                    
                    if not is_lethal_blow_predicted: 
                        splattercast.msg(f"HIT_DEBUG: Initial prediction was NOT lethal (sent '{initial_message_phase}'), but target IS dead. Sending definitive 'kill' message now.")
                        
                        final_kill_phase = "grapple_damage_kill" if grappling_this_target else "kill"
                        final_kill_messages = get_combat_message(
                            effective_message_weapon_type, final_kill_phase,
                            attacker=char, target=actual_damage_recipient, item=weapon_obj, damage=damage # Use weapon_obj
                        )

                        fk_attacker_msg = final_kill_messages.get("attacker_msg", f"You deliver a fatal blow to {actual_damage_recipient.key} (default kill msg).")
                        fk_observer_msg = final_kill_messages.get("observer_msg", f"{char.key} delivers a fatal blow to {actual_damage_recipient.key} (default kill msg).")
                        
                        char.msg(fk_attacker_msg)

                        final_observer_locations = {char.location, actual_damage_recipient.location if actual_damage_recipient.location else None}
                        final_observer_locations.discard(None)
                        for loc in final_observer_locations:
                            exclude_list = [char, actual_damage_recipient]
                            loc.msg_contents(fk_observer_msg, exclude=exclude_list)
                        splattercast.msg(f"HIT_DEBUG: Definitive 'kill' messages sent for phase '{final_kill_phase}'.")

                    self.remove_combatant(actual_damage_recipient)
                    for entry in list(self.db.combatants): 
                        if entry.get("target") == actual_damage_recipient:
                            entry["target"] = self.get_target(entry["char"])
                            splattercast.msg(f"{entry['char'].key} retargeted from slain {actual_damage_recipient.key} to {entry['target'].key if entry['target'] else 'None'}.")
                    continue 
            else: # Attack missed
                miss_phase = "grapple_damage_miss" if grappling_this_target else "miss"
                combat_messages = get_combat_message(
                    effective_message_weapon_type, miss_phase, 
                    attacker=char, target=target, item=weapon_obj # Use weapon_obj
                )

                attacker_msg = combat_messages.get("attacker_msg", f"You miss {target.key}.")
                victim_msg = combat_messages.get("victim_msg", f"{char.key} misses you.")
                observer_msg = combat_messages.get("observer_msg", f"{char.key} misses {target.key}.")

                char.msg(attacker_msg)
                if target != char: 
                    target.msg(victim_msg)

                observer_locations = set()
                if char.location:
                    observer_locations.add(char.location)
                if target.location:
                    observer_locations.add(target.location)

                for loc in observer_locations:
                    exclude_list = []
                    if loc == char.location:
                        exclude_list.append(char)
                    if loc == target.location:
                        if target not in exclude_list:
                            exclude_list.append(target)
                    loc.msg_contents(observer_msg, exclude=exclude_list)
                splattercast.msg(f"MISS_DEBUG: Attack by {char.key} on {target.key} is a MISS.")

        if not self.db.combatants:
            splattercast.msg(f"AT_REPEAT: Handler {self.key}. No combatants left after round processing. Stopping.")
            self.stop_combat_logic()
            return

        self.db.round += 1
        splattercast.msg(f"AT_REPEAT: Handler {self.key}. Round {self.db.round} scheduled for next interval.")

    def _resolve_grapple_attempt(self, attacker_entry, target_entry):
        """Performs the opposed roll for a grapple."""
        attacker = attacker_entry["char"]
        target = target_entry["char"]
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        attacker_roll = randint(1, max(1, getattr(attacker, "motorics", 1)))
        defender_roll = randint(1, max(1, getattr(target, "motorics", 1)))
        splattercast.msg(f"GRAPPLE_ROLL: {attacker.key} (roll {attacker_roll}) vs {target.key} (roll {defender_roll}).")
        
        return attacker_roll > defender_roll

    def _resolve_grapple_initiate(self, attacker_entry):
        """Resolves an all-or-nothing grapple that starts combat."""
        attacker = attacker_entry["char"]
        target = attacker_entry["target"]
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        
        if not target:
            splattercast.msg(f"GRAPPLE_INITIATE_ERROR: {attacker.key} has no valid target.")
            return False
            
        # Find target's combat entry
        target_entry = next((e for e in self.db.combatants if e["char"] == target), None)
        if not target_entry:
            splattercast.msg(f"GRAPPLE_INITIATE_ERROR: Target {target.key} has no combat entry.")
            return False

        # Check proximity first, if not in proximity, need to advance
        in_proximity = target in getattr(attacker.ndb, "in_proximity_with", set())
        advance_success = False
        
        if in_proximity:
            # Already in proximity, no need to advance
            advance_success = True
            splattercast.msg(f"GRAPPLE_INITIATE: {attacker.key} already in proximity with {target.key}.")
        else:
            # Not in proximity, attempt to advance
            caller_roll = randint(1, max(1, getattr(attacker, "motorics", 1)))
            target_roll = randint(1, max(1, getattr(target, "motorics", 1)))
            splattercast.msg(f"GRAPPLE_INITIATE (Advance Roll): {attacker.key} (roll {caller_roll}) vs {target.key} (roll {target_roll}).")
            
            if caller_roll > target_roll:
                # Successful advance
                advance_success = True
                # Update proximity for both
                if not hasattr(attacker.ndb, "in_proximity_with"):
                    attacker.ndb.in_proximity_with = set()
                if not hasattr(target.ndb, "in_proximity_with"):
                    target.ndb.in_proximity_with = set()
                    
                attacker.ndb.in_proximity_with.add(target)
                target.ndb.in_proximity_with.add(attacker)
                splattercast.msg(f"GRAPPLE_INITIATE: {attacker.key} successfully advanced into proximity with {target.key}.")
            # If advance fails, the entire initiate attempt fails

        # If advance succeeded, attempt the grapple
        if advance_success and self._resolve_grapple_attempt(attacker_entry, target_entry):
            # Success - establish grapple
            attacker.msg(f"|gYou successfully grapple {target.get_display_name(attacker)}!|n")
            target.msg(f"|r{attacker.get_display_name(target)} suddenly grapples you!|n")
            attacker.location.msg_contents(
                f"|r{attacker.get_display_name(attacker.location)} suddenly moves in and grapples {target.get_display_name(attacker.location)}, initiating combat!|n",
                exclude=[attacker, target]
            )
            
            attacker_entry["grappling"] = target
            target_entry["grappled_by"] = attacker
            
            # The initiator should be yielding (defense-oriented)
            attacker_entry["is_yielding"] = True
            
            splattercast.msg(f"GRAPPLE_RESOLVE (INITIATE): {attacker.key} succeeded against {target.key}.")
            return True
        else:
            # Failure - abort combat
            attacker.msg(f"|yYou fail to get a hold of {target.get_display_name(attacker)}.|n")
            target.msg(f"|y{attacker.get_display_name(target)} tries to grapple you, but you evade them.|n")
            attacker.location.msg_contents(
                f"|y{attacker.get_display_name(attacker.location)} tries to grapple {target.get_display_name(attacker.location)}, but fails.|n",
                exclude=[attacker, target]
            )
            
            splattercast.msg(f"GRAPPLE_RESOLVE (INITIATE): {attacker.key} failed against {target.key}. Combat is aborted.")
            
            # Remove both from combat - combat is aborted
            self.remove_combatant(attacker)
            self.remove_combatant(target)
            return False

    def _resolve_grapple_join(self, attacker_entry):
        """Resolves a grapple attempt within an ongoing combat."""
        attacker = attacker_entry["char"]
        target = attacker_entry["target"]
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        
        if not target:
            splattercast.msg(f"GRAPPLE_JOIN_ERROR: {attacker.key} has no valid target.")
            return False
            
        # Find target's combat entry
        target_entry = next((e for e in self.db.combatants if e["char"] == target), None)
        if not target_entry:
            splattercast.msg(f"GRAPPLE_JOIN_ERROR: Target {target.key} has no combat entry.")
            return False

        # Check proximity first, if not in proximity, need to advance
        in_proximity = target in getattr(attacker.ndb, "in_proximity_with", set())
        advance_success = False
        
        if in_proximity:
            # Already in proximity, no need to advance
            advance_success = True
            splattercast.msg(f"GRAPPLE_JOIN: {attacker.key} already in proximity with {target.key}.")
        else:
            # Not in proximity, attempt to advance
            caller_roll = randint(1, max(1, getattr(attacker, "motorics", 1)))
            target_roll = randint(1, max(1, getattr(target, "motorics", 1)))
            splattercast.msg(f"GRAPPLE_JOIN (Advance Roll): {attacker.key} (roll {caller_roll}) vs {target.key} (roll {target_roll}).")
            
            if caller_roll > target_roll:
                # Successful advance
                advance_success = True
                # Update proximity for both
                if not hasattr(attacker.ndb, "in_proximity_with"):
                    attacker.ndb.in_proximity_with = set()
                if not hasattr(target.ndb, "in_proximity_with"):
                    target.ndb.in_proximity_with = set()
                
                attacker.ndb.in_proximity_with.add(target)
                target.ndb.in_proximity_with.add(attacker)  # Fixed from add(target)
                attacker.msg(f"|gYou close the distance to {target.get_display_name(attacker)}.|n")
                splattercast.msg(f"GRAPPLE_JOIN: {attacker.key} successfully advanced into proximity with {target.key}.")
            else:
                # Failed advance - leaves attacker vulnerable
                attacker.msg(f"|rYou charge in to grapple but can't get close, leaving you exposed!|n")
                target.msg(f"|g{attacker.get_display_name(target)} tries to rush you but stumbles, leaving a wide opening!|n")
                attacker.location.msg_contents(
                    f"|y{attacker.get_display_name(attacker.location)} tries to rush {target.get_display_name(attacker.location)} but stumbles!|n",
                    exclude=[attacker, target]
                )
                
                # Mark attacker as flat-footed/vulnerable
                attacker_entry["flat_footed"] = True
                
                splattercast.msg(f"GRAPPLE_JOIN (Advance Roll): {attacker.key} failed. Is flat_footed.")
                
                # Give target a bonus attack
                self.resolve_bonus_attack(target, attacker)
                return False

    # Add this method to resolve a bonus attack when an attacker fails a grapple
    def resolve_bonus_attack(self, attacker, victim):
        """Immediately resolves a single bonus attack."""
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"BONUS_ATTACK: Resolving from {attacker.key} against {victim.key}.")
        
        attacker_entry = next((e for e in self.db.combatants if e["char"] == attacker), None)
        victim_entry = next((e for e in self.db.combatants if e["char"] == victim), None)
        
        if not attacker_entry or not victim_entry:
            splattercast.msg(f"BONUS_ATTACK: Could not find combat entries for attacker or victim.")
            return
            
        # This is a simplified attack resolution - we'll send some messages and deal damage
        attacker.msg(f"|gYou hit {victim.get_display_name(attacker)} with a swift counter-attack!|n")
        victim.msg(f"|r{attacker.get_display_name(victim)} counters your failed move, striking you!|n")
        attacker.location.msg_contents(
            f"{attacker.get_display_name(attacker.location)} counters {victim.get_display_name(attacker.location)}'s failed move!",
            exclude=[attacker, victim]
        )
        
        # Apply damage - simple implementation
        damage = 1
        if hasattr(victim, "take_damage"):
            victim.take_damage(damage)
            splattercast.msg(f"BONUS_ATTACK: {attacker.key} deals {damage} damage to {victim.key}.")
