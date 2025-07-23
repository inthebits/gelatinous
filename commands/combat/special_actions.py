"""
Special Combat Actions Module

Contains specialized combat commands that add tactical depth:
- CmdGrapple: Initiate a grapple with a target
- CmdEscapeGrapple: Attempt to escape from being grappled
- CmdReleaseGrapple: Release a grapple you have on someone
- CmdDisarm: Attempt to disarm a target's weapon
- CmdAim: Aim at a target or direction for ranged attacks

These commands provide advanced tactical options for experienced combatants
and add complexity to combat encounters.
"""

from evennia import Command
from evennia.comms.models import ChannelDB

from world.combat.constants import (
    MSG_GRAPPLE_WHO, MSG_GRAPPLE_NO_TARGET, MSG_CANNOT_GRAPPLE_SELF, MSG_CANNOT_GRAPPLE_TARGET,
    MSG_GRAPPLE_HANDLER_ERROR, MSG_GRAPPLE_COMBAT_ADD_ERROR, MSG_ALREADY_GRAPPLING,
    MSG_CANNOT_GRAPPLE_WHILE_GRAPPLED, MSG_TARGET_ALREADY_GRAPPLED, MSG_GRAPPLE_PREPARE,
    MSG_ESCAPE_NOT_IN_COMBAT, MSG_ESCAPE_NOT_REGISTERED, MSG_ESCAPE_NOT_GRAPPLED,
    MSG_RELEASE_NOT_IN_COMBAT, MSG_RELEASE_NOT_GRAPPLING,
    MSG_NOT_IN_COMBAT, MSG_DISARM_NO_TARGET, MSG_DISARM_NOT_IN_PROXIMITY, MSG_GRAPPLE_NOT_IN_PROXIMITY,
    MSG_DISARM_TARGET_EMPTY_HANDS, MSG_DISARM_FAILED, MSG_DISARM_RESISTED, MSG_DISARM_NOTHING_TO_DISARM,
    MSG_DISARM_SUCCESS_ATTACKER, MSG_DISARM_SUCCESS_VICTIM, MSG_DISARM_SUCCESS_OBSERVER,
    MSG_AIM_WHO_WHAT, MSG_AIM_SELF_TARGET, MSG_GRAPPLE_VIOLENT_SWITCH, MSG_GRAPPLE_ESCAPE_VIOLENT_SWITCH,
    DEBUG_PREFIX_GRAPPLE, SPLATTERCAST_CHANNEL, NDB_PROXIMITY,
    NDB_COMBAT_HANDLER, COMBAT_ACTION_DISARM, MSG_DISARM_PREPARE
)
from world.combat.utils import log_combat_action, get_numeric_stat, roll_stat, initialize_proximity_ndb


