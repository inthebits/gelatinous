"""
Wrest Command Implementation

The wrest command enables non-combat item snatching from other characters' hands.
It serves as the non-combat counterpart to the disarm command, allowing quick
opportunistic grabbing of objects without entering combat mechanics.

Design Philosophy:
- Grit vs Grit contest with grapple disadvantage mechanics
- Non-combat only (caller cannot be in combat)
- Target can be in combat (allows grabbing from distracted targets)
- Works with any hand configuration (Mr. Hand system flexibility)
"""

from evennia import Command
from evennia.comms.models import ChannelDB
from world.combat.constants import (
    MSG_WREST_SUCCESS_CALLER,
    MSG_WREST_SUCCESS_TARGET,
    MSG_WREST_SUCCESS_ROOM,
    MSG_WREST_FAILED_CALLER,
    MSG_WREST_FAILED_TARGET,
    MSG_WREST_FAILED_ROOM,
    MSG_WREST_IN_COMBAT,
    MSG_WREST_NO_FREE_HANDS,
    MSG_WREST_TARGET_NOT_FOUND,
    MSG_WREST_OBJECT_NOT_IN_HANDS,
    MSG_WREST_OBJECT_NOT_FOUND,
    MSG_WREST_SAME_ROOM_REQUIRED,
    DB_CHAR,
    DB_GRAPPLED_BY_DBREF,
    STAT_GRIT,
    SPLATTERCAST_CHANNEL
)
from world.combat.utils import roll_stat, roll_with_disadvantage


