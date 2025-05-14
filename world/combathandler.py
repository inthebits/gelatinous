from evennia import DefaultScript, create_script
from random import randint
from evennia.utils.utils import delay
from world.combat_messages import get_combat_message
from evennia.comms.models import ChannelDB

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    """
    Returns the active CombatHandler for this location, or creates one if needed.
    Logs all actions to Splattercast for debugging.
    Ensures only one handler per location.
    """
    splattercast = ChannelDB.objects.get_channel("Splattercast")
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            if script.is_active:
                splattercast.msg(f"Found active CombatHandler on {location.key}.")
                return script
            else:
                splattercast.msg(f"Found inactive CombatHandler on {location.key}, stopping and deleting it.")
                script.stop()
                script.delete()
    new_script = create_script(
        "world.combathandler.CombatHandler",
        key=COMBAT_SCRIPT_KEY,
        obj=location,
        persistent=True,
    )
    splattercast.msg(f"Created new CombatHandler on {location.key}.")
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
        self.db.ready_to_start = False
        self.db.round_scheduled = False

    def start(self):
        """
        Start the combat handler's repeat timer if not already active.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if self.is_active:
            splattercast.msg(f"CombatHandler is already active. Skipping redundant start.")
            return
        splattercast.msg(f"CombatHandler started.")
        self.is_active = True
        self.start_repeat(self.interval)

    def at_stop(self):
        """
        Clean up when combat ends. Remove all combatants and delete the handler.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        for entry in self.db.combatants:
            char = entry["char"]
            splattercast.msg(f"{char.key} removed from combat.")
            if char.ndb.combat_handler:
                del char.ndb.combat_handler
        splattercast.msg("Combat ends.")
        self.is_active = False
        self.delete()

    def add_combatant(self, char, target=None):
        """
        Add a character to combat, assigning initiative and an optional target.
        Logs if joining an already-running combat.
        Initializes grapple status and combat_action.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if any(entry["char"] == char for entry in self.db.combatants):
            return
        initiative = randint(1, max(1, char.db.motorics or 1))
        self.db.combatants.append({
            "char": char,
            "initiative": initiative,
            "target": target,
            "grappling": None,  # Character object this char is grappling
            "grappled_by": None,  # Character object grappling this char
            "combat_action": None, # Add combat_action here
        })
        char.ndb.combat_handler = self
        splattercast.msg(f"{char.key} joins combat with initiative {initiative}.")
        splattercast.msg(f"{char.key} added to combat. Total combatants: {len(self.db.combatants)}.")
        if self.db.round == 0:
            splattercast.msg(f"Combat is in setup phase (round 0). Waiting for more combatants.")
        elif self.is_active:
            splattercast.msg(f"{char.key} joined an already-running combat.")
        if len(self.db.combatants) > 1:
            self.db.ready_to_start = True
        if self.db.ready_to_start and not self.is_active:
            splattercast.msg(f"Enough combatants added. Starting combat.")
            self.start()

    def remove_combatant(self, char):
        """
        Remove a character from combat and clean up their handler reference.
        If only one or zero combatants remain, end combat.
        Also handles releasing any grapples involving this character.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        # Check if the removed character was grappling someone
        char_combat_entry = next((e for e in self.db.combatants if e["char"] == char), None)
        if char_combat_entry and char_combat_entry.get("grappling"):
            grappled_victim = char_combat_entry["grappling"]
            victim_entry = next((e for e in self.db.combatants if e["char"] == grappled_victim), None)
            if victim_entry:
                victim_entry["grappled_by"] = None
                splattercast.msg(f"{char.key} was grappling {grappled_victim.key}. {grappled_victim.key} is now free.")
        
        # Check if the removed character was grappled by someone
        # and release that grapple from the grappler's side
        for entry in self.db.combatants:
            if entry.get("grappling") == char:
                entry["grappling"] = None
                splattercast.msg(f"{entry['char'].key} was grappling {char.key} (now removed). {entry['char'].key} is no longer grappling.")
            if entry.get("char") == char and entry.get("grappled_by"): # Redundant due to above, but safe
                grappler = entry["grappled_by"]
                grappler_entry = next((e for e in self.db.combatants if e["char"] == grappler), None)
                if grappler_entry:
                    grappler_entry["grappling"] = None

        self.db.combatants = [entry for entry in self.db.combatants if entry["char"] != char]
        if char.ndb.combat_handler:
            del char.ndb.combat_handler
        splattercast.msg(f"{char.key} removed from combat.")
        if len(self.db.combatants) <= 1:
            self.stop()

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
            # Find attackers targeting this char
            attackers = [e["char"] for e in self.db.combatants if e.get("target") == char and e["char"] != char]
            splattercast.msg(
                f"Attackers targeting {char.key}: {[a.key for a in attackers]}"
            )
            if attackers:
                # Retarget to a random attacker
                target = attackers[randint(0, len(attackers) - 1)]
                splattercast.msg(
                    f"{char.key} now targets {target.key} (was being targeted)."
                )
                self.set_target(char, target)
            else:
                # No attackers, remove from combat
                splattercast.msg(
                    f"{char.key} is not being targeted by anyone and will be removed from combat."
                )
                return None
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
        Handles attacks, misses, deaths, and round progression.
        Removes combatants with no valid target or who are not being targeted.
        Includes logic for grapple actions.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if not self.is_active:
            return
        # Setup phase: wait for enough combatants to start
        if self.db.round == 0:
            active_combatants = [e for e in self.db.combatants if e["char"].location == self.obj]
            splattercast.msg(f"Round 0: Active combatants: {[e['char'].key for e in active_combatants]}.")
            if len(active_combatants) > 1:
                splattercast.msg(f"Enough combatants present. Starting combat in round 1.")
                self.db.round = 1
            else:
                splattercast.msg(f"Waiting for more combatants to join...")
                return
        splattercast.msg(f"Combat round {self.db.round} begins.")
        active_combatants = [e for e in self.db.combatants if e["char"].location == self.obj]
        splattercast.msg(f"Active combatants: {[e['char'].key for e in active_combatants]}.")
        if len(active_combatants) <= 1:
            splattercast.msg(f"Not enough combatants remain. Ending combat.")
            self.stop()
            return

        for combat_entry in list(self.get_initiative_order()): # Use list() for safe removal
            char = combat_entry["char"]
            if not char or char not in [e["char"] for e in self.db.combatants]: # char might have been removed
                continue

            # Retrieve the most current entry for char, as it might have been modified
            # by a previous combatant's grapple action in this same turn.
            current_char_combat_entry = next((e for e in self.db.combatants if e["char"] == char), None)
            if not current_char_combat_entry: # Should not happen if char is still in active_combatants
                splattercast.msg(f"Error: Could not find combat entry for {char.key} mid-turn.")
                continue

            # Retrieve action_intent from the combatant's entry in the handler
            action_intent = current_char_combat_entry.get("combat_action")

            if action_intent: # Clear after reading
                current_char_combat_entry["combat_action"] = None # Clear it from the handler's list

            # --- Handle Grapple States and Actions ---
            # State 1: Character is grappled by someone else
            if current_char_combat_entry.get("grappled_by"):
                grappler = current_char_combat_entry["grappled_by"]
                grappler_entry = next((e for e in self.db.combatants if e["char"] == grappler), None)

                if not grappler_entry: # Grappler might have been removed from combat
                    current_char_combat_entry["grappled_by"] = None
                    splattercast.msg(f"{char.key} was grappled by {grappler.key if grappler else 'Unknown'}, but grappler is gone. Releasing grapple.")
                    # Fall through to normal action or next state check
                
                elif action_intent and action_intent.get("type") == "escape":
                    splattercast.msg(f"{char.key} (grappled by {grappler.key}) attempts to escape.")
                    # Escape roll: char's grit vs grappler's grit (example)
                    escape_roll = randint(1, max(1, getattr(char, "grit", 1)))
                    hold_roll = randint(1, max(1, getattr(grappler, "grit", 1)))
                    if escape_roll > hold_roll:
                        current_char_combat_entry["grappled_by"] = None
                        if grappler_entry:
                             grappler_entry["grappling"] = None
                        msg = f"{char.key} escapes from {grappler.key}'s grapple!"
                        # msg = get_combat_message("grapple", "escape_success", attacker=char, target=grappler)
                        self.obj.msg_contents(f"|G{msg}|n")
                        splattercast.msg(msg)
                    else:
                        msg = f"{char.key} fails to escape from {grappler.key}'s grapple."
                        # msg = get_combat_message("grapple", "escape_fail", attacker=char, target=grappler)
                        self.obj.msg_contents(f"|y{msg}|n")
                        splattercast.msg(msg)
                    continue # Turn ends after escape attempt

                else: # Default action for grappled char: attack grappler
                    target = grappler
                    splattercast.msg(f"{char.key} is grappled by {grappler.key}, attacks back.")
                    # Proceed to standard attack logic below, with target set to grappler

            # State 2: Character is not grappled, and intends to grapple someone
            elif action_intent and action_intent.get("type") == "grapple":
                victim_char = action_intent.get("target")
                victim_entry = next((e for e in self.db.combatants if e["char"] == victim_char), None)

                if victim_char and victim_entry and victim_char != char:
                    if victim_entry.get("grappled_by"):
                        msg = f"{char.key} cannot grapple {victim_char.key}, they are already grappled by {victim_entry['grappled_by'].key}."
                        self.obj.msg_contents(f"|y{msg}|n")
                        splattercast.msg(msg)
                    elif current_char_combat_entry.get("grappling"):
                        msg = f"{char.key} cannot grapple {victim_char.key}, {char.key} is already grappling {current_char_combat_entry['grappling'].key}."
                        self.obj.msg_contents(f"|y{msg}|n")
                        splattercast.msg(msg)
                    else:
                        splattercast.msg(f"{char.key} attempts to grapple {victim_char.key}.")
                        grapple_roll = randint(1, max(1, getattr(char, "grit", 1)))
                        resist_roll = randint(1, max(1, getattr(victim_char, "motorics", 1)))
                        if grapple_roll > resist_roll:
                            # Find the index of the attacker's entry
                            attacker_idx = -1
                            for i, entry_dict in enumerate(self.db.combatants):
                                if entry_dict["char"] == char:
                                    attacker_idx = i
                                    break
                            
                            # Find the index of the victim's entry
                            victim_idx = -1
                            if victim_entry:
                                for i, entry_dict in enumerate(self.db.combatants):
                                    if entry_dict["char"] == victim_char:
                                        victim_idx = i
                                        break
                            
                            if attacker_idx != -1 and victim_idx != -1:
                                self.db.combatants[attacker_idx]["grappling"] = victim_char
                                self.db.combatants[victim_idx]["grappled_by"] = char
                                splattercast.msg(f"DEBUG ASSIGN VIA INDEX: Assigned to self.db.combatants[{attacker_idx}]['grappling'] and self.db.combatants[{victim_idx}]['grappled_by']")
                            else:
                                splattercast.msg(f"CRITICAL ERROR: Attacker (idx {attacker_idx}) or Victim (idx {victim_idx}) entry not found by index during grapple success for {char.key} and {victim_char.key}.")
                                # Decide how to handle this error

                            # --- Debug checks remain the same ---
                            splattercast.msg(
                                f"DEBUG GRAPPLE SET: Attacker {char.key}'s entry['grappling'] intended as {victim_char.key}. " 
                                f"Victim {victim_char.key}'s entry['grappled_by'] recorded as {char.key}."
                            )
                            attacker_entry_in_db = next((e for e in self.db.combatants if e["char"] == char), None)
                            if attacker_entry_in_db:
                                splattercast.msg(
                                    f"DEBUG GRAPPLE SET (DB CHECK): Attacker {char.key}'s DB entry['grappling'] is now "
                                    f"{attacker_entry_in_db.get('grappling').key if attacker_entry_in_db.get('grappling') else 'None'}"
                                )
                            victim_entry_in_db = next((e for e in self.db.combatants if e["char"] == victim_char), None)
                            if victim_entry_in_db:
                                splattercast.msg(
                                    f"DEBUG GRAPPLE SET (DB CHECK): Victim {victim_char.key}'s DB entry['grappled_by'] is now "
                                    f"{victim_entry_in_db.get('grappled_by').key if victim_entry_in_db.get('grappled_by') else 'None'}"
                                )
                            # --- END IMMEDIATE DEBUG ---
                            msg = f"{char.key} successfully grapples {victim_char.key}!"
                            self.obj.msg_contents(f"|g{msg}|n")
                        else:
                            msg = f"{char.key} fails to grapple {victim_char.key}."
                            self.obj.msg_contents(f"|y{msg}|n")
                            splattercast.msg(msg)
                else:
                    splattercast.msg(f"{char.key} tried to grapple invalid target {victim_char}.")
                    self.obj.msg_contents(f"{char.key} cannot grapple that.")
                continue # Turn ends after grapple attempt

            # State 3: Character is grappling someone, and not grappled themselves
            elif current_char_combat_entry.get("grappling"):
                grappled_victim_obj = current_char_combat_entry["grappling"] # Store the object for clarity
                victim_entry = next((e for e in self.db.combatants if e["char"] == grappled_victim_obj), None)

                if not victim_entry: 
                    # Victim is gone from combat. Character is no longer grappling them.
                    current_char_combat_entry["grappling"] = None
                    splattercast.msg(f"{char.key} was grappling {grappled_victim_obj.key if grappled_victim_obj else 'Unknown'}, but victim is gone. Releasing grapple.")
                    # No 'continue' here. Character is no longer grappling, 
                    # so they should proceed to State 4 to determine a new target/action for this turn.
                
                elif action_intent and action_intent.get("type") == "release_grapple":
                    # Explicit intent to release
                    current_char_combat_entry["grappling"] = None
                    # victim_entry is guaranteed to be valid here because (not victim_entry) was false.
                    victim_entry["grappled_by"] = None
                    msg = f"{char.key} releases {grappled_victim_obj.key}."
                    # Consider using: msg = get_combat_message("grapple", "release_success", attacker=char, target=grappled_victim_obj)
                    self.obj.msg_contents(f"|G{msg}|n")
                    splattercast.msg(msg)
                    continue # Turn ends

                else: 
                    # Default action for a character who is grappling someone: auto-release.
                    # This block is reached if:
                    # 1. They are grappling someone (current_char_combat_entry.get("grappling") is true).
                    # 2. Their victim is still in combat (victim_entry is valid).
                    # 3. They do not have an explicit "release_grapple" intent (or any other overriding intent).
                    
                    splattercast.msg(f"{char.key} is grappling {grappled_victim_obj.key}, and defaults to releasing them this turn.")
                    current_char_combat_entry["grappling"] = None
                    # victim_entry is guaranteed to be valid here.
                    victim_entry["grappled_by"] = None
                    
                    msg = f"{char.key} automatically releases {grappled_victim_obj.key}."
                    # Consider using: msg = get_combat_message("grapple", "release_auto", attacker=char, target=grappled_victim_obj)
                    self.obj.msg_contents(f"|g{msg}|n") # Using lowercase 'g' for auto-release, or choose another style.
                    splattercast.msg(f"AUTO-RELEASE: {msg}")
                    continue # Turn ends. They do not proceed to attack.

            # State 4: Standard action (usually attack)
            else:
                target = self.get_target(char) # Standard targeting

            # --- Standard Attack Sequence (if applicable after grapple logic) ---
            if not target: # Could be cleared if target was removed or grapple logic decided no attack
                splattercast.msg(f"{char.key} has no target for an attack this turn.")
                continue

            # Defensive attribute access for combat stats
            atk_roll = randint(1, max(1, getattr(char, "grit", 1)))
            def_roll = randint(1, max(1, getattr(target, "motorics", 1)))
            
            # Defensive access for hands/weapon
            hands = getattr(char, "hands", {})
            weapon = None
            for hand, item in hands.items():
                if item: # Assuming item is a weapon object
                    weapon = item
                    break
            weapon_type = "unarmed"
            if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type:
                weapon_type = str(weapon.db.weapon_type).lower()

            # --- Debugging for grapple message context ---
            grappling_this_target = False
            if current_char_combat_entry and current_char_combat_entry.get("grappling") and current_char_combat_entry.get("grappling") == target:
                grappling_this_target = True
            
            effective_message_weapon_type = "grapple" if grappling_this_target else weapon_type

            splattercast.msg(
                f"DEBUG MSG CONTEXT: Attacker: {char.key}, Target: {target.key}, "
                f"Attacker Grappling Target?: {grappling_this_target}, "
                f"Actual Weapon: {weapon_type}, Effective Msg Type: {effective_message_weapon_type}"
            )
            if current_char_combat_entry:
                splattercast.msg(
                    f"DEBUG MSG CONTEXT: current_char_combat_entry['grappling'] = {current_char_combat_entry.get('grappling').key if current_char_combat_entry.get('grappling') else 'None'}"
                )
            # --- End Debugging ---

            splattercast.msg(f"{char.key} (using {weapon_type}) attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")

            if atk_roll > def_roll:
                # Successful hit
                damage = getattr(char, "grit", 1) or 1 # Basic damage
                splattercast.msg(f"{char.key} hits {target.key} with {weapon_type} for {damage} damage.")
                
                msg = get_combat_message(
                    effective_message_weapon_type, # Use the debugged effective type
                    "hit", 
                    attacker=char,
                    target=target,
                    item=weapon,
                    damage=damage
                )
                # This log shows the message retrieved. The specific context (grapple or actual weapon)
                # would have been used by get_combat_message to select the appropriate string.
                splattercast.msg(f"get_combat_message (hit) returned: {msg!r}")
                if msg:
                    self.obj.msg_contents(f"|R{msg}|n")
                # Defensive: ensure take_damage exists
                if hasattr(target, "take_damage"):
                    target.take_damage(damage)
                if hasattr(target, "is_dead") and target.is_dead():
                    # Handle death and retargeting
                    splattercast.msg(f"{target.key} has been defeated and removed from combat.")
                    msg = get_combat_message(
                        effective_message_weapon_type, # Use the debugged effective type
                        "kill",
                        attacker=char,
                        target=target,
                        item=weapon,
                        damage=damage
                    )
                    splattercast.msg(f"get_combat_message (kill) returned: {msg!r}")
                    if msg:
                        self.obj.msg_contents(f"|R{msg}|n")
                    self.remove_combatant(target)
                    # Retarget anyone who was targeting the now-removed character
                    for entry in self.db.combatants:
                        if entry.get("target") == target:
                            new_target = self.get_target(entry["char"])
                            old_name = target.key if hasattr(target, "key") else str(target)
                            new_name = new_target.key if new_target else "None"
                            splattercast.msg(
                                f"{entry['char'].key} was targeting {old_name} (now removed) and now targets {new_name}."
                            )
                            entry["target"] = new_target
                    continue
            else:
                # Missed attack
                msg = get_combat_message(
                    effective_message_weapon_type, # Use the debugged effective type
                    "miss", 
                    attacker=char,
                    target=target,
                    item=weapon
                )
                # This log shows the message retrieved. The specific context (grapple or actual weapon)
                # would have been used by get_combat_message to select the appropriate string.
                splattercast.msg(f"get_combat_message (miss) returned: {msg!r}")
                if msg:
                    self.obj.msg_contents(f"|[X{msg}|n")
                else:
                    self.obj.msg_contents(f"{char.key} misses {target.key}.")
        self.db.round += 1
        splattercast.msg(f"Round {self.db.round} scheduled.")
