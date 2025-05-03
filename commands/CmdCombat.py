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
        caller.msg('[DEBUG] Target found. Proceeding to get_or_create_combat.')
        caller.msg(f'[DEBUG] Target is: {target.key}, Grit: {caller.grit}, Motorics: {target.motorics}')

        if target == caller:
            caller.msg("You can't attack yourself.")
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg("That can't be attacked.")
            return

        # Start or join combat
        caller.msg('[DEBUG] Calling get_or_create_combat...')
        combat = get_or_create_combat(caller.location)
        caller.msg('[DEBUG] Adding self to combat...')
        combat.add_combatant(caller)
        caller.msg('[DEBUG] Adding target to combat...')
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