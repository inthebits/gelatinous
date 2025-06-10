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
    Attack validity depends on weapon type and proximity to target.
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

        # --- WEAPON IDENTIFICATION (early) ---
        hands = getattr(caller, "hands", {})
        weapon_obj = next((item for hand, item in hands.items() if item), None)
        is_ranged_weapon = weapon_obj and hasattr(weapon_obj.db, "is_ranged") and weapon_obj.db.is_ranged
        weapon_name_for_msg = weapon_obj.key if weapon_obj else "your fists"
        weapon_type_for_msg = (str(weapon_obj.db.weapon_type).lower() if weapon_obj and hasattr(weapon_obj.db, "weapon_type") and weapon_obj.db.weapon_type else "unarmed")
        # --- END WEAPON IDENTIFICATION ---

        target_room = caller.location
        target_search_name = args

        # --- AIMING DIRECTION ATTACK ---
        aiming_direction = getattr(caller.ndb, "aiming_direction", None)
        if aiming_direction:
            splattercast.msg(f"ATTACK_CMD: {caller.key} is aiming {aiming_direction}, attempting remote attack on '{args}'.")
            
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

        # --- PROXIMITY AND WEAPON VALIDATION ---
        # Initialize caller's proximity NDB if missing (failsafe)
        if not hasattr(caller.ndb, "in_proximity_with") or not isinstance(caller.ndb.in_proximity_with, set):
            caller.ndb.in_proximity_with = set()
            splattercast.msg(f"ATTACK_CMD_FAILSAFE: Initialized in_proximity_with for {caller.key}.")

        if not aiming_direction: # SAME ROOM ATTACK
            splattercast.msg(f"ATTACK_CMD: Validating same-room attack by {caller.key} on {target.key}.")
            is_in_melee_proximity = target in caller.ndb.in_proximity_with

            if is_in_melee_proximity: # Caller is in melee with target
                if is_ranged_weapon:
                    caller.msg(f"You can't effectively use your {weapon_name_for_msg} while locked in melee with {target.get_display_name(caller)}!")
                    splattercast.msg(f"ATTACK_CMD_INVALID: {caller.key} tried to use ranged weapon '{weapon_name_for_msg}' on {target.key} while in melee proximity. Attack aborted.")
                    return
                splattercast.msg(f"ATTACK_CMD_VALID: {caller.key} attacking {target.key} with non-ranged '{weapon_name_for_msg}' while in melee proximity.")
            else: # Caller is NOT in melee with target (at range in same room)
                if not is_ranged_weapon:
                    caller.msg(f"You are too far away to hit {target.get_display_name(caller)} with your {weapon_name_for_msg}. Try advancing or charging.")
                    splattercast.msg(f"ATTACK_CMD_INVALID: {caller.key} tried to use non-ranged weapon '{weapon_name_for_msg}' on {target.key} who is not in melee proximity. Attack aborted.")
                    return
                splattercast.msg(f"ATTACK_CMD_VALID: {caller.key} attacking {target.key} with ranged weapon '{weapon_name_for_msg}' from distance in same room.")
        else: # ADJACENT ROOM ATTACK (aiming_direction is set)
            splattercast.msg(f"ATTACK_CMD: Validating ranged attack into {target_room.key} by {caller.key} on {target.key}.")
            if not is_ranged_weapon:
                caller.msg(f"You need a ranged weapon to attack {target.get_display_name(caller)} in the {aiming_direction} direction.")
                splattercast.msg(f"ATTACK_CMD_INVALID: {caller.key} tried to attack into {aiming_direction} (target: {target.key}) without a ranged weapon ({weapon_name_for_msg}). Attack aborted.")
                return
            splattercast.msg(f"ATTACK_CMD_VALID: {caller.key} attacking into {aiming_direction} with ranged weapon '{weapon_name_for_msg}'.")
        # --- END PROXIMITY AND WEAPON VALIDATION ---

        # --- Get/Create/Merge Combat Handlers ---
        caller_handler = get_or_create_combat(caller.location)
        target_handler = get_or_create_combat(target.location) # Might be the same if target_room is caller.location

        final_handler = caller_handler
        if caller_handler != target_handler:
            splattercast.msg(f"ATTACK_CMD: Cross-handler engagement! Caller's handler: {caller_handler.key} (on {caller_handler.obj.key}). Target's handler: {target_handler.key} (on {target_handler.obj.key}). Merging...")
            caller_handler.merge_handler(target_handler)
            splattercast.msg(f"ATTACK_CMD: Merge complete. Final handler is {final_handler.key}, now managing rooms: {[r.key for r in final_handler.db.managed_rooms]}.")
        else:
            splattercast.msg(f"ATTACK_CMD: Caller and target are (or will be) in the same handler zone: {final_handler.key} (on {final_handler.obj.key}).")
            final_handler.enroll_room(caller.location)
            final_handler.enroll_room(target.location)

        # --- CAPTURE PRE-ADDITION COMBAT STATE ---
        caller_was_in_final_handler = any(e["char"] == caller for e in final_handler.db.combatants)
        target_was_in_final_handler = any(e["char"] == target for e in final_handler.db.combatants)
        
        original_caller_target_in_handler = None
        if caller_was_in_final_handler:
            caller_entry_snapshot = next((e for e in final_handler.db.combatants if e["char"] == caller), None)
            if caller_entry_snapshot:
                original_caller_target_in_handler = caller_entry_snapshot.get("target")

        # --- Add combatants to the final_handler ---
        if not caller_was_in_final_handler:
            final_handler.add_combatant(caller, target=target)
        else: 
            caller_entry = next((e for e in final_handler.db.combatants if e["char"] == caller), None)
            if caller_entry: # Ensure entry exists
                caller_entry["target"] = target # This command updates the target
                caller_entry["is_yielding"] = False

        if not target_was_in_final_handler:
            final_handler.add_combatant(target, target=caller) 
        else: 
            target_entry = next((e for e in final_handler.db.combatants if e["char"] == target), None)
            if target_entry: # Ensure entry exists
                if not target_entry.get("target"): 
                     target_entry["target"] = caller
                # Do not automatically un-yield target if they were already yielding.
                # target_entry["is_yielding"] = False 

        # --- Messaging and Action ---
        if aiming_direction:
            # --- Attacking into an adjacent room ---
            splattercast.msg(f"ATTACK_CMD: Aiming direction attack by {caller.key} towards {aiming_direction} into {target_room.key} at {target.key}.")

            # --- ADDITIONAL AIMING DIRECTION LOGIC ---
            initiate_msg_obj = get_combat_message(weapon_type_for_msg, "initiate", attacker=caller, target=target, item=weapon_obj)
            
            std_attacker_initiate = ""
            std_victim_initiate = ""
            std_observer_initiate = ""

            if isinstance(initiate_msg_obj, dict):
                std_attacker_initiate = initiate_msg_obj.get("attacker_msg", f"You prepare to strike {target.key}!")
                std_victim_initiate = initiate_msg_obj.get("victim_msg", f"{caller.key} prepares to strike you!")
                std_observer_initiate = initiate_msg_obj.get("observer_msg", f"{caller.key} prepares to strike {target.key}!")
            elif isinstance(initiate_msg_obj, str): # Fallback if get_combat_message returns a single string for initiate
                splattercast.msg(f"CmdAttack (aiming): initiate_msg_obj for {weapon_type_for_msg} was a string. Using generic attacker/victim messages. String: {initiate_msg_obj}")
                std_observer_initiate = initiate_msg_obj
                std_attacker_initiate = f"You prepare to strike {target.key} with your {weapon_type_for_msg}!"
                std_victim_initiate = f"{caller.key} prepares to strike you with their {weapon_type_for_msg}!"
            else: # Unexpected type
                splattercast.msg(f"CmdAttack (aiming): Unexpected initiate_msg_obj type from get_combat_message for {weapon_type_for_msg}: {type(initiate_msg_obj)}. Content: {initiate_msg_obj}")
                std_attacker_initiate = f"You initiate an attack on {target.key}."
                std_victim_initiate = f"{caller.key} initiates an attack on you."
                std_observer_initiate = f"{caller.key} initiates an attack on {target.key}."

            # 2. Determine the direction from which the attack arrives in the target's room
            attacker_direction_from_target_perspective = "a nearby location" # Default
            exit_from_target_to_caller_room = None
            for ex_obj in target_room.exits:
                if ex_obj.destination == caller.location:
                    exit_from_target_to_caller_room = ex_obj
                    break
            if exit_from_target_to_caller_room:
                attacker_direction_from_target_perspective = exit_from_target_to_caller_room.key

            # 3. Construct and send messages (using |r for normal red)

            # Attacker's message
            prefix_attacker = f"|RAiming {aiming_direction} into {target_room.get_display_name(caller)}, "
            caller.msg(prefix_attacker + std_attacker_initiate)

            # Victim's message (in target_room)
            prefix_victim = f"|RSuddenly, you notice {caller.get_display_name(target)} to the {attacker_direction_from_target_perspective} aiming at you from {caller.location.get_display_name(target)}), "
            target.msg(prefix_victim + std_victim_initiate)

            # Observer message in caller's room (attacker's room)
            prefix_observer_caller_room = f"|R{caller.key} takes aim {aiming_direction} into {target_room.get_display_name(caller.location)}, "
            caller.location.msg_contents(prefix_observer_caller_room + std_observer_initiate, exclude=[caller])

            # Observer message in target's room
            prefix_observer_target_room = f"|RYour attention is drawn to the {attacker_direction_from_target_perspective} as {caller.key} aiming from {caller.location.get_display_name(target_room)}, "
            target_room.msg_contents(prefix_observer_target_room + std_observer_initiate, exclude=[target])
            
        else:
            # Standard local attack initiation message (use get_combat_message)
            initiate_msg_obj = get_combat_message(weapon_type_for_msg, "initiate", attacker=caller, target=target, item=weapon_obj)
            
            final_initiate_str = ""
            if isinstance(initiate_msg_obj, dict):
                final_initiate_str = initiate_msg_obj.get("observer_msg")
                if not final_initiate_str:
                    splattercast.msg(f"CmdAttack: weapon_type {weapon_type_for_msg} initiate message was dict but missing 'observer_msg'. Dict: {initiate_msg_obj}")
                    final_initiate_str = f"{caller.key} begins an action against {target.key if target else 'someone'}."
            elif isinstance(initiate_msg_obj, str):
                final_initiate_str = initiate_msg_obj
            else:
                splattercast.msg(f"CmdAttack: Unexpected initiate_msg_obj type from get_combat_message for {weapon_type_for_msg}: {type(initiate_msg_obj)}. Content: {initiate_msg_obj}")
                final_initiate_str = f"{caller.key} initiates an attack on {target.key if target else 'someone'}."

            caller.location.msg_contents(final_initiate_str)

        splattercast.msg(f"ATTACK_CMD: {caller.key} attacks {target.key if target else 'a direction'}. Combat managed by {final_handler.key}.")
        
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

        # ADD THIS DEBUG LINE:
        splattercast.msg(f"FLEE_CMD_DEBUG ({caller.key}): handler='{handler.key if handler else None}', aimer_locking_caller='{aimer_locking_caller.key if aimer_locking_caller else None}'")

        # --- Pre-checks: Nothing to flee from? ---
        if not handler and not aimer_locking_caller:
            caller.msg("You have nothing to flee from.")
            # Optional: Add log here too if condition met
            splattercast.msg(f"FLEE_CMD_DEBUG ({caller.key}): 'Nothing to flee from' condition met.")
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
                    caller.msg(f"|gYou deftly break free from {aimer_locking_caller.get_display_name(caller)}'s aim!|n")
                    if aimer_locking_caller.access(caller, "view"): 
                        aimer_locking_caller.msg(f"|y{caller.get_display_name(aimer_locking_caller)} breaks free from your aim!|n")
                    
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
                    target_char = caller 

                    # 1. Get/Create Combat Handler 
                    final_handler = get_or_create_combat(attacker_char.location)
                    final_handler.enroll_room(attacker_char.location) 

                    # 2. Add/Update combatants
                    attacker_entry = next((e for e in final_handler.db.combatants if e["char"] == attacker_char), None)
                    if not attacker_entry:
                        final_handler.add_combatant(attacker_char, target=target_char)
                    else:
                        attacker_entry["target"] = target_char
                        attacker_entry["is_yielding"] = False 
                    
                    target_entry = next((e for e in final_handler.db.combatants if e["char"] == target_char), None)
                    if not target_entry:
                        final_handler.add_combatant(target_char, target=attacker_char) 
                    else:
                        if not target_entry.get("target"): 
                            target_entry["target"] = attacker_char
                        target_entry["is_yielding"] = False 

                    # 3. Messaging for the attack
                    hands = getattr(attacker_char, "hands", {})
                    weapon = next((item for hand, item in hands.items() if item), None)
                    weapon_type = (str(weapon.db.weapon_type).lower() if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type else "unarmed")
                    
                    initiate_msg_obj = get_combat_message(weapon_type, "initiate", attacker=attacker_char, target=target_char, item=weapon)
                    
                    atk_msg_attacker = initiate_msg_obj.get("attacker_msg", f"|RYou attack {target_char.get_display_name(attacker_char)}!|n") if isinstance(initiate_msg_obj, dict) else f"|RYou attack {target_char.get_display_name(attacker_char)} with your {weapon_type}!|n"
                    atk_msg_victim = initiate_msg_obj.get("victim_msg", f"|R{attacker_char.get_display_name(target_char)} attacks you!|n") if isinstance(initiate_msg_obj, dict) else f"|R{attacker_char.get_display_name(target_char)} attacks you with their {weapon_type}!|n"
                    atk_msg_observer = initiate_msg_obj.get("observer_msg", f"|R{attacker_char.get_display_name(attacker_char.location)} attacks {target_char.get_display_name(target_char.location)}!|n") if isinstance(initiate_msg_obj, dict) else f"|R{attacker_char.get_display_name(attacker_char.location)} attacks {target_char.get_display_name(target_char.location)} with their {weapon_type}!|n"

                    opportunity_text_victim = f"|R{attacker_char.get_display_name(target_char)} seizes the opportunity!|n"
                    opportunity_text_attacker = "|RYou seize the opportunity!|n"
                    
                    caller.msg(caller_msg_flee_fail + " " + opportunity_text_victim + " " + atk_msg_victim)
                    
                    if aimer_msg_flee_fail: 
                        aimer_locking_caller.msg(f"|R{aimer_msg_flee_fail}|n {opportunity_text_attacker} {atk_msg_attacker}")
                    else: 
                        aimer_locking_caller.msg(f"|RYou maintain your aim on {target_char.get_display_name(aimer_locking_caller)} as they falter, and press the attack!|n {opportunity_text_attacker} {atk_msg_attacker}")
                    
                    observer_flee_fail_prefix = f"{caller.key} tries to break free from {aimer_locking_caller.key}'s aim but is kept pinned."
                    observer_opportunity_text = f"{aimer_locking_caller.key} seizes the opportunity!"
                    room_observer_msg = f"|R{observer_flee_fail_prefix} {observer_opportunity_text}|n {atk_msg_observer}"
                    caller.location.msg_contents(room_observer_msg, exclude=[caller, aimer_locking_caller])

                    if not final_handler.is_active:
                        final_handler.start()
                    
                    return 

        # --- Part 2: Attempt to flee from combat handler (if present and aim is not an issue) ---
        fled_combat_successfully = False
        if handler:
            if not aim_successfully_broken: # Should have returned if aim break failed
                # This case implies they were aimed at, and failed to break it.
                current_aimer_on_caller = getattr(caller.ndb, "aimed_at_by", None)
                if current_aimer_on_caller:
                    caller.msg(f"You must first break free from {current_aimer_on_caller.get_display_name(caller)}'s aim to flee combat.")
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
                        caller.msg("|RYou wrench yourself from the confrontation, the metallic tang of fear and blood still sharp as you make your escape.|n")
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
            splattercast.msg(f"FLEE_MOVE_CONDITION: Aim broken, not in combat. {caller.key} can move.") # Added log
        elif fled_combat_successfully: # Fled combat (aim must have been broken or not an issue)
            should_move_room = True
            splattercast.msg(f"FLEE_MOVE_CONDITION: Fled combat successfully. {caller.key} can move.") # Added log
        
        if should_move_room:
            available_exits = [ex for ex in caller.location.exits if ex.access(caller, 'traverse')]
            if not available_exits:
                caller.msg("There are no exits here to flee through.")
                splattercast.msg(f"FLEE_NO_EXITS: {caller.key} has no available exits from {caller.location.key}.")
                return # Stop if no exits at all

            safe_exits = []
            for potential_exit in available_exits:
                destination_room = potential_exit.destination
                is_destination_safe = True
                if destination_room: # Ensure destination exists
                    for char_in_dest in destination_room.contents:
                        if char_in_dest == caller or not hasattr(char_in_dest, "ndb"): # Skip self or objects without NDB
                            continue
                        
                        # Check if char_in_dest is an opponent targeting the caller with a ranged weapon
                        other_handler = getattr(char_in_dest.ndb, "combat_handler", None)
                        if other_handler and other_handler.db.combat_is_running: # Check if combat is active
                            other_entry = next((e for e in other_handler.db.combatants if e["char"] == char_in_dest), None)
                            if other_entry and other_entry.get("target") == caller:
                                # Check if char_in_dest has a ranged weapon equipped
                                other_hands = getattr(char_in_dest, "hands", {})
                                other_weapon_obj = next((item for hand, item in other_hands.items() if item), None)
                                other_is_ranged = other_weapon_obj and hasattr(other_weapon_obj.db, "is_ranged") and other_weapon_obj.db.is_ranged
                                
                                if other_is_ranged:
                                    is_destination_safe = False
                                    splattercast.msg(f"FLEE_UNSAFE_DESTINATION: {caller.key} cannot flee via {potential_exit.key} to {destination_room.key}. Reason: {char_in_dest.key} is targeting them with a ranged weapon ('{other_weapon_obj.key if other_weapon_obj else 'ranged'}').")
                                    break # This destination is unsafe
                
                if is_destination_safe:
                    safe_exits.append(potential_exit)
                else:
                    # Inform the player about this specific unsafe exit
                    caller.msg(f"|yYou consider fleeing {potential_exit.key}, but sense {destination_room.get_display_name(caller) if destination_room else 'that direction'} is covered by a ranged attacker targeting you.|n")

            if not safe_exits:
                caller.msg("|rYou try to flee, but all escape routes seem covered by ranged attackers targeting you!|n")
                splattercast.msg(f"FLEE_MOVE_BLOCKED_ALL_SAFE_EXITS: {caller.key} has no safe exits. All covered by ranged attackers.")
                # Consider if a penalty should apply here if they were in combat and successfully disengaged but can't move.
                # For now, just blocks movement.
                return

            # Proceed with a safe exit
            chosen_exit = choice(safe_exits)
            
            flee_message_verb = "flees"
            if aim_successfully_broken and not fled_combat_successfully and not handler: # Only broke aim
                flee_message_verb = "breaks free and flees"
            
            caller.location.msg_contents(f"{caller.key} {flee_message_verb} {chosen_exit.key}.", exclude=caller)
            caller.msg(f"You {flee_message_verb} {chosen_exit.key}.")
            
            # Use the exit's at_traverse method, which handles aim clearing for the traverser
            # and other standard traversal effects.
            chosen_exit.at_traverse(caller, chosen_exit.destination)
            splattercast.msg(f"FLEE_MOVE_SUCCESS: {caller.key} fled via {chosen_exit.key} to {chosen_exit.destination.key}.")
        else:
            # This 'else' corresponds to 'if should_move_room:'
            # It means a prior flee step (aim break or combat disengage) failed and returned,
            # or no flee was needed initially.
            splattercast.msg(f"FLEE_NO_MOVE: {caller.key} - conditions for movement not met (should_move_room is False). This usually means a prior flee step failed and returned, or no flee was initiated.")


