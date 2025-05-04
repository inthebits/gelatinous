#Mr. Hands System Inventory Management
# This should probably be moved to a separate file
# but for now, it's here for simplicity.
from evennia import Command
from evennia.utils.search import search_object

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

        # Search for item in inventory
        item = caller.search(itemname, location=caller)
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
        itemname = self.args.strip().lower()

        if not itemname:
            caller.msg("What do you want to unwield?")
            return

        hands = caller.hands
        for hand, held_item in hands.items():
            if held_item and itemname in held_item.key.lower():
                result = caller.unwield_item(hand)
                caller.msg(result)
                return

        caller.msg(f"You aren't holding '{itemname}'.")


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

        if not items and all(v is None for v in hands.values()):
            caller.msg("You aren't carrying or holding anything.")
            return

        lines = []

        # Carried (not wielded)
        if items:
            lines.append("|wCarrying:|n")
            for obj in items:
                lines.append(f"  {obj.name}")
            lines.append("")

        # Held (in hands)
        lines.append("|wHeld:|n")
        for hand, item in hands.items():
            if item:
                lines.append(f"A {item.name} is held in your {hand.lower()} hand.")
            else:
                lines.append(f"Nothing is in your {hand.lower()} hand.")

        caller.msg("\n".join(lines))

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

        # Try inventory first
        obj = caller.search(args, location=caller, quiet=True)

        # If not found, search hands
        if not obj:
            for hand, item in caller.hands.items():
                if item and args.lower() in item.key.lower():
                    obj = [item]
                    break

        if not obj:
            caller.msg("You aren't carrying or holding that.")
            return

        obj = obj[0]

        # If it's wielded, remove it from the hand
        for hand, item in caller.hands.items():
            if item == obj:
                caller.hands[hand] = None
                caller.msg(f"You release {obj.key} from your {hand} hand.")
                break

        # Move the item to the room
        obj.move_to(caller.location, quiet=True)
        caller.msg(f"You drop {obj.key}.")
        caller.location.msg_contents(f"{caller.key} drops {obj.key}.", exclude=caller)


class CmdGet(Command):
    """
    Pick up an item and hold it if a hand is free.

    Usage:
        get <item>
    """

    key = "get"
    aliases = ["take", "grab"]

    def func(self):
        caller = self.caller
        itemname = self.args.strip().lower()

        if not itemname:
            caller.msg("Get what?")
            return

        # Search in the room
        item = caller.search(itemname, location=caller.location)
        if not item:
            return

        # Try to put it in a free hand
        for hand, held in caller.hands.items():
            if held is None:
                caller.hands[hand] = item
                item.location = caller
                caller.msg(f"You pick up {item.key} and hold it in your {hand} hand.")
                caller.location.msg_contents(
                    f"{caller.key} picks up {item.key} and holds it in {hand} hand.", exclude=caller
                )
                return

        # No free hands — move the first held item to inventory
        for hand, held in caller.hands.items():
            if held:
                held.location = caller  # move to inventory
                caller.hands[hand] = item
                item.location = caller
                caller.msg(
                    f"Your hands are full. You move {held.key} to inventory "
                    f"and hold {item.key} in your {hand} hand."
                )
                caller.location.msg_contents(
                    f"{caller.key} picks up {item.key}, shifting {held.key} to inventory.",
                    exclude=caller
                )
                return

        # Edge case fallback — just add to inventory
        item.location = caller
        caller.msg(f"You pick up {item.key} and stow it.")
