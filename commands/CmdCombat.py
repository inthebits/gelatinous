from evennia import Command
from evennia.utils.utils import inherits_from
from random import randint, choice
from world.combathandler import get_or_create_combat, COMBAT_SCRIPT_KEY
from world.combat_messages import get_combat_message
from evennia.comms.models import ChannelDB
from evennia.utils import utils
from evennia.utils.evtable import EvTable 


class CmdAttack(Command):
    """
    Attack a target in your current room or in the direction you are aiming.

    Usage:
        attack <target>
        kill <target>

    Initiates combat and adds you and your target to the CombatHandler.
    """

    key = "attack"
    aliases = ["kill"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        if not args:
            caller.msg("Attack who?")
            return

        target_room = caller.location
        target_search_name = args

        # --- AIMING DIRECTION ATTACK ---
        aiming_direction = getattr(caller.ndb, "aiming_direction", None)
        if aiming_direction:
            splattercast.msg(f"ATTACK_CMD: {caller.key} is aiming {aiming_direction}, attempting remote attack on '{args}'.")
            
            # Make alias check more robust for case
            aiming_direction_lower = aiming_direction.lower()
            exit_obj = None
            for ex in caller.location.exits:
                current_exit_aliases_lower = [alias.lower() for alias in (ex.aliases.all() if hasattr(ex.aliases, "all") else [])]
                if ex.key.lower() == aiming_direction_lower or aiming_direction_lower in current_exit_aliases_lower:
                    exit_obj = ex
                    break
            
            if not exit_obj or not exit_obj.destination:
                caller.msg(f"You are aiming {aiming_direction}, but there's no clear path to attack through.")
                return
            target_room = exit_obj.destination
            splattercast.msg(f"ATTACK_CMD: Remote attack target room is {target_room.key}.")
        # --- END AIMING DIRECTION ATTACK ---

        # Search for target in the determined target_room
        # Using a more robust search that considers character type
        potential_targets = [
            obj for obj in target_room.contents
            if inherits_from(obj, "typeclasses.characters.Character") and
               (target_search_name.lower() in obj.key.lower() or
                any(target_search_name.lower() in alias.lower() for alias in (obj.aliases.all() if hasattr(obj.aliases, "all") else [])))
        ]
        if not potential_targets:
            caller.msg(f"You don't see '{target_search_name}' {(f'in the {aiming_direction} direction' if aiming_direction else 'here')}.")
            return
        target = potential_targets[0]

        if target == caller:
            caller.msg("You can't attack yourself.")
            return
        # (Keep other initial validations for target type)

        # --- Get/Create/Merge Combat Handlers ---
        caller_handler = get_or_create_combat(caller.location)
        target_handler = get_or_create_combat(target.location) # Might be the same if target_room is caller.location

        final_handler = caller_handler
        if caller_handler != target_handler:
            splattercast.msg(f"ATTACK_CMD: Cross-handler engagement! Caller's handler: {caller_handler.key} (on {caller_handler.obj.key}). Target's handler: {target_handler.key} (on {target_handler.obj.key}). Merging...")
            # Simple merge rule: caller's handler absorbs target's handler
            # More complex rules could be: older handler, handler with more combatants, etc.
            caller_handler.merge_handler(target_handler)
            # final_handler is already caller_handler
            splattercast.msg(f"ATTACK_CMD: Merge complete. Final handler is {final_handler.key}, now managing rooms: {[r.key for r in final_handler.db.managed_rooms]}.")
        else:
            splattercast.msg(f"ATTACK_CMD: Caller and target are (or will be) in the same handler zone: {final_handler.key} (on {final_handler.obj.key}).")
            # Ensure both rooms are explicitly managed if it's a local attack but aiming expanded the zone
            final_handler.enroll_room(caller.location)
            final_handler.enroll_room(target.location)


        # --- Add combatants to the final_handler ---
        # add_combatant now also enrolls the char's room if needed.
        # It also handles not re-adding if already present.
        if not any(e["char"] == caller for e in final_handler.db.combatants):
            final_handler.add_combatant(caller, target=target)
        else: # Caller already in this handler, update target and ensure not yielding
            caller_entry = next(e for e in final_handler.db.combatants if e["char"] == caller)
            caller_entry["target"] = target
            caller_entry["is_yielding"] = False


        if not any(e["char"] == target for e in final_handler.db.combatants):
            final_handler.add_combatant(target, target=caller) # Target initially targets attacker
        else: # Target already in this handler, ensure they target back if not already
            target_entry = next(e for e in final_handler.db.combatants if e["char"] == target)
            if not target_entry.get("target"): # If they had no target, they target the attacker
                 target_entry["target"] = caller


        # --- Messaging and Action ---
        if aiming_direction:
            # --- Attacking into an adjacent room ---
            splattercast.msg(f"ATTACK_CMD: Aiming direction attack by {caller.key} towards {aiming_direction} into {target_room.key} at {target.key}.")

            # 1. Get weapon details
            hands = getattr(caller, "hands", {})
            weapon = next((item for hand, item in hands.items() if item), None)
            weapon_type = (str(weapon.db.weapon_type).lower() if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type else "unarmed")

            # 2. Get standard initiate messages from get_combat_message
            initiate_msg_obj = get_combat_message(weapon_type, "initiate", attacker=caller, target=target, item=weapon)
            
            std_attacker_initiate = ""
            std_victim_initiate = ""
            std_observer_initiate = ""

            if isinstance(initiate_msg_obj, dict):
                std_attacker_initiate = initiate_msg_obj.get("attacker_msg", f"You prepare to strike {target.key}!")
                std_victim_initiate = initiate_msg_obj.get("victim_msg", f"{caller.key} prepares to strike you!")
                std_observer_initiate = initiate_msg_obj.get("observer_msg", f"{caller.key} prepares to strike {target.key}!")
            elif isinstance(initiate_msg_obj, str): # Fallback if get_combat_message returns a single string for initiate
                splattercast.msg(f"CmdAttack (aiming): initiate_msg_obj for {weapon_type} was a string. Using generic attacker/victim messages. String: {initiate_msg_obj}")
                std_observer_initiate = initiate_msg_obj
                std_attacker_initiate = f"You prepare to strike {target.key} with your {weapon_type}!"
                std_victim_initiate = f"{caller.key} prepares to strike you with their {weapon_type}!"
            else: # Unexpected type
                splattercast.msg(f"CmdAttack (aiming): Unexpected initiate_msg_obj type from get_combat_message for {weapon_type}: {type(initiate_msg_obj)}. Content: {initiate_msg_obj}")
                std_attacker_initiate = f"You initiate an attack on {target.key}."
                std_victim_initiate = f"{caller.key} initiates an attack on you."
                std_observer_initiate = f"{caller.key} initiates an attack on {target.key}."

            # 3. Determine the direction from which the attack arrives in the target's room
            attacker_direction_from_target_perspective = "a nearby location" # Default
            # Find the exit in target_room that leads back to caller.location
            exit_from_target_to_caller_room = None
            for ex_obj in target_room.exits:
                if ex_obj.destination == caller.location:
                    exit_from_target_to_caller_room = ex_obj
                    break
            if exit_from_target_to_caller_room:
                attacker_direction_from_target_perspective = exit_from_target_to_caller_room.key

            # 4. Construct and send messages (using |r for normal red)

            # Attacker's message
            prefix_attacker = f"|RAiming {aiming_direction} into {target_room.get_display_name(caller)}, "
            caller.msg(prefix_attacker + std_attacker_initiate)

            # Victim's message (in target_room)
            prefix_victim = f"|RSuddenly, you notice {caller.get_display_name(target)} to the {attacker_direction_from_target_perspective} aiming at you from {caller.location.get_display_name(target)}), "
            target.msg(prefix_victim + std_victim_initiate)

            # Observer message in caller's room (attacker's room)
            prefix_observer_caller_room = f"|R{caller.key} takes aim {aiming_direction} into {target_room.get_display_name(caller.location)}, "
            # Exclude caller; target is not in this room.
            caller.location.msg_contents(prefix_observer_caller_room + std_observer_initiate, exclude=[caller])

            # Observer message in target's room
            prefix_observer_target_room = f"|RYour attention is drawn to the {attacker_direction_from_target_perspective} as {caller.key} aiming from {caller.location.get_display_name(target_room)}, "
            # Exclude target; caller is not in this room.
            target_room.msg_contents(prefix_observer_target_room + std_observer_initiate, exclude=[target])
            
        else:
            # Standard local attack initiation message (use get_combat_message)
            hands = getattr(caller, "hands", {})
            weapon = next((item for hand, item in hands.items() if item), None)
            weapon_type = (str(weapon.db.weapon_type).lower() if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type else "unarmed")
            initiate_msg_obj = get_combat_message(weapon_type, "initiate", attacker=caller, target=target, item=weapon)
            
            final_initiate_str = ""
            if isinstance(initiate_msg_obj, dict):
                # For types like "unarmed", get_combat_message may return a dict.
                # We need the observer message for a general room broadcast.
                final_initiate_str = initiate_msg_obj.get("observer_msg")
                if not final_initiate_str:
                    # Fallback if "observer_msg" is missing
                    splattercast.msg(f"CmdAttack: weapon_type {weapon_type} initiate message was dict but missing 'observer_msg'. Dict: {initiate_msg_obj}")
                    final_initiate_str = f"{caller.key} begins an action against {target.key if target else 'someone'}."
            elif isinstance(initiate_msg_obj, str):
                # For types that return a single formatted string.
                final_initiate_str = initiate_msg_obj
            else:
                # Unexpected type, provide a generic fallback
                splattercast.msg(f"CmdAttack: Unexpected initiate_msg_obj type from get_combat_message for {weapon_type}: {type(initiate_msg_obj)}. Content: {initiate_msg_obj}")
                final_initiate_str = f"{caller.key} initiates an attack on {target.key if target else 'someone'}."

            # Send the string directly; get_combat_message now handles coloring for "initiate"
            caller.location.msg_contents(final_initiate_str)


        splattercast.msg(f"ATTACK_CMD: {caller.key} attacks {target.key if target else 'a direction'}. Combat managed by {final_handler.key}.")
        
        # The combat handler will resolve the actual hit on its next at_repeat
        # Ensure it's running if it wasn't
        if not final_handler.is_active:
            final_handler.start()


class CmdFlee(Command):
    """
    Attempt to flee from an aimer or combat.

    Usage:
      flee

    If someone is aiming at you, you will first attempt to break their aim.
    If successful, or if no one was aiming at you and you are in combat,
    you will attempt to escape the current combat and leave the room.
    If you fail any step, you remain in place (and may skip your next combat turn if failing to flee combat).
    Cannot be used if you are currently grappled in combat.
    """

    key = "flee"
    locks = "cmd:all()" # Consider if cmd:in_combat() is too restrictive if fleeing aim lock is desired outside combat

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        
        handler = getattr(caller.ndb, "combat_handler", None)
        aimer_locking_caller = getattr(caller.ndb, "aimed_at_by", None)

        # --- Pre-checks: Nothing to flee from? ---
        if not handler and not aimer_locking_caller:
            caller.msg("You have nothing to flee from.")
            return

        # --- Part 1: Attempt to break an aim lock if present ---
        aim_successfully_broken = False
        if aimer_locking_caller:
            # Validate aimer is still present, in the same room, and actually aiming at the caller
            if not aimer_locking_caller.location or \
               aimer_locking_caller.location != caller.location or \
               getattr(aimer_locking_caller.ndb, "aiming_at", None) != caller:
                
                caller.msg(f"The one aiming at you ({aimer_locking_caller.get_display_name(caller) if aimer_locking_caller else 'someone'}) seems to have stopped or departed; you are no longer locked by their aim.")
                if hasattr(caller.ndb, "aimed_at_by"): del caller.ndb.aimed_at_by
                if aimer_locking_caller and hasattr(aimer_locking_caller.ndb, "aiming_at") and aimer_locking_caller.ndb.aiming_at == caller:
                    del aimer_locking_caller.ndb.aiming_at
                splattercast.msg(f"FLEE_CMD: Aim lock on {caller.key} by {aimer_locking_caller.key if aimer_locking_caller else 'Unknown Aimer'} was stale/invalid. Lock broken.")
                aimer_locking_caller = None 
                aim_successfully_broken = True 
            else:
                splattercast.msg(f"FLEE_CMD: {caller.key} is attempting to break aim lock by {aimer_locking_caller.key}.")
                aimer_perception = getattr(aimer_locking_caller, "perception", 1) # Stat to maintain aim
                caller_motorics = getattr(caller, "motorics", 1)
                
                flee_roll = randint(1, max(1, caller_motorics))
                resist_roll = randint(1, max(1, aimer_perception))

                splattercast.msg(f"FLEE_AIM_ROLL: {caller.key}(motorics:{flee_roll}) vs {aimer_locking_caller.key}(perception:{resist_roll})")

                if flee_roll > resist_roll:
                    caller.msg(f"|rYou deftly break free from {aimer_locking_caller.get_display_name(caller)}'s aim!|n")
                    if aimer_locking_caller.access(caller, "view"): # Check if aimer can see it
                        aimer_locking_caller.msg(f"|r{caller.get_display_name(aimer_locking_caller)} breaks free from your aim!|n")
                    
                    # Use clear_aim_state on the aimer to notify them and clear their aim
                    if hasattr(aimer_locking_caller, "clear_aim_state"):
                        aimer_locking_caller.clear_aim_state(reason_for_clearing=f"as {caller.key} breaks free")
                    else: # Fallback if aimer doesn't have the method
                        if hasattr(aimer_locking_caller.ndb, "aiming_at"): del aimer_locking_caller.ndb.aiming_at
                    
                    # Clear on the caller as well
                    if hasattr(caller.ndb, "aimed_at_by"): del caller.ndb.aimed_at_by
                    
                    splattercast.msg(f"FLEE_AIM_SUCCESS: {caller.key} broke free from {aimer_locking_caller.key}'s aim.")
                    aimer_locking_caller = None # Aim lock now broken
                    aim_successfully_broken = True
                else: # Failed to break aim - AIMER ATTACKS!
                    caller_msg_flee_fail = f"|RYou try to break free from {aimer_locking_caller.get_display_name(caller)}'s aim, but they keep you pinned!|n"
                    aimer_msg_flee_fail = ""
                    if aimer_locking_caller.access(caller, "view"):
                        aimer_msg_flee_fail = f"{caller.get_display_name(aimer_locking_caller)} tries to break your aim, but you maintain focus."
                    
                    splattercast.msg(f"FLEE_AIM_FAIL: {caller.key} failed to break {aimer_locking_caller.key}'s aim. {aimer_locking_caller.key} initiates an attack.")

                    # --- Aimer attacks on failed flee attempt ---
                    attacker_char = aimer_locking_caller
                    target_char = caller # 'caller' is the one who typed 'flee'

                    # 1. Get/Create Combat Handler (they are in the same room)
                    final_handler = get_or_create_combat(attacker_char.location)
                    final_handler.enroll_room(attacker_char.location) # Ensure room is managed

                    # 2. Add/Update combatants
                    # Attacker (the aimer)
                    attacker_entry = next((e for e in final_handler.db.combatants if e["char"] == attacker_char), None)
                    if not attacker_entry:
                        final_handler.add_combatant(attacker_char, target=target_char)
                    else:
                        attacker_entry["target"] = target_char
                        attacker_entry["is_yielding"] = False # No longer yielding if they take this opportunity
                    
                    # Target (the fleer)
                    target_entry = next((e for e in final_handler.db.combatants if e["char"] == target_char), None)
                    if not target_entry:
                        final_handler.add_combatant(target_char, target=attacker_char) # Target might auto-retaliate
                    else:
                        if not target_entry.get("target"): # If they had no target, they might target back
                            target_entry["target"] = attacker_char
                        target_entry["is_yielding"] = False # Being attacked, no longer yielding if they were

                    # 3. Messaging for the attack
                    hands = getattr(attacker_char, "hands", {})
                    weapon = next((item for hand, item in hands.items() if item), None)
                    weapon_type = (str(weapon.db.weapon_type).lower() if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type else "unarmed")
                    
                    initiate_msg_obj = get_combat_message(weapon_type, "initiate", attacker=attacker_char, target=target_char, item=weapon)
                    
                    # Ensure fallbacks are colored
                    atk_msg_attacker = initiate_msg_obj.get("attacker_msg", f"|RYou attack {target_char.get_display_name(attacker_char)}!|n") if isinstance(initiate_msg_obj, dict) else f"|rYou attack {target_char.get_display_name(attacker_char)} with your {weapon_type}!|n"
                    atk_msg_victim = initiate_msg_obj.get("victim_msg", f"|R{attacker_char.get_display_name(target_char)} attacks you!|n") if isinstance(initiate_msg_obj, dict) else f"|r{attacker_char.get_display_name(target_char)} attacks you with their {weapon_type}!|n"
                    atk_msg_observer = initiate_msg_obj.get("observer_msg", f"|R{attacker_char.get_display_name(attacker_char.location)} attacks {target_char.get_display_name(target_char.location)}!|n") if isinstance(initiate_msg_obj, dict) else f"|r{attacker_char.get_display_name(attacker_char.location)} attacks {target_char.get_display_name(target_char.location)} with their {weapon_type}!|n"

                    # Prepare texts for clarity
                    opportunity_text_victim = f"|R{attacker_char.get_display_name(target_char)} seizes the opportunity!|n"
                    opportunity_text_attacker = "|RYou seize the opportunity!|n"
                    
                    # Send combined messages
                    # To the fleer (target_char)
                    # caller_msg_flee_fail is already "|r...|n"
                    caller.msg(caller_msg_flee_fail + " " + opportunity_text_victim + " " + atk_msg_victim)
                    
                    # To the aimer (attacker_char)
                    if aimer_msg_flee_fail: # Aimer saw the flee attempt (aimer_msg_flee_fail is plain)
                        aimer_locking_caller.msg(f"|r{aimer_msg_flee_fail}|n {opportunity_text_attacker} {atk_msg_attacker}")
                    else: # Aimer might not have seen the flee attempt
                        aimer_locking_caller.msg(f"|rYou maintain your aim on {target_char.get_display_name(aimer_locking_caller)} as they falter, and press the attack!|n {opportunity_text_attacker} {atk_msg_attacker}")
                    
                    # To room observers
                    observer_flee_fail_prefix = f"{caller.key} tries to break free from {aimer_locking_caller.key}'s aim but is kept pinned."
                    observer_opportunity_text = f"{aimer_locking_caller.key} seizes the opportunity!"
                    room_observer_msg = f"|r{observer_flee_fail_prefix} {observer_opportunity_text}|n {atk_msg_observer}"
                    caller.location.msg_contents(room_observer_msg, exclude=[caller, aimer_locking_caller])

                    # 4. Ensure combat handler is active
                    if not final_handler.is_active:
                        final_handler.start()
                    
                    return # Failed to break aim, attack was initiated. Flee command ends here.
        else: # Not being aimed at initially
            aim_successfully_broken = True # Effectively, no aim to break

        # --- Part 2: Attempt to flee from combat handler (if present and aim is not an issue) ---
        fled_combat_successfully = False
        if handler:
            if not aim_successfully_broken: # Should have returned if aim break failed
                # This case implies they were aimed at, and failed to break it.
                caller.msg(f"You must first break free from {getattr(caller.ndb, 'aimed_at_by', 'someone').get_display_name(caller)}'s aim to flee combat.")
                return

            splattercast.msg(f"FLEE_CMD: {caller.key} in handler {handler.key}, attempting combat flee.")
            caller_combat_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
            if not caller_combat_entry:
                caller.msg("|rError: Your combat entry is missing. Please report to an admin.|n")
                splattercast.msg(f"CRITICAL_FLEE: {caller.key} has combat_handler but no entry in {handler.key}")
                return

            if caller_combat_entry.get("grappled_by"):
                grappler = caller_combat_entry.get("grappled_by")
                caller.msg(f"You cannot flee while {grappler.key if grappler else 'someone'} is grappling you! Try 'escape' or 'resist'.|n")
                splattercast.msg(f"{caller.key} tried to flee while grappled by {grappler.key if grappler else 'Unknown'}. Flee blocked.")
                return

            attackers = [e["char"] for e in handler.db.combatants if e.get("target") == caller and e["char"] != caller and e["char"]]
            
            if not attackers:
                caller.msg("No one is actively attacking you in combat; you disengage.")
                splattercast.msg(f"{caller.key} flees combat unopposed (handler {handler.key}).")
                fled_combat_successfully = True
            else:
                flee_roll = randint(1, getattr(caller, "motorics", 1))
                valid_attackers = [att for att in attackers if hasattr(att, "motorics")]
                if not valid_attackers:
                    caller.msg("Your attackers seem unable to stop you; you disengage.")
                    splattercast.msg(f"{caller.key} flees combat, attackers unable to resist (handler {handler.key}).")
                    fled_combat_successfully = True
                else:
                    resist_rolls = [(attacker, randint(1, getattr(attacker, "motorics", 1))) for attacker in valid_attackers]
                    highest_attacker, highest_resist = max(resist_rolls, key=lambda x: x[1])

                    splattercast.msg(f"{caller.key} attempts to flee combat: {flee_roll} vs highest resist {highest_resist} ({highest_attacker.key})")
                    if flee_roll > highest_resist:
                        caller.msg("|gYou successfully flee from combat!|n")
                        splattercast.msg(f"{caller.key} flees successfully from combat (handler {handler.key}).")
                        fled_combat_successfully = True
                    else:
                        caller.msg("|rYou try to flee from combat, but fail!|n")
                        splattercast.msg(f"{caller.key} tries to flee combat but fails (handler {handler.key}).")
                        caller.location.msg_contents(f"{caller.key} tries to flee combat but fails.", exclude=caller)
                        caller.ndb.skip_combat_round = True 
                        return # Failed combat flee, stop here.
            
            if fled_combat_successfully:
                if handler.pk and handler.db: 
                    handler.remove_combatant(caller)
                else: 
                    splattercast.msg(f"CmdFlee: Handler for {caller.key} was already gone before remove_combatant call.")
                    if hasattr(caller.ndb, "combat_handler"): del caller.ndb.combat_handler

                if handler.pk and handler.db: 
                    if len(handler.db.combatants) <= 1:
                        splattercast.msg(f"CmdFlee: {caller.key} fled. Remaining combatants: {len(handler.db.combatants)}. Calling stop_combat_logic.")
                        handler.stop_combat_logic(cleanup_combatants=True)
                else:
                    splattercast.msg(f"CmdFlee: {caller.key} fled. Handler {handler.key if handler else 'Unknown'} seems to have been deleted.")
        
        # --- Part 3: Perform movement if any flee condition allows it ---
        # Move if:
        #   1. Aim was successfully broken AND caller is NOT in a combat handler.
        #   2. OR Fled combat successfully (which implies aim was already broken or not an issue).
        
        should_move_room = False
        if aim_successfully_broken and not handler: # Broke aim, was not in combat
            should_move_room = True
        elif fled_combat_successfully: # Fled combat (aim must have been broken or not an issue)
            should_move_room = True
        
        if should_move_room:
            exits = [ex for ex in caller.location.exits if ex.access(caller, 'traverse')]
            if exits:
                chosen_exit = choice(exits)
                
                flee_message_verb = "flees"
                if aim_successfully_broken and not fled_combat_successfully and not handler: # Only broke aim
                    flee_message_verb = "breaks free and flees"
                
                caller.location.msg_contents(f"{caller.key} {flee_message_verb} {chosen_exit.key}.", exclude=caller)
                caller.msg(f"You {flee_message_verb} {chosen_exit.key}.")
                chosen_exit.at_traverse(caller, chosen_exit.destination) # This will also clear aim on the caller if they were aiming
            else:
                # Tailor message based on context
                if fled_combat_successfully:
                    caller.msg("You flee from combat, but there's nowhere to go!")
                elif aim_successfully_broken:
                     caller.msg("You break free from the aim, but there's nowhere to go!")
                # else: this case should not be hit if logic is correct
        # If not should_move_room, it means a flee attempt failed and returned, or no flee was needed initially.


class CmdDisarm(Command):
    """
    Attempt to disarm your current combat target, sending their weapon (or held item) to the ground.

    Usage:
        disarm

    You must be in combat and have a valid target.
    The command will prioritize disarming weapons, but will disarm any held item if no weapon is found.
    """

    key = "disarm"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        handler = getattr(caller.ndb, "combat_handler", None)
        if not handler:
            caller.msg("You are not in combat.")
            splattercast.msg(f"{caller.key} tried to disarm but is not in combat.")
            return

        target = handler.get_target(caller)
        if not target:
            caller.msg("You have no valid target to disarm.")
            splattercast.msg(f"{caller.key} tried to disarm but has no valid target.")
            return

        hands = getattr(target, "hands", {})
        if not hands:
            caller.msg(f"{target.key} has nothing in their hands to disarm.")
            splattercast.msg(f"{caller.key} tried to disarm {target.key}, but they have nothing in their hands.")
            return

        # Grit vs Grit check
        attacker_grit = getattr(caller, "grit", 1)
        defender_grit = getattr(target, "grit", 1)
        disarm_roll = randint(1, max(1, attacker_grit))
        resist_roll = randint(1, max(1, defender_grit))
        splattercast.msg(
            f"{caller.key} attempts to disarm {target.key}: {disarm_roll} (grit) vs {resist_roll} (grit)"
        )

        if disarm_roll < resist_roll:
            caller.msg(f"You try to disarm {target.key}, but they resist!")
            target.msg(f"{caller.key} tried to disarm you, but you resisted!")
            splattercast.msg(f"{caller.key} failed to disarm {target.key}.")
            return

        # Prioritize weapon-type items
        weapon_hand = None
        for hand, item in hands.items():
            if item and hasattr(item.db, "weapon_type") and item.db.weapon_type:
                weapon_hand = hand
                break

        # If no weapon, disarm any held item
        if not weapon_hand:
            for hand, item in hands.items():
                if item:
                    weapon_hand = hand
                    break

        if not weapon_hand:
            caller.msg(f"{target.key} has nothing to disarm.")
            splattercast.msg(f"{caller.key} tried to disarm {target.key}, but nothing was found.")
            return

        item = hands[weapon_hand]
        # Remove from hand and move to ground
        hands[weapon_hand] = None
        item.move_to(target.location, quiet=True)
        caller.msg(f"You disarm {target.key}, sending {item.key} to the ground!")
        target.msg(f"{caller.key} disarms you! {item.key} falls to the ground.")
        target.location.msg_contents(
            f"{caller.key} disarms {target.key}, and {item.key} falls to the ground.",
            exclude=[caller, target]
        )
        splattercast.msg(f"{caller.key} disarmed {target.key} ({item.key}) in {target.location.key}.")


class CmdGrapple(Command):
    """
    Attempt to grapple a target in your current room.

    Usage:
        grapple <target>

    If you are not in combat, this will initiate combat.
    If successful, you will be grappling the target, and they will be grappled by you.
    """
    key = "grapple"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        if not self.args:
            caller.msg("Grapple whom?")
            return

        # --- Target searching (similar to CmdAttack) ---
        search_name = self.args.strip().lower()
        candidates = caller.location.contents
        matches = [
            obj for obj in candidates
            if search_name in obj.key.lower()
            or any(search_name in alias.lower() for alias in (obj.aliases.all() if hasattr(obj.aliases, "all") else []))
        ]

        if not matches:
            caller.msg("No valid target found to grapple.")
            splattercast.msg(
                f"{caller.key} tried to grapple '{search_name}' but found no valid target in the room."
            )
            return

        target = matches[0]

        if target == caller:
            caller.msg("You can't grapple yourself.")
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg("That can't be grappled.")
            splattercast.msg(
                f"{caller.key} tried to grapple {target.key}, but it's not a valid character."
            )
            return

        # --- Get or create combat handler ---
        handler = get_or_create_combat(caller.location)
        if not handler:
            caller.msg("Error: Could not find or create combat handler.") # Should be rare
            return

        # --- Add caller and target to combat if not already in ---
        # Record if the caller initiated combat with this action
        caller_initiated_combat_this_action = not any(e["char"] == caller for e in handler.db.combatants)

        caller_is_in_combat = any(e["char"] == caller for e in handler.db.combatants)
        target_is_in_combat = any(e["char"] == target for e in handler.db.combatants) # 'target' is the grapple victim

        if not caller_is_in_combat:
            splattercast.msg(f"{caller.key} is initiating grapple combat with {target.key}.")
            handler.add_combatant(caller) 
            handler.add_combatant(target) 
        elif not target_is_in_combat: 
            splattercast.msg(f"{caller.key} (in combat) is attempting to grapple {target.key} (adding to combat).")
            handler.add_combatant(target)
        
        # --- Now retrieve combat entries; they should exist ---
        caller_combat_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        target_combat_entry = next((e for e in handler.db.combatants if e["char"] == target), None)

        if not caller_combat_entry: 
            caller.msg("There was an issue adding you to combat. Please try again.")
            splattercast.msg(f"CRITICAL: {caller.key} failed to be added to combat by CmdGrapple.")
            return
        if not target_combat_entry: 
            caller.msg(f"There was an issue adding {target.key} to combat. Please try again.")
            splattercast.msg(f"CRITICAL: {target.key} failed to be added to combat by CmdGrapple.")
            return

        # Default to not yielding if already in combat or grapple fails.
        # This will be overridden if grapple is successful AND initiated combat.
        caller_combat_entry["is_yielding"] = False 

        # --- Grapple-specific checks (already grappling, being grappled, target grappled) ---
        if caller_combat_entry.get("grappling"):
            caller.msg(f"You are already grappling {caller_combat_entry['grappling'].key}. You must release them first.")
            splattercast.msg(f"{caller.key} tried to grapple {target.key} while already grappling {caller_combat_entry['grappling'].key}.")
            return
        
        if caller_combat_entry.get("grappled_by"):
            caller.msg(f"You cannot initiate a grapple while {caller_combat_entry['grappled_by'].key} is grappling you. Try to escape first.")
            splattercast.msg(f"{caller.key} tried to grapple {target.key} while being grappled by {caller_combat_entry['grappled_by'].key}.")
            return

        if target_combat_entry.get("grappled_by"):
            # Check if it's the caller grappling them (should be caught above, but good for clarity)
            # Or if someone *else* is grappling them
            if target_combat_entry["grappled_by"] != caller:
                 caller.msg(f"{target.key} is already being grappled by {target_combat_entry['grappled_by'].key}.")
                 splattercast.msg(f"{caller.key} tried to grapple {target.key}, but they are already grappled by {target_combat_entry['grappled_by'].key}.")
                 return
        
        # --- Set combat action ---
        # Ensure combat_action key exists for the entry
        if "combat_action" not in caller_combat_entry:
            caller_combat_entry["combat_action"] = {}
            
        # Store the flag for the handler to check upon successful grapple
        caller_combat_entry["combat_action"] = {
            "type": "grapple", 
            "target": target,
            "initiated_combat": caller_initiated_combat_this_action 
        }
        caller.msg(f"You prepare to grapple {target.key}...")
        splattercast.msg(f"{caller.key} sets combat action to grapple {target.key} (initiated_combat: {caller_initiated_combat_this_action}).")
        # The combat handler will process this on the character's turn


class CmdEscapeGrapple(Command):
    """
    Attempts to escape from a grapple.

    Usage:
      escape
      resist

    This command allows a character to attempt to break free if they
    are currently being grappled by another character in combat.
    """
    key = "escape"
    aliases = ["resist"]
    help_category = "Combat"
    locks = "cmd:in_combat()" # Ensure character is in combat

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        # Get the combat handler from the caller's NDB.
        # The cmd:in_combat() lock should ensure this is set if they are in combat.
        handler = getattr(caller.ndb, "combat_handler", None) 
        
        if not handler:
            # This message should ideally not be reached if the in_combat lock is effective.
            caller.msg("You are not in combat.") 
            splattercast.msg(f"{caller.key} tried to escape, but no combat_handler found in ndb (check cmd:in_combat() lock).")
            return

        # Find the caller's entry in the combat handler
        caller_combat_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)

        if not caller_combat_entry:
            caller.msg("You are not properly registered in the current combat.")
            splattercast.msg(f"{caller.key} tried to escape, but not found in combatants list of handler {handler.key}.")
            return

        grappler = caller_combat_entry.get("grappled_by")

        if not grappler:
            caller.msg("You are not currently being grappled by anyone.")
            splattercast.msg(f"{caller.key} tried to escape, but is not grappled.")
            return

        # Set the combat action in the handler's list for the caller
        caller_combat_entry["combat_action"] = {"type": "escape"}
        caller.msg(f"You prepare to escape from {grappler.key}'s grasp...")
        splattercast.msg(f"{caller.key} sets combat action to escape from {grappler.key} (via handler {handler.key}).")
        # The combat handler will process this on the character's turn