class CmdGrapple(Command):
    """
    Attempt to grapple a target in your current room.

    Usage:
        grapple <target>

    If you are not in combat, this will initiate combat and allow you to rush in.
    If you are in combat, you must be in melee proximity with the target.
    If the target is already grappled by someone else, you will contest against
    the current grappler to take control of the grapple.
    
    If successful, you will be grappling the target, and they will be grappled by you.
    """
    key = "grapple"
    aliases = ["wrestle"]
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        from world.combat.handler import get_or_create_combat
        from evennia.utils.utils import inherits_from
        
        caller = self.caller

        if not self.args:
            caller.msg(MSG_GRAPPLE_WHO)
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
            caller.msg(MSG_GRAPPLE_NO_TARGET)
            log_combat_action(caller, "grapple_fail", details=f"tried to grapple '{search_name}' but found no valid target in the room")
            return

        target = matches[0]

        if target == caller:
            caller.msg(MSG_CANNOT_GRAPPLE_SELF)
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg(MSG_CANNOT_GRAPPLE_TARGET)
            log_combat_action(caller, "grapple_fail", target, details="tried to grapple non-character object")
            return

        # --- Get or create combat handler ---
        handler = get_or_create_combat(caller.location)
        if not handler:
            caller.msg(MSG_GRAPPLE_HANDLER_ERROR)
            return

        # --- Add caller and target to combat if not already in ---
        # Record if the caller initiated combat with this action
        caller_initiated_combat_this_action = not any(e["char"] == caller for e in handler.db.combatants)

        caller_is_in_combat = any(e["char"] == caller for e in handler.db.combatants)
        target_is_in_combat = any(e["char"] == target for e in handler.db.combatants)

        if not caller_is_in_combat:
            log_combat_action(caller, "grapple_initiate", target, details="initiating grapple combat")
            handler.add_combatant(caller) 
            handler.add_combatant(target) 
        elif not target_is_in_combat: 
            log_combat_action(caller, "grapple_join", target, details="attempting to grapple (adding target to combat)")
            handler.add_combatant(target)
        
        # --- Now retrieve combat entries; they should exist ---
        caller_combat_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        target_combat_entry = next((e for e in handler.db.combatants if e["char"] == target), None)

        if not caller_combat_entry: 
            caller.msg(MSG_GRAPPLE_COMBAT_ADD_ERROR)
            log_combat_action(caller, "grapple_error", details="CRITICAL: failed to be added to combat")
            return
        if not target_combat_entry: 
            caller.msg(f"There was an issue adding {target.key} to combat. Please try again.")
            log_combat_action(caller, "grapple_error", target, details="CRITICAL: target failed to be added to combat")
            return

        # Default to not yielding if already in combat or grapple fails.
        # This will be overridden if grapple is successful AND initiated combat.
        caller_combat_entry["is_yielding"] = False 

        # --- Grapple-specific checks (already grappling, being grappled, target grappled) ---
        if handler.get_grappling_obj(caller_combat_entry):
            currently_grappling = handler.get_grappling_obj(caller_combat_entry)
            caller.msg(MSG_ALREADY_GRAPPLING.format(target=currently_grappling.key))
            log_combat_action(caller, "grapple_fail", target, details=f"already grappling {currently_grappling.key}")
            return
        
        if handler.get_grappled_by_obj(caller_combat_entry):
            grappler = handler.get_grappled_by_obj(caller_combat_entry)
            caller.msg(MSG_CANNOT_GRAPPLE_WHILE_GRAPPLED.format(grappler=grappler.key))
            log_combat_action(caller, "grapple_fail", target, details=f"being grappled by {grappler.key}")
            return

        if handler.get_grappled_by_obj(target_combat_entry):
            # Check if it's the caller grappling them (should be caught above, but good for clarity)
            # Or if someone *else* is grappling them
            target_grappler = handler.get_grappled_by_obj(target_combat_entry)
            if target_grappler != caller:
                 caller.msg(MSG_TARGET_ALREADY_GRAPPLED.format(target=target.key, grappler=target_grappler.key))
                 log_combat_action(caller, "grapple_fail", target, details=f"target already grappled by {target_grappler.key}")
                 return

        # --- Proximity check (unless initiating combat) ---
        # If caller initiated combat this action, they can rush in without proximity
        # Otherwise, they must be in melee proximity to grapple
        if not caller_initiated_combat_this_action:
            initialize_proximity_ndb(caller)
            if not hasattr(caller.ndb, NDB_PROXIMITY) or target not in caller.ndb.in_proximity_with:
                caller.msg(MSG_GRAPPLE_NOT_IN_PROXIMITY.format(target=target.key))
                log_combat_action(caller, "grapple_fail", target, details="not in melee proximity")
                return
        
        # --- Set combat action ---
        # Ensure combat_action key exists for the entry
        if "combat_action" not in caller_combat_entry:
            caller_combat_entry["combat_action"] = {}
            
        # Store whether caller initiated combat for use in handler
        caller_combat_entry["initiated_combat_this_action"] = caller_initiated_combat_this_action
        
        # Store whether target initiated combat (for failed grapple yielding logic)
        target_initiated_combat_this_action = not target_is_in_combat
        target_combat_entry["initiated_combat_this_action"] = target_initiated_combat_this_action
        
        # --- Establish proximity for grapple combat ---
        if caller.location == target.location:
            # Same room grapple - establish proximity for melee combat
            from world.combat.proximity import establish_proximity
            establish_proximity(caller, target)
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_GRAPPLE}: Established proximity between {caller.key} and {target.key} for grapple combat.")

        # --- Determine grapple type based on target's current grapple state ---
        target_is_currently_grappled = handler.get_grappled_by_obj(target_combat_entry) is not None
        
        if target_is_currently_grappled:
            # Target is already being grappled by someone - this is a join attempt
            caller_combat_entry["combat_action"] = "grapple_join"  
            handler.set_target(caller, target)
            log_combat_action(caller, "grapple_action", target, details="combat action set to grapple_join")
        else:
            # Target is not currently grappled - this is a grapple initiation
            caller_combat_entry["combat_action"] = "grapple_initiate"
            handler.set_target(caller, target)
            log_combat_action(caller, "grapple_action", target, details="combat action set to grapple_initiate")

        caller.msg(MSG_GRAPPLE_PREPARE.format(target=target.key))
        # The combat handler will process this on the character's turn


