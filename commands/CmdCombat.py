from evennia import Command
from evennia.utils.utils import inherits_from
from random import randint
from world.combathandler import get_or_create_combat


class CmdAttack(Command):
    """
    Attack a target in your current room.

    Usage:
        attack <target>
        kill <target>

    Initiates combat and attempts a hit based on your Grit vs their Motorics.
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
        combat.add_combatant(caller)
        combat.add_combatant(target)

        # Attack resolution
        atk_roll = randint(1, max(1, caller.grit))
        def_roll = randint(1, max(1, target.motorics))

        caller.msg(f"You attempt to strike {target.key}!")
        target.msg(f"{caller.key} attacks you!")

        if atk_roll > def_roll:
            damage = caller.grit
            target.hp -= damage
            caller.msg(f"|rHit!|n You deal {damage} damage.")
            target.msg(f"|rYou've been hit for {damage} damage!|n")

            if target.hp <= 0:
                caller.msg(f"|R{target.key} collapses from your blow.|n")
                target.msg(f"|RYou feel your body fail and fall...|n")
                target.die()
        else:
            caller.msg("You miss.")
            target.msg(f"You dodge {caller.key}'s strike.")