class CmdReleaseGrapple(Command):
    """
    Release a target you are currently grappling.

    Usage:
        release
        release grapple

    You must be grappling someone to use this command.
    """
    key = "release"
    aliases = ["release grapple"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        handler = getattr(caller.ndb, "combat_handler", None)
        if not handler:
            caller.msg("You are not in combat.")
            splattercast.msg(f"{caller.key} tried to release grapple but is not in combat.")
            return

        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry or not caller_entry.get("grappling"):
            caller.msg("You are not currently grappling anyone.")
            splattercast.msg(f"{caller.key} tried to release grapple but is not grappling anyone.")
            return
            
        grappled_victim = caller_entry["grappling"]
        caller_entry["combat_action"] = {"type": "release_grapple"} 
        caller.msg(f"You prepare to release {grappled_victim.key}...")
        splattercast.msg(f"{caller.key} sets combat action to release grapple on {grappled_victim.key}.")
        # The combat handler will process this


class CmdStop(Command):
    """
    Stop a specific action, such as aiming or attacking.

    Usage:
        stop aiming
        stop attacking

    'stop aiming' will cease any current aiming.
    'stop attacking' will cause you to yield in combat.
    """

    key = "stop"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        if args == "aiming":
            self._stop_aiming(caller, splattercast)
        elif args == "attacking":
            self._stop_attacking(caller, splattercast)
        else:
            caller.msg("Stop what? You can 'stop aiming' or 'stop attacking'.")

    def _stop_aiming(self, caller, splattercast):
        """Helper function to handle stopping aim."""
        action_taken_aiming = False
        if hasattr(caller, "clear_aim_state"):
            if hasattr(caller.ndb, "aiming_at") or hasattr(caller.ndb, "aiming_direction"):
                action_taken_aiming = caller.clear_aim_state(reason_for_clearing="as you stop aiming")
                if action_taken_aiming: # clear_aim_state gives its own message
                    splattercast.msg(f"STOP_CMD: {caller.key} stopped aiming.")
            else:
                caller.msg("You are not currently aiming at anything.")
        else:
            caller.msg("|rError: Cannot process 'stop aiming'. Character is missing 'clear_aim_state' method.|n")
            splattercast.msg(f"CRITICAL_STOP_AIMING: {caller.key} lacks 'clear_aim_state' method.")

    def _stop_attacking(self, caller, splattercast):
        """Helper function to handle stopping attacks (yielding)."""
        handler = getattr(caller.ndb, "combat_handler", None)
        if not handler:
            caller.msg("You are not in combat to stop attacking.")
            return

        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry:
            caller.msg("You are not properly registered in the current combat.")
            splattercast.msg(f"STOP_ATTACKING_WARNING: {caller.key} has combat_handler but no entry in {handler.key}.")
            return

        if not caller_entry.get("is_yielding"):
            caller_entry["is_yielding"] = True
            caller_entry["target"] = None # Explicitly clear their offensive target
            
            msg_room = f"{caller.key} lowers their guard, appearing to yield."
            caller.location.msg_contents(f"|y{msg_room}|n", exclude=[caller])
            caller.msg("|gYou lower your guard and will not actively attack (you are now yielding).|n")
            splattercast.msg(f"STOP_ATTACKING: {caller.key} is now yielding. Their target has been cleared.")
        else:
            caller.msg("You are already yielding (not actively attacking).")


class CmdAim(Command):
    """
    Aim in a direction or at a character.

    Usage:
        aim <direction or character>
        aim at <character or direction>
        aim stop  (or aim with no args to stop aiming)

    Aiming in a direction allows you to use look and attack/kill as though you were in the room.
    Aiming at a character locks them in place, preventing them from traversing exits unless they successfully flee.
    """

    key = "aim"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        raw_args = self.args.strip()

        # Handle "aim stop" or "aim" with no args to stop aiming
        if not raw_args or raw_args.lower() == "stop":
            if hasattr(caller, "clear_aim_state"):
                action_taken = caller.clear_aim_state(reason_for_clearing="as you stop aiming")
                if not action_taken: 
                    caller.msg("You are not aiming at anything or in any direction. To aim, use 'aim <target/direction>'.")
            else:
                caller.msg("|rError: Cannot process stop aim command. Character is missing 'clear_aim_state' method.|n")
                splattercast.msg(f"CRITICAL_AIM_STOP (via CmdAim): {caller.key} lacks 'clear_aim_state' method.")
            return

        search_term = raw_args.lower()
        if search_term.startswith("at "):
            search_term = search_term[3:].strip() 
            if not search_term:
                caller.msg("Aim at whom or in what direction?")
                return
        
        # Clear any previous aim state before setting a new one.
        if hasattr(caller, "clear_aim_state"):
            # The reason "as you aim anew" will be used if something was cleared.
            caller.clear_aim_state(reason_for_clearing="as you aim anew") 
        else:
            # This would be a problem, as old aim state might persist.
            splattercast.msg(f"AIM_WARNING: {caller.key} lacks clear_aim_state method, cannot clear old aim before setting new in CmdAim.")

        # 1. Attempt to aim at a character
        target_character_result = caller.search(search_term, typeclass="typeclasses.characters.Character", quiet=True)
        target_character = None # Initialize target_character

        if isinstance(target_character_result, list):
            if target_character_result: # If the list is not empty
                target_character = target_character_result[0] # Take the first match
        else: # If search returned a single object or None
            target_character = target_character_result


        if target_character:
            if target_character == caller:
                caller.msg("You can't aim at yourself.")
                return

            caller.ndb.aiming_at = target_character
            target_character.ndb.aimed_at_by = caller
            
            caller.msg(f"You take careful aim at {target_character.get_display_name(caller)}.")
            target_character.msg(f"|r{caller.get_display_name(target_character)} takes careful aim at you! You are locked in place.|n")
            
            room_message = f"{caller.get_display_name(caller.location)} takes careful aim at {target_character.get_display_name(caller.location)}."
            caller.location.msg_contents(room_message, exclude=[caller, target_character])
            splattercast.msg(f"AIM: {caller.key} is now aiming at character {target_character.key}.")
            return

        # 2. If not a character, attempt to aim in a direction
        found_exit = None
        for ex in caller.location.exits:
            exit_aliases_lower = [alias.lower() for alias in ex.aliases.all()] if hasattr(ex.aliases, 'all') else []
            if ex.key.lower() == search_term or search_term in exit_aliases_lower:
                found_exit = ex
                break
        
        if found_exit:
            caller.ndb.aiming_direction = found_exit.key 
            
            # Get weapon details
            hands = getattr(caller, "hands", {})
            weapon = next((item for hand, item in hands.items() if item), None)
            
            if weapon:
                caller_msg_text = f"You aim your {weapon.key} towards the {found_exit.key}."
                room_msg_text = f"{caller.get_display_name(caller.location)} aims their {weapon.key} towards the {found_exit.key}."
            else:
                caller_msg_text = f"You fix your gaze towards the {found_exit.key}."
                room_msg_text = f"{caller.get_display_name(caller.location)} fixes their gaze towards the {found_exit.key}."

            caller.msg(caller_msg_text)
            caller.location.msg_contents(room_msg_text, exclude=[caller])
            splattercast.msg(f"AIM: {caller.key} is now aiming in direction {found_exit.key} {'with ' + weapon.key if weapon else 'unarmed'}.")
            return

        # 3. If neither character nor direction found
        caller.msg(f"You can't aim at '{raw_args}'. It's not a character present here or a clear direction you can aim towards.")
        splattercast.msg(f"AIM_FAIL: {caller.key} tried to aim at '{raw_args}', no valid character or direction found.")


class CmdLook(Command):
    """
    Look around or at a specific object/character or in a direction.

    Usage:
        look
        look <object or character>
        look <direction>

    Allows you to look around the room or at a specific object or direction.
    If aiming at a character:
        'look' will show a detailed view of the character you are aiming at.
        'look <target>' will look at <target> in your current room, without breaking your aim.
    If aiming in a direction:
        'look' will show the room you are aiming into (description and characters).
        'look <object>' will try to find and describe the object in the room you are aiming into.
    If not aiming, 'look <direction>' will show the characters present in the room in that direction.
    """

    key = "look"
    locks = "cmd:all()"

    def _show_characters_in_room(self, caller, room, prefix_message="You also see"):
        if not room or not hasattr(room, "contents"):
            return

        characters_in_room = [
            char.get_display_name(caller) 
            for char in room.contents 
            if inherits_from(char, "typeclasses.characters.Character") and char != caller
        ]
        if characters_in_room:
            # Ensure the message ends with a period if not already.
            suffix = " here." if not prefix_message.endswith(".") else ""
            caller.msg(f"{prefix_message} {', '.join(characters_in_room)}{suffix}")


    def func(self):
        caller = self.caller
        args = self.args.strip()
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        # --- 1. Handle 'look' while AIMING AT A CHARACTER ---
        aiming_at_char = getattr(caller.ndb, "aiming_at", None)
        if aiming_at_char:
            splattercast.msg(f"LOOK: {caller.key} is aiming at character {aiming_at_char.key}.")
            if not args:
                caller.msg(f"You focus your gaze on {aiming_at_char.get_display_name(caller)} (aimed)...")
                caller.msg(aiming_at_char.return_appearance(caller))
                splattercast.msg(f"LOOK: {caller.key} looked at aimed character {aiming_at_char.key}.")
                return
            else:
                target_in_current_room_result = caller.search(args, quiet=True)
                target_in_current_room = None
                if isinstance(target_in_current_room_result, list):
                    if target_in_current_room_result:
                        target_in_current_room = target_in_current_room_result[0]
                else:
                    target_in_current_room = target_in_current_room_result
                
                if target_in_current_room:
                    if target_in_current_room == aiming_at_char:
                         caller.msg(f"You continue to focus on {aiming_at_char.get_display_name(caller)} (aimed)...")
                    else:
                        caller.msg(f"While still aiming at {aiming_at_char.get_display_name(caller)}, you look at {target_in_current_room.get_display_name(caller)}...")
                    caller.msg(target_in_current_room.return_appearance(caller))
                    splattercast.msg(f"LOOK: {caller.key} (aiming at {aiming_at_char.key}) looked at {target_in_current_room.key} in current room.")
                else:
                    caller.msg(f"While aiming at {aiming_at_char.get_display_name(caller)}, you don't see '{args}' here.")
                    splattercast.msg(f"LOOK: {caller.key} (aiming at {aiming_at_char.key}) failed to find '{args}' in current room.")
                return

        # --- 2. Handle 'look' while AIMING IN A DIRECTION ---
        aiming_direction_name = getattr(caller.ndb, "aiming_direction", None)
        if aiming_direction_name:
            splattercast.msg(f"LOOK: {caller.key} is aiming {aiming_direction_name}, attempting remote look.")
            
            exit_obj = None
            for ex in caller.location.exits:
                exit_aliases_lower = [alias.lower() for alias in ex.aliases.all()] if ex.aliases and hasattr(ex.aliases, 'all') else []
                if ex.key.lower() == aiming_direction_name.lower() or aiming_direction_name.lower() in exit_aliases_lower:
                    exit_obj = ex
                    break
            
            if not exit_obj or not exit_obj.destination:
                caller.msg(f"You aim in the {aiming_direction_name} direction, but there's no clear path or view that way.")
                splattercast.msg(f"LOOK: {caller.key} tried to look via aiming {aiming_direction_name}, but no valid exit/destination found.")
                if not args: return 
            else:
                remote_room = exit_obj.destination
                if not args: 
                    caller.msg(f"You peer into the {aiming_direction_name} direction, towards {remote_room.get_display_name(caller)}...")
                    caller.msg(remote_room.return_appearance(caller))
                    splattercast.msg(f"LOOK: {caller.key} successfully looked into {remote_room.key} via aiming {aiming_direction_name}.")
                    return
                else: 
                    caller.msg(f"You peer into the {aiming_direction_name} direction (towards {remote_room.get_display_name(caller)}) and look for '{args}'...")
                    
                    target_in_remote_room_result = caller.search(args, location=remote_room, quiet=True)
                    target_in_remote_room = None
                    if isinstance(target_in_remote_room_result, list):
                        if target_in_remote_room_result: 
                            target_in_remote_room = target_in_remote_room_result[0]
                    else: 
                        target_in_remote_room = target_in_remote_room_result
                                        
                    if target_in_remote_room:
                        caller.msg(target_in_remote_room.return_appearance(caller))
                        splattercast.msg(f"LOOK: {caller.key} successfully looked at {target_in_remote_room.key} in remote room {remote_room.key} via aiming.")
                    else:
                        caller.msg(f"You don't see '{args}' clearly in the {aiming_direction_name} direction (in {remote_room.get_display_name(caller)}).")
                        splattercast.msg(f"LOOK: {caller.key} tried to look at '{args}' in remote room {remote_room.key} via aiming, but not found.")
                    return

        # --- 3. Handle 'look <args>' (when NOT aiming, or aiming look failed and fell through) ---
        if args:
            possible_exit_obj = None
            for ex in caller.location.exits:
                exit_aliases_lower = [alias.lower() for alias in ex.aliases.all()] if ex.aliases and hasattr(ex.aliases, 'all') else []
                if args.lower() == ex.key.lower() or args.lower() in exit_aliases_lower:
                    possible_exit_obj = ex
                    break
            
            if possible_exit_obj and possible_exit_obj.destination:
                remote_room = possible_exit_obj.destination
                caller.msg(f"You look {possible_exit_obj.key} (towards {remote_room.get_display_name(caller)})...")
                self._show_characters_in_room(caller, remote_room, f"Looking {possible_exit_obj.key}, you also see")
                splattercast.msg(f"LOOK: {caller.key} looked into direction {possible_exit_obj.key} at {remote_room.key}.")
                return
            else:
                target_result = caller.search(args) 
                target = None
                if isinstance(target_result, list):
                    if target_result:
                        target = target_result[0]
                else:
                    target = target_result

                if target:
                    caller.msg(target.return_appearance(caller))
                return 
        
        # --- 4. Handle plain 'look' (no args, not aiming at char, not aiming directionally) ---
        else: 
            caller.msg(caller.location.return_appearance(caller))
            return