class CmdRetreat(Command):
    """
    Attempt to disengage from melee proximity.

    Usage:
      retreat

    If you are in melee proximity with one or more opponents, you will
    attempt to break away, creating distance within the same room.
    Success depends on an opposed roll against those in proximity.
    Failure means you remain engaged.
    """
    key = "retreat"
    aliases = ["disengage"]
    locks = "cmd:all()" # Potentially "cmd:in_combat()" if retreat only makes sense then
    help_category = "Combat"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        handler = getattr(caller.ndb, "combat_handler", None)

        if not handler:
            caller.msg("You are not in combat and thus not in melee proximity with anyone.")
            return

        if not hasattr(caller.ndb, "in_proximity_with") or not isinstance(caller.ndb.in_proximity_with, set):
            caller.msg("Your proximity status is unclear. This shouldn't happen. (Error: NDB missing/invalid)")
            splattercast.msg(f"RETREAT_ERROR: {caller.key} ndb.in_proximity_with missing or not a set.")
            # Initialize it as a failsafe, though it should be set by handler
            caller.ndb.in_proximity_with = set()
            # Still, probably best to return if it was missing, as state is unknown.
            return

        if not caller.ndb.in_proximity_with:
            caller.msg("You are not in direct melee proximity with anyone to retreat from.")
            splattercast.msg(f"RETREAT_INFO: {caller.key} tried to retreat but not in proximity with anyone.")
            return

        # --- Opposed Roll to Retreat ---
        # For now, let's use a simple success chance or a basic opposed roll.
        # We'll refine the opponent selection for the roll later.
        
        opponents_in_proximity = list(caller.ndb.in_proximity_with) # Get a list of who they are near
        
        # Simplistic: Highest motorics of anyone they are near.
        # More complex: Highest motorics of those in proximity *who are targeting the caller*.
        # For now, let's keep it simple.
        highest_opponent_motorics_val = 0
        resisting_opponent_for_log = None
        if opponents_in_proximity:
            # Filter for valid characters with motorics
            valid_opponents = [
                opp for opp in opponents_in_proximity 
                if opp and hasattr(opp, "motorics") # Check direct attribute
            ]
            if valid_opponents:
                # Get numeric motorics values, defaulting to 1 if non-numeric
                opponent_motorics_values = []
                for opp in valid_opponents:
                    val = getattr(opp, "motorics", 1)
                    opponent_motorics_values.append(val if isinstance(val, (int, float)) else 1)
                
                if opponent_motorics_values: # Ensure list is not empty after filtering
                    highest_opponent_motorics_val = max(opponent_motorics_values)
                    # For logging, find one of the opponents with max motorics
                    for opp in valid_opponents:
                        val = getattr(opp, "motorics", 1)
                        numeric_val = val if isinstance(val, (int, float)) else 1
                        if numeric_val == highest_opponent_motorics_val:
                            resisting_opponent_for_log = opp
                            break
        
        caller_motorics_val = getattr(caller, "motorics", 1) # Changed from caller.db
        caller_motorics_for_roll = caller_motorics_val if isinstance(caller_motorics_val, (int, float)) else 1
        
        retreat_roll = randint(1, max(1, caller_motorics_for_roll))
        resist_roll = randint(1, max(1, highest_opponent_motorics_val))

        splattercast.msg(f"RETREAT_ROLL: {caller.key} (motorics:{caller_motorics_for_roll}, roll:{retreat_roll}) vs "
                         f"Proximity (highest motorics:{highest_opponent_motorics_val}, opponent for log: {resisting_opponent_for_log.key if resisting_opponent_for_log else 'N/A'}, roll:{resist_roll})")

        if retreat_roll > resist_roll:
            # --- Success ---
            caller.msg("|gYou manage to break away from the immediate melee!|n")
            caller.location.msg_contents(
                f"|y{caller.get_display_name(caller.location)} breaks away from the melee!|n",
                exclude=[caller]
            )
            splattercast.msg(f"RETREAT_SUCCESS: {caller.key} successfully retreated from proximity.")

            # Update proximity for all involved
            for other_char in opponents_in_proximity: # opponents_in_proximity is a list copy
                if hasattr(other_char.ndb, "in_proximity_with") and isinstance(other_char.ndb.in_proximity_with, set):
                    other_char.ndb.in_proximity_with.discard(caller)
                    splattercast.msg(f"RETREAT_UPDATE: Removed {caller.key} from {other_char.key}'s proximity set.")
            
            caller.ndb.in_proximity_with.clear()
            splattercast.msg(f"RETREAT_UPDATE: Cleared {caller.key}'s proximity set.")
            
            # Potentially, a successful retreat might allow a character to queue a ranged action next turn,
            # or prevent melee attacks against them until someone advances. This will be handled by CmdAttack checks.

        else:
            # --- Failure ---
            caller.msg("|rYou try to break away, but you're held fast in the melee!|n")
            caller.location.msg_contents(
                f"|y{caller.get_display_name(caller.location)} tries to break away from the melee but is held fast!|n",
                exclude=[caller]
            )
            splattercast.msg(f"RETREAT_FAIL: {caller.key} failed to retreat from proximity.")
            
            # Consider adding a penalty, like skipping next turn's offensive action
            # caller.ndb.skip_combat_round = True 
            # For now, just failure to change proximity.

        # Ensure the combat handler is running if it somehow stopped (unlikely here but good practice)
        if handler and not handler.is_active:
            handler.start()


