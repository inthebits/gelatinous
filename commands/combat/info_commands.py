"""
Info Combat Commands Module

Contains commands that provide information during combat:
- CmdLook: Enhanced look command with combat-specific behavior and direction aiming support

These commands help players understand the current combat situation
and make informed tactical decisions.
"""

from evennia import default_cmds
from evennia.comms.models import ChannelDB

from world.combat.constants import SPLATTERCAST_CHANNEL


class CmdLook(default_cmds.CmdLook):
    """
    Look around, with enhanced combat information and direction aiming support.

    Usage:
      look
      look <target>

    When used during combat, provides additional information about
    proximity, grappling status, and aiming states.
    
    When aiming in a direction and no target is specified, look will
    show the room you're aiming at instead of your current room.
    """

    key = "look"
    aliases = ["l"]
    locks = "cmd:all()"
    priority = 101  # Higher than default commands to ensure this overrides Evennia's look

    def func(self):
        """
        Handle the looking with combat enhancements and direction aiming support.
        
        If the caller is aiming in a direction and no arguments are provided,
        look in the aimed direction instead of the current room.
        """
        caller = self.caller
        args = self.args.strip()
        
        # Debug: Log that our custom look command is being called
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"CUSTOM_LOOK: {caller.key} using enhanced look command with args='{args}'")
        
        # Check if caller is aiming in a direction and no specific target was given
        aiming_direction = getattr(caller.ndb, "aiming_direction", None)
        splattercast.msg(f"CUSTOM_LOOK: {caller.key} aiming_direction={aiming_direction}")
        
        if not args and aiming_direction:
            # Player typed 'look' while aiming in a direction - show the aimed room
            current_location = caller.location
            target_room = None
            
            splattercast.msg(f"CUSTOM_LOOK: Looking for exit matching '{aiming_direction}' in {current_location.key}")
            splattercast.msg(f"CUSTOM_LOOK: Total exits in room: {len(current_location.exits)}")
            
            # Find the exit that matches the aiming direction
            for i, ex in enumerate(current_location.exits):
                splattercast.msg(f"CUSTOM_LOOK: Exit {i}: key='{ex.key}', type={type(ex)}")
                
                exit_aliases = getattr(ex, 'aliases', [])
                splattercast.msg(f"CUSTOM_LOOK: Exit {i} aliases raw: {exit_aliases}, type: {type(exit_aliases)}")
                
                # Handle both list and manager cases
                if hasattr(exit_aliases, 'all'):
                    exit_aliases = [alias.lower() for alias in exit_aliases.all()]
                    splattercast.msg(f"CUSTOM_LOOK: Exit {i} aliases after .all(): {exit_aliases}")
                else:
                    exit_aliases = [alias.lower() for alias in exit_aliases]
                    splattercast.msg(f"CUSTOM_LOOK: Exit {i} aliases as list: {exit_aliases}")
                
                splattercast.msg(f"CUSTOM_LOOK: Checking exit {ex.key} (aliases: {exit_aliases}) vs direction '{aiming_direction}'")
                
                # Check key match
                key_matches = ex.key.lower() == aiming_direction.lower()
                alias_matches = aiming_direction.lower() in exit_aliases
                splattercast.msg(f"CUSTOM_LOOK: Key matches: {key_matches}, Alias matches: {alias_matches}")
                
                if key_matches or alias_matches:
                    target_room = ex.destination
                    splattercast.msg(f"CUSTOM_LOOK: Found matching exit! Target room: {target_room.key if target_room else 'None'}")
                    break
            
            splattercast.msg(f"CUSTOM_LOOK: Final target_room = {target_room.key if target_room else 'None'}")
            
            if target_room:
                # Show the target room with a special header
                caller.msg(f"|y[ Aiming {aiming_direction} into: {target_room.get_display_name(caller)} ]|n")
                # Use the target room's at_look method to get the proper description
                look_string = target_room.return_appearance(caller)
                caller.msg(look_string)
                caller.msg(f"|y[ You are currently aiming {aiming_direction} from {current_location.get_display_name(caller)} ]|n")
                return
            else:
                # This shouldn't happen if aiming was set properly, but handle gracefully
                caller.msg(f"|rError: You are aiming {aiming_direction} but can't see in that direction.|n")
                # Fall through to normal look behavior
        
        # Default look behavior for all other cases, with potential combat enhancements
        super().func()
        
        # TODO: Add combat-specific information here:
        # - Who is in proximity with whom
        # - Who is grappling/being grappled  
        # - Who is aiming at what/where
        # - Combat handler status
