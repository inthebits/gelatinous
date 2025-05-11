from evennia import Command
from evennia.utils.search import search_object
from world.combat_messages import get_combat_message

class CmdHeal(Command):
    """
    Instantly heal a target character, mob, or everyone in a location.

    Usage:
        @heal <target> [= <amount>]
        @heal here [= <amount>]
        @heal <room #> [= <amount>]

    If no amount is provided, HP is fully restored to max.
    """

    key = "@heal"
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        if not self.args:
            caller.msg("|rUsage: @heal <target|here|room #> [= <amount>]|n")
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

        targets = []

        # Handle 'here' keyword
        if target_name.lower() == "here":
            location = caller.location
            if not location:
                caller.msg("|rYou have no location.|n")
                return
            # Heal all objects in location with hp/hp_max
            targets = [obj for obj in location.contents if hasattr(obj, "hp") and hasattr(obj, "hp_max")]
            if not targets:
                caller.msg("|yNo healable targets found in this location.|n")
                return
            target_desc = f"everyone in {location.key}"
        # Handle room dbref (number)
        elif target_name.startswith("#") and target_name[1:].isdigit():
            room = search_object(target_name)
            if not room:
                caller.msg(f"|rNo room found with dbref {target_name}.|n")
                return
            room = room[0]
            targets = [obj for obj in room.contents if hasattr(obj, "hp") and hasattr(obj, "hp_max")]
            if not targets:
                caller.msg(f"|yNo healable targets found in {room.key}.|n")
                return
            target_desc = f"everyone in {room.key}"
        # Handle character dbref (number)
        elif target_name.isdigit():
            char = search_object(f"#{target_name}")
            if not char:
                caller.msg(f"|rNo character found with dbref #{target_name}.|n")
                return
            char = char[0]
            if not hasattr(char, "hp") or not hasattr(char, "hp_max"):
                caller.msg(f"|r{char.key} does not have HP stats.|n")
                return
            targets = [char]
            target_desc = char.key
        else:
            # Normal name search
            matches = search_object(target_name)
            if not matches:
                caller.msg(f"|rNo character named '{target_name}' found.|n")
                return
            target = matches[0]
            if not hasattr(target, "hp") or not hasattr(target, "hp_max"):
                caller.msg(f"|r{target.key} does not have HP stats.|n")
                return
            targets = [target]
            target_desc = target.key

        # Heal all targets
        for target in targets:
            old_hp = target.hp
            if amount is None:
                target.hp = target.hp_max
                caller.msg(f"|g{target.key} fully healed from {old_hp} to {target.hp_max} HP.|n")
            else:
                new_hp = min(target.hp + amount, target.hp_max)
                target.hp = new_hp
                caller.msg(f"|g{target.key} healed from {old_hp} to {new_hp} HP.|n")

        if len(targets) > 1:
            caller.msg(f"|gHealed {len(targets)} targets in {target_desc}.|n")