class CmdAdvance(Command):
    """
    Attempt to close distance and engage a target in melee.

    Usage:
      advance [target]

    If no target is specified, attempts to advance on your current
    combat target.
    If the target is in the same room but not in melee proximity,
    you will attempt to close the distance and enter melee.
    If the target is in an adjacent, managed combat room, you will
    attempt to move to that room. Engaging in melee proximity
    will require a subsequent action.
    Success depends on an opposed roll. Failure means you do not
    close the distance or fail to enter the room effectively.
    """
    key = "advance"
    aliases = ["engage", "close"]
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        handler = getattr(caller.ndb, "combat_handler", None)

        if not handler:
            caller.msg("You need to be in combat to advance on a target.")
            return

        target_char = None
        target_search_name = args
        target_in_adjacent_room = False # Initialize here

        if not args:
            # --- NO ARGUMENTS GIVEN, TRY TO USE CURRENT TARGET ---
            caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
            if caller_entry and caller_entry.get("target"):
                target_char = caller_entry.get("target")
                target_search_name = target_char.key # For error messages

                # Validate current target is still valid and in a managed room
                if not (target_char.location and target_char.location in handler.db.managed_rooms and \
                        any(e["char"] == target_char for e in handler.db.combatants)):
                    caller.msg(f"Your current target ({target_char.key if target_char else 'None'}) is no longer valid or reachable for advance.")
                    splattercast.msg(f"ADVANCE_CMD (NO ARGS): {caller.key} tried to advance on default target {target_char.key if target_char else 'None'}, but target invalid/unreachable.")
                    return
                
                # NEW: Check if this default target is in an adjacent room
                if target_char.location != caller.location:
                    # Target is in a different room. Check if it's an adjacent, managed, reachable room.
                    if target_char.location in handler.db.managed_rooms: # Should be true due to above check
                        can_reach_adj_room = any(ex.destination == target_char.location for ex in caller.location.exits)
                        if can_reach_adj_room:
                            target_in_adjacent_room = True
                            splattercast.msg(f"ADVANCE_CMD (NO ARGS): Default target {target_char.key} is in adjacent room {target_char.location.key}. Path exists.")
                        else:
                            caller.msg(f"Your current target ({target_char.key}) is in {target_char.location.key}, but there's no direct path to advance there from here.")
                            splattercast.msg(f"ADVANCE_CMD (NO ARGS): Default target {target_char.key} in {target_char.location.key}, but no direct path. Treating as same-room for proximity check or advance will fail if opposed roll is for inter-room.")
                            # If no direct path, it cannot be an adjacent room advance.
                            # target_in_adjacent_room remains False. The opposed roll logic will then treat it as same-room.
                            # If they are indeed in different, non-adjacent rooms, the later proximity checks or move_to will fail or be weird.
                            # This scenario (target in different, non-adjacent but managed room) might need more specific handling if it's common.
                            # For now, if no direct exit, it's not an "adjacent room advance".
                            target_in_adjacent_room = False # Explicitly ensure it's false if no path
                    # else: target is in an unmanaged room, already caught by initial validation.
                else: # Target is in the same room as caller
                    splattercast.msg(f"ADVANCE_CMD (NO ARGS): Default target {target_char.key} is in the same room ({caller.location.key}).")
                    # target_in_adjacent_room remains False, which is correct.

                splattercast.msg(f"ADVANCE_CMD: No target specified. Defaulting to current target: {target_char.key}. Adjacent: {target_in_adjacent_room}.")

            else:
                caller.msg("Advance on whom? (You have no current target).")
                return
        else:
            # --- ARGUMENTS GIVEN, SEARCH FOR TARGET (LOCAL FIRST) ---
            target_result = caller.search(args, location=caller.location, quiet=True)
            if isinstance(target_result, list):
                if target_result: target_char = target_result[0]
            else:
                target_char = target_result
        
            # If no local target found by name, or if initial target_char is invalid, check for remote targets
            if not target_char or not inherits_from(target_char, "typeclasses.characters.Character"):
                if args: # Only search remote if args were provided
                    all_combatants_in_handler = [entry["char"] for entry in handler.db.combatants if entry["char"]]
                    potential_remote_targets = [
                        char for char in all_combatants_in_handler 
                        if args.lower() in char.key.lower() and char.location != caller.location
                    ]
                    if potential_remote_targets:
                        target_char = potential_remote_targets[0] # Simplistic: take first match
                        if target_char.location in handler.db.managed_rooms:
                            can_reach_adj_room = any(ex.destination == target_char.location for ex in caller.location.exits)
                            if can_reach_adj_room:
                                target_in_adjacent_room = True # Correctly set here for arg-based remote target
                                splattercast.msg(f"ADVANCE_TARGET (ARGS): {caller.key} targeting {target_char.key} in adjacent room {target_char.location.key}.")
                            else:
                                caller.msg(f"You see {target_char.key} in the distance, but there's no direct path to advance on them from here.")
                                return
                        else:
                            caller.msg(f"You know of {target_char.key}, but they are not in a directly accessible combat area to advance on.")
                            return
                    else: # No local or remote target found by this name
                        caller.msg(f"You don't see '{args}' here or in an adjacent combat area to advance on.")
                        return
                # No 'elif not target_char:' here because if args were given and no target found, it's handled by the final check.
            # If a local target was found with args, target_in_adjacent_room remains False, which is correct.

        # Final check on target_char validity (could be None if args were given but no target found)
        if not target_char:
            caller.msg(f"You don't see '{target_search_name}' to advance on.")
            return

        if target_char == caller:
            caller.msg("You cannot advance on yourself.")
            return

        # Initialize NDB proximity sets if they don't exist (failsafe)
        for char_obj in [caller, target_char]:
            if not hasattr(char_obj.ndb, "in_proximity_with") or not isinstance(char_obj.ndb.in_proximity_with, set):
                char_obj.ndb.in_proximity_with = set()
                splattercast.msg(f"ADVANCE_FAILSAFE: Initialized in_proximity_with for {char_obj.key}.")

        # If already in proximity (and target is in the same room)
        if not target_in_adjacent_room and target_char in caller.ndb.in_proximity_with:
            caller.msg(f"You are already in melee proximity with {target_char.get_display_name(caller)}.")
            return

        # --- Opposed Roll to Advance/Engage ---
        caller_motorics_val = getattr(caller, "motorics", 1)
        caller_motorics_for_roll = caller_motorics_val if isinstance(caller_motorics_val, (int, float)) else 1
        
        target_motorics_val = getattr(target_char, "motorics", 1)
        target_motorics_for_roll = target_motorics_val if isinstance(target_motorics_val, (int, float)) else 1

        advance_roll = randint(1, max(1, caller_motorics_for_roll))
        resist_roll = randint(1, max(1, target_motorics_for_roll))

        splattercast.msg(f"ADVANCE_ROLL: {caller.key} (motorics:{caller_motorics_for_roll}, roll:{advance_roll}) vs "
                         f"{target_char.key} (motorics:{target_motorics_for_roll}, roll:{resist_roll})")

        if advance_roll > resist_roll:
            # --- Success ---
            if target_in_adjacent_room:
                # --- SUCCESSFUL ADVANCE TO ADJACENT ROOM ---
                original_caller_location = caller.location # Store original location for messages
                caller.location.msg_contents(f"{caller.get_display_name(original_caller_location)} advances out of the area, heading towards {target_char.location.get_display_name(original_caller_location)}!", exclude=[caller])
                
                # Move the caller
                caller.move_to(target_char.location, quiet=False, move_hooks=False)
                
                # 1. Clear the advancer's (caller's) own aim state
                if hasattr(caller, "clear_aim_state"):
                    caller.clear_aim_state(reason_for_clearing="as you advance to another area")
                    splattercast.msg(f"ADVANCE_AIM_CLEAR (CALLER): {caller.key}'s aim state cleared after advancing to {target_char.location.key}.")
                else:
                    splattercast.msg(f"ADVANCE_AIM_CLEAR_FAIL (CALLER): {caller.key} lacks clear_aim_state method after advancing.")

                # 2. Handle target_char's aim adjustment if they were focused on the caller or caller's direction of approach
                if target_char and target_char.location == caller.location: # Ensure target is still in the new room with caller
                    was_aiming_at_caller_specifically = getattr(target_char.ndb, "aiming_at", None) == caller
                    target_aiming_direction = getattr(target_char.ndb, "aiming_direction", None)
                    was_aiming_directionally_towards_caller = False

                    if target_aiming_direction and not was_aiming_at_caller_specifically:
                        exit_towards_caller_original_room = None
                        # Check exits from target's current room (which is now also caller's room)
                        for ex in target_char.location.exits:
                            if ex.destination == original_caller_location: # original_caller_location is where caller came from
                                if ex.key.lower() == target_aiming_direction.lower() or \
                                   any(alias.lower() == target_aiming_direction.lower() for alias in (ex.aliases.all() if hasattr(ex.aliases, "all") else [])):
                                    exit_towards_caller_original_room = ex
                                    break
                        if exit_towards_caller_original_room:
                            was_aiming_directionally_towards_caller = True

                    if was_aiming_at_caller_specifically:
                        # Target was already aiming at the caller. Aim persists.
                        target_char.msg(f"|y{caller.get_display_name(target_char)} advances directly into your sights! Your aim remains locked.|n")
                        caller.msg(f"|y{target_char.get_display_name(caller)} keeps you in their sights as you arrive!|n")
                        splattercast.msg(f"ADVANCE_AIM_PERSIST: {target_char.key}'s aim remains on {caller.key} after advance.")
                    
                    elif was_aiming_directionally_towards_caller:
                        # Target was aiming in the direction. Transition to aiming at caller.
                        # Clear target's previous directional aim (and any other character aim they might have had).
                        # This will message the target about stopping their old aim.
                        if hasattr(target_char, "clear_aim_state"):
                            target_char.clear_aim_state(reason_for_clearing=f"as {caller.get_display_name(target_char)} arrives from that direction")
                        
                        # Set new character-specific aim
                        target_char.ndb.aiming_at = caller
                        
                        # If caller was aimed at by someone else, break that old aim
                        # This ensures caller.ndb.aimed_at_by is exclusively target_char now.
                        previous_aimer_on_caller = getattr(caller.ndb, "aimed_at_by", None)
                        if previous_aimer_on_caller and previous_aimer_on_caller != target_char:
                            if hasattr(previous_aimer_on_caller, "clear_aim_state"):
                                previous_aimer_on_caller.clear_aim_state(reason_for_clearing=f"as {caller.get_display_name(previous_aimer_on_caller)}'s attention is diverted")
                            splattercast.msg(f"AIM_INTERRUPT: {previous_aimer_on_caller.key}'s aim on {caller.key} broken due to {target_char.key} now aiming at {caller.key}.")
                        
                        caller.ndb.aimed_at_by = target_char 

                        target_char.msg(f"|yYou shift your aim from the {target_aiming_direction} to focus directly on {caller.get_display_name(target_char)}!|n")
                        caller.msg(f"|y{target_char.get_display_name(caller)} was aiming in your direction of approach and now focuses their aim directly on you!|n")
                        splattercast.msg(f"ADVANCE_AIM_FOLLOW: {target_char.key} (was aiming {target_aiming_direction}) now aiming at {caller.key} after advance.")
                    
                    # else: Target was not aiming at caller or in their direction of approach.
                    # Their aim is unaffected by this specific "follow" logic.
                    # If they were aiming at a different character or a different direction, that aim persists.
                
                caller.msg(f"|gYou advance into {target_char.location.get_display_name(caller)}, the same area as {target_char.get_display_name(caller)}.|n")
                
                # Message to the room the caller arrived in
                arrival_message_room = f"{caller.get_display_name(target_char.location)} advances into the area!"
                # Notify target specifically if they are there (they already got aim-related messages if applicable)
                if target_char in target_char.location.contents:
                    # The target might have already received a specific aim-related message.
                    # This is a general arrival awareness message if not covered by aim.
                    # We can make this conditional or rephrase if aim messages are sufficient.
                    # For now, let's assume the aim messages are primary if they occurred.
                    if not was_aiming_at_caller_specifically and not was_aiming_directionally_towards_caller:
                         target_char.msg(f"|y{caller.get_display_name(target_char)} advances into your area!|n")
                    target_char.location.msg_contents(arrival_message_room, exclude=[caller, target_char])
                else: 
                    target_char.location.msg_contents(arrival_message_room, exclude=[caller])

                splattercast.msg(f"ADVANCE_SUCCESS (ADJACENT): {caller.key} moved to {target_char.location.key} (target: {target_char.key}). Proximity NOT automatically established.")
                
                # DO NOT ESTABLISH PROXIMITY HERE FOR ADJACENT ROOM ADVANCE

            else: # --- SUCCESSFUL ADVANCE IN SAME ROOM ---
                caller.msg(f"|gYou close the distance and engage {target_char.get_display_name(caller)} in melee!|n")
                caller.location.msg_contents(
                    f"|y{caller.get_display_name(caller.location)} closes in on {target_char.get_display_name(caller.location)}, engaging them in melee!|n",
                    exclude=[caller, target_char]
                )
                if target_char in caller.location.contents: # Check if target is still there
                    target_char.msg(f"|y{caller.get_display_name(target_char)} closes in, engaging you in melee!|n")
                splattercast.msg(f"ADVANCE_SUCCESS (SAME ROOM): {caller.key} engaged {target_char.key} in melee in room {caller.location.key}.")

                # Update proximity for caller, target, and scrum effect - ONLY for same-room advance
                caller.ndb.in_proximity_with.add(target_char)
                target_char.ndb.in_proximity_with.add(caller)
                splattercast.msg(f"ADVANCE_PROXIMITY: {caller.key} and {target_char.key} are now in proximity.")

                # Scrum effect (ensure NDB attributes exist before adding)
                for existing_prox_char in list(target_char.ndb.in_proximity_with):
                    if existing_prox_char != caller: 
                        caller.ndb.in_proximity_with.add(existing_prox_char)
                        if hasattr(existing_prox_char, "ndb") and hasattr(existing_prox_char.ndb, "in_proximity_with") and isinstance(existing_prox_char.ndb.in_proximity_with, set):
                            existing_prox_char.ndb.in_proximity_with.add(caller)
                        splattercast.msg(f"ADVANCE_SCRUM: {caller.key} also now in proximity with {existing_prox_char.key} (via {target_char.key}).")
                
                for callers_original_prox_char in list(caller.ndb.in_proximity_with): 
                    if callers_original_prox_char != target_char and callers_original_prox_char != caller:
                        if hasattr(callers_original_prox_char, "ndb") and hasattr(callers_original_prox_char.ndb, "in_proximity_with") and isinstance(callers_original_prox_char.ndb.in_proximity_with, set):
                            callers_original_prox_char.ndb.in_proximity_with.add(target_char)
                        if hasattr(target_char, "ndb") and hasattr(target_char.ndb, "in_proximity_with") and isinstance(target_char.ndb.in_proximity_with, set):
                            target_char.ndb.in_proximity_with.add(callers_original_prox_char)
                        splattercast.msg(f"ADVANCE_SCRUM_CALLER_GROUP: {callers_original_prox_char.key} (from {caller.key}'s group) now in proximity with {target_char.key}.")
                        
                        for targets_new_prox_char in list(target_char.ndb.in_proximity_with):
                            if targets_new_prox_char != caller and targets_new_prox_char != target_char and targets_new_prox_char != callers_original_prox_char:
                                if hasattr(callers_original_prox_char, "ndb") and hasattr(callers_original_prox_char.ndb, "in_proximity_with") and isinstance(callers_original_prox_char.ndb.in_proximity_with, set):
                                    callers_original_prox_char.ndb.in_proximity_with.add(targets_new_prox_char)
                                if hasattr(targets_new_prox_char, "ndb") and hasattr(targets_new_prox_char.ndb, "in_proximity_with") and isinstance(targets_new_prox_char.ndb.in_proximity_with, set):
                                    targets_new_prox_char.ndb.in_proximity_with.add(callers_original_prox_char)
                                splattercast.msg(f"ADVANCE_SCRUM_CALLER_TARGET_GROUP: {callers_original_prox_char.key} also now in proximity with {targets_new_prox_char.key}.")
            
            # Set the advancer's target in the combat handler (applies to both adjacent and same-room success)
            if handler:
                advancer_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
                if advancer_entry:
                    advancer_entry["target"] = target_char
                    advancer_entry["is_yielding"] = False 
                    splattercast.msg(f"ADVANCE_TARGET_SET: {caller.key}'s target in handler set to {target_char.key}.")
                    # Diagnostic Log:
                    splattercast.msg(f"ADVANCE_DEBUG_POST_SET: In CmdAdvance for {caller.key} (advancer), handler ID {handler.id if handler else 'None'}, entry target is now {advancer_entry.get('target').key if advancer_entry.get('target') else 'None'}. Full entry: {advancer_entry}")
                else:
                    splattercast.msg(f"ADVANCE_WARNING: Could not find {caller.key}'s entry in handler {handler.key} to set target after advance.")
            else: 
                splattercast.msg(f"ADVANCE_WARNING: No handler found for {caller.key} after successful advance to set target.")

        else:
            # --- Failure ---
            if target_in_adjacent_room:
                caller.msg(f"|rYou try to advance on {target_char.get_display_name(caller)} in {target_char.location.get_display_name(caller)}, but they (or the situation) prevent your approach!|n")
                splattercast.msg(f"ADVANCE_FAIL (ADJACENT): {caller.key} failed to advance to {target_char.location.key} to engage {target_char.key}.")
            else: # Same room
                caller.msg(f"|rYou try to close with {target_char.get_display_name(caller)}, but they maintain their distance!|n")
                caller.location.msg_contents(
                    f"|y{caller.get_display_name(caller.location)} attempts to close with {target_char.get_display_name(caller.location)} but fails.|n",
                    exclude=[caller, target_char]
                )
                if target_char in caller.location.contents: # Check if target is still there
                    target_char.msg(f"|y{caller.get_display_name(target_char)} tries to close with you but fails to gain ground.|n")
                splattercast.msg(f"ADVANCE_FAIL (SAME ROOM): {caller.key} failed to engage {target_char.key} in melee in room {caller.location.key}.")
            
        # Ensure combat handler is running if it somehow stopped (unlikely here but good practice)
        if handler and not handler.db.combat_is_running and len(handler.db.combatants) > 0:
            handler.start()


