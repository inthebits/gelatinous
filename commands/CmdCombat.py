from evennia import Command
from evennia.utils.utils import inherits_from
from random import randint, choice
from world.combathandler import get_or_create_combat, COMBAT_SCRIPT_KEY
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
        combat.add_combatant(caller, target)      # Attacker targets defender
        combat.add_combatant(target, caller)      # Defender targets attacker

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
            # Remove from combat first so exit doesn't block movement
            handler.remove_combatant(caller)
            if handler and handler.db.combatants and len(handler.db.combatants) <= 1:
                handler.stop()
            # Now move through a random available exit
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
            if handler and handler.db.combatants and len(handler.db.combatants) <= 1:
                handler.stop()

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

        # Grit vs Grit check
        attacker_grit = getattr(caller, "grit", 1)
        defender_grit = getattr(target, "grit", 1)
        disarm_roll = randint(1, max(1, attacker_grit))
        resist_roll = randint(1, max(1, defender_grit))
        splattercast.msg(
            f"{caller.key} attempts to disarm {target.key}: {disarm_roll} (grit) vs {resist_roll} (grit)"
        )

        if disarm_roll < resist_roll:
            caller.msg(f"You try to disarm {target.key}, but they resist!")
            target.msg(f"{caller.key} tried to disarm you, but you resisted!")
            splattercast.msg(f"{caller.key} failed to disarm {target.key}.")
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


class CmdGrapple(Command):
    """
    Attempt to grapple a target in your current room.

    Usage:
        grapple <target>

    You must be in combat to attempt a grapple.
    If successful, you will be grappling the target, and they will be grappled by you.
    """
    key = "grapple"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        if not self.args:
            caller.msg("Grapple whom?")
            return

        handler = get_or_create_combat(caller.location)
        if not handler:
            caller.msg("Error: Could not find or create combat handler.")
            return

        caller_combat_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_combat_entry:
            caller.msg("You are not in combat or there's an issue finding your combat entry.")
            return

        # Check if caller is already grappling someone
        if caller_combat_entry.get("grappling"):
            caller.msg(f"You are already grappling {caller_combat_entry['grappling'].key}. You must release them first.")
            splattercast.msg(f"{caller.key} tried to grapple while already grappling {caller_combat_entry['grappling'].key}.")
            return
        
        # Check if caller is currently grappled by someone else
        if caller_combat_entry.get("grappled_by"):
            caller.msg(f"You cannot initiate a grapple while {caller_combat_entry['grappled_by'].key} is grappling you. Try to escape first.")
            splattercast.msg(f"{caller.key} tried to grapple while being grappled by {caller_combat_entry['grappled_by'].key}.")
            return

        search_name = self.args.strip().lower()
        # Ensure target is in the same combat
        valid_targets = [e["char"] for e in handler.db.combatants if e["char"] != caller]
        
        matches = [
            obj for obj in valid_targets
            if search_name in obj.key.lower()
            or any(search_name in alias.lower() for alias in (obj.aliases.all() if hasattr(obj.aliases, "all") else []))
        ]

        if not matches:
            caller.msg("No valid target to grapple in this combat.")
            splattercast.msg(
                f"{caller.key} tried to grapple '{search_name}' but found no valid target in combat."
            )
            return

        target = matches[0]

        if target == caller: # Should be caught by valid_targets but good to double check
            caller.msg("You can't grapple yourself.")
            return

        # Check if target is already grappled by someone else
        target_entry = next((e for e in handler.db.combatants if e["char"] == target), None)
        if target_entry and target_entry.get("grappled_by"):
            caller.msg(f"{target.key} is already being grappled by {target_entry['grappled_by'].key}.")
            splattercast.msg(f"{caller.key} tried to grapple {target.key}, but they are already grappled by {target_entry['grappled_by'].key}.")
            return

        caller_combat_entry["combat_action"] = {"type": "grapple", "target": target}
        caller.msg(f"You prepare to grapple {target.key}...")
        splattercast.msg(f"{caller.key} sets combat action to grapple {target.key} (via handler).")
        # The combat handler will process this on the character's turn


class CmdEscapeGrapple(Command):
    """
    Attempts to escape from a grapple.

    Usage:
      escape
      resist

    This command allows a character to attempt to break free if they
    are currently being grappled by another character in combat.
    """
    key = "escape"
    aliases = ["resist"]
    help_category = "Combat"
    locks = "cmd:in_combat()" # Ensure character is in combat

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        # Get the combat handler from the caller's NDB.
        # The cmd:in_combat() lock should ensure this is set if they are in combat.
        handler = getattr(caller.ndb, "combat_handler", None) 
        
        if not handler:
            # This message should ideally not be reached if the in_combat lock is effective.
            caller.msg("You are not in combat.") 
            splattercast.msg(f"{caller.key} tried to escape, but no combat_handler found in ndb (check cmd:in_combat() lock).")
            return

        # Find the caller's entry in the combat handler
        caller_combat_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)

        if not caller_combat_entry:
            caller.msg("You are not properly registered in the current combat.")
            splattercast.msg(f"{caller.key} tried to escape, but not found in combatants list of handler {handler.key}.")
            return

        grappler = caller_combat_entry.get("grappled_by")

        if not grappler:
            caller.msg("You are not currently being grappled by anyone.")
            splattercast.msg(f"{caller.key} tried to escape, but is not grappled.")
            return

        # Set the combat action in the handler's list for the caller
        caller_combat_entry["combat_action"] = {"type": "escape"}
        caller.msg(f"You prepare to escape from {grappler.key}'s grasp...")
        splattercast.msg(f"{caller.key} sets combat action to escape from {grappler.key} (via handler {handler.key}).")
        # The combat handler will process this on the character's turn


class CmdReleaseGrapple(Command):
    """
    Release a target you are currently grappling.

    Usage:
        release
        release grapple

    You must be grappling someone to use this command.
    """
    key = "release"
    aliases = ["release grapple"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        handler = getattr(caller.ndb, "combat_handler", None)
        if not handler:
            caller.msg("You are not in combat.")
            splattercast.msg(f"{caller.key} tried to release grapple but is not in combat.")
            return

        caller_entry = next((e for e in handler.db.combatants if e["char"] == caller), None)
        if not caller_entry or not caller_entry.get("grappling"):
            caller.msg("You are not currently grappling anyone.")
            splattercast.msg(f"{caller.key} tried to release grapple but is not grappling anyone.")
            return
            
        grappled_victim = caller_entry["grappling"]
        caller.ndb.combat_action = {"type": "release_grapple"} # Target is implicit (who they are grappling)
        caller.msg(f"You prepare to release {grappled_victim.key}...")
        splattercast.msg(f"{caller.key} sets combat action to release grapple on {grappled_victim.key}.")
        # The combat handler will process this
