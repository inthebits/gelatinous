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
        
        # Access grit attribute with and without category
        grit = self.caller.db.grit
        if grit is None:
            grit = self.caller.attributes.get("grit", category="stat")
        
        self.caller.msg(f"Your grit is: {grit}.")
# ...