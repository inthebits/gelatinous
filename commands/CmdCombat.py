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
    '''
    Attempt to flee combat.

    Usage:
      flee

    Attempts to escape from combat. If successful, you are removed from combat.
    If you fail, you lose your turn this round.
    '''

    key = "flee"

    def func(self):
        caller = self.caller
        location = caller.location

        handler = location.scripts.get("combat_handler")
        if not handler:
            caller.msg("[DEBUG] You are not in combat.")
            return

        handler = handler[0]
        combatants = [entry["char"] for entry in handler.db.combatants if entry["char"] != caller and entry["char"].location == location]

        if not combatants:
            caller.msg("[DEBUG] There's no one left to flee from.")
            return

        flee_roll = randint(1, max(1, caller.motorics))
        avg_motorics = sum(c.motorics for c in combatants) / len(combatants)
        opponent_roll = randint(1, max(1, int(avg_motorics)))

        location.msg_contents(f"[DEBUG] {caller.key} attempts to flee! (You: {flee_roll} vs Opponents: {opponent_roll})")

        if flee_roll > opponent_roll:
            handler.remove_combatant(caller)
            location.msg_contents(f"[DEBUG] {caller.key} successfully flees from combat.")
        else:
            caller.ndb.skip_combat_round = True
            location.msg_contents(f"[DEBUG] {caller.key} fails to flee and loses their action.")
