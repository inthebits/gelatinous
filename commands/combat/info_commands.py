"""
Info Combat Commands Module

Contains commands that provide information during combat:
- CmdLook: Enhanced look command with combat-specific behavior

These commands help players understand the current combat situation
and make informed tactical decisions.
"""

from evennia import Command
from evennia.comms.models import ChannelDB

from world.combat.constants import SPLATTERCAST_CHANNEL


class CmdLook(Command):
    """
    Look around, with enhanced combat information.

    Usage:
      look
      look <target>

    When used during combat, provides additional information about
    proximity, grappling status, and aiming states.
    """

    key = "look"
    aliases = ["l"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        
        # Enhanced look logic would continue here...
        # This would include combat-specific information like:
        # - Who is in proximity with whom
        # - Who is grappling/being grappled
        # - Who is aiming at what/where
        # - Combat handler status
        
        # For now, just call the parent look command
        # In a full implementation, this would be enhanced
        caller.msg("Enhanced combat look functionality would be implemented here.")
