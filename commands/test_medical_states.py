"""
Testing commands for medical revival system.

These commands allow testing of the death/unconscious command restriction system.
"""

from evennia import Command


class CmdTestDeath(Command):
    """
    Test death state command restrictions.
    
    Usage:
        testdeath [<target>] [force]
        
    This command toggles the death state for testing command restrictions.
    If no target is specified, affects yourself.
    If 'force' is specified, applies restrictions even to staff.
    """
    key = "testdeath"
    aliases = ["td"]
    locks = "cmd:perm(Builder)"
    help_category = "Testing"
    
    def func(self):
        caller = self.caller
        args = self.args.strip()
        
        # Parse arguments for target and force flag
        force_test = "force" in args.lower()
        target_name = args.replace("force", "").strip()
        
        # Determine target
        if target_name:
            target = caller.search(target_name, global_search=True)
            if not target:
                caller.msg(f"Could not find '{target_name}'.")
                return
            if not hasattr(target, 'is_dead'):
                caller.msg(f"{target.key} is not a character.")
                return
        else:
            target = caller
        
        if target.is_dead():
            # Character is dead, revive them
            target.remove_death_state()
            caller.msg(f"|g{target.key} has been revived from death for testing.|n")
            if target != caller:
                target.msg("|gYou have been revived from death for testing.|n")
        else:
            # Character is alive, kill them for testing
            # Temporarily set a death state without actual medical damage
            target.db._test_death_state = True
            target.apply_death_state(force_test=force_test)
            caller.msg(f"|r{target.key} has been killed for testing command restrictions.|n")
            if target != caller:
                target.msg("|rYou have been killed for testing command restrictions.|n")
            if force_test:
                caller.msg("|yForce mode: restrictions apply even to staff.|n")
                if target != caller:
                    target.msg("|yForce mode: restrictions apply even to staff.|n")


class CmdTestUnconscious(Command):
    """
    Test unconscious state command restrictions.
    
    Usage:
        testunconscious [<target>] [force]
        
    This command toggles the unconscious state for testing command restrictions.
    If no target is specified, affects yourself.
    If 'force' is specified, applies restrictions even to staff.
    """
    key = "testunconscious"
    aliases = ["tu"]
    locks = "cmd:perm(Builder)"
    help_category = "Testing"
    
    def func(self):
        caller = self.caller
        args = self.args.strip()
        
        # Parse arguments for target and force flag
        force_test = "force" in args.lower()
        target_name = args.replace("force", "").strip()
        
        # Determine target
        if target_name:
            target = caller.search(target_name, global_search=True)
            if not target:
                caller.msg(f"Could not find '{target_name}'.")
                return
            if not hasattr(target, 'is_unconscious'):
                caller.msg(f"{target.key} is not a character.")
                return
        else:
            target = caller
        
        if target.is_unconscious():
            # Character is unconscious, wake them up
            target.remove_unconscious_state()
            caller.msg(f"|g{target.key} has been awakened from unconsciousness for testing.|n")
            if target != caller:
                target.msg("|gYou have been awakened from unconsciousness for testing.|n")
        else:
            # Character is conscious, make them unconscious for testing
            # Temporarily set an unconscious state without actual medical damage
            target.db._test_unconscious_state = True
            target.apply_unconscious_state(force_test=force_test)
            caller.msg(f"|r{target.key} has been knocked unconscious for testing command restrictions.|n")
            if target != caller:
                target.msg("|rYou have been knocked unconscious for testing command restrictions.|n")
            if force_test:
                caller.msg("|yForce mode: restrictions apply even to staff.|n")
                if target != caller:
                    target.msg("|yForce mode: restrictions apply even to staff.|n")


class CmdTestMedicalClear(Command):
    """
    Clear all test medical states and restore normal commands.
    
    Usage:
        testmedicalclear [<target>]
        
    This command removes any test death/unconscious states and restores
    the normal command set. If no target is specified, affects yourself.
    """
    key = "testmedicalclear"
    aliases = ["tmc"]
    locks = "cmd:perm(Builder)"
    help_category = "Testing"
    
    def func(self):
        caller = self.caller
        target_name = self.args.strip()
        
        # Determine target
        if target_name:
            target = caller.search(target_name, global_search=True)
            if not target:
                caller.msg(f"Could not find '{target_name}'.")
                return
            if not hasattr(target, 'db'):
                caller.msg(f"{target.key} is not a character.")
                return
        else:
            target = caller
        
        # Clear test flags
        if hasattr(target.db, '_test_death_state'):
            del target.db._test_death_state
        if hasattr(target.db, '_test_unconscious_state'):
            del target.db._test_unconscious_state
        
        # Remove any medical state restrictions
        try:
            target.remove_death_state()
        except Exception:
            pass
            
        try:
            target.remove_unconscious_state()
        except Exception:
            pass
        
        caller.msg(f"|gAll test medical states cleared for {target.key}. Normal commands restored.|n")
        if target != caller:
            target.msg("|gAll test medical states cleared. Normal commands restored.|n")


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