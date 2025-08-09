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
        and usually displays things like exits, inventory, etc. 
        
        We override this to customize exit display for edges and gaps.
        """
        # Get the standard footer from parent (typically shows exits, contents, etc.)
        footer = super().get_display_footer(looker, **kwargs)
        
        # Replace the standard exit display with our custom one
        custom_exits = self.get_custom_exit_display(looker)
        
        if custom_exits:
            # Remove any existing "Exits:" line from the footer and replace it
            footer_lines = footer.split('\n') if footer else []
            filtered_lines = []
            
            for line in footer_lines:
                # Skip any line that starts with "Exits:" or "Exit:" 
                if not (line.strip().startswith("Exits:") or line.strip().startswith("Exit:")):
                    filtered_lines.append(line)
            
            # Add our custom exit display
            filtered_lines.append(custom_exits)
            footer = '\n'.join(filtered_lines)
        
        return footer
    
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
