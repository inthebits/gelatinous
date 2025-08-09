"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom
from world.combat.constants import NDB_FLYING_OBJECTS

from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """
    
    # Override the appearance template to use our custom footer only
    # This avoids duplicate display issues with the default template variables
    # See: https://www.evennia.com/docs/latest/Components/Objects.html#changing-an-objects-appearance
    appearance_template = """
{header}
|c{name}|n
{desc}
{footer}
"""

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Enhanced to show flying objects during throw mechanics.
        """
        # Get the base description from the parent class
        appearance = super().return_appearance(looker, **kwargs)
        
        # Add flying objects if any exist
        flying_objects = getattr(self.ndb, NDB_FLYING_OBJECTS, [])
        if flying_objects:
            flying_desc = []
            for obj in flying_objects:
                flying_desc.append(f"|y{obj.key} is flying through the air|n")
            
            if flying_desc:
                # Add flying objects section to room description
                appearance += "\n\n" + "\n".join(flying_desc)
        
        return appearance
    
    def get_display_footer(self, looker, **kwargs):
        """
        Get the 'footer' of the object description. This is called by return_appearance
        and displays exits, characters, and objects with custom formatting.
        """
        lines = []
        
        # Add our custom exit display
        custom_exits = self.get_custom_exit_display(looker)
        if custom_exits:
            lines.append(custom_exits)
        
        # Add characters in the room (excluding the looker themselves)
        things = self.contents
        
        # Debug: Let's see what's in the room
        try:
            from evennia.comms.models import ChannelDB
            from evennia import utils
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            if splattercast:
                all_things = [f"{thing.key}(is_character:{utils.inherits_from(thing, 'evennia.objects.objects.DefaultCharacter')})" for thing in things]
                splattercast.msg(f"ROOM_DEBUG: All contents: {all_things}")
                splattercast.msg(f"ROOM_DEBUG: Looker: {looker.key}")
        except:
            pass
        
        # Use proper character detection via inherits_from DefaultCharacter
        from evennia import utils
        characters = [thing for thing in things 
                     if utils.inherits_from(thing, 'evennia.objects.objects.DefaultCharacter') and thing != looker]
        if characters:
            char_names = [char.get_display_name(looker) for char in characters]
            lines.append(f"Characters: {', '.join(char_names)}")
        
        # Add objects in the room (excluding characters and exits)
        objects = [thing for thing in things 
                  if not utils.inherits_from(thing, 'evennia.objects.objects.DefaultCharacter') and not hasattr(thing, 'destination')]
        
        # Debug: Let's see what objects we found
        try:
            if splattercast:
                obj_debug = [f"{thing.key}(has_destination:{hasattr(thing, 'destination')})" for thing in things 
                           if not utils.inherits_from(thing, 'evennia.objects.objects.DefaultCharacter')]
                splattercast.msg(f"ROOM_DEBUG: Non-character objects: {obj_debug}")
                splattercast.msg(f"ROOM_DEBUG: Final objects list: {[obj.key for obj in objects]}")
        except:
            pass
        
        if objects:
            obj_names = [obj.get_display_name(looker) for obj in objects]
            lines.append(f"You see: {', '.join(obj_names)}")
        
        return '\n'.join(lines) if lines else ""
    
    def get_custom_exit_display(self, looker):
        """
        Get custom exit display that separates edges, gaps, and regular exits.
        
        Returns:
            str: Formatted exit display string
        """
        exits = self.exits
        if not exits:
            return ""
        
        regular_exits = []
        edge_exits = []
        gap_exits = []
        
        # Categorize exits
        for exit_obj in exits:
            is_edge = getattr(exit_obj.db, "is_edge", False)
            is_gap = getattr(exit_obj.db, "is_gap", False)
            
            if is_edge and is_gap:
                gap_exits.append(f"{exit_obj.key} (edge gap)")
            elif is_edge:
                edge_exits.append(f"{exit_obj.key} (edge)")
            elif is_gap:
                gap_exits.append(f"{exit_obj.key} (gap)")
            else:
                regular_exits.append(exit_obj.key)
        
        # Build display
        lines = []
        
        if regular_exits:
            lines.append(f"Exits: {', '.join(regular_exits)}")
        
        if edge_exits:
            lines.append(f"|yEdges|n: {', '.join(edge_exits)} |c(use 'jump off <direction> edge')|n")
        
        if gap_exits:
            lines.append(f"|rGaps|n: {', '.join(gap_exits)} |c(use 'jump across <direction> edge')|n")
        
        if not regular_exits and not edge_exits and not gap_exits:
            return ""
        
        return "\n".join(lines)
