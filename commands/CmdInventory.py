# Mr. Hands System Inventory Management
# 
# Complete inventory management system for the Mr. Hand system including:
# - CmdWield/CmdUnwield: Hand-based item management
# - CmdFreeHands: Unwield all held items at once
# - CmdInventory: Display carried vs held items
# - CmdDrop/CmdGet: Smart item pickup/drop with hand integration
# - CmdGive: Player-to-player item transfer with hand support
# - CmdWrest: Non-combat item snatching with contest mechanics
#
from evennia import Command
from evennia.utils.search import search_object
from world.combat.constants import NDB_PROXIMITY_UNIVERSAL

class CmdWield(Command):
    """
    Wield an item into one of your hands.

    Usage:
        wield <item>
        wield <item> in <hand>

    Examples:
        wield shiv
        wield baton in left
        hold crowbar
    """

    key = "wield"
    aliases = ["hold"]

    def func(self):
        caller = self.caller
        args = self.args.strip().lower()

        if not args:
            caller.msg("Wield what?")
            return

        # Parse syntax: "<item> in <hand>"
        if " in " in args:
            itemname, hand = [s.strip() for s in args.split(" in ", 1)]
        else:
            itemname, hand = args, None

        # Search for item in inventory - enhanced search
        item = self._find_item_in_inventory(caller, itemname)
        if not item:
            return  # error already sent

        hands = caller.hands

        # If hand is specified, match it
        if hand:
            matched_hand = next((h for h in hands if hand in h.lower()), None)
            if not matched_hand:
                caller.msg(f"You don't have a hand named '{hand}'.")
                return

            result = caller.wield_item(item, matched_hand)
            caller.msg(result)
            return

        # No hand specified — find the first free one
        for hand_name, held_item in hands.items():
            if held_item is None:
                result = caller.wield_item(item, hand_name)
                caller.msg(result)
                return

        # All hands are full
        caller.msg("Your hands are full.")
        
    def _find_item_in_inventory(self, caller, itemname):
        """Search for an item in the caller's inventory using Evennia's search system."""
        # Use caller.search with candidates limited to inventory
        # This will automatically handle ordinal numbers via ObjectParent
        candidates = list(caller.contents)
        if not candidates:
            caller.msg(f"You don't have a '{itemname}'.")
            return None
            
        result = caller.search(itemname, candidates=candidates, quiet=True)
        if result:
            return result[0] if isinstance(result, list) else result
        
        caller.msg(f"You don't have a '{itemname}'.")
        return None


class CmdUnwield(Command):
    """
    Unwield an item you are currently holding.

    Usage:
        unwield <item>

    Example:
        unwield shiv
    """

    key = "unwield"

    def func(self):
        caller = self.caller
        itemname = self.args.strip()

        if not itemname:
            caller.msg("What do you want to unwield?")
            return

        hands = caller.hands
        # Get list of held items
        held_items = [item for item in hands.values() if item]
        
        if not held_items:
            caller.msg("You aren't holding anything to unwield.")
            return
        
        # Use caller.search with candidates limited to held items
        # This will automatically handle ordinal numbers via ObjectParent
        result = caller.search(itemname, candidates=held_items, quiet=True)
        if not result:
            caller.msg(f"You aren't holding '{itemname}'.")
            return
            
        held_item = result[0] if isinstance(result, list) else result
        
        # Find which hand is holding this item
        for hand, item in hands.items():
            if item == held_item:
                result = caller.unwield_item(hand)
                caller.msg(result)
                return


