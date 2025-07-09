"""
Debug Aim Command

Simple command to check current aiming state for debugging purposes.
"""

from evennia import Command
from evennia.comms.models import ChannelDB

from world.combat.constants import SPLATTERCAST_CHANNEL


class CmdDebugAim(Command):
    """
    Debug command to check current aiming state.

    Usage:
      debugaim

    Shows current aiming target and direction for debugging.
    """

    key = "debugaim"
    locks = "cmd:all()"
    help_category = "Debug"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)

        aiming_at = getattr(caller.ndb, "aiming_at", None)
        aiming_direction = getattr(caller.ndb, "aiming_direction", None)
        
        caller.msg(f"|yDebug Aim State:|n")
        caller.msg(f"  aiming_at: {aiming_at.key if aiming_at else 'None'}")
        caller.msg(f"  aiming_direction: {aiming_direction if aiming_direction else 'None'}")
        
        splattercast.msg(f"DEBUG_AIM: {caller.key} - aiming_at={aiming_at.key if aiming_at else 'None'}, aiming_direction={aiming_direction if aiming_direction else 'None'}")
