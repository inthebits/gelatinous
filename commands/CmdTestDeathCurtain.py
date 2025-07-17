"""
Test command for the death curtain effect.
"""

from evennia import Command
from typeclasses.curtain_of_death import (
    send_death_curtain, 
    send_death_curtain_instant,
    death_by_combat,
    death_by_magic,
    death_by_poison,
    death_peaceful
)


class CmdTestDeathCurtain(Command):
    """
    Test the death curtain animation effect.
    
    Usage:
        testdeathcurtain [type]
        
    Types:
        standard - Standard death curtain (default)
        instant - All frames at once
        combat - Combat death variant
        magic - Magical death variant
        poison - Poison death variant
        peaceful - Peaceful death variant
        custom <message> - Custom message
    
    Examples:
        testdeathcurtain
        testdeathcurtain combat
        testdeathcurtain custom "You have been slain by a dragon!"
    """
    
    key = "testdeathcurtain"
    aliases = ["testcurtain", "deathtest"]
    locks = "cmd:all()"
    
    def func(self):
        """Execute the command."""
        args = self.args.strip().split()
        
        if not args:
            # Default test
            send_death_curtain(self.caller)
            return
            
        test_type = args[0].lower()
        
        if test_type == "instant":
            send_death_curtain_instant(self.caller)
            
        elif test_type == "combat":
            death_by_combat(self.caller)
            
        elif test_type == "magic":
            death_by_magic(self.caller)
            
        elif test_type == "poison":
            death_by_poison(self.caller)
            
        elif test_type == "peaceful":
            death_peaceful(self.caller)
            
        elif test_type == "custom":
            if len(args) < 2:
                self.caller.msg("Usage: testdeathcurtain custom <message>")
                return
            
            custom_message = " ".join(args[1:])
            send_death_curtain(self.caller, custom_message)
            
        else:
            self.caller.msg("Unknown test type. Use: standard, instant, combat, magic, poison, peaceful, or custom")
            return
            
        self.caller.msg("|gDeath curtain test complete.|n")
