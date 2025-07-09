"""
Combat Command Set

Defines the command set for all combat-related commands, organized using
the new modular structure. This provides a clean interface for adding
combat commands to characters during combat situations.

This replaces the old monolithic approach with a well-organized, maintainable
structure that follows Python and Evennia best practices.
"""

from evennia import CmdSet

# Import commands from our organized modules
from .core_actions import CmdAttack, CmdStop
from .movement import CmdFlee, CmdRetreat, CmdAdvance, CmdCharge
from .special_actions import CmdGrapple, CmdEscapeGrapple, CmdReleaseGrapple, CmdDisarm, CmdAim
# Note: Removed CmdLook import to avoid overriding default look command


class CombatCmdSet(CmdSet):
    """
    Command set for combat commands.
    
    This cmdset contains all commands related to combat, organized into
    logical groups for better maintainability and understanding.
    """
    
    key = "CombatCmdSet"
    priority = 1  # Higher priority than default commands during combat
    mergetype = "Union"
    no_exits = False  # Allow normal exits during combat
    no_objs = False   # Allow normal object interactions during combat
    
    def at_cmdset_creation(self):
        """
        Populate the cmdset with combat commands.
        """
        # Core combat actions
        self.add(CmdAttack)
        self.add(CmdStop)
        
        # Movement commands
        self.add(CmdFlee)
        self.add(CmdRetreat)
        self.add(CmdAdvance)
        self.add(CmdCharge)
        
        # Special actions
        self.add(CmdGrapple)
        self.add(CmdEscapeGrapple)
        self.add(CmdReleaseGrapple)
        self.add(CmdDisarm)
        self.add(CmdAim)
        
        # Note: CmdLook removed to avoid overriding default look command
