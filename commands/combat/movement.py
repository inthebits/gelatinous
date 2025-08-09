"""
Movement Combat Commands Module

Contains commands related to movement and positioning in combat:
- CmdFlee: Attempt to flee from combat or aiming
- CmdRetreat: Disengage from melee proximity within the same room
- CmdAdvance: Close distance with a target
- CmdCharge: Recklessly charge at a target

These commands handle the tactical movement aspects of combat,
allowing players to control distance and positioning strategically.
"""

from evennia import Command
from evennia.utils.utils import inherits_from, delay
from evennia import create_object
from random import choice
from world.combat.handler import get_or_create_combat
from world.combat.constants import COMBAT_SCRIPT_KEY
from world.combat.messages import get_combat_message
from evennia.comms.models import ChannelDB

from world.combat.constants import (
    MSG_NOTHING_TO_FLEE, MSG_FLEE_NO_EXITS, MSG_FLEE_PINNED_BY_AIM, MSG_FLEE_TRAPPED_IN_COMBAT,
    MSG_FLEE_ALL_EXITS_COVERED, MSG_FLEE_BREAK_FREE_AIM, MSG_FLEE_FAILED_BREAK_AIM,
    MSG_FLEE_COMBAT_FAILED, MSG_FLEE_NO_TARGET_ERROR, MSG_FLEE_DISENGAGE_NO_ATTACKERS,
    MSG_FLEE_DISENGAGE_SUCCESS_GENERIC, MSG_FLEE_PARTIAL_SUCCESS, MSG_FLEE_AIM_BROKEN_NO_MOVE,
    MSG_RETREAT_NOT_IN_COMBAT, MSG_RETREAT_COMBAT_DATA_MISSING, MSG_RETREAT_PROXIMITY_UNCLEAR,
    MSG_RETREAT_NO_PROXIMITY, MSG_RETREAT_SUCCESS, MSG_RETREAT_FAILED, MSG_CANNOT_WHILE_GRAPPLED_RETREAT,
    MSG_ADVANCE_NOT_IN_COMBAT, MSG_ADVANCE_COMBAT_DATA_MISSING, MSG_ADVANCE_NO_TARGET, MSG_ADVANCE_SELF_TARGET,
    MSG_CHARGE_NOT_IN_COMBAT, MSG_CHARGE_COMBAT_DATA_MISSING, MSG_CHARGE_NO_TARGET, MSG_CHARGE_SELF_TARGET,
    MSG_CHARGE_FAILED_PENALTY,
    DEBUG_PREFIX_FLEE, DEBUG_PREFIX_RETREAT, DEBUG_PREFIX_ADVANCE, DEBUG_PREFIX_CHARGE, DEBUG_PREFIX_JUMP,
    DEBUG_FAILSAFE, DEBUG_SUCCESS, DEBUG_FAIL, DEBUG_ERROR,
    NDB_PROXIMITY, NDB_SKIP_ROUND, SPLATTERCAST_CHANNEL,
    COMBAT_ACTION_RETREAT, MSG_RETREAT_PREPARE, MSG_RETREAT_QUEUE_SUCCESS,
    COMBAT_ACTION_ADVANCE, MSG_ADVANCE_PREPARE, MSG_ADVANCE_QUEUE_SUCCESS,
    COMBAT_ACTION_CHARGE, MSG_CHARGE_PREPARE, MSG_CHARGE_QUEUE_SUCCESS,
    COMBAT_ACTION_DISARM, MSG_DISARM_PREPARE, MSG_DISARM_QUEUE_SUCCESS
)
from world.combat.utils import (
    initialize_proximity_ndb, get_wielded_weapon, roll_stat, opposed_roll,
    log_combat_action, get_display_name_safe, validate_combat_target,
    get_highest_opponent_stat, get_numeric_stat, filter_valid_opponents,
    roll_with_advantage, roll_with_disadvantage, standard_roll,
    is_wielding_ranged_weapon, clear_aim_state, clear_mutual_aim
)
from world.combat.proximity import (
    establish_proximity, break_proximity, clear_all_proximity,
    is_in_proximity, get_proximity_list, proximity_opposed_roll
)
from world.combat.grappling import (
    get_grappling_target, get_grappled_by, establish_grapple, break_grapple,
    is_grappling, is_grappled, validate_grapple_action
)