class CmdFreeHands(Command):
    """
    Unwield all items from your hands at once.

    Usage:
        freehands
        free hands

    This command will automatically unwield every item you're currently
    holding in any hand, using the normal unwield process for each item.
    """

    key = "freehands"
    aliases = ["free hands"]

    def func(self):
        caller = self.caller
        hands = caller.hands
        
        # Find all items currently being held
        held_items = []
        for hand, item in hands.items():
            if item:
                held_items.append((hand, item))
        
        if not held_items:
            caller.msg("Your hands are already empty.")
            return
        
        # Unwield each item using the existing unwield_item method
        results = []
        for hand, item in held_items:
            result = caller.unwield_item(hand)
            results.append(result)
        
        # Send all results as a single message
        caller.msg("\n".join(results))


class CmdInventory(Command):
    """
    Check what you're carrying or holding.

    Usage:
      inventory
      inv
    """

    key = "inventory"
    aliases = ["inv"]

    def func(self):
        caller = self.caller
        items = caller.contents
        hands = caller.hands
        
        # Get worn items
        worn_items = caller.get_worn_items() if hasattr(caller, 'get_worn_items') else []

        held_items = set(item for item in hands.values() if item)
        worn_items_set = set(worn_items)
        inventory_items = [obj for obj in items if obj not in held_items and obj not in worn_items_set]

        if not inventory_items and all(v is None for v in hands.values()) and not worn_items:
            caller.msg("You aren't carrying, holding, or wearing anything.")
            return

        lines = []

        # Worn items (with style states)
        if worn_items:
            lines.append("|wWearing:|n")
            
            # Show worn items with style states
            for item in worn_items:
                item_name = item.get_display_name(caller)
                style_states = self._get_style_state_display(item)
                if style_states:
                    lines.append(f"  {item_name} (worn, {style_states})")
                else:
                    lines.append(f"  {item_name} (worn)")
            lines.append("")

        # Carried (not wielded or worn)
        if inventory_items:
            lines.append("|wCarrying:|n")
            
            # Consolidate identical items and count them
            item_counts = {}
            for obj in inventory_items:
                item_name = obj.get_display_name(caller)
                if item_name in item_counts:
                    item_counts[item_name] += 1
                else:
                    item_counts[item_name] = 1
            
            # Display items with counts
            for item_name, count in item_counts.items():
                if count > 1:
                    lines.append(f"  {item_name} ({count})")
                else:
                    lines.append(f"  {item_name}")
            lines.append("")

        # Held (in hands)
        lines.append("|wHeld:|n")
        for hand, item in hands.items():
            if item:
                lines.append(f"A {item.get_display_name(caller)} is held in your {hand.lower()} hand.")
            else:
                lines.append(f"Nothing is in your {hand.lower()} hand.")

        caller.msg("\n".join(lines))
    
    def _get_style_state_display(self, item):
        """Get display string for non-default style states"""
        if not hasattr(item, 'style_properties') or not item.style_properties:
            return ""
        
        from world.combat.constants import STYLE_STATE_NORMAL
        
        # Collect non-default style states
        non_default_states = []
        for property_name, state in item.style_properties.items():
            if state != STYLE_STATE_NORMAL:
                if property_name == "adjustable" and state == "rolled":
                    non_default_states.append("rolled up")
                elif property_name == "closure" and state == "unzipped":
                    non_default_states.append("unzipped")
                elif property_name == "closure" and state == "zipped":
                    # Only show "zipped" if it's explicitly a non-default state
                    # (some items might default to unzipped)
                    non_default_states.append("zipped")
        
        return ", ".join(non_default_states)

from evennia import Command