class CmdCharge(Command):
    """
    Charge recklessly at a target to engage in melee.

    Usage:
      charge [target]

    If no target is specified, attempts to charge your current
    combat target.
    A more aggressive, but potentially more dangerous, way to close
    distance with a target in the same room or an adjacent one.
    Success may grant a bonus on your next attack, but failure or
    the act of charging might leave you vulnerable.
    Charge always attempts to establish melee proximity on success.
    """
    key = "charge"
    aliases = ["rush"]
    locks = "cmd:all()" # Potentially "cmd:in_combat()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        handler = getattr(caller.ndb, "combat_handler", None)

        if not handler:
            caller.msg("You need to be in combat to charge a target.")
            return

        target_char = None
        target_search_name = args # Used for error messages if a specific name was given
        target_in_adjacent_room = False # Initialize here

        if not args:
            # --- NO ARGUMENTS GIVEN, TRY TO USE CURRENT TARGET ---
            caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
            if caller_entry and caller_entry.get("target"):
                target_char = caller_entry.get("target")
                target_search_name = target_char.key # For error messages

                # Validate current target
                if not (target_char.location and target_char.location in handler.db.managed_rooms and \
                        any(e["char"] == target_char for e in handler.db.combatants)):
                    caller.msg(f"Your current target ({target_char.key if target_char else 'None'}) is no longer valid or reachable for a charge.")
                    splattercast.msg(f"CHARGE_CMD (NO ARGS): {caller.key} tried to charge default target {target_char.key if target_char else 'None'}, but target invalid/unreachable.")
                    return
                
                # Check if this default target is in an adjacent room
                if target_char.location != caller.location:
                    if target_char.location in handler.db.managed_rooms:
                        can_reach_adj_room = any(ex.destination == target_char.location for ex in caller.location.exits)
                        if can_reach_adj_room:
                            target_in_adjacent_room = True
                            splattercast.msg(f"CHARGE_CMD (NO ARGS): Default target {target_char.key} is in adjacent room {target_char.location.key}. Path exists.")
                        else:
                            # If no direct path, they can't charge there.
                            caller.msg(f"Your current target ({target_char.key}) is in {target_char.location.key}, but there's no direct path to charge there from here.")
                            splattercast.msg(f"CHARGE_CMD (NO ARGS): Default target {target_char.key} in {target_char.location.key}, but no direct path. Charge aborted.")
                            return # Cannot charge to non-adjacent/unreachable room
                    # else: target is in an unmanaged room, already caught by initial validation.
                else: # Target is in the same room as caller
                    splattercast.msg(f"CHARGE_CMD (NO ARGS): Default target {target_char.key} is in the same room ({caller.location.key}).")
                
                splattercast.msg(f"CHARGE_CMD: No target specified. Defaulting to current target: {target_char.key}. Adjacent: {target_in_adjacent_room}.")
            else:
                caller.msg("Charge whom? (You have no current target).")
                return
        else:
            # --- ARGUMENTS GIVEN, SEARCH FOR TARGET (LOCAL FIRST) ---
            target_result = caller.search(args, location=caller.location, quiet=True)
            if isinstance(target_result, list):
                if target_result: target_char = target_result[0]
            else:
                target_char = target_result
        
            # If no local target found by name, or if initial target_char is invalid, check for remote targets
            if not target_char or not inherits_from(target_char, "typeclasses.characters.Character"):
                if args: # Only search remote if args were provided
                    all_combatants_in_handler = [entry["char"] for entry in handler.db.combatants if entry["char"]]
                    potential_remote_targets = [
                        char for char in all_combatants_in_handler 
                        if args.lower() in char.key.lower() and char.location != caller.location
                    ]
                    if potential_remote_targets:
                        target_char = potential_remote_targets[0] # Simplistic: take first match
                        if target_char.location in handler.db.managed_rooms:
                            can_reach_adj_room = any(ex.destination == target_char.location for ex in caller.location.exits)
                            if can_reach_adj_room:
                                target_in_adjacent_room = True
                                splattercast.msg(f"CHARGE_TARGET (ARGS): {caller.key} targeting {target_char.key} in adjacent room {target_char.location.key}.")
                            else:
                                caller.msg(f"You see {target_char.key} in the distance, but there's no direct path to charge them from here.")
                                return
                        else:
                            caller.msg(f"You know of {target_char.key}, but they are not in a directly accessible combat area to charge.")
                            return
                    else: # No local or remote target found by this name
                        caller.msg(f"You don't see '{args}' here or in an adjacent combat area to charge.")
                        return
            # If a local target was found with args, target_in_adjacent_room remains False, which is correct.

        # Final check on target_char validity
        if not target_char:
            caller.msg(f"You don't see '{target_search_name}' to charge.") # Use target_search_name which holds original arg or default target's name
            return

        if target_char == caller:
            caller.msg("You cannot charge yourself. That would be silly.")
            return

        # Failsafe NDB init for proximity sets
        for char_obj in [caller, target_char]:
            if not hasattr(char_obj.ndb, "in_proximity_with") or not isinstance(char_obj.ndb.in_proximity_with, set):
                char_obj.ndb.in_proximity_with = set()
                splattercast.msg(f"CHARGE_FAILSAFE: Initialized in_proximity_with for {char_obj.key}.")

        # Check if already in proximity (only if target is in the same room)
        if not target_in_adjacent_room and target_char in caller.ndb.in_proximity_with:
            caller.msg(f"You are already in melee proximity with {target_char.get_display_name(caller)}; no need to charge.")
            return

        # --- Opposed Roll for Charge ---
        caller_motorics_val = getattr(caller, "motorics", 1)
        caller_motorics_for_roll = caller_motorics_val if isinstance(caller_motorics_val, (int, float)) else 1
        
        target_motorics_val = getattr(target_char, "motorics", 1)
        target_motorics_for_roll = target_motorics_val if isinstance(target_motorics_val, (int, float)) else 1

        charge_bonus = 2 
        charge_roll = randint(1, max(1, caller_motorics_for_roll)) + charge_bonus
        resist_roll = randint(1, max(1, target_motorics_for_roll))

        splattercast.msg(f"CHARGE_ROLL: {caller.key} (motorics:{caller_motorics_for_roll}, roll:{charge_roll} incl. bonus {charge_bonus}) vs "
                         f"{target_char.key} (motorics:{target_motorics_for_roll}, roll:{resist_roll})")
        
        caller.ndb.charging_vulnerability_active = True 

        if charge_roll > resist_roll:
            # --- Success ---
            if target_in_adjacent_room:
                # --- SUCCESSFUL CHARGE TO ADJACENT ROOM ---
                original_caller_location = caller.location 
                caller.location.msg_contents(f"{caller.get_display_name(original_caller_location)} charges towards {target_char.location.get_display_name(original_caller_location)}!", exclude=[caller])
                
                caller.move_to(target_char.location, quiet=False, move_hooks=False)
                
                if hasattr(caller, "clear_aim_state"):
                    caller.clear_aim_state(reason_for_clearing="as you charge into another area")
                    splattercast.msg(f"CHARGE_AIM_CLEAR (CALLER): {caller.key}'s aim state cleared after charging to {target_char.location.key}.")
                else:
                    splattercast.msg(f"CHARGE_AIM_CLEAR_FAIL (CALLER): {caller.key} lacks clear_aim_state method after charging.")

                if target_char and target_char.location == caller.location: 
                    was_aiming_at_caller_specifically = getattr(target_char.ndb, "aiming_at", None) == caller
                    target_aiming_direction = getattr(target_char.ndb, "aiming_direction", None)
                    was_aiming_directionally_towards_caller = False

                    if target_aiming_direction and not was_aiming_at_caller_specifically:
                        exit_towards_caller_original_room = None
                        for ex in target_char.location.exits:
                            if ex.destination == original_caller_location: 
                                if ex.key.lower() == target_aiming_direction.lower() or \
                                   any(alias.lower() == target_aiming_direction.lower() for alias in (ex.aliases.all() if hasattr(ex.aliases, "all") else [])):
                                    exit_towards_caller_original_room = ex
                                    break
                        if exit_towards_caller_original_room:
                            was_aiming_directionally_towards_caller = True

                    if was_aiming_at_caller_specifically:
                        target_char.msg(f"|y{caller.get_display_name(target_char)} charges directly into your sights! Your aim remains locked.|n")
                        caller.msg(f"|y{target_char.get_display_name(caller)} keeps you in their sights as you charge in!|n")
                        splattercast.msg(f"CHARGE_AIM_PERSIST: {target_char.key}'s aim remains on {caller.key} after charge.")
                    
                    elif was_aiming_directionally_towards_caller:
                        if hasattr(target_char, "clear_aim_state"):
                            target_char.clear_aim_state(reason_for_clearing=f"as {caller.get_display_name(target_char)} charges in from that direction")
                        
                        target_char.ndb.aiming_at = caller
                        previous_aimer_on_caller = getattr(caller.ndb, "aimed_at_by", None)
                        if previous_aimer_on_caller and previous_aimer_on_caller != target_char:
                            if hasattr(previous_aimer_on_caller, "clear_aim_state"):
                                previous_aimer_on_caller.clear_aim_state(reason_for_clearing=f"as {caller.get_display_name(previous_aimer_on_caller)}'s attention is diverted by the charge")
                            splattercast.msg(f"AIM_INTERRUPT (CHARGE): {previous_aimer_on_caller.key}'s aim on {caller.key} broken due to {target_char.key} now aiming at {caller.key}.")
                        caller.ndb.aimed_at_by = target_char 

                        target_char.msg(f"|yYou shift your aim from the {target_aiming_direction} to focus directly on the charging {caller.get_display_name(target_char)}!|n")
                        caller.msg(f"|y{target_char.get_display_name(caller)} was aiming in your direction of approach and now focuses their aim directly on you as you charge!|n")
                        splattercast.msg(f"CHARGE_AIM_FOLLOW: {target_char.key} (was aiming {target_aiming_direction}) now aiming at {caller.key} after charge.")
                
                caller.msg(f"|gYou charge into {target_char.location.get_display_name(caller)}, the same area as {target_char.get_display_name(caller)}!|n")

                arrival_message_room = f"{caller.get_display_name(target_char.location)} charges into the area!"
                if target_char in target_char.location.contents:
                    # Conditional message to avoid spam if aim messages were sent
                    if not (target_char and target_char.location == caller.location and \
                            (getattr(target_char.ndb, "aiming_at", None) == caller or \
                             (getattr(target_char.ndb, "aiming_direction", None) and \
                              any(ex.destination == original_caller_location and (ex.key.lower() == getattr(target_char.ndb, "aiming_direction", "").lower() or \
                                   any(alias.lower() == getattr(target_char.ndb, "aiming_direction", "").lower() for alias in (ex.aliases.all() if hasattr(ex.aliases, "all") else []))) for ex in target_char.location.exits)))):
                         target_char.msg(f"|y{caller.get_display_name(target_char)} charges into your area!|n")
                    target_char.location.msg_contents(arrival_message_room, exclude=[caller, target_char])
                else: 
                    target_char.location.msg_contents(arrival_message_room, exclude=[caller])
                
                splattercast.msg(f"CHARGE_SUCCESS (ADJACENT): {caller.key} charged to {target_char.location.key} (target: {target_char.key}).")

            else: # --- SUCCESSFUL CHARGE IN SAME ROOM ---
                caller.msg(f"|gYou charge across the area and slam into {target_char.get_display_name(caller)}!|n")
                caller.location.msg_contents(
                    f"|y{caller.get_display_name(caller.location)} charges wildly at {target_char.get_display_name(caller.location)}, slamming into them!|n",
                    exclude=[caller, target_char]
                )
                if target_char in caller.location.contents:
                    target_char.msg(f"|y{caller.get_display_name(target_char)} charges wildly and slams into you!|n")
                splattercast.msg(f"CHARGE_SUCCESS (SAME ROOM): {caller.key} charged {target_char.key} in room {caller.location.key}.")

            # Proximity updates (applies to both adjacent and same-room charge)
            caller.ndb.in_proximity_with.add(target_char)
            target_char.ndb.in_proximity_with.add(caller)
            splattercast.msg(f"CHARGE_PROXIMITY: {caller.key} and {target_char.key} are now in proximity.")

            # Scrum effect
            # ... (scrum effect logic remains the same) ...
            for existing_prox_char in list(target_char.ndb.in_proximity_with):
                if existing_prox_char != caller: 
                    caller.ndb.in_proximity_with.add(existing_prox_char)
                    if hasattr(existing_prox_char, "ndb") and hasattr(existing_prox_char.ndb, "in_proximity_with") and isinstance(existing_prox_char.ndb.in_proximity_with, set):
                        existing_prox_char.ndb.in_proximity_with.add(caller)
                    splattercast.msg(f"CHARGE_SCRUM: {caller.key} also now in proximity with {existing_prox_char.key} (via {target_char.key}).")
            
            for callers_original_prox_char in list(caller.ndb.in_proximity_with): 
                if callers_original_prox_char != target_char and callers_original_prox_char != caller:
                    if hasattr(callers_original_prox_char, "ndb") and hasattr(callers_original_prox_char.ndb, "in_proximity_with") and isinstance(callers_original_prox_char.ndb.in_proximity_with, set):
                        callers_original_prox_char.ndb.in_proximity_with.add(target_char)
                    if hasattr(target_char, "ndb") and hasattr(target_char.ndb, "in_proximity_with") and isinstance(target_char.ndb.in_proximity_with, set):
                        target_char.ndb.in_proximity_with.add(callers_original_prox_char)
                    splattercast.msg(f"CHARGE_SCRUM_CALLER_GROUP: {callers_original_prox_char.key} (from {caller.key}'s group) now in proximity with {target_char.key}.")
                    
                    for targets_new_prox_char in list(target_char.ndb.in_proximity_with):
                        if targets_new_prox_char != caller and targets_new_prox_char != target_char and targets_new_prox_char != callers_original_prox_char:
                            if hasattr(callers_original_prox_char, "ndb") and hasattr(callers_original_prox_char.ndb, "in_proximity_with") and isinstance(callers_original_prox_char.ndb.in_proximity_with, set):
                                callers_original_prox_char.ndb.in_proximity_with.add(targets_new_prox_char)
                            if hasattr(targets_new_prox_char, "ndb") and hasattr(targets_new_prox_char.ndb, "in_proximity_with") and isinstance(targets_new_prox_char.ndb.in_proximity_with, set):
                                targets_new_prox_char.ndb.in_proximity_with.add(callers_original_prox_char)
                            splattercast.msg(f"CHARGE_SCRUM_CALLER_TARGET_GROUP: {callers_original_prox_char.key} also now in proximity with {targets_new_prox_char.key}.")


            # Set the charger's target in the combat handler
            if handler:
                charger_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
                if charger_entry:
                    charger_entry["target"] = target_char
                    charger_entry["is_yielding"] = False 
                    splattercast.msg(f"CHARGE_TARGET_SET: {caller.key}'s target in handler set to {target_char.key}.")

            caller.ndb.charge_attack_bonus_active = True
            splattercast.msg(f"CHARGE_EFFECT: {caller.key} gains charge_attack_bonus_active.")

        else:
            # --- Failure ---
            # ... (failure logic remains the same) ...
            caller.msg(f"|rYou charge towards {target_char.get_display_name(caller)}, but they deftly avoid your reckless rush!|n")
            if target_in_adjacent_room:
                caller.location.msg_contents(f"|y{caller.get_display_name(caller.location)} charges towards {target_char.location.get_display_name(caller.location)} but stumbles, failing to reach them.|n", exclude=[caller])
                splattercast.msg(f"CHARGE_FAIL (ADJACENT): {caller.key} failed to charge to {target_char.location.key} to engage {target_char.key}.")
            else: # Same room
                caller.location.msg_contents(f"|y{caller.get_display_name(caller.location)} charges wildly at {target_char.get_display_name(caller.location)} but misses!|n", exclude=[caller, target_char])
                if target_char in caller.location.contents:
                    target_char.msg(f"|y{caller.get_display_name(target_char)} charges at you but stumbles, failing to connect!|n")
                splattercast.msg(f"CHARGE_FAIL (SAME ROOM): {caller.key} failed to charge {target_char.key} in room {caller.location.key}.")
            
            caller.ndb.skip_combat_round = True
            caller.msg("|rYour failed charge leaves you off-balance for a moment.|n")
            splattercast.msg(f"CHARGE_PENALTY: {caller.key} set to skip_combat_round due to failed charge.")

        if handler and not handler.db.combat_is_running and len(handler.db.combatants) > 0:
            handler.start()


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
