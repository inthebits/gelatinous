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
    MSG_NOT_IN_COMBAT, MSG_DISARM_NO_TARGET, MSG_DISARM_TARGET_EMPTY_HANDS,
    MSG_DISARM_FAILED, MSG_DISARM_RESISTED, MSG_DISARM_NOTHING_TO_DISARM,
    MSG_DISARM_SUCCESS_ATTACKER, MSG_DISARM_SUCCESS_VICTIM, MSG_DISARM_SUCCESS_OBSERVER,
    MSG_AIM_WHO_WHAT, MSG_AIM_SELF_TARGET,
    DEBUG_PREFIX_GRAPPLE, SPLATTERCAST_CHANNEL,
    NDB_COMBAT_HANDLER, STAT_GRIT
)
from world.combat.utils import log_combat_action, get_numeric_stat, roll_stat


class CmdGrapple(Command):
    """
    Attempt to grapple a target in your current room.

    Usage:
        grapple <target>

    If you are not in combat, this will initiate combat.
    If successful, you will be grappling the target, and they will be grappled by you.
    """
    key = "grapple"
    aliases = ["grab", "wrestle"]
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
            log_combat_action(f"{caller.key} tried to grapple '{search_name}' but found no valid target in the room.")
            return

        target = matches[0]

        if target == caller:
            caller.msg(MSG_CANNOT_GRAPPLE_SELF)
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg(MSG_CANNOT_GRAPPLE_TARGET)
            log_combat_action(f"{caller.key} tried to grapple {target.key}, but it's not a valid character.")
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
            log_combat_action(f"{caller.key} is initiating grapple combat with {target.key}.")
            handler.add_combatant(caller) 
            handler.add_combatant(target) 
        elif not target_is_in_combat: 
            log_combat_action(f"{caller.key} (in combat) is attempting to grapple {target.key} (adding to combat).")
            handler.add_combatant(target)
        
        # --- Now retrieve combat entries; they should exist ---
        caller_combat_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        target_combat_entry = next((e for e in handler.db.combatants if e["char"] == target), None)

        if not caller_combat_entry: 
            caller.msg(MSG_GRAPPLE_COMBAT_ADD_ERROR)
            log_combat_action(f"CRITICAL: {caller.key} failed to be added to combat by CmdGrapple.")
            return
        if not target_combat_entry: 
            caller.msg(f"There was an issue adding {target.key} to combat. Please try again.")
            log_combat_action(f"CRITICAL: {target.key} failed to be added to combat by CmdGrapple.")
            return

        # Default to not yielding if already in combat or grapple fails.
        # This will be overridden if grapple is successful AND initiated combat.
        caller_combat_entry["is_yielding"] = False 

        # --- Grapple-specific checks (already grappling, being grappled, target grappled) ---
        if handler.get_grappling_obj(caller_combat_entry):
            currently_grappling = handler.get_grappling_obj(caller_combat_entry)
            caller.msg(MSG_ALREADY_GRAPPLING.format(target=currently_grappling.key))
            log_combat_action(f"{caller.key} tried to grapple {target.key} while already grappling {currently_grappling.key}.")
            return
        
        if handler.get_grappled_by_obj(caller_combat_entry):
            grappler = handler.get_grappled_by_obj(caller_combat_entry)
            caller.msg(MSG_CANNOT_GRAPPLE_WHILE_GRAPPLED.format(grappler=grappler.key))
            log_combat_action(f"{caller.key} tried to grapple {target.key} while being grappled by {grappler.key}.")
            return

        if handler.get_grappled_by_obj(target_combat_entry):
            # Check if it's the caller grappling them (should be caught above, but good for clarity)
            # Or if someone *else* is grappling them
            target_grappler = handler.get_grappled_by_obj(target_combat_entry)
            if target_grappler != caller:
                 caller.msg(MSG_TARGET_ALREADY_GRAPPLED.format(target=target.key, grappler=target_grappler.key))
                 log_combat_action(f"{caller.key} tried to grapple {target.key}, but they are already grappled by {target_grappler.key}.")
                 return
        
        # --- Set combat action ---
        # Ensure combat_action key exists for the entry
        if "combat_action" not in caller_combat_entry:
            caller_combat_entry["combat_action"] = {}
            
        # --- Set combat action ---
        if caller_initiated_combat_this_action:
            # This is a grapple to initiate combat - use all-or-nothing approach
            caller_combat_entry["combat_action"] = "grapple_initiate"
            handler.set_target(caller, target)
            log_combat_action(f"{caller.key} sets combat action to grapple_initiate against {target.key}.")
        else:
            # This is a grapple during ongoing combat - use risk-based approach
            caller_combat_entry["combat_action"] = "grapple_join"  
            handler.set_target(caller, target)
            log_combat_action(f"{caller.key} sets combat action to grapple_join against {target.key}.")

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

        # Escape logic would continue here...
        # Truncated for demonstration


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

        # Release logic would continue here...
        # Truncated for demonstration


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
        from random import randint
        
        caller = self.caller
        
        handler = getattr(caller.ndb, NDB_COMBAT_HANDLER, None)
        if not handler:
            caller.msg(MSG_NOT_IN_COMBAT)
            log_combat_action(f"{caller.key} tried to disarm but is not in combat.")
            return

        target = handler.get_target(caller)
        if not target:
            caller.msg(MSG_DISARM_NO_TARGET)
            log_combat_action(f"{caller.key} tried to disarm but has no valid target.")
            return

        hands = getattr(target, "hands", {})
        if not hands:
            caller.msg(MSG_DISARM_TARGET_EMPTY_HANDS.format(target=target.key))
            log_combat_action(f"{caller.key} tried to disarm {target.key}, but they have nothing in their hands.")
            return

        # Grit vs Grit check
        attacker_grit = get_numeric_stat(caller, STAT_GRIT)
        defender_grit = get_numeric_stat(target, STAT_GRIT)
        disarm_roll = roll_stat(attacker_grit)
        resist_roll = roll_stat(defender_grit)
        
        log_combat_action(
            f"{caller.key} attempts to disarm {target.key}: {disarm_roll} (grit) vs {resist_roll} (grit)"
        )

        if disarm_roll <= resist_roll:
            caller.msg(MSG_DISARM_FAILED.format(target=target.key))
            target.msg(MSG_DISARM_RESISTED.format(attacker=caller.key))
            log_combat_action(f"{caller.key} failed to disarm {target.key}.")
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
            caller.msg(MSG_DISARM_NOTHING_TO_DISARM.format(target=target.key))
            log_combat_action(f"{caller.key} tried to disarm {target.key}, but nothing was found.")
            return

        item = hands[weapon_hand]
        # Remove from hand and move to ground
        hands[weapon_hand] = None
        item.move_to(target.location, quiet=True)
        
        caller.msg(MSG_DISARM_SUCCESS_ATTACKER.format(target=target.key, item=item.key))
        target.msg(MSG_DISARM_SUCCESS_VICTIM.format(attacker=caller.key, item=item.key))
        target.location.msg_contents(
            MSG_DISARM_SUCCESS_OBSERVER.format(attacker=caller.key, target=target.key, item=item.key),
            exclude=[caller, target]
        )
        log_combat_action(f"{caller.key} disarmed {target.key} ({item.key}) in {target.location.key}.")


class CmdAim(Command):
    """
    Aim at a target or in a direction.

    Usage:
      aim <target>
      aim <direction>

    Establishes an aim lock on a target or direction, potentially
    granting bonuses to subsequent ranged attacks.
    """

    key = "aim"
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg(MSG_AIM_WHO_WHAT)
            return

        # Aim logic would continue here...
        # Truncated for demonstration
