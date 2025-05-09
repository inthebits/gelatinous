from evennia import Command
from evennia.utils.search import search_object
from world.combat_messages import get_combat_message

class CmdHeal(Command):
    """
    Instantly heal a target character or mob.

    Usage:
        @heal <target> [= <amount>]

    If no amount is provided, HP is fully restored to max.
    """

    key = "@heal"
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        if not self.args:
            caller.msg("|rUsage: @heal <target> [= <amount>]|n")
            return

        parts = self.args.split("=", 1)
        target_name = parts[0].strip()
        amount = None

        if len(parts) > 1:
            try:
                amount = int(parts[1].strip())
                if amount < 0:
                    caller.msg("|rAmount must be zero or positive.|n")
                    return
            except ValueError:
                caller.msg("|rAmount must be an integer.|n")
                return

        matches = search_object(target_name)
        if not matches:
            caller.msg(f"|rNo character named '{target_name}' found.|n")
            return

        target = matches[0]

        if not hasattr(target, "hp") or not hasattr(target, "hp_max"):
            caller.msg(f"|r{target.key} does not have HP stats.|n")
            return

        old_hp = target.hp
        if amount is None:
            target.hp = target.hp_max
            caller.msg(f"|g{target.key} fully healed from {old_hp} to {target.hp_max} HP.|n")
        else:
            new_hp = min(target.hp + amount, target.hp_max)
            target.hp = new_hp
            caller.msg(f"|g{target.key} healed from {old_hp} to {new_hp} HP.|n")

class CmdTestCombatMsg(Command):
    """
    Test the get_combat_message utility.

    Usage:
        @testcombatmsg [<weapon_type> <phase> [damage]]

    Example:
        @testcombatmsg
        @testcombatmsg unarmed hit 5
    """
    key = "@testcombatmsg"
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"

    def func(self):
        args = self.args.strip().split()
        # Defaults
        weapon_type = "unarmed"
        phase = "hit"
        damage = 0

        if len(args) >= 1:
            weapon_type = args[0]
        if len(args) >= 2:
            phase = args[1]
        if len(args) >= 3:
            try:
                damage = int(args[2])
            except ValueError:
                self.caller.msg("Damage must be an integer.")
                return

        msg = get_combat_message(
            weapon_type,
            phase,
            attacker=self.caller,
            target=self.caller,
            item=None,
            damage=damage
        )
        if msg:
            self.caller.msg(f"Result: {msg}")
        else:
            self.caller.msg("No message template found for those parameters.")
