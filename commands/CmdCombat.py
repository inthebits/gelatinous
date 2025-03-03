from evennia import Command

class CmdAttack(Command):
    """
    Attack another character.
    
    Usage:
        attack <character>
        kill <character>
    
    Example:
        kill Bob
        attack Bob
    """
    key = "kill"
    aliases = ["attack"]

    def func(self):
        self.caller.msg(f"Echo: '{self.args.strip()}'")
        grit = self.caller.db.grit
        self.caller.msg(f"Your grit is: {self.caller.db.grit}.")
# ...