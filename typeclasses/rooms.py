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
    appearance_template = """{header}|c{name}|n
{desc}
{things}
{characters}
{footer}"""

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
    
    def get_display_characters(self, looker, **kwargs):
        """
        Custom character display using placement descriptions.
        
        Uses @override_place, @temp_place, or @look_place attributes to create
        natural language character positioning instead of "Characters:" listing.
        
        Args:
            looker: Character looking at the room
            
        Returns:
            str: Natural language character placement descriptions
        """
        characters = []
        
        for obj in self.contents:
            if obj.is_typeclass("typeclasses.characters.Character") and obj != looker:
                if obj.access(looker, "view"):
                    characters.append(obj)
        
        if not characters:
            return ""
        
        # Group characters by their placement description
        placement_groups = {}
        
        for char in characters:
            # Check placement hierarchy: override_place > temp_place > look_place > fallback
            # Empty strings are treated as not set
            override_place = char.override_place or ""
            temp_place = char.temp_place or ""
            look_place = char.look_place or ""
            
            placement = (override_place if override_place else
                        temp_place if temp_place else
                        look_place if look_place else
                        "standing here.")
            
            if placement not in placement_groups:
                placement_groups[placement] = []
            placement_groups[placement].append(char.get_display_name(looker))
        
        # Generate natural language descriptions
        descriptions = []
        for placement, char_names in placement_groups.items():
            if len(char_names) == 1:
                descriptions.append(f"{char_names[0]} is {placement}")
            elif len(char_names) == 2:
                descriptions.append(f"{char_names[0]} and {char_names[1]} are {placement}")
            else:
                # Handle 3+ characters: "A, B, and C are here"
                all_but_last = ", ".join(char_names[:-1])
                descriptions.append(f"{all_but_last}, and {char_names[-1]} are {placement}")
        
        return " ".join(descriptions) if descriptions else ""
    
    def get_display_things(self, looker, **kwargs):
        """
        Override things display to exclude @integrate objects and use natural language formatting.
        
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
        
        if not things:
            return ""
        
        # Format using natural language similar to character placement
        if len(things) == 1:
            return f"You see a {things[0]}."
        elif len(things) == 2:
            return f"You see a {things[0]} and {things[1]}."
        else:
            # Handle 3+ objects: "You see: A, B, and C"
            all_but_last = ", ".join(things[:-1])
            return f"You see a {all_but_last}, and {things[-1]}."
    
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
    
    def format_appearance(self, appearance, looker, **kwargs):
        """
        Final formatting step for room appearance.
        
        This is called last in the appearance pipeline and allows for final
        adjustments like adding line breaks between sections.
        
        Args:
            appearance (str): The formatted appearance string from the template
            looker: Character looking at the room
            
        Returns:
            str: Final formatted appearance
        """
        # Get the actual template variables directly
        things = self.get_display_things(looker, **kwargs)
        characters = self.get_display_characters(looker, **kwargs)
        desc = self.db.desc or ""
        footer = self.get_display_footer(looker, **kwargs)
        
        result = appearance
        
        # Only modify spacing if we have actual content (items or characters)
        if things or characters:
            # Add spacing between items and characters if both exist
            if things and characters:
                old_pattern = things + '\n' + characters
                new_pattern = things + '\n\n' + characters
                result = result.replace(old_pattern, new_pattern)
            
            # Add spacing between room description and first content section
            first_content = things if things else characters
            old_pattern = desc + '\n' + first_content
            new_pattern = desc + '\n\n' + first_content
            result = result.replace(old_pattern, new_pattern)
        else:
            # For empty rooms, fix excessive line breaks before footer
            if desc and footer and '\n\n\n' in result:
                # Replace triple line breaks with double
                result = result.replace('\n\n\n', '\n\n')
        
        return result
    
    def get_custom_exit_display(self, looker):
        """
        Get smart exit display using natural language based on destination room types.
        
        Returns:
            str: Formatted natural language exit display string
        """
        exits = self.exits
        if not exits:
            return ""
        
        # Group exits by destination type and special properties
        exit_groups = {
            'streets': [],
            'edges': [],
            'gaps': [],
            'custom_types': {},
            'fallback': []
        }
        
        # Analyze each exit
        for exit_obj in exits:
            direction = exit_obj.key
            aliases = exit_obj.aliases.all()
            alias = aliases[0] if aliases else None
            destination = exit_obj.destination
            
            # Check if exit leads to a sky room (skip unless edge/gap)
            destination_is_sky = False
            if destination:
                destination_is_sky = getattr(destination.db, "is_sky_room", False)
            
            if destination_is_sky and not (getattr(exit_obj.db, "is_edge", False) or getattr(exit_obj.db, "is_gap", False)):
                continue  # Skip pure sky rooms
            
            # Check for edge/gap first (highest priority)
            if getattr(exit_obj.db, "is_edge", False):
                exit_groups['edges'].append((direction, alias))
            elif getattr(exit_obj.db, "is_gap", False):
                exit_groups['gaps'].append((direction, alias))
            # Check destination type
            elif destination and hasattr(destination.db, 'type') and destination.db.type:
                dest_type = destination.db.type
                if dest_type == 'street':
                    exit_groups['streets'].append((direction, alias))
                else:
                    if dest_type not in exit_groups['custom_types']:
                        exit_groups['custom_types'][dest_type] = []
                    exit_groups['custom_types'][dest_type].append((direction, alias))
            else:
                # Fallback for exits without type information
                exit_groups['fallback'].append((direction, alias))
        
        # Generate natural language descriptions
        return self.format_exit_groups(exit_groups)
    
    def format_exit_groups(self, exit_groups):
        """
        Format grouped exits into natural language descriptions.
        
        Args:
            exit_groups (dict): Dictionary of grouped exits by type
            
        Returns:
            str: Formatted natural language exit descriptions
        """
        descriptions = []
        
        # Format streets (grouped)
        if exit_groups['streets']:
            street_dirs = [self.format_direction_with_alias(direction, alias) 
                          for direction, alias in exit_groups['streets']]
            if len(street_dirs) == 1:
                descriptions.append(f"The street continues {street_dirs[0]}")
            else:
                street_desc = self.format_direction_list(street_dirs)
                descriptions.append(f"The street continues {street_desc}")
        
        # Format custom types (grouped by type)
        for dest_type, exits in exit_groups['custom_types'].items():
            type_dirs = [self.format_direction_with_alias(direction, alias) 
                        for direction, alias in exits]
            if len(type_dirs) == 1:
                descriptions.append(f"There is a {dest_type} to the {type_dirs[0]}")
            else:
                type_desc = self.format_direction_list(type_dirs)
                descriptions.append(f"There are {dest_type}s to the {type_desc}")
        
        # Format edges (grouped)
        if exit_groups['edges']:
            edge_dirs = [self.format_direction_with_alias(direction, alias) 
                        for direction, alias in exit_groups['edges']]
            if len(edge_dirs) == 1:
                descriptions.append(f"There is an edge to the {edge_dirs[0]}")
            else:
                edge_desc = self.format_direction_list(edge_dirs)
                descriptions.append(f"There are edges to the {edge_desc}")
        
        # Format gaps (grouped)
        if exit_groups['gaps']:
            gap_dirs = [self.format_direction_with_alias(direction, alias) 
                       for direction, alias in exit_groups['gaps']]
            if len(gap_dirs) == 1:
                descriptions.append(f"There is a gap to the {gap_dirs[0]}")
            else:
                gap_desc = self.format_direction_list(gap_dirs)
                descriptions.append(f"There are gaps to the {gap_desc}")
        
        # Format fallback exits
        if exit_groups['fallback']:
            fallback_dirs = [self.format_direction_with_alias(direction, alias) 
                           for direction, alias in exit_groups['fallback']]
            if len(fallback_dirs) == 1:
                descriptions.append(f"There is an exit to the {fallback_dirs[0]}")
            else:
                fallback_desc = self.format_direction_list(fallback_dirs)
                descriptions.append(f"There are exits to the {fallback_desc}")
        
        return " ".join(descriptions) if descriptions else ""
    
    def format_direction_with_alias(self, direction, alias):
        """
        Format a direction with its alias in parentheses if available.
        
        Args:
            direction (str): The direction name
            alias (str): The alias, if any
            
        Returns:
            str: Formatted direction string
        """
        if alias and alias != direction:
            return f"{direction} ({alias})"
        return direction
    
    def format_direction_list(self, directions):
        """
        Format a list of directions using natural language conjunctions.
        
        Args:
            directions (list): List of formatted direction strings
            
        Returns:
            str: Natural language list of directions
        """
        if len(directions) == 1:
            return directions[0]
        elif len(directions) == 2:
            return f"{directions[0]} and {directions[1]}"
        else:
            # Handle 3+ directions: "north, south, and east"
            all_but_last = ", ".join(directions[:-1])
            return f"{all_but_last}, and {directions[-1]}"
