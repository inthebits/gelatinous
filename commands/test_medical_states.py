"""
Testing commands for medical revival system.

These commands allow testing of the death/unconscious command restriction system.
"""

from evennia import Command


class CmdTestDeath(Command):
    """
    Test death state command restrictions.
    
    Usage:
        testdeath [force]
        
    This command toggles the death state for testing command restrictions.
    If 'force' is specified, applies restrictions even to staff.
    """
    key = "testdeath"
    aliases = ["td"]
    locks = "cmd:perm(Builder)"
    help_category = "Testing"
    
    def func(self):
        caller = self.caller
        force_test = "force" in self.args.lower()
        
        if caller.is_dead():
            # Character is dead, revive them
            caller.remove_death_state()
            caller.msg("|gYou have been revived from death for testing.|n")
        else:
            # Character is alive, kill them for testing
            # Temporarily set a death state without actual medical damage
            caller.db._test_death_state = True
            caller.apply_death_state(force_test=force_test)
            caller.msg("|rYou have been killed for testing command restrictions.|n")
            if force_test:
                caller.msg("|yForce mode: restrictions apply even to staff.|n")


class CmdTestUnconscious(Command):
    """
    Test unconscious state command restrictions.
    
    Usage:
        testunconscious [force]
        
    This command toggles the unconscious state for testing command restrictions.
    If 'force' is specified, applies restrictions even to staff.
    """
    key = "testunconscious"
    aliases = ["tu"]
    locks = "cmd:perm(Builder)"
    help_category = "Testing"
    
    def func(self):
        caller = self.caller
        force_test = "force" in self.args.lower()
        
        if caller.is_unconscious():
            # Character is unconscious, wake them up
            caller.remove_unconscious_state()
            caller.msg("|gYou have been awakened from unconsciousness for testing.|n")
        else:
            # Character is conscious, make them unconscious for testing
            # Temporarily set an unconscious state without actual medical damage
            caller.db._test_unconscious_state = True
            caller.apply_unconscious_state(force_test=force_test)
            caller.msg("|rYou have been knocked unconscious for testing command restrictions.|n")
            if force_test:
                caller.msg("|yForce mode: restrictions apply even to staff.|n")


class CmdTestMedicalClear(Command):
    """
    Clear all test medical states and restore normal commands.
    
    Usage:
        testmedicalclear
        
    This command removes any test death/unconscious states and restores
    the normal command set.
    """
    key = "testmedicalclear"
    aliases = ["tmc"]
    locks = "cmd:perm(Builder)"
    help_category = "Testing"
    
    def func(self):
        caller = self.caller
        
        # Clear test flags
        if hasattr(caller.db, '_test_death_state'):
            del caller.db._test_death_state
        if hasattr(caller.db, '_test_unconscious_state'):
            del caller.db._test_unconscious_state
        
        # Remove any medical state restrictions
        try:
            caller.remove_death_state()
        except Exception:
            pass
            
        try:
            caller.remove_unconscious_state()
        except Exception:
            pass
        
        caller.msg("|gAll test medical states cleared. Normal commands restored.|n")


# Modify the character's medical state methods to check for test flags
def test_aware_is_dead(original_method):
    """Decorator to make is_dead() check test flags"""
    def wrapper(self):
        # Check for test flag first
        if hasattr(self.db, '_test_death_state') and self.db._test_death_state:
            return True
        # Fall back to original method
        return original_method(self)
    return wrapper


def test_aware_is_unconscious(original_method):
    """Decorator to make is_unconscious() check test flags"""
    def wrapper(self):
        # Check for test flag first
        if hasattr(self.db, '_test_unconscious_state') and self.db._test_unconscious_state:
            return True
        # Fall back to original method
        return original_method(self)
    return wrapper