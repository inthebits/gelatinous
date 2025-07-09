"""
Core Combat Actions Module

Contains the fundamental combat commands that initiate or control combat flow:
- CmdAttack: Primary combat initiation command
- CmdStop: Stop attacking/aiming commands

These commands form the core of the combat system and are used most frequently
by players during combat encounters.
"""

from evennia import Command
from evennia.utils.utils import inherits_from
from random import randint, choice
from world.combat.handler import get_or_create_combat
from world.combat.constants import COMBAT_SCRIPT_KEY
from world.combat.messages import get_combat_message
from evennia.comms.models import ChannelDB
from evennia.utils import utils
from evennia.utils.evtable import EvTable

from world.combat.constants import (
    MSG_ATTACK_WHO, MSG_SELF_TARGET, MSG_NOT_IN_COMBAT, MSG_NO_COMBAT_DATA,
    MSG_STOP_WHAT, MSG_STOP_NOT_AIMING, MSG_STOP_AIM_ERROR, MSG_STOP_NOT_IN_COMBAT,
    MSG_STOP_NOT_REGISTERED, MSG_STOP_YIELDING, MSG_STOP_ALREADY_ACCEPTING_GRAPPLE,
    MSG_STOP_ALREADY_YIELDING,
    DEBUG_PREFIX_ATTACK, DEBUG_FAILSAFE, DEBUG_SUCCESS, DEBUG_FAIL, DEBUG_ERROR,
    NDB_PROXIMITY, DEFAULT_WEAPON_TYPE, COLOR_SUCCESS, COLOR_FAILURE, COLOR_WARNING
)
from world.combat.utils import (
    initialize_proximity_ndb, get_wielded_weapon, roll_stat, opposed_roll,
    log_combat_action, get_display_name_safe, validate_combat_target
)
from world.combat.proximity import (
    establish_proximity, break_proximity, clear_all_proximity, 
    is_in_proximity, get_proximity_list, proximity_opposed_roll
)
from world.combat.grappling import (
    get_grappling_target, get_grappled_by, establish_grapple, break_grapple,
    is_grappling, is_grappled, validate_grapple_action
)


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
            caller.msg(MSG_ATTACK_WHO)
            return

        # --- WEAPON IDENTIFICATION (early) ---
        hands = getattr(caller, "hands", {})
        weapon_obj = next((item for hand, item in hands.items() if item), None)
        
        # Debug weapon detection
        splattercast.msg(f"WEAPON_DETECT: {caller.key} hands={hands}, weapon_obj={weapon_obj.key if weapon_obj else 'None'}")
        if weapon_obj:
            splattercast.msg(f"WEAPON_DETECT: {weapon_obj.key} has db={hasattr(weapon_obj, 'db')}, "
                           f"db.is_ranged={getattr(weapon_obj.db, 'is_ranged', 'MISSING') if hasattr(weapon_obj, 'db') else 'NO_DB'}, "
                           f"db.weapon_type={getattr(weapon_obj.db, 'weapon_type', 'MISSING') if hasattr(weapon_obj, 'db') else 'NO_DB'}")
        
        is_ranged_weapon = weapon_obj and hasattr(weapon_obj, "db") and getattr(weapon_obj.db, "is_ranged", False)
        weapon_name_for_msg = weapon_obj.key if weapon_obj else "your fists"
        weapon_type_for_msg = (str(weapon_obj.db.weapon_type).lower() if weapon_obj and hasattr(weapon_obj, "db") and hasattr(weapon_obj.db, "weapon_type") and weapon_obj.db.weapon_type else "unarmed")
        
        splattercast.msg(f"WEAPON_FINAL: {caller.key} is_ranged={is_ranged_weapon}, weapon_type={weapon_type_for_msg}")
        # --- END WEAPON IDENTIFICATION ---

        target_room = caller.location
        target_search_name = args

        # --- AIMING DIRECTION ATTACK ---
        aiming_direction = getattr(caller.ndb, "aiming_direction", None)
        if aiming_direction:
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: {caller.key} is aiming {aiming_direction}, attempting remote attack on '{args}'.")
            
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
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Remote attack target room is {target_room.key}.")
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
            caller.msg(MSG_SELF_TARGET)
            return

        # --- PROXIMITY AND WEAPON VALIDATION ---
        # Initialize caller's proximity NDB if missing (failsafe)
        if initialize_proximity_ndb(caller):
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}_{DEBUG_FAILSAFE}: Initialized {NDB_PROXIMITY} for {caller.key}.")

        if not aiming_direction: # SAME ROOM ATTACK
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Validating same-room attack by {caller.key} on {target.key}.")
            is_in_melee_proximity = target in caller.ndb.in_proximity_with

            if is_in_melee_proximity: # Caller is in melee with target
                if is_ranged_weapon:
                    caller.msg(f"You can't effectively use your {weapon_name_for_msg} while locked in melee with {target.get_display_name(caller)}!")
                    splattercast.msg(f"{DEBUG_PREFIX_ATTACK}_{DEBUG_FAIL}: {caller.key} tried to use ranged weapon '{weapon_name_for_msg}' on {target.key} while in melee proximity. Attack aborted.")
                    return
                splattercast.msg(f"{DEBUG_PREFIX_ATTACK}_{DEBUG_SUCCESS}: {caller.key} attacking {target.key} with non-ranged '{weapon_name_for_msg}' while in melee proximity.")
            else: # Caller is NOT in melee with target (at range in same room)
                if not is_ranged_weapon:
                    caller.msg(f"You are too far away to hit {target.get_display_name(caller)} with your {weapon_name_for_msg}. Try advancing or charging.")
                    splattercast.msg(f"{DEBUG_PREFIX_ATTACK}_{DEBUG_FAIL}: {caller.key} tried to use non-ranged weapon '{weapon_name_for_msg}' on {target.key} who is not in melee proximity. Attack aborted.")
                    return
                splattercast.msg(f"{DEBUG_PREFIX_ATTACK}_{DEBUG_SUCCESS}: {caller.key} attacking {target.key} with ranged weapon '{weapon_name_for_msg}' from distance in same room.")
        else: # ADJACENT ROOM ATTACK (aiming_direction is set)
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Validating ranged attack into {target_room.key} by {caller.key} on {target.key}.")
            if not is_ranged_weapon:
                caller.msg(f"You need a ranged weapon to attack {target.get_display_name(caller)} in the {aiming_direction} direction.")
                splattercast.msg(f"{DEBUG_PREFIX_ATTACK}_{DEBUG_FAIL}: {caller.key} tried to attack into {aiming_direction} (target: {target.key}) without a ranged weapon ({weapon_name_for_msg}). Attack aborted.")
                return
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}_{DEBUG_SUCCESS}: {caller.key} attacking into {aiming_direction} with ranged weapon '{weapon_name_for_msg}'.")
        # --- END PROXIMITY AND WEAPON VALIDATION ---

        # --- Get/Create/Merge Combat Handlers ---
        caller_handler = get_or_create_combat(caller.location)
        target_handler = get_or_create_combat(target.location) # Might be the same if target_room is caller.location

        final_handler = caller_handler
        if caller_handler != target_handler:
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Cross-handler engagement! Caller's handler: {caller_handler.key} (on {caller_handler.obj.key}). Target's handler: {target_handler.key} (on {target_handler.obj.key}). Merging...")
            caller_handler.merge_handler(target_handler)
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Merge complete. Final handler is {final_handler.key}, now managing rooms: {[r.key for r in final_handler.db.managed_rooms]}.")
        else:
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Caller and target are (or will be) in the same handler zone: {final_handler.key} (on {final_handler.obj.key}).")
            final_handler.enroll_room(caller.location)
            final_handler.enroll_room(target.location)

        # --- CAPTURE PRE-ADDITION COMBAT STATE ---
        caller_was_in_final_handler = any(e["char"] == caller for e in final_handler.db.combatants)
        target_was_in_final_handler = any(e["char"] == target for e in final_handler.db.combatants)
        
        original_caller_target_in_handler = None
        if caller_was_in_final_handler:
            caller_entry_snapshot = next((e for e in final_handler.db.combatants if e["char"] == caller), None)
            if caller_entry_snapshot:
                original_caller_target_in_handler = final_handler.get_target_obj(caller_entry_snapshot)

        # --- Add combatants to the final_handler ---
        if not caller_was_in_final_handler:
            final_handler.add_combatant(caller, target=target)
        else: 
            caller_entry = next((e for e in final_handler.db.combatants if e["char"] == caller), None)
            if caller_entry: # Ensure entry exists
                final_handler.set_target(caller, target) # This command updates the target
                caller_entry["is_yielding"] = False

        if not target_was_in_final_handler:
            final_handler.add_combatant(target, target=caller) 
        else: 
            target_entry = next((e for e in final_handler.db.combatants if e["char"] == target), None)
            if target_entry: # Ensure entry exists
                if not final_handler.get_target_obj(target_entry): 
                     final_handler.set_target(target, caller)
                # Do not automatically un-yield target if they were already yielding.
                # target_entry["is_yielding"] = False

        # --- ESTABLISH PROXIMITY FOR SAME-ROOM COMBAT ---
        if not aiming_direction and caller.location == target.location:
            # Same room attack - establish proximity for melee combat
            if not is_ranged_weapon:  # Only for melee weapons
                establish_proximity(caller, target)
                splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Established proximity between {caller.key} and {target.key} for melee combat.")

        # --- Messaging and Action ---
        if aiming_direction:
            # --- Attacking into an adjacent room ---
            splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: Aiming direction attack by {caller.key} towards {aiming_direction} into {target_room.key}.")

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

        splattercast.msg(f"{DEBUG_PREFIX_ATTACK}: {caller.key} attacks {target.key if target else 'a direction'}. Combat managed by {final_handler.key}.")
        
        if not final_handler.is_active:
            final_handler.start()


