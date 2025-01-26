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

    def func(self):
        self.caller.msg(f"Echo: '{self.args.strip()}'")
        truegrit = self.grit
        self.caller.msg(f"Your grit is: '{self.grit}'.'")
# ...