class CmdFlee(Command):
    """
    Attempt to flee from an aimer or combat.

    Usage:
      flee

    If someone is aiming at you, you will first attempt to break their aim.
    If successful, or if no one was aiming at you and you are in combat,
    you will attempt to escape the current combat and leave the room.
    You cannot flee into a room where an opponent is already targeting
    you with a ranged weapon.
    If you fail any step, you remain in place (and may skip your next combat turn if failing to flee combat).
    Cannot be used if you are currently grappled in combat.
    If you disengage from local attackers but cannot find a safe exit, you remain in combat.
    """

    key = "flee"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        original_handler_at_flee_start = getattr(caller.ndb, "combat_handler", None)
        # This is the specific character who has an NDB-level aim lock on the caller.
        # This aimer could be in the same room or an adjacent one.
        ndb_aimer_locking_caller = getattr(caller.ndb, "aimed_at_by", None) 

        splattercast.msg(f"{DEBUG_PREFIX_FLEE}_DEBUG ({caller.key}): Initial Handler='{original_handler_at_flee_start.key if original_handler_at_flee_start else None}', NDB Aimer='{ndb_aimer_locking_caller.key if ndb_aimer_locking_caller else None}'")

        # --- PRE-FLEE SAFETY CHECK: PINNED BY RANGED TARGETERS IN ADJACENT ROOMS ---
        available_exits = [ex for ex in caller.location.exits if ex.access(caller, 'traverse')]
        
        if not available_exits:
            # No exits at all.
            if ndb_aimer_locking_caller:
                caller.msg(MSG_FLEE_PINNED_BY_AIM.format(aimer=ndb_aimer_locking_caller.get_display_name(caller)))
            elif original_handler_at_flee_start:
                caller.msg(MSG_FLEE_TRAPPED_IN_COMBAT)
            else:
                # This case (no exits, not aimed at, not in combat) might be caught by the later "nothing to flee from"
                # but if it reaches here, it means flee was typed with no actual threat and no exits.
                caller.msg(MSG_FLEE_NO_EXITS)
            splattercast.msg(f"{DEBUG_PREFIX_FLEE}_ABORT_NO_EXITS: {caller.key} has no exits. NDB Aimer: {ndb_aimer_locking_caller.key if ndb_aimer_locking_caller else 'None'}, Handler: {original_handler_at_flee_start.key if original_handler_at_flee_start else 'None'}.")
            return
        else:
            # Exits exist, check if they ALL lead to ranged targeters.
            all_exits_lead_to_ranged_targeters = True 
            for potential_exit in available_exits:
                destination_room = potential_exit.destination
                is_this_exit_safe_from_ranged_targeters = True # Assume safe until proven otherwise
                if destination_room:
                    for char_in_dest in destination_room.contents:
                        if char_in_dest == caller or not hasattr(char_in_dest, "ndb"): continue
                        
                        # Check if char_in_dest is in combat, targeting caller, with a ranged weapon
                        other_h = getattr(char_in_dest.ndb, "combat_handler", None)
                        if other_h and other_h.db.combat_is_running and other_h.db.combatants:
                            other_entry = next((e for e in other_h.db.combatants if e["char"] == char_in_dest), None)
                            if other_entry and other_h.get_target_obj(other_entry) == caller:
                                other_hands = getattr(char_in_dest, "hands", {})
                                other_weapon_obj = next((item for hand, item in other_hands.items() if item), None)
                                other_is_ranged = other_weapon_obj and hasattr(other_weapon_obj.db, "is_ranged") and other_weapon_obj.db.is_ranged
                                if other_is_ranged:
                                    is_this_exit_safe_from_ranged_targeters = False
                                    splattercast.msg(f"{DEBUG_PREFIX_FLEE}_PRE_CHECK_UNSAFE_EXIT: {caller.key} - exit {potential_exit.key} to {destination_room.key} is unsafe. Reason: {char_in_dest.key} is a ranged targeter in combat handler {other_h.key}.")
                                    break # This destination is unsafe due to this char_in_dest
                
                if is_this_exit_safe_from_ranged_targeters:
                    all_exits_lead_to_ranged_targeters = False # Found at least one safe exit
                    splattercast.msg(f"{DEBUG_PREFIX_FLEE}_PRE_CHECK_SAFE_EXIT_FOUND: {caller.key} found safe exit {potential_exit.key}.")
                    break # No need to check other exits if one safe one is found

            if all_exits_lead_to_ranged_targeters:
                caller.msg(MSG_FLEE_ALL_EXITS_COVERED)
                splattercast.msg(f"{DEBUG_PREFIX_FLEE}_ABORT_ALL_EXITS_TO_RANGED_TARGETERS: {caller.key}. Flee aborted.")
                return
        # --- END PRE-FLEE SAFETY CHECK ---

        # If the pre-flee safety check didn't abort, now check if there's anything to flee *from*.
        if not original_handler_at_flee_start and not ndb_aimer_locking_caller:
            caller.msg(MSG_NOTHING_TO_FLEE)
            splattercast.msg(f"{DEBUG_PREFIX_FLEE}_DEBUG ({caller.key}): 'Nothing to flee from' condition met (post-safety-check).")
            return

        # --- Part 1: Attempt to break an NDB-level aim lock ---
        # `current_aimer_for_break_attempt` is used locally for this part.
        # It starts as the NDB aimer and can be set to None if the aim is broken.
        current_aimer_for_break_attempt = ndb_aimer_locking_caller
        aim_successfully_broken = False

        if current_aimer_for_break_attempt:
            # Stale/Invalid Aim Check
            if not current_aimer_for_break_attempt.location or \
               current_aimer_for_break_attempt.location != caller.location or \
               getattr(current_aimer_for_break_attempt.ndb, "aiming_at", None) != caller:
                caller.msg(f"The one aiming at you ({current_aimer_for_break_attempt.get_display_name(caller)}) seems to have stopped or departed; you are no longer locked by their aim.")
                if hasattr(caller.ndb, "aimed_at_by"): del caller.ndb.aimed_at_by
                if hasattr(current_aimer_for_break_attempt.ndb, "aiming_at") and current_aimer_for_break_attempt.ndb.aiming_at == caller:
                    del current_aimer_for_break_attempt.ndb.aiming_at
                splattercast.msg(f"{DEBUG_PREFIX_FLEE}_CMD (AIM_BREAK_PHASE): NDB Aim lock on {caller.key} by {current_aimer_for_break_attempt.key} was stale/invalid. Lock broken.")
                current_aimer_for_break_attempt = None 
                aim_successfully_broken = True 
            else:
                # Active Aim Lock - Attempt to Break
                splattercast.msg(f"{DEBUG_PREFIX_FLEE}_CMD (AIM_BREAK_PHASE): {caller.key} is attempting to break NDB aim lock by {current_aimer_for_break_attempt.key}.")
                aimer_motorics_to_resist = get_numeric_stat(current_aimer_for_break_attempt, "motorics")
                caller_motorics = get_numeric_stat(caller, "motorics")
                flee_roll, _, _ = standard_roll(caller_motorics)
                resist_roll, _, _ = standard_roll(aimer_motorics_to_resist)
                splattercast.msg(f"{DEBUG_PREFIX_FLEE}_AIM_ROLL: {caller.key}(motorics:{flee_roll}) vs {current_aimer_for_break_attempt.key}(motorics:{resist_roll})")

                if flee_roll > resist_roll:
                    caller.msg(MSG_FLEE_BREAK_FREE_AIM.format(aimer=current_aimer_for_break_attempt.get_display_name(caller)))
                    if current_aimer_for_break_attempt.access(caller, "view"): 
                        current_aimer_for_break_attempt.msg(f"|y{caller.get_display_name(current_aimer_for_break_attempt)} breaks free from your aim!|n")
                    
                    if hasattr(current_aimer_for_break_attempt, "clear_aim_state"):
                        current_aimer_for_break_attempt.clear_aim_state(reason_for_clearing=f"as {caller.key} breaks free")
                    else: # Fallback if clear_aim_state is missing on aimer
                        if hasattr(current_aimer_for_break_attempt.ndb, "aiming_at"): del current_aimer_for_break_attempt.ndb.aiming_at
                    
                    if hasattr(caller.ndb, "aimed_at_by"): del caller.ndb.aimed_at_by # Clear on caller too
                    
                    splattercast.msg(f"{DEBUG_PREFIX_FLEE}_AIM_SUCCESS: {caller.key} broke free from {current_aimer_for_break_attempt.key}'s NDB aim.")
                    current_aimer_for_break_attempt = None # Successfully broke this aim
                    aim_successfully_broken = True
                else: # Failed to break NDB aim - AIMER ATTACKS!
                    caller_msg_flee_fail = MSG_FLEE_FAILED_BREAK_AIM.format(aimer=current_aimer_for_break_attempt.get_display_name(caller))
                    aimer_msg_flee_fail = ""
                    if current_aimer_for_break_attempt.access(caller, "view"):
                        aimer_msg_flee_fail = f"{caller.get_display_name(current_aimer_for_break_attempt)} tries to break your aim, but you maintain focus."
                    
                    splattercast.msg(f"{DEBUG_PREFIX_FLEE}_AIM_FAIL: {caller.key} failed to break {current_aimer_for_break_attempt.key}'s NDB aim. {current_aimer_for_break_attempt.key} initiates an attack.")
                    
                    # Aimer gets an immediate attack on the failed flee attempt
                    # Import and execute the attack command from the aimer's perspective
                    from commands.combat.core_actions import CmdAttack
                    
                    # Create a temporary attack command instance for the aimer
                    attack_cmd = CmdAttack()
                    attack_cmd.caller = current_aimer_for_break_attempt
                    attack_cmd.args = caller.key  # Target is the caller who failed to flee
                    attack_cmd.cmdstring = "attack"
                    
                    # Display messages about the aimer's opportunity attack
                    caller.msg(caller_msg_flee_fail)
                    if current_aimer_for_break_attempt.access(caller, "view"):
                        current_aimer_for_break_attempt.msg(aimer_msg_flee_fail)
                    
                    # Execute the attack
                    attack_cmd.func()
                    
                    return # Flee attempt ends here, aimer gets an attack.

        # --- Part 2: Combat Disengagement and Movement ---
        # If we reach here, any aim locks have been handled. Now attempt to flee from combat.
        splattercast.msg(f"{DEBUG_PREFIX_FLEE}_COMBAT_PHASE: {caller.key} attempting to disengage from combat.")
        
        # If we successfully broke an aim but have no combat handler, just move to safety
        if aim_successfully_broken and not original_handler_at_flee_start:
            chosen_exit = choice(available_exits)
            destination = chosen_exit.destination
            
            # Move to the chosen exit
            caller.move_to(destination, quiet=True)
            
            # Check for rigged grenades after successful movement
            from commands.CmdThrow import check_rigged_grenade, check_auto_defuse
            check_rigged_grenade(caller, chosen_exit)
            
            # Check for auto-defuse opportunities after fleeing to new room
            check_auto_defuse(caller)
            
            # Messages
            caller.msg(f"|gYou successfully flee {chosen_exit.key} to {destination.key}!|n")
            caller.location.msg_contents(f"|y{caller.get_display_name(caller.location)} has arrived, fleeing from an aimer.|n", exclude=[caller])
            
            # Message the room they left
            if hasattr(caller, 'previous_location') and caller.previous_location:
                caller.previous_location.msg_contents(f"|y{caller.get_display_name(caller.previous_location)} flees {chosen_exit.key}!|n")
            
            splattercast.msg(f"{DEBUG_PREFIX_FLEE}_SUCCESS: {caller.key} successfully fled after breaking aim via {chosen_exit.key} to {destination.key}.")
            return
        
        if original_handler_at_flee_start:
            # Character is in combat - attempt to disengage
            caller_entry = next((e for e in original_handler_at_flee_start.db.combatants if e["char"] == caller), None)
            if not caller_entry:
                # This shouldn't happen if ndb.combat_handler is properly managed
                caller.msg("Your combat state seems confused. Moving freely.")
                splattercast.msg(f"{DEBUG_PREFIX_FLEE}_ERROR: {caller.key} has combat handler but no entry.")
                super().at_traverse(caller, choice(available_exits).destination)
                return
                
            # Check if grappled - can't flee while grappled
            grappled_by_char = original_handler_at_flee_start.get_grappled_by_obj(caller_entry)
            if grappled_by_char:
                caller.msg(f"|rYou cannot flee while {grappled_by_char.get_display_name(caller)} is grappling you! Try to escape the grapple first.|n")
                splattercast.msg(f"{DEBUG_PREFIX_FLEE}_BLOCKED: {caller.key} cannot flee while grappled by {grappled_by_char.key}.")
                return
                
            # Attempt to disengage from combat
            # Get all opponents targeting the caller
            opponents_targeting_caller = []
            combatants_list = getattr(original_handler_at_flee_start.db, "combatants", [])
            if combatants_list:
                for entry in combatants_list:
                    if entry["char"] != caller:
                        target_obj = original_handler_at_flee_start.get_target_obj(entry)
                        if target_obj == caller:
                            opponents_targeting_caller.append(entry["char"])
            
            # Opposed roll to disengage
            if opponents_targeting_caller:
                valid_opponents = filter_valid_opponents(opponents_targeting_caller)
                highest_opponent_motorics, blocking_opponent = get_highest_opponent_stat(valid_opponents, "motorics")
                caller_motorics = get_numeric_stat(caller, "motorics")
                
                flee_roll, _, _ = standard_roll(caller_motorics)
                block_roll, _, _ = standard_roll(highest_opponent_motorics)
                
                splattercast.msg(f"{DEBUG_PREFIX_FLEE}_DISENGAGE_ROLL: {caller.key} (motorics:{caller_motorics}, roll:{flee_roll}) vs opponents (highest:{highest_opponent_motorics}, blocker:{blocking_opponent.key if blocking_opponent else 'None'}, roll:{block_roll})")
                
                if flee_roll <= block_roll:
                    # Failed to disengage
                    caller.msg(f"|rYou try to flee but {blocking_opponent.get_display_name(caller) if blocking_opponent else 'your opponents'} block your escape!|n")
                    if blocking_opponent:
                        blocking_opponent.msg(f"|gYou successfully block {caller.get_display_name(blocking_opponent)}'s attempt to flee!|n")
                    caller.location.msg_contents(
                        f"|y{caller.get_display_name(caller.location)} tries to flee but is blocked by their opponents!|n",
                        exclude=[caller] + opponents_targeting_caller
                    )
                    splattercast.msg(f"{DEBUG_PREFIX_FLEE}_DISENGAGE_FAIL: {caller.key} failed to disengage from combat.")
                    
                    # Apply flee failure penalty (skip next turn)
                    setattr(caller.ndb, NDB_SKIP_ROUND, True)
                    caller.msg("|rYour failed escape attempt leaves you vulnerable!|n")
                    return
            
            # Successfully disengaged (or no opponents targeting) - choose exit and move
            safe_exits = []
            for exit_obj in available_exits:
                destination = exit_obj.destination
                if destination:
                    # Check if this exit leads away from ranged targeters (already done in pre-check, but double-check)
                    is_safe = True
                    for char_in_dest in destination.contents:
                        if char_in_dest == caller or not hasattr(char_in_dest, "ndb"):
                            continue
                        other_handler = getattr(char_in_dest.ndb, "combat_handler", None)
                        if other_handler and getattr(other_handler.db, "combat_is_running", False):
                            other_entry = next((e for e in getattr(other_handler.db, "combatants", []) if e["char"] == char_in_dest), None)
                            if other_entry and original_handler_at_flee_start.get_target_obj(other_entry) == caller:
                                other_hands = getattr(char_in_dest, "hands", {})
                                other_weapon = next((item for hand, item in other_hands.items() if item), None)
                                if other_weapon and getattr(other_weapon.db, "is_ranged", False):
                                    is_safe = False
                                    break
                    if is_safe:
                        safe_exits.append(exit_obj)
            
            if not safe_exits:
                safe_exits = available_exits  # Fallback to any exit if none are "safe"
                
            chosen_exit = choice(safe_exits)
            destination = chosen_exit.destination
            
            # Remove from combat before moving (this also clears proximity)
            original_handler_at_flee_start.remove_combatant(caller)
            
            # Clear aim states before moving (consistent with traversal)
            if hasattr(caller, "clear_aim_state"):
                caller.clear_aim_state(reason_for_clearing="as you flee")
            else:
                clear_aim_state(caller)
            
            # Move to the chosen exit
            caller.move_to(destination, quiet=True)
            
            # Check for rigged grenades after successful movement
            from commands.CmdThrow import check_rigged_grenade, check_auto_defuse
            check_rigged_grenade(caller, chosen_exit)
            
            # Check for auto-defuse opportunities after fleeing to new room
            check_auto_defuse(caller)
            
            # Messages
            caller.msg(f"|gYou successfully flee {chosen_exit.key} to {destination.key}!|n")
            caller.location.msg_contents(f"|y{caller.get_display_name(caller.location)} has arrived, fleeing from combat.|n", exclude=[caller])
            
            # Message the room they left
            if caller.location != destination:  # Safety check
                old_location = caller.location
                old_location.msg_contents(f"|y{caller.get_display_name(old_location)} flees {chosen_exit.key}!|n")
            
            splattercast.msg(f"{DEBUG_PREFIX_FLEE}_SUCCESS: {caller.key} successfully fled via {chosen_exit.key} to {destination.key}.")
            
        else:
            # No combat handler and no aim was broken - this means nothing to flee from
            caller.msg("You have nothing to flee from.")
            splattercast.msg(f"{DEBUG_PREFIX_FLEE}_ERROR: {caller.key} reached flee movement phase with no combat handler and no aim broken.")

        # Ensure combat handler is updated if it still exists
        if original_handler_at_flee_start and hasattr(original_handler_at_flee_start, 'is_active'):
            if not original_handler_at_flee_start.is_active:
                original_handler_at_flee_start.start()


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
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        handler = getattr(caller.ndb, "combat_handler", None)

        if not handler:
            caller.msg(MSG_RETREAT_NOT_IN_COMBAT)
            return

        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry:
            caller.msg(MSG_RETREAT_COMBAT_DATA_MISSING)
            splattercast.msg(f"{DEBUG_PREFIX_RETREAT}_{DEBUG_ERROR}: {caller.key} has handler but no combat entry.")
            return

        # --- Check if caller is being grappled ---
        grappler_obj = handler.get_grappled_by_obj(caller_entry)
        if grappler_obj:
            caller.msg(MSG_CANNOT_WHILE_GRAPPLED_RETREAT.format(grappler=grappler_obj.get_display_name(caller) if grappler_obj else 'someone'))
            splattercast.msg(f"{DEBUG_PREFIX_RETREAT}_{DEBUG_FAIL}: {caller.key} attempted to retreat while grappled by {grappler_obj.key if grappler_obj else 'Unknown'}.")
            return

        if not hasattr(caller.ndb, "in_proximity_with") or not isinstance(caller.ndb.in_proximity_with, set):
            caller.msg(MSG_RETREAT_PROXIMITY_UNCLEAR)
            splattercast.msg(f"{DEBUG_PREFIX_RETREAT}_{DEBUG_ERROR}: {caller.key} ndb.in_proximity_with missing or not a set.")
            # Initialize it as a failsafe, though it should be set by handler
            caller.ndb.in_proximity_with = set()
            return

        if not caller.ndb.in_proximity_with:
            caller.msg(MSG_RETREAT_NO_PROXIMITY)
            splattercast.msg(f"{DEBUG_PREFIX_RETREAT}_INFO: {caller.key} tried to retreat but not in proximity with anyone.")
            return

        # Set retreat action to be processed on caller's next turn
        caller_entry["combat_action"] = COMBAT_ACTION_RETREAT
        caller.msg(MSG_RETREAT_PREPARE)
        splattercast.msg(f"{DEBUG_PREFIX_RETREAT}: {caller.key} queued retreat action for next turn.")

        # Ensure the combat handler is running
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
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Use robust handler validation to catch merge-related issues
        from world.combat.utils import validate_character_handler_reference
        is_valid, handler, error_msg = validate_character_handler_reference(caller)
        
        if not is_valid:
            splattercast.msg(f"{DEBUG_PREFIX_ADVANCE}_{DEBUG_ERROR}: {caller.key} handler validation failed: {error_msg}")
            caller.msg(MSG_ADVANCE_NOT_IN_COMBAT)
            return

        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry:
            caller.msg(MSG_ADVANCE_COMBAT_DATA_MISSING)
            splattercast.msg(f"{DEBUG_PREFIX_ADVANCE}_{DEBUG_ERROR}: {caller.key} has handler but no combat entry.")
            return

        # Check if being grappled
        grappled_by_char_obj = handler.get_grappled_by_obj(caller_entry)
        if grappled_by_char_obj:
            caller.msg(f"You cannot advance while {grappled_by_char_obj.get_display_name(caller) if grappled_by_char_obj else 'someone'} is grappling you. Try 'escape' first.")
            splattercast.msg(f"{DEBUG_PREFIX_ADVANCE}_{DEBUG_FAIL}: {caller.key} attempted to advance while grappled by {grappled_by_char_obj.key if grappled_by_char_obj else 'Unknown'}.")
            return

        # Determine target
        target = None
        if args:
            target = caller.search(args, location=caller.location, quiet=True)
            # Handle case where search returns a list
            if isinstance(target, list):
                if len(target) == 1:
                    target = target[0]
                elif len(target) > 1:
                    caller.msg(f"Multiple targets match '{args}'. Please be more specific.")
                    return
                else:
                    target = None
                    
            if not target:
                # Try searching in adjacent combat rooms
                managed_rooms = getattr(handler.db, "managed_rooms", [])
                for room in managed_rooms:
                    if room != caller.location:
                        potential_target = caller.search(args, location=room, quiet=True)
                        # Handle list results for adjacent rooms too
                        if isinstance(potential_target, list):
                            if len(potential_target) == 1:
                                target = potential_target[0]
                                break
                            elif len(potential_target) > 1:
                                caller.msg(f"Multiple targets match '{args}' in {room.key}. Please be more specific.")
                                return
                        elif potential_target:
                            target = potential_target
                            break
                            
            if not target:
                caller.msg(f"You cannot find '{args}' to advance on.")
                return
                
            if target == caller:
                caller.msg(MSG_ADVANCE_SELF_TARGET)
                return
        else:
            # Use current combat target
            target = handler.get_target_obj(caller_entry)
            if not target:
                caller.msg(MSG_ADVANCE_NO_TARGET)
                return

        # Check if target is valid
        target_entry = next((e for e in handler.db.combatants if e["char"] == target), None)
        if not target_entry:
            caller.msg(f"{target.get_display_name(caller)} is not in combat.")
            return

        # Check if already in proximity
        if hasattr(caller.ndb, "in_proximity_with") and caller.ndb.in_proximity_with and target in caller.ndb.in_proximity_with:
            caller.msg(f"You are already in melee proximity with {target.get_display_name(caller)}.")
            return

        # Set advance action to be processed on caller's next turn
        caller_entry["combat_action"] = COMBAT_ACTION_ADVANCE
        caller_entry["combat_action_target"] = target  # Store target for handler processing
        caller.msg(MSG_ADVANCE_PREPARE.format(target=target.get_display_name(caller)))
        splattercast.msg(f"{DEBUG_PREFIX_ADVANCE}: {caller.key} queued advance action on {target.key} for next turn.")

        # Ensure combat handler is active
        if handler and not handler.is_active:
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
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        handler = getattr(caller.ndb, "combat_handler", None)

        if not handler:
            caller.msg(MSG_CHARGE_NOT_IN_COMBAT)
            return

        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry:
            caller.msg(MSG_CHARGE_COMBAT_DATA_MISSING)
            splattercast.msg(f"{DEBUG_PREFIX_CHARGE}_{DEBUG_ERROR}: {caller.key} has handler but no combat entry.")
            return

        # Check if being grappled
        grappled_by_char_obj = handler.get_grappled_by_obj(caller_entry)
        if grappled_by_char_obj:
            caller.msg(f"You cannot charge while {grappled_by_char_obj.get_display_name(caller) if grappled_by_char_obj else 'someone'} is grappling you. Try 'escape' first.")
            splattercast.msg(f"{DEBUG_PREFIX_CHARGE}_{DEBUG_FAIL}: {caller.key} attempted to charge while grappled by {grappled_by_char_obj.key if grappled_by_char_obj else 'Unknown'}.")
            return

        # Check if caller is grappling someone
        grappling_victim_obj = handler.get_grappling_obj(caller_entry)
        if grappling_victim_obj:
            if args:
                # Caller specified a target while grappling
                target_search = caller.search(args, location=caller.location, quiet=True)
                # Handle case where search returns a list
                if isinstance(target_search, list):
                    if len(target_search) == 1:
                        target_search = target_search[0]
                    elif len(target_search) > 1:
                        caller.msg(f"Multiple targets match '{args}'. Please be more specific.")
                        return
                    else:
                        target_search = None
                        
                if not target_search:
                    # Try searching in adjacent combat rooms
                    managed_rooms = getattr(handler.db, "managed_rooms", [])
                    for room in managed_rooms:
                        if room != caller.location:
                            potential_target = caller.search(args, location=room, quiet=True)
                            # Handle list results for adjacent rooms too
                            if isinstance(potential_target, list):
                                if len(potential_target) == 1:
                                    target_search = potential_target[0]
                                    break
                                elif len(potential_target) > 1:
                                    caller.msg(f"Multiple targets match '{args}' in {room.key}. Please be more specific.")
                                    return
                            elif potential_target:
                                target_search = potential_target
                                break
                
                if target_search == grappling_victim_obj:
                    # Trying to charge the person they're grappling
                    caller.msg(f"You cannot charge {grappling_victim_obj.get_display_name(caller)} while you are grappling them! Release the grapple first or choose a different target.")
                    splattercast.msg(f"{DEBUG_PREFIX_CHARGE}_{DEBUG_FAIL}: {caller.key} attempted to charge their grapple victim {grappling_victim_obj.key}.")
                    return
                elif target_search:
                    # Charging someone else - prepare to potentially release grapple on successful charge
                    # (Grapple release will be handled by combat handler only on successful charge)
                    caller.msg(f"|yYou prepare to release your grapple on {grappling_victim_obj.get_display_name(caller)} and charge {target_search.get_display_name(caller)}!|n")
                    splattercast.msg(f"{DEBUG_PREFIX_CHARGE}_GRAPPLE_CHARGE: {caller.key} preparing to charge {target_search.key} while grappling {grappling_victim_obj.key}.")
                    # Continue with normal charge logic using target_search
                else:
                    caller.msg(f"You cannot find '{args}' to charge at.")
                    return
            else:
                # No target specified while grappling - require explicit target
                caller.msg(f"You are currently grappling {grappling_victim_obj.get_display_name(caller)}. You must specify a target to charge, or use 'escape' to release the grapple first.")
                splattercast.msg(f"{DEBUG_PREFIX_CHARGE}_{DEBUG_FAIL}: {caller.key} attempted to charge with no target while grappling {grappling_victim_obj.key}.")
                return

        # Determine target
        target = None
        if args:
            target = caller.search(args, location=caller.location, quiet=True)
            # Handle case where search returns a list
            if isinstance(target, list):
                if len(target) == 1:
                    target = target[0]
                elif len(target) > 1:
                    caller.msg(f"Multiple targets match '{args}'. Please be more specific.")
                    return
                else:
                    target = None
                    
            if not target:
                # Try searching in adjacent combat rooms
                managed_rooms = getattr(handler.db, "managed_rooms", [])
                for room in managed_rooms:
                    if room != caller.location:
                        potential_target = caller.search(args, location=room, quiet=True)
                        # Handle list results for adjacent rooms too
                        if isinstance(potential_target, list):
                            if len(potential_target) == 1:
                                target = potential_target[0]
                                break
                            elif len(potential_target) > 1:
                                caller.msg(f"Multiple targets match '{args}' in {room.key}. Please be more specific.")
                                return
                        elif potential_target:
                            target = potential_target
                            break
                            
            if not target:
                caller.msg(f"You cannot find '{args}' to charge.")
                return
                
            if target == caller:
                caller.msg(MSG_CHARGE_SELF_TARGET)
                return
        else:
            # Use current combat target
            target = handler.get_target_obj(caller_entry)
            if not target:
                caller.msg(MSG_CHARGE_NO_TARGET)
                return

        # Check if target is valid
        target_entry = next((e for e in handler.db.combatants if e["char"] == target), None)
        if not target_entry:
            caller.msg(f"{target.get_display_name(caller)} is not in combat.")
            return

        # Check if already in proximity
        if hasattr(caller.ndb, "in_proximity_with") and caller.ndb.in_proximity_with and target in caller.ndb.in_proximity_with:
            caller.msg(f"You are already in melee proximity with {target.get_display_name(caller)}.")
            return

        # Set charge action to be processed on caller's next turn
        caller_entry["combat_action"] = COMBAT_ACTION_CHARGE
        caller_entry["combat_action_target"] = target  # Store target for handler processing
        caller.msg(MSG_CHARGE_PREPARE.format(target=target.get_display_name(caller)))
        splattercast.msg(f"{DEBUG_PREFIX_CHARGE}: {caller.key} queued charge action on {target.key} for next turn.")

        # Ensure combat handler is active
        if handler and not handler.is_active:
            handler.start()