class CmdDrop(Command):
    """
    Drop an item from your inventory or your hand.

    Usage:
        drop <item>

    This drops an item you're carrying or currently holding.
    """

    key = "drop"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Drop what?")
            return

        # Enhanced search - try inventory first
        obj = self._find_item_to_drop(caller, args)

        if not obj:
            caller.msg("You aren't carrying or holding that.")
            return

        # If it's wielded, remove it from the hand
        was_wielded = False
        hand_name = None
        for hand, item in caller.hands.items():
            if item == obj:
                caller.hands[hand] = None
                was_wielded = True
                hand_name = hand
                break

        # Move the item to the room
        obj.move_to(caller.location, quiet=True)

        # Apply gravity if item is dropped in a sky room
        from commands.combat.movement import apply_gravity_to_items
        apply_gravity_to_items(caller.location)
        
        # Universal proximity assignment for all dropped objects
        if not hasattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL):
            setattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        proximity_list = getattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        if proximity_list is None:
            proximity_list = []
            setattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, proximity_list)
        if caller not in proximity_list:
            proximity_list.append(caller)
        
        # Send appropriate message based on whether it was wielded
        if was_wielded:
            caller.msg(f"You release {obj.get_display_name(caller)} from your {hand_name} hand and drop it.")
            caller.location.msg_contents(f"{caller.key} drops {obj.get_display_name(caller)}.", exclude=caller)
        else:
            caller.msg(f"You drop {obj.get_display_name(caller)}.")
            caller.location.msg_contents(f"{caller.key} drops {obj.get_display_name(caller)}.", exclude=caller)

    def _find_item_to_drop(self, caller, itemname):
        """Search for an item to drop using Evennia's search system."""
        # First search inventory
        inventory_candidates = list(caller.contents)
        if inventory_candidates:
            result = caller.search(itemname, candidates=inventory_candidates, quiet=True)
            if result:
                return result[0] if isinstance(result, list) else result
        
        # If not found in inventory, search hands
        hands = caller.hands
        held_items = [item for item in hands.values() if item]
        if held_items:
            result = caller.search(itemname, candidates=held_items, quiet=True)
            if result:
                return result[0] if isinstance(result, list) else result
        
        return None


class CmdGet(Command):
    """
    Pick up an item and hold it if a hand is free.

    Usage:
        get <item>
    """

    key = "get"
    aliases = ["take", "grab"]

    def func(self):
        from typeclasses.items import Item
        
        caller = self.caller
        itemname = self.args.strip()

        if not itemname:
            caller.msg("Get what?")
            return

        # Search in the room - enhanced search by display name and aliases
        item = self._find_item_in_room(caller, itemname)
        if not item:
            return

        # Only allow picking up actual items
        if not isinstance(item, Item):
            caller.msg(f"You can't pick up {item.get_display_name(caller)}.")
            return

        # Try to put it in a free hand
        for hand, held in caller.hands.items():
            if held is None:
                caller.hands[hand] = item
                item.location = caller
                caller.msg(f"You pick up {item.get_display_name(caller)} and hold it in your {hand} hand.")
                caller.location.msg_contents(
                    f"{caller.key} picks up {item.get_display_name(caller)} and holds it in {hand} hand.", exclude=caller
                )
                return

        # No free hands — move the first held item to inventory
        for hand, held in caller.hands.items():
            if held:
                held.location = caller  # move to inventory
                caller.hands[hand] = item
                item.location = caller
                caller.msg(
                    f"Your hands are full. You move {held.get_display_name(caller)} to inventory "
                    f"and hold {item.get_display_name(caller)} in your {hand} hand."
                )
                caller.location.msg_contents(
                    f"{caller.key} picks up {item.get_display_name(caller)}, shifting {held.get_display_name(caller)} to inventory.",
                    exclude=caller
                )
                return
    
    def _find_item_in_room(self, caller, itemname):
        """Search for an item in the room using Evennia's search system."""
        # Get room contents excluding the caller
        room_candidates = [obj for obj in caller.location.contents if obj != caller]
        if not room_candidates:
            caller.msg(f"You don't see a '{itemname}' here.")
            return None
            
        result = caller.search(itemname, candidates=room_candidates, quiet=True)
        if result:
            return result[0] if isinstance(result, list) else result
        
        caller.msg(f"You don't see a '{itemname}' here.")
        return None

        # Edge case fallback — just add to inventory
        item.location = caller
        caller.msg(f"You pick up {item.key} and stow it.")


