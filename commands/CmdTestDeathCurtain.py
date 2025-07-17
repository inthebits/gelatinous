"""
Test command for the death curtain animation.
"""

from evennia import Command
from typeclasses.curtain_of_death import show_death_curtain


class CmdTestDeathCurtain(Command):
    """
    Test the death curtain animation with various messages.
    
    Usage:
        testdeathcurtain [message]
        
    Examples:
        testdeathcurtain
        testdeathcurtain You feel your strength ebbing away...
        testdeathcurtain The darkness consumes you
    """
    
    key = "testdeathcurtain"
    aliases = ["testcurtain", "curtaintest"]
    locks = "cmd:all()"
    
    def func(self):
        """Execute the command."""
        caller = self.caller
        
        # Use custom message if provided, otherwise use default
        if self.args.strip():
            message = self.args.strip()
            caller.msg(f"|yStarting death curtain animation with message: '{message}'|n")
        else:
            message = None
            caller.msg("|yStarting death curtain animation with default message...|n")
            
        show_death_curtain(caller, message)
