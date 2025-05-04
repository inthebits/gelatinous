from evennia import Command
from evennia.utils.utils import inherits_from
from random import randint, choice
from world.combathandler import get_or_create_combat


class CmdAttack(Command):
    """
    Attack a target in your current room.

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

        if not self.args:
            caller.msg("Attack who?")
            return

        search_name = self.args.strip().lower()
        candidates = caller.location.contents

        # Match against key or aliases, case-insensitive partials allowed
        matches = [
            obj for obj in candidates
            if search_name in obj.key.lower()
            or any(search_name in alias.lower() for alias in (obj.aliases.all() if hasattr(obj.aliases, "all") else []))
        ]

        if not matches:
            caller.msg("No valid target found.")
            return

        target = matches[0]

        if target == caller:
            caller.msg("You can't attack yourself.")
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg("That can't be attacked.")
            return

        # Start or join combat
        combat = get_or_create_combat(caller.location)
        combat.add_combatant(caller, target)
        combat.add_combatant(target)

        caller.msg(f"You prepare to attack {target.key}!")
        target.msg(f"{caller.key} prepares to attack you!")


class CmdFlee(Command):
    """
    Attempt to flee combat.

    Usage:
      flee

    If successful, you will escape the current combat and leave the room.
    If you fail, you will skip your next turn.
    """

    key = "flee"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        handler = caller.ndb.combat_handler

        if not handler:
            caller.msg("You're not in combat.")
            return

        target = handler.get_target(caller)
        if not target:
            caller.msg("You have no current target to flee from.")
            return

        flee_roll = randint(1, caller.motorics)
        resist_roll = randint(1, target.motorics)
        caller.msg(f"[DEBUG] Flee roll: {flee_roll} vs {resist_roll} ({target.key})")

        if flee_roll > resist_roll:
            caller.msg("You flee successfully!")
            caller.ndb.skip_combat_round = True

            exits = [ex for ex in caller.location.exits if ex.access(caller, 'traverse')]
            if exits:
                chosen_exit = choice(exits)
                caller.msg(f"[DEBUG] You flee through {chosen_exit.key}!")
                caller.location.msg_contents(
                    f"[DEBUG] {caller.key} flees {chosen_exit.key}.",
                    exclude=caller
                )
                chosen_exit.at_traverse(caller, chosen_exit.destination)
            else:
                caller.msg("You flee, but there's nowhere to go!")

        else:
            caller.msg("You try to flee, but fail!")
            caller.location.msg_contents(
                f"[DEBUG] {caller.key} tries to flee but fails.",
                exclude=caller
            )
            caller.ndb.skip_combat_round = True

#Mr. Hands System Inventory Management
# This should probably be moved to a separate file
# but for now, it's here for simplicity.
from evennia import Command

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

