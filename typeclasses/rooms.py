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
    
    # Override the appearance template to use our custom footer for exits
    # and custom things display to handle @integrate objects
    # This avoids duplicate display issues with exits while letting Evennia handle characters
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

        Enhanced to show flying objects during throw mechanics and 
        integrate @integrate objects into the room description.
        """
        # Get the base description from the parent class
        appearance = super().return_appearance(looker, **kwargs)
        
        # Process @integrate objects and flying objects - append to room description
        integrated_content = self.get_integrated_objects_content(looker)
        if integrated_content:
            # Simple approach: find room description and append integrated content
            lines = appearance.split('\n')
            room_name_found = False
            
            for i, line in enumerate(lines):
                # Skip until we find the room name
                if not room_name_found and line.startswith('|c') and line.endswith('|n'):
                    room_name_found = True
                    continue
                
                # After room name, find first non-empty line (room description) and append
                if room_name_found and line.strip() and not line.startswith('Characters:') and not line.startswith('You see:') and not line.startswith('Exits:'):
                    lines[i] += f" {integrated_content}"
                    break
            
            appearance = '\n'.join(lines)
        
        return appearance
    
    def get_integrated_objects_content(self, looker):
        """
        Get content from all @integrate objects in this room.
        
        Objects with @integrate = True contribute to the room description
        instead of appearing in the traditional object list.
        
        Flying objects are automatically integrated regardless of @integrate status.
        
        Args:
            looker: Character looking at the room
            
        Returns:
            str: Combined integrated content from all @integrate objects and flying objects
        """
        # Find all @integrate objects in this room
        integrated_objects = []
        
        # Get flying objects list managed by CmdThrow
        flying_objects = getattr(self.ndb, NDB_FLYING_OBJECTS, [])
        if flying_objects is None:
            flying_objects = []
        
        # Add all flying objects first (they get highest priority)
        for obj in flying_objects:
            priority = 1  # High priority for flying objects
            integrated_objects.append((priority, obj, True))
        
        for obj in self.contents:
            # Only check items for integration (can expand to vehicles, etc. later)
            if not obj.is_typeclass("typeclasses.items.Item"):
                continue
            
            # Skip if already added as flying object
            if obj in flying_objects:
                continue
            
            # Check if item should be integrated
            is_integrate = getattr(obj.db, "integrate", False)
            
            if is_integrate:
                # Regular @integrate objects use their configured priority
                priority = getattr(obj.db, "integration_priority", 5)
                integrated_objects.append((priority, obj, False))
        
        if not integrated_objects:
            return ""
        
        # Sort by priority (lower number = appears first)
        integrated_objects.sort(key=lambda x: x[0])
        
        # Collect integration content
        content_parts = []
        for priority, obj, is_flying in integrated_objects:
            if is_flying:
                # Use flying-specific description with teal item name
                content = f"A |c{obj.key}|n is flying through the air."
            else:
                # Use regular integration content
                content = self.get_object_integration_content(obj, looker)
            
            if content:
                content_parts.append(content)
        
        # Join all integration content
        if content_parts:
            return " ".join(content_parts)
        
        return ""
    
    def get_object_integration_content(self, obj, looker):
        """
        Get the integration content for a specific object.
        
        Uses sensory contributions as primary content source.
        Later this will be enhanced to check character sensory abilities.
        
        Args:
            obj: The object to get integration content for
            looker: Character looking at the room
            
        Returns:
            str: Integration content for this object
        """
        # Check for sensory contributions (primary content source)
        sensory_contributions = getattr(obj.db, "sensory_contributions", {})
        
        if sensory_contributions:
            # Collect available sensory content
            # For now, use all available senses - later we'll filter by character abilities
            content_parts = []
            
            # Standard sensory order: visual, auditory, olfactory, tactile, etc.
            sensory_order = ["visual", "auditory", "olfactory", "tactile", "gustatory"]
            
            for sense in sensory_order:
                if sense in sensory_contributions:
                    content_parts.append(sensory_contributions[sense])
            
            # Add any other sensory contributions not in standard order
            for sense, content in sensory_contributions.items():
                if sense not in sensory_order:
                    content_parts.append(content)
            
            if content_parts:
                return " ".join(content_parts)
        
        # Fall back to basic integration description if no sensory data
        integration_desc = getattr(obj.db, "integration_desc", "")
        if integration_desc:
            return integration_desc
        
        # Last resort: use the object's short_desc or key
        return getattr(obj.db, "integration_fallback", f"{obj.key} is here")
    
    def get_display_things(self, looker, **kwargs):
        """
        Override things display to exclude @integrate objects.
        
        @integrate objects are woven into the room description and
        should not appear in the traditional object listing.
        """
        things = []
        
        for obj in self.contents:
            # Skip characters (handled by get_display_characters)
            if obj.is_typeclass("typeclasses.characters.Character"):
                continue
            
            # Skip exits (handled by get_display_footer)
            if obj.is_typeclass("typeclasses.exits.Exit"):
                continue
            
            # Skip @integrate items - they're handled in room description
            if obj.is_typeclass("typeclasses.items.Item") and getattr(obj.db, "integrate", False):
                continue
            
            # Skip objects the looker can't see
            if not obj.access(looker, "view"):
                continue
            
            things.append(obj.get_display_name(looker))
        
        if things:
            return f"|wYou see:|n {', '.join(things)}"
        
        return ""
    
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
            
            # Check if exit leads to a sky room
            destination = exit_obj.destination
            destination_is_sky = False
            if destination:
                destination_is_sky = getattr(destination.db, "is_sky_room", False)
            
            # Filter out exits to sky rooms unless they're also edges/gaps
            if destination_is_sky and not (is_edge or is_gap):
                # Skip this exit - pure sky rooms are hidden from display
                continue
            
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
            lines.append(f"|wExits:|n {', '.join(regular_exits)}")
        
        if edge_exits:
            lines.append(f"|wEdges:|n {', '.join(edge_exits)}")
        
        if not regular_exits and not edge_exits:
            return ""
        
        return "\n".join(lines)