class CmdEscapeGrapple(Command):
    """
    Attempt to escape from being grappled.

    Usage:
      escape

    Attempts to break free from a grapple hold. Success depends
    on an opposed roll against your grappler.
    """

    key = "escape"
    aliases = ["break", "breakfree"]
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        handler = getattr(caller.ndb, "combat_handler", None)

        if not handler:
            caller.msg(MSG_ESCAPE_NOT_IN_COMBAT)
            return

        # Get caller's combat entry
        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry:
            caller.msg("You are not properly registered in combat.")
            return

        # Check if being grappled
        grappler_obj = handler.get_grappled_by_obj(caller_entry)
        if not grappler_obj:
            caller.msg("You are not being grappled.")
            return

        # When someone actively escapes, they are no longer yielding
        was_yielding = caller_entry.get("is_yielding", False)
        caller_entry["is_yielding"] = False
        
        if was_yielding:
            caller.msg(MSG_GRAPPLE_ESCAPE_VIOLENT_SWITCH.format(grappler=grappler_obj.key))

        # Set escape action for the combat handler to process
        caller_entry["combat_action"] = "escape_grapple"
        caller.msg(f"You prepare to struggle violently against {grappler_obj.key}'s hold!")
        log_combat_action(caller, "escape_action", grappler_obj, details="combat action set to escape_grapple")


class CmdReleaseGrapple(Command):
    """
    Release a grapple you have on someone.

    Usage:
      release

    Voluntarily releases a grapple hold you have on another character.
    This action always succeeds.
    """

    key = "release"
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        handler = getattr(caller.ndb, "combat_handler", None)

        if not handler:
            caller.msg(MSG_RELEASE_NOT_IN_COMBAT)
            return

        # Get caller's combat entry
        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry:
            caller.msg("You are not properly registered in combat.")
            return

        # Check if grappling someone
        victim_obj = handler.get_grappling_obj(caller_entry)
        if not victim_obj:
            caller.msg("You are not grappling anyone.")
            return

        # Set release action for the combat handler to process
        caller_entry["combat_action"] = "release_grapple"
        caller.msg(f"You prepare to release your hold on {victim_obj.key}.")
        log_combat_action(caller, "release_action", victim_obj, details="combat action set to release_grapple")


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
    help_category = "Combat"

    def func(self):
        caller = self.caller
        
        handler = getattr(caller.ndb, NDB_COMBAT_HANDLER, None)
        if not handler:
            caller.msg(MSG_NOT_IN_COMBAT)
            log_combat_action(caller, "disarm_fail", details="not in combat")
            return

        target = handler.get_target(caller)
        if not target:
            caller.msg(MSG_DISARM_NO_TARGET)
            log_combat_action(caller, "disarm_fail", details="has no valid target")
            return

        # Check if in melee proximity with target
        initialize_proximity_ndb(caller)
        if not hasattr(caller.ndb, NDB_PROXIMITY) or target not in caller.ndb.in_proximity_with:
            caller.msg(MSG_DISARM_NOT_IN_PROXIMITY.format(target=target.key))
            log_combat_action(caller, "disarm_fail", target, details="not in melee proximity")
            return

        # Get combatant entry and set disarm action
        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry:
            caller.msg("You are not registered in combat.")
            return

        # Set disarm action to be processed on caller's next turn
        caller_entry["combat_action"] = COMBAT_ACTION_DISARM
        caller_entry["combat_action_target"] = target  # Store target for handler processing
        caller.msg(MSG_DISARM_PREPARE.format(target=target.get_display_name(caller)))
        
        # Debug message
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        if splattercast:
            splattercast.msg(f"DISARM: {caller.key} queued disarm action on {target.key} for next turn.")

        # Ensure combat handler is active
        if handler and not handler.is_active:
            handler.start()


