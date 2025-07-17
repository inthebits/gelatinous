"""
Test command for the curtain of death effect
"""
from evennia import Command


class CmdTestDeathCurtain(Command):
    """
    Test the death curtain effect
    
    Usage:
        testdeath [instant] [message]
    
    Examples:
        testdeath
        testdeath instant
        testdeath "Your custom death message here"
        testdeath instant "Quick death message"
    """
    
    key = "testdeath"
    locks = "cmd:perm(Admin)"
    help_category = "Admin"
    
    def func(self):
        """Execute the test."""
        args = self.args.strip()
        
        # Parse arguments
        instant = False
        message = None
        
        if args:
            parts = args.split(' ', 1)
            if parts[0].lower() == 'instant':
                instant = True
                if len(parts) > 1:
                    message = parts[1].strip('"')
            else:
                message = args.strip('"')
        
        # Send the effect
        if instant:
            send_death_curtain_instant(self.caller, message)
            self.caller.msg("|gDeath curtain test (instant mode) sent!|n")
        else:
            send_death_curtain(self.caller, message)
            self.caller.msg("|gDeath curtain test (animated) started!|n")


class CmdSetDeathMode(Command):
    """
    Set your death animation preference
    
    Usage:
        deathmode [instant|animated]
    
    Without arguments, shows current setting.
    """
    
    key = "deathmode"
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the command."""
        args = self.args.strip().lower()
        
        if not args:
            # Show current setting
            current = getattr(self.caller.db, 'instant_death', False)
            mode = "instant" if current else "animated"
            self.caller.msg(f"|gYour death mode is currently set to: {mode}|n")
            return
        
        if args == "instant":
            self.caller.db.instant_death = True
            self.caller.msg("|gDeath mode set to instant.|n")
        elif args == "animated":
            self.caller.db.instant_death = False
            self.caller.msg("|gDeath mode set to animated.|n")
        else:
            self.caller.msg("|rUsage: deathmode [instant|animated]|n")