class CmdStop(Command):
    """
    Stop attacking or aiming.

    Usage:
      stop aiming
      stop attacking

    Stops your current aggressive actions. 'stop aiming' clears any aim locks
    you have on targets or directions. 'stop attacking' makes you yield in
    combat (stop actively attacking but remain in combat).
    """

    key = "stop"
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()
        
        if not args:
            caller.msg(MSG_STOP_WHAT)
            return

        if args == "aiming" or args == "aim":
            # Check if currently aiming
            if not hasattr(caller.ndb, "aiming_at") and not hasattr(caller.ndb, "aiming_direction"):
                caller.msg(MSG_STOP_NOT_AIMING)
            elif hasattr(caller, "clear_aim_state"):
                caller.clear_aim_state()
            else:
                caller.msg(MSG_STOP_AIM_ERROR)
                
        elif args == "attacking" or args == "attack":
            handler = getattr(caller.ndb, "combat_handler", None)
            
            if not handler:
                caller.msg(MSG_STOP_NOT_IN_COMBAT)
                return

            caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
            if not caller_entry:
                caller.msg(MSG_STOP_NOT_REGISTERED)
                return

            # Check if being grappled - different message in this case
            grappler_obj = handler.get_grappled_by_obj(caller_entry)
            if grappler_obj:
                if not caller_entry.get("is_yielding", False):
                    caller_entry["is_yielding"] = True
                    caller.msg(MSG_STOP_YIELDING)
                else:
                    caller.msg(MSG_STOP_ALREADY_ACCEPTING_GRAPPLE)
            else:
                if not caller_entry.get("is_yielding", False):
                    caller_entry["is_yielding"] = True
                    caller.msg(MSG_STOP_YIELDING)
                else:
                    caller.msg(MSG_STOP_ALREADY_YIELDING)
        else:
            caller.msg(MSG_STOP_WHAT)
