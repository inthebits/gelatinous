from evennia import Command
from evennia.utils.utils import inherits_from
from random import randint, choice
from world.combathandler import get_or_create_combat
from world.combat_messages import get_combat_message
from evennia.comms.models import ChannelDB


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
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        if not self.args:
            caller.msg("Attack who?")
            return

        search_name = self.args.strip().lower()
        candidates = caller.location.contents

        matches = [
            obj for obj in candidates
            if search_name in obj.key.lower()
            or any(search_name in alias.lower() for alias in (obj.aliases.all() if hasattr(obj.aliases, "all") else []))
        ]

        if not matches:
            caller.msg("No valid target found.")
            splattercast.msg(
                f"{caller.key} tried to attack '{search_name}' but found no valid target."
            )
            return

        target = matches[0]

        if target == caller:
            caller.msg("You can't attack yourself.")
            splattercast.msg(
                f"{caller.key} tried to attack themselves. Ignored."
            )
            return

        if not inherits_from(target, "typeclasses.characters.Character"):
            caller.msg("That can't be attacked.")
            splattercast.msg(
                f"{caller.key} tried to attack {target.key}, but it's not a valid character."
            )
            return

        # --- Combat/targeting logic ---
        caller_handler = getattr(caller.ndb, "combat_handler", None)
        target_handler = getattr(target.ndb, "combat_handler", None)

        if caller_handler:
            if not target_handler or target_handler != caller_handler:
                caller.msg("You can't attack someone not already in combat while you're fighting!")
                splattercast.msg(
                    f"{caller.key} tried to attack {target.key} but target is not in same combat."
                )
                return
            # Both are in the same combat
            # Check if already targeting this person
            for entry in caller_handler.db.combatants:
                if entry["char"] == caller and entry.get("target") == target:
                    caller.msg(f"You're already attacking {target.key}.")
                    splattercast.msg(
                        f"{caller.key} tried to switch target to {target.key}, but was already targeting them."
                    )
                    return
            # Switch target
            caller_handler.set_target(caller, target)
            caller.msg(f"You switch your target to {target.key}.")
            splattercast.msg(
                f"{caller.key} switches target to {target.key} in combat."
            )
            return

        # If not in combat, initiate as normal
        combat = get_or_create_combat(caller.location)
        splattercast.msg(
            f"{caller.key} initiates combat with {target.key}."
        )
        combat.add_combatant(caller, target)
        combat.add_combatant(target)

        # --- Find weapon and weapon_type for both hit and miss ---
        hands = getattr(caller, "hands", {})
        weapon = None
        for hand, item in hands.items():
            if item:
                weapon = item
                break
        weapon_type = "unarmed"
        if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type:
            weapon_type = str(weapon.db.weapon_type).lower()

        splattercast.msg(
            f"{caller.key} is wielding {weapon.key if weapon else 'nothing'} ({weapon_type})."
        )

        # --- Player-facing initiate message ---
        msg = get_combat_message(weapon_type, "initiate", attacker=caller, target=target, item=weapon)
        caller.location.msg_contents(f"|R{msg}|n")


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
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        if not handler:
            caller.msg("You're not in combat.")
            return

        # Find all attackers targeting the caller
        attackers = [e["char"] for e in handler.db.combatants if e.get("target") == caller and e["char"] != caller]
        if not attackers:
            caller.msg("No one is attacking you; you can just leave.")
            splattercast.msg(
                f"{caller.key} flees unopposed and leaves combat."
            )
            handler.remove_combatant(caller)
            # End combat if only one or zero remain
            if len(handler.db.combatants) <= 1:
                handler.stop()
            return

        flee_roll = randint(1, getattr(caller, "motorics", 1))
        resist_rolls = [(attacker, randint(1, getattr(attacker, "motorics", 1))) for attacker in attackers]
        highest_attacker, highest_resist = max(resist_rolls, key=lambda x: x[1])

        splattercast.msg(
            f"{caller.key} attempts to flee: {flee_roll} vs highest resist {highest_resist} ({highest_attacker.key})"
        )

        if flee_roll > highest_resist:
            caller.msg("You flee successfully!")
            splattercast.msg(
                f"{caller.key} flees successfully from combat."
            )
            handler.remove_combatant(caller)

            exits = [ex for ex in caller.location.exits if ex.access(caller, 'traverse')]
            if exits:
                chosen_exit = choice(exits)
                splattercast.msg(
                    f"{caller.key} flees through {chosen_exit.key}."
                )
                caller.location.msg_contents(
                    f"{caller.key} flees {chosen_exit.key}.",
                    exclude=caller
                )
                chosen_exit.at_traverse(caller, chosen_exit.destination)
            else:
                caller.msg("You flee, but there's nowhere to go!")

            # End combat if only one or zero remain
            if len(handler.db.combatants) <= 1:
                handler.stop()
        else:
            caller.msg("You try to flee, but fail!")
            splattercast.msg(
                f"{caller.key} tries to flee but fails."
            )
            caller.location.msg_contents(
                f"{caller.key} tries to flee but fails.",
                exclude=caller
            )
            caller.ndb.skip_combat_round = True


class CmdDisarm(Command):
    """
    Attempt to disarm your current combat target, sending their weapon (or held item) to the ground.

    Usage:
        disarm

    You must be in combat and have a valid target.
    The command will prioritize disarming weapons, but will disarm any held item if no weapon is found.
    """

    key = "disarm"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        handler = getattr(caller.ndb, "combat_handler", None)
        if not handler:
            caller.msg("You are not in combat.")
            splattercast.msg(f"{caller.key} tried to disarm but is not in combat.")
            return

        target = handler.get_target(caller)
        if not target:
            caller.msg("You have no valid target to disarm.")
            splattercast.msg(f"{caller.key} tried to disarm but has no valid target.")
            return

        hands = getattr(target, "hands", {})
        if not hands:
            caller.msg(f"{target.key} has nothing in their hands to disarm.")
            splattercast.msg(f"{caller.key} tried to disarm {target.key}, but they have nothing in their hands.")
            return

        # Prioritize weapon-type items
        weapon_hand = None
        for hand, item in hands.items():
            if item and hasattr(item.db, "weapon_type") and item.db.weapon_type:
                weapon_hand = hand
                break

        # If no weapon, disarm any held item
        if not weapon_hand:
            for hand, item in hands.items():
                if item:
                    weapon_hand = hand
                    break

        if not weapon_hand:
            caller.msg(f"{target.key} has nothing to disarm.")
            splattercast.msg(f"{caller.key} tried to disarm {target.key}, but nothing was found.")
            return

        item = hands[weapon_hand]
        # Remove from hand and move to ground
        hands[weapon_hand] = None
        item.move_to(target.location, quiet=True)
        caller.msg(f"You disarm {target.key}, sending {item.key} to the ground!")
        target.msg(f"{caller.key} disarms you! {item.key} falls to the ground.")
        target.location.msg_contents(
            f"{caller.key} disarms {target.key}, and {item.key} falls to the ground.",
            exclude=[caller, target]
        )
        splattercast.msg(f"{caller.key} disarmed {target.key} ({item.key}) in {target.location.key}.")

        # Optionally: you could add a roll or resistance mechanic here for more depth.