class CmdGive(Command):
    """
    Give an item to another character.

    Usage:
        give <item> to <target>
        give <item> <target>

    This command works with the Mr. Hand system. Items can be given from
    your hands or inventory. The recipient will receive the item in their
    hands if possible, otherwise in their inventory.
    """

    key = "give"

    def parse(self):
        """Parse 'give <item> to <target>' or 'give <item> <target>' syntax."""
        self.item_name = ""
        self.target_name = ""
        
        args = self.args.strip().lower()
        if not args:
            return
            
        # Look for "to" keyword first
        if " to " in args:
            parts = args.split(" to ", 1)
            if len(parts) == 2:
                self.item_name = parts[0].strip()
                self.target_name = parts[1].strip()
        else:
            # Try "give <item> <target>" syntax (no "to")
            parts = args.split(None, 1)  # Split on whitespace, max 2 parts
            if len(parts) == 2:
                words = args.split()
                if len(words) >= 2:
                    # Take first word as item, last word as target
                    self.item_name = words[0]
                    self.target_name = words[-1]
                    # If there are more words, they're part of the item name
                    if len(words) > 2:
                        self.item_name = " ".join(words[:-1])

    def func(self):
        caller = self.caller
        
        # Basic syntax validation
        if not self.item_name or not self.target_name:
            caller.msg("Usage: give <item> to <target> or give <item> <target>")
            return

        # Find target in the same room
        target = caller.search(self.target_name, location=caller.location)
        if not target:
            return  # Error message already sent by search

        # Check if caller has hands
        if not hasattr(caller, 'hands'):
            caller.msg("You have no hands to give items with.")
            return

        # Check if caller actually has any hands at all
        caller_hands = getattr(caller, 'hands', {})
        if not caller_hands:
            caller.msg("You have no hands to give items with.")
            return

        # Check if target has hands (is a character)
        if not hasattr(target, 'hands'):
            caller.msg(f"You can't give items to {target.key} - they have no hands to receive them.")
            return

        # Check if target actually has any hands at all
        target_hands = getattr(target, 'hands', {})
        if not target_hands:
            caller.msg(f"You can't give items to {target.key} - they have no hands to receive them.")
            return

        # Check if target has any free hands
        free_hand = None
        for hand, held_item in target_hands.items():
            if held_item is None:
                free_hand = hand
                break

        if not free_hand:
            caller.msg(f"{target.key}'s hands are full and cannot receive {self.item_name}.")
            return

        # Find the item - first check hands, then inventory
        item = None
        from_hand = None
        
        # First check if it's in hands
        for hand, held_item in caller.hands.items():
            if held_item and self.item_name.lower() in held_item.key.lower():
                item = held_item
                from_hand = hand
                break
        
        # If not found in hands, check inventory
        if not item:
            items = caller.search(self.item_name, location=caller, quiet=True)
            if items:
                item = items[0]

        if not item:
            caller.msg(f"You aren't carrying or holding '{self.item_name}'.")
            return

        # If giving from inventory, need to wield it first
        if not from_hand:
            # Find a free hand to wield it
            caller_free_hand = None
            for hand, held_item in caller.hands.items():
                if held_item is None:
                    caller_free_hand = hand
                    break
            
            if not caller_free_hand:
                caller.msg(f"Your hands are full. You need a free hand to give {item.key}.")
                return
            
            # Wield the item first
            wield_result = caller.wield_item(item, caller_free_hand)
            if "wield" not in wield_result.lower():
                caller.msg(f"Failed to prepare {item.key} for giving: {wield_result}")
                return
            
            # Announce the wield action to match standard wield messages
            caller.msg(f"You wield {item.key} in your {caller_free_hand} hand.")
            caller.location.msg_contents(
                f"{caller.key} wields {item.key} in their {caller_free_hand} hand.",
                exclude=caller
            )
            
            from_hand = caller_free_hand

        # Now transfer from caller's hand to target's hand
        caller.hands[from_hand] = None
        target_hands[free_hand] = item
        item.move_to(target, quiet=True)
        
        # Success messages
        caller.msg(f"You give {item.key} to {target.key}.")
        target.msg(f"{caller.key} gives you {item.key}. You hold it in your {free_hand} hand.")
        caller.location.msg_contents(
            f"{caller.key} gives {item.key} to {target.key}.",
            exclude=[caller, target]
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

        # Import combat constants here to avoid circular imports
        from evennia.comms.models import ChannelDB
        from world.combat.constants import (
            MSG_WREST_SUCCESS_CALLER, MSG_WREST_SUCCESS_TARGET, MSG_WREST_SUCCESS_ROOM,
            MSG_WREST_FAILED_CALLER, MSG_WREST_FAILED_TARGET, MSG_WREST_FAILED_ROOM,
            MSG_WREST_IN_COMBAT, MSG_WREST_NO_FREE_HANDS, MSG_WREST_TARGET_NOT_FOUND,
            MSG_WREST_OBJECT_NOT_IN_HANDS, DB_CHAR, DB_GRAPPLED_BY_DBREF,
            STAT_GRIT, SPLATTERCAST_CHANNEL
        )
        from world.combat.utils import roll_stat, roll_with_disadvantage

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
            success = self._execute_grit_contest(caller, target, is_grappled, roll_stat, roll_with_disadvantage)

        # 7. Handle result
        if success:
            self._execute_transfer(caller, target, target_object, free_hand, target_hand)
            self._announce_success(caller, target, target_object, MSG_WREST_SUCCESS_CALLER, MSG_WREST_SUCCESS_TARGET, MSG_WREST_SUCCESS_ROOM)
        else:
            self._announce_failure(caller, target, target_object, MSG_WREST_FAILED_CALLER, MSG_WREST_FAILED_TARGET, MSG_WREST_FAILED_ROOM)

    def _is_caller_in_combat(self):
        """Check if caller is currently in combat."""
        from world.combat.constants import DB_CHAR
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
        from world.combat.constants import DB_CHAR, DB_GRAPPLED_BY_DBREF
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

    def _execute_grit_contest(self, caller, target, target_is_grappled, roll_stat, roll_with_disadvantage):
        """Execute Grit vs Grit contest, with disadvantage for grappled targets."""
        from evennia.comms.models import ChannelDB
        from world.combat.constants import STAT_GRIT, SPLATTERCAST_CHANNEL
        
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

    def _announce_success(self, caller, target, obj, msg_caller, msg_target, msg_room):
        """Announce successful wrest to all relevant parties."""
        object_name = obj.get_display_name(caller)
        
        # Message to caller
        caller.msg(msg_caller.format(
            object=object_name,
            target=target.get_display_name(caller)
        ))
        
        # Message to target
        target.msg(msg_target.format(
            caller=caller.get_display_name(target),
            object=object_name
        ))
        
        # Message to room (exclude caller and target)
        caller.location.msg_contents(
            msg_room.format(
                caller=caller.get_display_name(None),
                target=target.get_display_name(None),
                object=object_name
            ),
            exclude=[caller, target]
        )

    def _announce_failure(self, caller, target, obj, msg_caller, msg_target, msg_room):
        """Announce failed wrest attempt to all relevant parties."""
        object_name = obj.get_display_name(caller)
        
        # Message to caller
        caller.msg(msg_caller.format(
            object=object_name,
            target=target.get_display_name(caller)
        ))
        
        # Message to target
        target.msg(msg_target.format(
            caller=caller.get_display_name(target),
            object=object_name
        ))
        
        # Message to room (exclude caller and target)
        caller.location.msg_contents(
            msg_room.format(
                caller=caller.get_display_name(None),
                target=target.get_display_name(None),
                object=object_name
            ),
            exclude=[caller, target]
        )
