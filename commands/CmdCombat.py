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
class CmdWield(Command):
    """
    Wield an item into a specific hand.

    Usage:
        wield <item> [= <hand>]

    Example:
        wield shiv = right
        wield baton        (defaults to right)
    """

    key = "wield"

    def func(self):
        caller = self.caller

        if "=" in self.args:
            itemname, hand = [s.strip() for s in self.args.split("=", 1)]
        else:
            itemname = self.args.strip()
            hand = "right"

        item = caller.search(itemname, location=caller)
        if not item:
            return

        result = caller.wield_item(item, hand)
        caller.msg(result)

class CmdUnwield(Command):
    """
    Unwield an item from a specific hand.

    Usage:
        unwield <hand>

    Example:
        unwield right
        unwield left
    """

    key = "unwield"

    def func(self):
        caller = self.caller
        hand = self.args.strip().lower()

        if not hand:
            caller.msg("You must specify which hand to unwield from.")
            return

        result = caller.unwield_item(hand)
        caller.msg(result)
