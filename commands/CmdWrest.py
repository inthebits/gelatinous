"""
Wrest Command Implementation

The wrest command enables non-combat item snatching from other characters' hands.
It serves as the non-combat counterpart to the disarm command, allowing quick
opportunistic grabbing of objects without entering combat mechanics.

Design Philosophy:
- Instant success (no resistance rolls)
- Non-combat only (caller cannot be in combat)
- Target can be in combat (allows grabbing from distracted targets)
- Works with any hand configuration (Mr. Hand system flexibility)
"""

from evennia import Command
from evennia.utils.search import search_object
from world.combat.constants import (
    MSG_WREST_SUCCESS_CALLER,
    MSG_WREST_SUCCESS_TARGET,
    MSG_WREST_SUCCESS_ROOM,
    MSG_WREST_IN_COMBAT,
    MSG_WREST_NO_FREE_HANDS,
    MSG_WREST_TARGET_NOT_FOUND,
    MSG_WREST_OBJECT_NOT_IN_HANDS,
    MSG_WREST_OBJECT_NOT_FOUND,
    MSG_WREST_SAME_ROOM_REQUIRED,
    DB_CHAR
)


class CmdWrest(Command):
    """
    Quickly snatch an item from another character's hands.

    Usage:
        wrest <object> from <target>

    Examples:
        wrest knife from bob
        wrest phone from alice
        wrest keys from guard

    This command allows opportunistic item grabbing outside of combat.
    It works instantly with no resistance rolls, making it ideal for
    quick snatch-and-run tactics or disarming distracted opponents.

    Requirements:
    - You must NOT be in combat (use 'disarm' during combat instead)
    - You must have at least one free hand
    - Target must be in the same room
    - Object must be wielded in target's hands
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

        # 5. Execute transfer
        self._execute_wrest(caller, target, target_object, free_hand, target_hand)

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
        # Search for target in current room
        targets = search_object(self.target_name, location=self.caller.location)
        
        # Filter to only characters
        for target in targets:
            if hasattr(target, 'hands'):  # Basic character check
                return target
        return None

    def _find_object_in_target_hands(self, target):
        """Find specified object in target's hands."""
        hands = getattr(target, 'hands', {})
        for hand_name, held_item in hands.items():
            if held_item and self.object_name.lower() in held_item.key.lower():
                return hand_name, held_item
        return None, None

    def _execute_wrest(self, caller, target, target_object, caller_hand, target_hand):
        """Execute the actual wrest transfer."""
        # Use the existing Mr. Hand system methods for proper state management
        
        # Remove object from target's hand
        target_unwield_result = target.unwield_item(target_hand)
        
        # Add object to caller's hand
        caller_wield_result = caller.wield_item(target_object, caller_hand)
        
        # Verify the transfer worked
        if "wield" not in caller_wield_result.lower():
            # Something went wrong, try to restore target's state
            target.wield_item(target_object, target_hand)
            caller.msg("Something went wrong with the wrest attempt.")
            return

        # Announce the successful wrest
        self._announce_wrest_success(caller, target, target_object)

    def _announce_wrest_success(self, caller, target, obj):
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