class CmdWrest(Command):
    """
    Quickly snatch an item from another character's hands.

    Usage:
        wrest <object> from <target>

    Examples:
        wrest knife from bob
        wrest phone from alice
        wrest keys from guard

    This command allows opportunistic item grabbing outside of combat
    using a Grit vs Grit contest. Grappled targets roll with disadvantage,
    making them vulnerable to item theft.

    Requirements:
    - You must NOT be in combat (use 'disarm' during combat instead)
    - You must have at least one free hand
    - Target must be in the same room
    - Object must be wielded in target's hands

    Mechanics:
    - Grit vs Grit contest determines success
    - Grappled targets roll with disadvantage
    - Instant success only against unconscious/dead targets
    """

    key = "wrest"
    locks = "cmd:all()"
    help_category = "Combat"

    def parse(self):
        """Parse 'wrest <object> from <target>' syntax."""
        self.object_name = ""
        self.target_name = ""
        
        args = self.args.strip().lower()
        if not args:
            return
            
        # Look for "from" keyword
        if " from " in args:
            parts = args.split(" from ", 1)
            if len(parts) == 2:
                self.object_name = parts[0].strip()
                self.target_name = parts[1].strip()

    def func(self):
        caller = self.caller
        
        # Basic syntax validation
        if not self.object_name or not self.target_name:
            caller.msg("Usage: wrest <object> from <target>")
            return

        # 1. Check caller not in combat
        if self._is_caller_in_combat():
            caller.msg(MSG_WREST_IN_COMBAT)
            return

        # 2. Check caller has free hand
        free_hand = self._find_free_hand(caller)
        if not free_hand:
            caller.msg(MSG_WREST_NO_FREE_HANDS)
            return

        # 3. Find and validate target
        target = self._find_target_in_room()
        if not target:
            caller.msg(MSG_WREST_TARGET_NOT_FOUND.format(target=self.target_name))
            return

        # 4. Find object in target's hands
        target_hand, target_object = self._find_object_in_target_hands(target)
        if not target_object:
            caller.msg(MSG_WREST_OBJECT_NOT_IN_HANDS.format(
                target=target.get_display_name(caller), 
                object=self.object_name
            ))
            return

        # 5. Check if target is grappled (for disadvantage)
        is_grappled = self._is_target_grappled(target)

        # 6. Execute Grit vs Grit contest (unless target is unconscious/dead)
        if self._is_target_unconscious_or_dead(target):
            # Instant success against unconscious/dead targets
            success = True
        else:
            # Grit vs Grit contest
            success = self._execute_grit_contest(caller, target, is_grappled)

        # 7. Handle result
        if success:
            self._execute_transfer(caller, target, target_object, free_hand, target_hand)
            self._announce_success(caller, target, target_object)
        else:
            self._announce_failure(caller, target, target_object)

    def _is_caller_in_combat(self):
        """Check if caller is currently in combat."""
        # Check for combat handler reference
        combat_handler = getattr(self.caller.ndb, "combat_handler", None)
        if combat_handler:
            # Verify handler is still active
            combatants = getattr(combat_handler.db, "combatants", None)
            if combatants:
                # Check if caller is in the combatants list using correct field name
                return any(entry.get(DB_CHAR) == self.caller for entry in combatants)
        return False

    def _find_free_hand(self, character):
        """Find first available free hand in character's hands dictionary."""
        hands = getattr(character, 'hands', {})
        for hand_name, held_item in hands.items():
            if held_item is None:
                return hand_name
        return None

    def _find_target_in_room(self):
        """Find target character in the same room."""
        # Search for target in current room using caller's search method
        target = self.caller.search(self.target_name, location=self.caller.location)
        
        # Check if target is a character with hands
        if target and hasattr(target, 'hands'):
            return target
        return None

    def _find_object_in_target_hands(self, target):
        """Find specified object in target's hands."""
        hands = getattr(target, 'hands', {})
        for hand_name, held_item in hands.items():
            if held_item and self.object_name.lower() in held_item.key.lower():
                return hand_name, held_item
        return None, None

    def _is_target_grappled(self, target):
        """Check if target is currently grappled."""
        # Check if target has a combat handler with grapple status
        combat_handler = getattr(target.ndb, "combat_handler", None)
        if combat_handler:
            combatants = getattr(combat_handler.db, "combatants", None)
            if combatants:
                # Find target's entry in combatants list
                target_entry = next((entry for entry in combatants if entry.get(DB_CHAR) == target), None)
                if target_entry:
                    grappled_by = target_entry.get(DB_GRAPPLED_BY_DBREF)
                    return grappled_by is not None
        return False

    def _is_target_unconscious_or_dead(self, target):
        """Check if target is unconscious or dead (instant success condition)."""
        # TODO: Implement when unconscious/dead states are added to the system
        # For now, always return False (no instant success)
        return False

    def _execute_grit_contest(self, caller, target, target_is_grappled):
        """Execute Grit vs Grit contest, with disadvantage for grappled targets."""
        # Caller rolls normally
        caller_roll = roll_stat(caller, STAT_GRIT)
        
        # Target rolls with disadvantage if grappled
        if target_is_grappled:
            target_grit = getattr(target, STAT_GRIT, 1)
            target_roll, _, _ = roll_with_disadvantage(target_grit)
        else:
            target_roll = roll_stat(target, STAT_GRIT)
        
        # Caller wins ties (advantage to active player)
        success = caller_roll >= target_roll
        
        # Debug output for testing
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        if splattercast:
            grapple_status = " (grappled)" if target_is_grappled else ""
            splattercast.msg(f"WREST CONTEST: {caller.key} {caller_roll} vs {target.key} {target_roll}{grapple_status} - {'SUCCESS' if success else 'FAILURE'}")
        
        return success

    def _execute_transfer(self, caller, target, target_object, caller_hand, target_hand):
        """Execute the actual object transfer using the same method as disarm."""
        # Get target's hands dictionary
        target_hands = getattr(target, 'hands', {})
        
        # Remove object from target's hand (like disarm does)
        target_hands[target_hand] = None
        
        # Move object to caller's inventory first (like disarm does with move_to location)
        target_object.move_to(caller, quiet=True)
        
        # Then wield the object in caller's hand
        caller_wield_result = caller.wield_item(target_object, caller_hand)
        
        # Verify the transfer worked
        if "wield" not in caller_wield_result.lower():
            # Something went wrong, try to restore target's state
            target_hands[target_hand] = target_object
            target_object.move_to(target, quiet=True)
            caller.msg(f"Transfer failed: {caller_wield_result}")
            return False
        
        return True

    def _announce_success(self, caller, target, obj):
        """Announce successful wrest to all relevant parties."""
        object_name = obj.get_display_name(caller)
        
        # Message to caller
        caller.msg(MSG_WREST_SUCCESS_CALLER.format(
            object=object_name,
            target=target.get_display_name(caller)
        ))
        
        # Message to target
        target.msg(MSG_WREST_SUCCESS_TARGET.format(
            caller=caller.get_display_name(target),
            object=object_name
        ))
        
        # Message to room (exclude caller and target)
        caller.location.msg_contents(
            MSG_WREST_SUCCESS_ROOM.format(
                caller=caller.get_display_name(None),
                target=target.get_display_name(None),
                object=object_name
            ),
            exclude=[caller, target]
        )

    def _announce_failure(self, caller, target, obj):
        """Announce failed wrest attempt to all relevant parties."""
        object_name = obj.get_display_name(caller)
        
        # Message to caller
        caller.msg(MSG_WREST_FAILED_CALLER.format(
            object=object_name,
            target=target.get_display_name(caller)
        ))
        
        # Message to target
        target.msg(MSG_WREST_FAILED_TARGET.format(
            caller=caller.get_display_name(target),
            object=object_name
        ))
        
        # Message to room (exclude caller and target)
        caller.location.msg_contents(
            MSG_WREST_FAILED_ROOM.format(
                caller=caller.get_display_name(None),
                target=target.get_display_name(None),
                object=object_name
            ),
            exclude=[caller, target]
        )
