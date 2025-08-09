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
    
    # Override the appearance template to use our custom footer for exits only
    # This avoids duplicate display issues with exits while letting Evennia handle characters/objects
    # See: https://www.evennia.com/docs/latest/Components/Objects.html#changing-an-objects-appearance
    appearance_template = """
{header}
|c{name}|n
{desc}
{characters}
{things}
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
        Get custom footer display for exits with edge/gap categorization.
        Let Evennia handle characters and objects via {characters} and {things} template variables.
        
        Returns:
            str: Formatted footer display string
        """
        lines = []
        
        # Only handle custom exit categorization in footer
        exit_display = self.get_custom_exit_display(looker)
        if exit_display:
            lines.append(exit_display)
        
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
        
        # Categorize exits
        for exit_obj in exits:
            is_edge = getattr(exit_obj.db, "is_edge", False)
            is_gap = getattr(exit_obj.db, "is_gap", False)
            
            if is_edge or is_gap:
                # Mark gaps for special display
                if is_gap:
                    edge_exits.append(exit_obj.key)
                else:
                    edge_exits.append(exit_obj.key)
            else:
                regular_exits.append(exit_obj.key)
        
        # Build display
        lines = []
        
        if regular_exits:
            lines.append(f"Exits: {', '.join(regular_exits)}")
        
        if edge_exits:
            lines.append(f"Edges: {', '.join(edge_exits)}")
        
        if not regular_exits and not edge_exits:
            return ""
        
        return "\n".join(lines)