class CmdJump(Command):
    """
    Perform heroic explosive sacrifice or tactical descent/gap jumping.

    Usage:
      jump on <explosive>           # Heroic sacrifice - absorb explosive damage
      jump off <direction> edge     # Tactical descent from elevated position  
      jump across <direction> edge  # Horizontal leap across gaps at same level

    Examples:
      jump on grenade              # Absorb grenade blast to protect others
      jump off north edge          # Descend from rooftop/balcony to north
      jump across east edge        # Leap across gap to the east

    The jump command serves heroic and tactical functions. Jumping on explosives
    provides complete protection to others in proximity at the cost of taking all
    damage yourself. Edge jumping allows vertical descent from elevated positions
    or horizontal gap crossing with risk/reward mechanics.

    All edge jumps require Motorics skill checks and may result in falling if failed.
    Explosive sacrifice is instant and always succeeds but consumes your life for others.
    """
    
    key = "jump"
    locks = "cmd:all()"
    help_category = "Combat"
    
    def parse(self):
        """Parse jump command with syntax detection."""
        self.args = self.args.strip()
        
        # Initialize parsing results
        self.explosive_name = None
        self.direction = None
        self.jump_type = None  # 'on_explosive', 'off_edge', 'across_gap'
        
        if not self.args:
            return
        
        # Parse for "on" keyword - explosive sacrifice
        if self.args.startswith("on "):
            parts = self.args.split(" ", 1)
            if len(parts) == 2:
                self.explosive_name = parts[1].strip()
                self.jump_type = "on_explosive"
                return
        
        # Parse for "off" keyword - tactical descent
        if self.args.startswith("off "):
            parts = self.args.split(" ", 1)
            if len(parts) == 2:
                direction_part = parts[1].strip()
                if direction_part.endswith(" edge"):
                    self.direction = direction_part[:-5].strip()  # Remove " edge"
                    self.jump_type = "off_edge"
                    return
        
        # Parse for "across" keyword - gap jumping
        if self.args.startswith("across "):
            parts = self.args.split(" ", 1)
            if len(parts) == 2:
                direction_part = parts[1].strip()
                if direction_part.endswith(" edge"):
                    self.direction = direction_part[:-5].strip()  # Remove " edge"
                    self.jump_type = "across_gap"
                    return
    
    def func(self):
        """Execute the jump command."""
        if not self.args:
            self.caller.msg("Jump how? Use 'jump on <explosive>', 'jump off <direction> edge', or 'jump across <direction> edge'.")
            return
        
        if self.jump_type == "on_explosive":
            self.handle_explosive_sacrifice()
        elif self.jump_type == "off_edge":
            self.handle_edge_descent()
        elif self.jump_type == "across_gap":
            self.handle_gap_jump()
        else:
            self.caller.msg("Invalid jump syntax. Use 'jump on <explosive>', 'jump off <direction> edge', or 'jump across <direction> edge'.")
    
    def handle_explosive_sacrifice(self):
        """Handle jumping on explosive for heroic sacrifice."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not self.explosive_name:
            self.caller.msg("Jump on what explosive?")
            return
        
        # Find explosive in current room
        explosive = self.caller.search(self.explosive_name, location=self.caller.location, quiet=True)
        if not explosive:
            self.caller.msg(f"You don't see '{self.explosive_name}' here.")
            return
        
        explosive = explosive[0]  # Take first match
        
        # Validate it's an explosive
        if not getattr(explosive.db, "is_explosive", False):
            self.caller.msg(f"{explosive.key} is not an explosive device.")
            return
        
        # Check if it's armed (pin pulled)
        if not getattr(explosive.db, "pin_pulled", False):
            self.caller.msg(f"{explosive.key} is not armed - you cannot sacrifice yourself for an inactive explosive.")
            return
        
        # Check if it has an active countdown
        remaining_time = getattr(explosive.ndb, "countdown_remaining", None)
        if remaining_time is None or remaining_time <= 0:
            self.caller.msg(f"{explosive.key} is no longer counting down - too late for heroic sacrifice.")
            return
        
        splattercast.msg(f"JUMP_SACRIFICE: {self.caller.key} attempting heroic sacrifice on {explosive.key} with {remaining_time}s remaining.")
        
        # Get blast damage
        blast_damage = getattr(explosive.db, "blast_damage", 10)
        
        # Heroic sacrifice: caller takes ALL damage, others take none
        from world.combat.utils import apply_damage
        apply_damage(self.caller, blast_damage)
        
        # Move caller to explosive's location and inherit ALL its proximity relationships
        from world.combat.proximity import establish_proximity, get_proximity_list
        
        # Get everyone currently in proximity to the explosive
        explosive_proximity = getattr(explosive.ndb, NDB_PROXIMITY, set())
        if explosive_proximity:
            for char in list(explosive_proximity):
                if char != self.caller and hasattr(char, 'location') and char.location:
                    establish_proximity(self.caller, char)
                    splattercast.msg(f"JUMP_SACRIFICE_PROXIMITY: Established proximity between {self.caller.key} and {char.key}")
        
        # Stop any active timer script on the explosive FIRST
        timer_scripts_stopped = 0
        for script in explosive.scripts.all():
            if "timer" in script.key.lower() or "countdown" in script.key.lower() or "grenade" in script.key.lower():
                script.stop()
                timer_scripts_stopped += 1
                splattercast.msg(f"JUMP_SACRIFICE: Stopped timer script {script.key} on {explosive.key}")
        
        # Cancel delay timers stored in NDB (the actual timer mechanism)
        delay_timers_stopped = 0
        if hasattr(explosive.ndb, "grenade_timer"):
            timer = getattr(explosive.ndb, "grenade_timer", None)
            if timer:
                try:
                    timer.cancel()  # Cancel the utils.delay timer
                    delay_timers_stopped += 1
                    splattercast.msg(f"JUMP_SACRIFICE: Cancelled delay timer on {explosive.key}")
                except:
                    splattercast.msg(f"JUMP_SACRIFICE: Failed to cancel delay timer on {explosive.key}")
            delattr(explosive.ndb, "grenade_timer")
        
        # Clear explosive's timer attributes
        if hasattr(explosive.ndb, "countdown_remaining"):
            delattr(explosive.ndb, "countdown_remaining")
        
        splattercast.msg(f"JUMP_SACRIFICE: Stopped {timer_scripts_stopped} timer scripts, {delay_timers_stopped} delay timers, cleared countdown attributes")
        
        # Prevent chain reactions - explosive is absorbed by hero
        explosive.delete()
        
        # Dramatic messaging
        self.caller.location.msg_contents(
            f"|R{self.caller.key} makes the ultimate sacrifice, leaping onto {self.explosive_name} and absorbing the full blast to protect everyone else!|n"
        )
        
        splattercast.msg(f"JUMP_SACRIFICE_SUCCESS: {self.caller.key} absorbed {blast_damage} damage from {explosive.key}, protecting all others in proximity.")
        
        # Skip turn if in combat (heroic actions have consequences)
        setattr(self.caller.ndb, NDB_SKIP_ROUND, True)
    
    def handle_edge_descent(self):
        """Handle jumping off edge for tactical descent."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not self.direction:
            self.caller.msg("Jump off which direction?")
            return
        
        # Find exit in the specified direction
        exit_obj = self.find_edge_exit(self.direction)
        if not exit_obj:
            return
        
        # Validate it's an edge
        if not getattr(exit_obj.db, "is_edge", False):
            self.caller.msg(f"The {self.direction} exit is not an edge you can jump from.")
            return
        
        destination = exit_obj.destination
        if not destination:
            self.caller.msg(f"The {self.direction} edge doesn't lead anywhere safe to land.")
            return
        
        # Check if caller is grappled (can't jump while grappled)
        handler = getattr(self.caller.ndb, "combat_handler", None)
        if handler:
            caller_entry = next((e for e in getattr(handler.db, "combatants", []) if e.get("char") == self.caller), None)
            if caller_entry:
                grappler_obj = handler.get_grappled_by_obj(caller_entry)
                if grappler_obj:
                    self.caller.msg(f"You cannot jump while {grappler_obj.key} is grappling you!")
                    return
        
        # Edge descent is tactical - requires Motorics check for safe landing
        caller_motorics = get_numeric_stat(self.caller, "motorics")
        edge_difficulty = getattr(exit_obj.db, "edge_difficulty", 8)  # Default moderate difficulty
        
        motorics_roll, _, _ = standard_roll(caller_motorics)
        success = motorics_roll >= edge_difficulty
        
        splattercast.msg(f"JUMP_EDGE_DESCENT: {self.caller.key} motorics:{motorics_roll} vs difficulty:{edge_difficulty}, success:{success}")
        
        if success:
            # Successful descent
            self.caller.move_to(destination, quiet=True)
            
            # Clear combat state if fleeing via edge
            if handler:
                handler.remove_combatant(self.caller)
            
            # Clear aim states
            clear_aim_state(self.caller)
            
            # Check for rigged grenades at destination
            from commands.CmdThrow import check_rigged_grenade, check_auto_defuse
            check_rigged_grenade(self.caller, exit_obj)
            check_auto_defuse(self.caller)
            
            # Success messages
            self.caller.msg(f"|gYou successfully leap from the {self.direction} edge and land safely in {destination.key}!|n")
            self.caller.location.msg_contents(f"|y{self.caller.key} arrives with a tactical leap from above.|n", exclude=[self.caller])
            
            # Message the room they left
            if hasattr(self.caller, 'previous_location') and self.caller.previous_location:
                self.caller.previous_location.msg_contents(f"|y{self.caller.key} leaps off the {self.direction} edge!|n")
            
            splattercast.msg(f"JUMP_EDGE_SUCCESS: {self.caller.key} successfully descended via {self.direction} edge to {destination.key}")
        else:
            # Failed descent - potential fall damage
            self.handle_fall_failure(exit_obj, destination, "edge descent")
    
    def handle_gap_jump(self):
        """Handle jumping across gap between same-level areas."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not self.direction:
            self.caller.msg("Jump across which direction?")
            return
        
        # Find exit in the specified direction
        exit_obj = self.find_edge_exit(self.direction)
        if not exit_obj:
            return
        
        # Validate it's a gap
        if not getattr(exit_obj.db, "is_gap", False):
            self.caller.msg(f"The {self.direction} exit is not a gap you can jump across.")
            return
        
        destination = exit_obj.destination
        if not destination:
            self.caller.msg(f"The {self.direction} gap doesn't lead anywhere safe to land.")
            return
        
        # Check if caller is grappled (can't jump while grappled)
        handler = getattr(self.caller.ndb, "combat_handler", None)
        if handler:
            caller_entry = next((e for e in getattr(handler.db, "combatants", []) if e.get("char") == self.caller), None)
            if caller_entry:
                grappler_obj = handler.get_grappled_by_obj(caller_entry)
                if grappler_obj:
                    self.caller.msg(f"You cannot jump while {grappler_obj.key} is grappling you!")
                    return
        
        # Gap jumping requires Motorics check vs gap difficulty
        caller_motorics = get_numeric_stat(self.caller, "motorics")
        gap_difficulty = getattr(exit_obj.db, "gap_difficulty", 10)  # Default hard difficulty
        
        motorics_roll, _, _ = standard_roll(caller_motorics)
        success = motorics_roll >= gap_difficulty
        
        splattercast.msg(f"JUMP_GAP: {self.caller.key} motorics:{motorics_roll} vs difficulty:{gap_difficulty}, success:{success}")
        
        if success:
            # Successful gap jump
            self.execute_successful_gap_jump(exit_obj, destination)
        else:
            # Failed gap jump - create sky room for transit and fall
            self.handle_gap_jump_failure(exit_obj, destination)
    
    def find_edge_exit(self, direction):
        """Find and validate an exit in the specified direction."""
        # Search for exit by direction name
        exit_obj = self.caller.search(direction, location=self.caller.location, quiet=True)
        
        if not exit_obj:
            self.caller.msg(f"There is no exit to the {direction}.")
            return None
        
        exit_obj = exit_obj[0]  # Take first match
        
        # Verify it's actually an exit with a destination
        if not hasattr(exit_obj, 'destination') or not exit_obj.destination:
            self.caller.msg(f"The {direction} exit doesn't lead anywhere.")
            return None
        
        return exit_obj
    
    def execute_successful_gap_jump(self, exit_obj, destination):
        """Execute a successful gap jump with sky room transit."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Find or use existing sky room for this gap
        sky_room = self.get_sky_room_for_gap(self.caller.location, destination, self.direction)
        if not sky_room:
            # Fallback: direct movement if no sky room configured
            splattercast.msg(f"JUMP_GAP_NO_SKY: No sky room configured for {self.caller.location.key} -> {destination.key}, using direct movement")
            self.caller.move_to(destination, quiet=True)
            self.finalize_successful_gap_jump(destination)
            return
        
        # Move to sky room first (transit phase)
        self.caller.move_to(sky_room, quiet=True)
        
        # Message the origin room
        if hasattr(self.caller, 'previous_location') and self.caller.previous_location:
            self.caller.previous_location.msg_contents(f"|y{self.caller.key} leaps across the {self.direction} gap!|n")
        
        # Brief sky room experience
        self.caller.msg(f"|CYou soar through the air across the {self.direction} gap...|n")
        
        # Delay before landing (simulate transit time)
        def land_successfully():
            if self.caller.location == sky_room:
                self.caller.move_to(destination, quiet=True)
                self.finalize_successful_gap_jump(destination)
        
        # Schedule landing
        delay(2, land_successfully)
    
    def finalize_successful_gap_jump(self, destination):
        """Finalize successful gap jump with cleanup and messaging."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Clear combat state if fleeing via gap
        handler = getattr(self.caller.ndb, "combat_handler", None)
        if handler:
            handler.remove_combatant(self.caller)
        
        # Clear aim states
        clear_aim_state(self.caller)
        
        # Check for rigged grenades at destination
        from commands.CmdThrow import check_rigged_grenade, check_auto_defuse
        exit_obj = self.find_edge_exit(self.direction)
        if exit_obj:
            check_rigged_grenade(self.caller, exit_obj)
        check_auto_defuse(self.caller)
        
        # Success messages
        self.caller.msg(f"|gYou successfully leap across the gap and land safely in {destination.key}!|n")
        self.caller.location.msg_contents(f"|y{self.caller.key} arrives with a spectacular leap from across the gap.|n", exclude=[self.caller])
        
        splattercast.msg(f"JUMP_GAP_SUCCESS: {self.caller.key} successfully crossed gap to {destination.key}")
    
    def handle_gap_jump_failure(self, exit_obj, destination):
        """Handle failed gap jump with fall consequences."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Find or use existing sky room for this gap
        sky_room = self.get_sky_room_for_gap(self.caller.location, destination, self.direction)
        if not sky_room:
            # Fallback: apply damage in current room if no sky room configured
            splattercast.msg(f"JUMP_GAP_FAIL_NO_SKY: No sky room configured for {self.caller.location.key} -> {destination.key}, applying damage in place")
            self.handle_fall_failure(exit_obj, destination, "gap jump")
            return
        
        # Move to sky room first (failed transit)
        self.caller.move_to(sky_room, quiet=True)
        
        # Message the origin room
        if hasattr(self.caller, 'previous_location') and self.caller.previous_location:
            self.caller.previous_location.msg_contents(f"|r{self.caller.key} attempts to leap across the {self.direction} gap but falls short!|n")
        
        # Failed jump experience
        self.caller.msg(f"|rYou leap for the {self.direction} gap but don't make it far enough... you're falling!|n")
        
        # Find fall room (existing room, not created)
        fall_room = self.get_fall_room_for_gap(destination, exit_obj)
        
        # Calculate fall damage
        fall_distance = getattr(exit_obj.db, "fall_distance", 2)  # Default 2 rooms
        fall_damage = fall_distance * 5  # 5 damage per room fallen
        
        def handle_fall_landing():
            if self.caller.location == sky_room:
                # Move to fall room
                self.caller.move_to(fall_room, quiet=True)
                
                # Apply fall damage
                from world.combat.utils import apply_damage
                apply_damage(self.caller, fall_damage)
                
                # Clear combat state (fell out of combat)
                handler = getattr(self.caller.ndb, "combat_handler", None)
                if handler:
                    handler.remove_combatant(self.caller)
                
                # Clear aim states
                clear_aim_state(self.caller)
                
                # Failure messages
                self.caller.msg(f"|rYou fall {fall_distance} stories and crash into {fall_room.key}, taking {fall_damage} damage!|n")
                self.caller.location.msg_contents(f"|r{self.caller.key} crashes down from above, having failed a gap jump!|n", exclude=[self.caller])
                
                splattercast.msg(f"JUMP_GAP_FAIL: {self.caller.key} fell {fall_distance} rooms, took {fall_damage} damage, landed in {fall_room.key}")
        
        # Schedule fall landing
        delay(2, handle_fall_landing)
    
    def handle_fall_failure(self, exit_obj, destination, fall_type):
        """Handle general fall failure (for edge descent failures)."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # For edge descent failure, apply damage but stay in current room
        fall_damage = getattr(exit_obj.db, "fall_damage", 8)  # Default moderate damage
        
        from world.combat.utils import apply_damage
        apply_damage(self.caller, fall_damage)
        
        # Skip turn due to failed attempt
        setattr(self.caller.ndb, NDB_SKIP_ROUND, True)
        
        # Failure messages
        self.caller.msg(f"|rYou slip during your {fall_type} attempt and take {fall_damage} damage from the awkward landing!|n")
        self.caller.location.msg_contents(f"|r{self.caller.key} slips during a {fall_type} attempt and crashes back down!|n", exclude=[self.caller])
        
        splattercast.msg(f"JUMP_FALL_FAIL: {self.caller.key} failed {fall_type}, took {fall_damage} damage, remained in {self.caller.location.key}")
    
    def get_sky_room_for_gap(self, origin, destination, direction):
        """Get the existing sky room for this gap jump route."""
        # Strategy 1: Look for sky room tagged with origin+destination combination
        sky_room_tag = f"sky_{origin.id}_{destination.id}"
        sky_rooms = origin.search(sky_room_tag, global_search=True, quiet=True)
        if sky_rooms:
            return sky_rooms[0]
        
        # Strategy 2: Look for sky room with explicit origin/destination properties
        # This will work when builders manually create sky rooms
        from evennia.utils.search import search_object
        potential_sky_rooms = search_object(tag="sky_room", category="room_type")
        for sky_room in potential_sky_rooms:
            sky_origin = getattr(sky_room.db, "origin_room", None)
            sky_destination = getattr(sky_room.db, "destination_room", None)
            if sky_origin == origin and sky_destination == destination:
                return sky_room
        
        # Strategy 3: Look for bidirectional sky room (works for both directions)
        for sky_room in potential_sky_rooms:
            sky_origin = getattr(sky_room.db, "origin_room", None)
            sky_destination = getattr(sky_room.db, "destination_room", None)
            if (sky_origin == origin and sky_destination == destination) or \
               (sky_origin == destination and sky_destination == origin):
                return sky_room
        
        # No sky room found - this gap doesn't have sky transit configured
        return None
    
    def get_fall_room_for_gap(self, intended_destination, exit_obj):
        """Get the fall room for a failed gap jump."""
        # Strategy 1: Check if exit specifies a fall room
        fall_room = getattr(exit_obj.db, "fall_room", None)
        if fall_room and hasattr(fall_room, 'location'):
            return fall_room
        
        # Strategy 2: Look for room tagged as fall room for this destination
        fall_tag = f"fall_room_{intended_destination.id}"
        fall_rooms = intended_destination.search(fall_tag, global_search=True, quiet=True)
        if fall_rooms:
            return fall_rooms[0]
        
        # Strategy 3: Look for dedicated crash site near destination
        potential_fall_rooms = intended_destination.search("crash", location=intended_destination, quiet=True)
        if potential_fall_rooms:
            for room in potential_fall_rooms:
                if getattr(room.db, "is_fall_room", False):
                    return room
        
        # Fallback: Use intended destination (soft landing)
        return intended_destination