class CmdAim(Command):
    """
    Aim at a target or in a direction.

    Usage:
      aim <target>
      aim <direction>
      aim stop

    Establishes an aim lock on a target or direction, potentially
    granting bonuses to subsequent ranged attacks. While aiming at
    a target, they cannot move. Use 'aim stop' to cease aiming.
    """

    key = "aim"
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Debug: Verify our enhanced aim command is being called
        splattercast.msg(f"ENHANCED_AIM: {caller.key} called enhanced aim command with args='{args}'")

        if not args:
            caller.msg(MSG_AIM_WHO_WHAT)
            return

        # Handle "aim at <target>" syntax - remove "at" if present
        if args.lower().startswith("at "):
            args = args[3:].strip()
            
        if not args:
            caller.msg(MSG_AIM_WHO_WHAT)
            return

        # Handle stopping aim
        if args.lower() in ("stop", "clear", "cancel"):
            current_target = getattr(caller.ndb, "aiming_at", None)
            if not current_target:
                caller.msg("|yYou are not currently aiming at anything.|n")
                return
            
            # Clear the aim relationship
            delattr(caller.ndb, "aiming_at")
            if hasattr(current_target, "ndb") and hasattr(current_target.ndb, "aimed_at_by") and getattr(current_target.ndb, "aimed_at_by") == caller:
                delattr(current_target.ndb, "aimed_at_by")
            
            caller.msg(f"|gYou stop aiming at {current_target.key}.|n")
            current_target.msg(f"|g{caller.key} stops aiming at you.|n")
            splattercast.msg(f"AIM_STOP: {caller.key} stopped aiming at {current_target.key}.")
            return

        # Clear any existing aim first
        current_target = getattr(caller.ndb, "aiming_at", None)
        current_direction = getattr(caller.ndb, "aiming_direction", None)
        
        if current_target:
            if hasattr(current_target, "ndb") and hasattr(current_target.ndb, "aimed_at_by") and getattr(current_target.ndb, "aimed_at_by") == caller:
                delattr(current_target.ndb, "aimed_at_by")
            delattr(caller.ndb, "aiming_at")
            current_target.msg(f"|g{caller.key} stops aiming at you.|n")
            
        if current_direction:
            splattercast.msg(f"AIM_DEBUG: Clearing existing aiming_direction '{current_direction}' for {caller.key}")
            delattr(caller.ndb, "aiming_direction")

        # Try to find target in current room first
        target = caller.search(args, location=caller.location, quiet=True)
        
        # Debug: Show what search found
        splattercast.msg(f"AIM_DEBUG: caller.search('{args}') returned: {target} (type: {type(target)})")
        
        # Handle search results - caller.search can return None, empty list, or list with objects
        if target:
            # If search returns a list, take the first match
            if isinstance(target, (list, tuple)):
                if len(target) > 0:
                    target = target[0]
                    splattercast.msg(f"AIM_DEBUG: Found target from list: {target.key}")
                else:
                    target = None
                    splattercast.msg(f"AIM_DEBUG: Empty list returned, no target")
            else:
                splattercast.msg(f"AIM_DEBUG: Found single target: {target.key}")
        else:
            splattercast.msg(f"AIM_DEBUG: No target found by search")
        
        if target and hasattr(target, 'key'):
            # Check if the "target" is actually an exit - if so, treat as direction aiming
            if hasattr(target, 'destination') and target.destination:
                splattercast.msg(f"AIM_DEBUG: Found object is an exit, treating as direction aiming")
                # This is an exit, treat as direction aiming instead of target aiming
                direction = args.strip().lower()
                
                # Clear any existing aim first
                current_target = getattr(caller.ndb, "aiming_at", None)
                current_direction = getattr(caller.ndb, "aiming_direction", None)
                
                if current_target:
                    if hasattr(current_target, "ndb") and hasattr(current_target.ndb, "aimed_at_by") and getattr(current_target.ndb, "aimed_at_by") == caller:
                        delattr(current_target.ndb, "aimed_at_by")
                    delattr(caller.ndb, "aiming_at")
                    current_target.msg(f"|g{caller.key} stops aiming at you.|n")
                    
                if current_direction:
                    splattercast.msg(f"AIM_DEBUG: Clearing existing aiming_direction '{current_direction}' for {caller.key}")
                    delattr(caller.ndb, "aiming_direction")
                
                # Check if caller has a ranged weapon for direction aiming
                hands = getattr(caller, "hands", {})
                weapon = next((item for hand, item in hands.items() if item), None)
                
                is_ranged_weapon = False
                if weapon:
                    weapon_db = getattr(weapon, "db", None)
                    if weapon_db:
                        is_ranged_weapon = getattr(weapon_db, "is_ranged", False)
                
                if not is_ranged_weapon:
                    caller.msg("|rYou need a ranged weapon to aim in a direction.|n")
                    return
                
                # Set direction aiming
                setattr(caller.ndb, "aiming_direction", direction)
                
                # Debug: Verify the direction was set
                splattercast.msg(f"AIM_DEBUG: Set aiming_direction to '{direction}' for {caller.key}")
                splattercast.msg(f"AIM_DEBUG: Verification - getattr result: '{getattr(caller.ndb, 'aiming_direction', 'NOT_FOUND')}'")
                splattercast.msg(f"AIM_DEBUG: Direct ndb check: hasattr={hasattr(caller.ndb, 'aiming_direction')}")
                
                # Test retrieval immediately
                test_direction = getattr(caller.ndb, "aiming_direction", None)
                splattercast.msg(f"AIM_DEBUG: Immediate test retrieval: '{test_direction}'")
                
                caller.msg(f"|yYou take careful aim {direction}.|n")
                caller.location.msg_contents(
                    f"|y{caller.key} takes careful aim {direction}.|n",
                    exclude=[caller]
                )
                
                splattercast.msg(f"AIM_DIRECTION: {caller.key} is now aiming {direction}.")
                caller.msg("|gYour next ranged attack in this direction will have improved accuracy.|n")
                return
            
            # Target found in room and it's not an exit - prevent self-targeting
            if target == caller:
                caller.msg(MSG_AIM_SELF_TARGET)
                return

            # Check if caller has a ranged weapon
            hands = getattr(caller, "hands", {})
            weapon = next((item for hand, item in hands.items() if item), None)
            
            is_ranged_weapon = False
            if weapon:
                weapon_db = getattr(weapon, "db", None)
                if weapon_db:
                    is_ranged_weapon = getattr(weapon_db, "is_ranged", False)
            
            if not is_ranged_weapon:
                caller.msg("|yYou need a ranged weapon to aim effectively.|n")
                # Allow aiming without ranged weapon but with warning

            # Set target aim relationship
            setattr(caller.ndb, "aiming_at", target)
            setattr(target.ndb, "aimed_at_by", caller)

            # Send messages
            caller.msg(f"|yYou carefully aim at {target.key}.|n")
            target.msg(f"|r{caller.key} is aiming at you! You feel locked in place.|n")
            caller.location.msg_contents(
                f"|y{caller.key} takes careful aim at {target.key}.|n",
                exclude=[caller, target]
            )

            splattercast.msg(f"AIM_SET: {caller.key} is now aiming at {target.key}.")
            
            # Provide feedback about the aiming bonus
            if is_ranged_weapon:
                caller.msg("|gYour next ranged attack will have improved accuracy.|n")
            else:
                caller.msg("|yWithout a ranged weapon, this aim provides limited benefit.|n")
                
        else:
            # No target found in room - check if it's a direction
            direction = args.strip().lower()
            exits = caller.location.exits
            
            splattercast.msg(f"AIM_DEBUG: No target found, checking direction '{direction}'")
            splattercast.msg(f"AIM_DEBUG: Room has {len(exits)} exits")
            
            # Check if the direction matches any exit
            valid_direction = False
            for i, ex in enumerate(exits):
                # Use the same approach as core_actions.py for consistency
                current_exit_aliases_lower = [alias.lower() for alias in (ex.aliases.all() if hasattr(ex.aliases, "all") else [])]
                
                splattercast.msg(f"AIM_DEBUG: Exit {i}: key='{ex.key}', aliases={current_exit_aliases_lower}")
                splattercast.msg(f"AIM_DEBUG: Checking '{direction}' vs key='{ex.key.lower()}' or aliases={current_exit_aliases_lower}")
                    
                if ex.key.lower() == direction or direction in current_exit_aliases_lower:
                    valid_direction = True
                    splattercast.msg(f"AIM_DEBUG: Found valid direction match!")
                    break
                    
            if valid_direction:
                splattercast.msg(f"AIM_DEBUG: Direction '{direction}' is valid, proceeding with aiming")
                # Check if caller has a ranged weapon for direction aiming
                hands = getattr(caller, "hands", {})
                weapon = next((item for hand, item in hands.items() if item), None)
                
                is_ranged_weapon = False
                if weapon:
                    weapon_db = getattr(weapon, "db", None)
                    if weapon_db:
                        is_ranged_weapon = getattr(weapon_db, "is_ranged", False)
                
                if not is_ranged_weapon:
                    caller.msg("|rYou need a ranged weapon to aim in a direction.|n")
                    return
                
                # Set direction aiming
                setattr(caller.ndb, "aiming_direction", direction)
                
                # Debug: Verify the direction was set
                splattercast.msg(f"AIM_DEBUG: Set aiming_direction to '{direction}' for {caller.key}")
                splattercast.msg(f"AIM_DEBUG: Verification - getattr result: '{getattr(caller.ndb, 'aiming_direction', 'NOT_FOUND')}'")
                splattercast.msg(f"AIM_DEBUG: Direct ndb check: hasattr={hasattr(caller.ndb, 'aiming_direction')}")
                
                # Test retrieval immediately
                test_direction = getattr(caller.ndb, "aiming_direction", None)
                splattercast.msg(f"AIM_DEBUG: Immediate test retrieval: '{test_direction}'")
                
                caller.msg(f"|yYou take careful aim {direction}.|n")
                caller.location.msg_contents(
                    f"|y{caller.key} takes careful aim {direction}.|n",
                    exclude=[caller]
                )
                
                splattercast.msg(f"AIM_DIRECTION: {caller.key} is now aiming {direction}.")
                caller.msg("|gYour next ranged attack in this direction will have improved accuracy.|n")
                
            else:
                splattercast.msg(f"AIM_DEBUG: Direction '{direction}' was not found as valid exit")
                caller.msg(f"|rYou don't see '{args}' here, and it's not a valid direction.|n")
