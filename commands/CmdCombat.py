from evennia import Command
from evennia.utils.search import search_object
from evennia.utils.utils import inherits_from
from random import randint
from world.combathandler import get_or_create_combat

class CmdAttack(Command):
    """
    Engage in combat with a target.

    Usage:
        attack <target>
        kill <target>

    Rolls initiative and a to-hit check.
    """

    key = "attack"
    aliases = ["kill"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller

        if not self.args:
            caller.msg("Attack who?")
            return

        matches = search_object(self.args.strip(), location=caller.location)
        if not matches:
            caller.msg("No such target found.")
            return

        target = matches[0]

        if target == caller:
            caller.msg("Attacking yourself won't get you far.")
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg("That target can't be attacked.")
            return

        # Start or join combat
        combat = get_or_create_combat(caller.location)
        combat.add_combatant(caller)
        combat.add_combatant(target)

        # Attack roll
        atk_roll = randint(1, max(1, caller.grit))
        def_roll = randint(1, max(1, target.motorics))

        caller.msg(f"You lunge at {target.key}!")
        target.msg(f"{caller.key} attacks you!")

        if atk_roll > def_roll:
            damage = caller.grit
            target.hp -= damage
            caller.msg(f"|rHit!|n You deal {damage} damage.")
            target.msg(f"|rYou've been hit for {damage} damage!|n")

            if target.hp <= 0:
                caller.msg(f"|r{target.key} collapses.|n")
                target.msg(f"|RYou feel your body shutting down...|n")
                target.die()
        else:
            caller.msg("Your strike misses!")
            target.msg(f"You dodge {caller.key}'s attack.")
