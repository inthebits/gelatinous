"""
Long Description System Commands

Commands for setting and managing detailed character body part descriptions.
"""

from evennia import Command
from evennia.utils.utils import inherits_from
from world.combat.constants import (
    MAX_DESCRIPTION_LENGTH,
    VALID_LONGDESC_LOCATIONS,
    PERM_BUILDER
)


class CmdLongdesc(Command):
    """
    Set or view detailed descriptions for your character's body parts.

    Usage:
        @longdesc <location> "<description>"    - Set description for a body part
        @longdesc <location>                    - View current description for location
        @longdesc                               - List all your current longdescs
        @longdesc/list                          - List all available body locations
        @longdesc/clear <location>              - Remove description for location
        @longdesc/clear                         - Remove all longdescs (with confirmation)

    Staff Usage:
        @longdesc <character> <location> "<description>"  - Set on another character
        @longdesc/clear <character> <location>             - Clear on another character
        @longdesc/clear <character>                        - Clear all on another character

    Examples:
        @longdesc face "weathered features with high cheekbones"
        @longdesc left_eye "a piercing blue eye with flecks of gold"
        @longdesc right_hand "a prosthetic metal hand with intricate engravings"
        @longdesc/clear face
        @longdesc face
        @longdesc/list

    Body locations include: head, face, left_eye, right_eye, left_ear, right_ear,
    neck, chest, back, abdomen, groin, left_arm, right_arm, left_hand, right_hand,
    left_thigh, right_thigh, left_shin, right_shin, left_foot, right_foot.

    Extended anatomy (tails, wings, etc.) is supported for modified characters.
    Descriptions appear when others look at you, integrated with your base description.
    """

    key = "@longdesc"
    aliases = ["@desc"]
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        """Execute the longdesc command."""
        caller = self.caller
        args = self.args.strip()
        switches = self.switches

        # Handle switches
        if "list" in switches:
            self._handle_list_locations(caller)
            return

        if "clear" in switches:
            self._handle_clear(caller, args)
            return

        # Parse arguments for main command
        if not args:
            # Show all current longdescs
            self._show_all_longdescs(caller)
            return

        # Check if this is staff targeting another character
        target_char = None
        remaining_args = args

        if caller.check_permstring(PERM_BUILDER):
            # Staff can target other characters
            parts = args.split(None, 1)
            if len(parts) >= 1:
                potential_target = caller.search(parts[0], global_search=True)
                if potential_target and inherits_from(potential_target, "typeclasses.characters.Character"):
                    target_char = potential_target
                    remaining_args = parts[1] if len(parts) > 1 else ""

        if not target_char:
            target_char = caller
            remaining_args = args

        # Parse location and description
        if '"' in remaining_args:
            # Setting a description
            if remaining_args.count('"') < 2:
                caller.msg("Please enclose the description in quotes.")
                return

            quote_start = remaining_args.find('"')
            quote_end = remaining_args.rfind('"')

            if quote_start == quote_end:
                caller.msg("Please provide both opening and closing quotes.")
                return

            location = remaining_args[:quote_start].strip()
            description = remaining_args[quote_start + 1:quote_end]

            self._set_longdesc(caller, target_char, location, description)

        else:
            # Viewing a specific location
            location = remaining_args.strip()
            if location:
                self._view_longdesc(caller, target_char, location)
            else:
                self._show_all_longdescs(caller, target_char)

    def _handle_list_locations(self, caller):
        """Show all available body locations for the character."""
        locations = caller.get_available_locations()
        if not locations:
            caller.msg("No body locations available.")
            return

        # Group locations by type for better display
        from world.combat.constants import ANATOMICAL_REGIONS

        grouped_locations = {}
        extended_locations = []

        for location in locations:
            found_region = None
            for region_name, region_locations in ANATOMICAL_REGIONS.items():
                if location in region_locations:
                    if region_name not in grouped_locations:
                        grouped_locations[region_name] = []
                    grouped_locations[region_name].append(location)
                    found_region = True
                    break
            
            if not found_region:
                extended_locations.append(location)

        # Display grouped locations
        caller.msg("|wAvailable body locations:|n")
        
        region_display_names = {
            "head_region": "Head Region",
            "torso_region": "Torso Region", 
            "arm_region": "Arm Region",
            "leg_region": "Leg Region"
        }

        for region_name in ["head_region", "torso_region", "arm_region", "leg_region"]:
            if region_name in grouped_locations:
                display_name = region_display_names[region_name]
                locations_list = ", ".join(grouped_locations[region_name])
                caller.msg(f"  |c{display_name}:|n {locations_list}")

        if extended_locations:
            caller.msg(f"  |cExtended Anatomy:|n {', '.join(extended_locations)}")

    def _handle_clear(self, caller, args):
        """Handle clear commands."""
        if not args:
            # Clear all longdescs with confirmation
            self._clear_all_longdescs(caller)
            return

        # Check if targeting another character (staff only)
        target_char = None
        location = args

        if caller.check_permstring(PERM_BUILDER):
            parts = args.split(None, 1)
            if len(parts) >= 1:
                potential_target = caller.search(parts[0], global_search=True)
                if potential_target and inherits_from(potential_target, "typeclasses.characters.Character"):
                    target_char = potential_target
                    location = parts[1] if len(parts) > 1 else ""

        if not target_char:
            target_char = caller
            location = args

        if not location:
            # Clear all for target character
            self._clear_all_longdescs(caller, target_char)
        else:
            # Clear specific location
            self._clear_specific_location(caller, target_char, location)

    def _set_longdesc(self, caller, target_char, location, description):
        """Set a longdesc for a specific location."""
        if not location:
            caller.msg("Please specify a body location.")
            return

        # Validate location exists on character
        if not target_char.has_location(location):
            caller.msg(f"'{location}' is not a valid body location for {target_char.get_display_name(caller)}.")
            available = ", ".join(target_char.get_available_locations()[:10])  # Show first 10
            caller.msg(f"Available locations include: {available}...")
            caller.msg("Use '@longdesc/list' to see all available locations.")
            return

        # Validate description length
        if len(description) > MAX_DESCRIPTION_LENGTH:
            caller.msg(f"Description is too long ({len(description)} characters). Maximum is {MAX_DESCRIPTION_LENGTH} characters.")
            return

        if len(description.strip()) == 0:
            # Empty description means clear
            target_char.set_longdesc(location, None)
            if target_char == caller:
                caller.msg(f"Cleared description for {location}.")
            else:
                caller.msg(f"Cleared description for {location} on {target_char.get_display_name(caller)}.")
            return

        # Set the description
        success = target_char.set_longdesc(location, description.strip())
        if success:
            if target_char == caller:
                caller.msg(f"Set description for {location}: \"{description.strip()}\"")
            else:
                caller.msg(f"Set description for {location} on {target_char.get_display_name(caller)}: \"{description.strip()}\"")
        else:
            caller.msg("Failed to set description. Please try again.")

    def _view_longdesc(self, caller, target_char, location):
        """View a specific longdesc."""
        if not target_char.has_location(location):
            caller.msg(f"'{location}' is not a valid body location.")
            return

        description = target_char.get_longdesc(location)
        if description:
            if target_char == caller:
                caller.msg(f"{location}: \"{description}\"")
            else:
                caller.msg(f"{target_char.get_display_name(caller)}'s {location}: \"{description}\"")
        else:
            if target_char == caller:
                caller.msg(f"No description set for {location}.")
            else:
                caller.msg(f"No description set for {location} on {target_char.get_display_name(caller)}.")

    def _show_all_longdescs(self, caller, target_char=None):
        """Show all current longdescs for a character."""
        if not target_char:
            target_char = caller

        longdescs = target_char.longdesc or {}
        set_descriptions = {loc: desc for loc, desc in longdescs.items() if desc}

        if not set_descriptions:
            if target_char == caller:
                caller.msg("You have no longdesc descriptions set.")
            else:
                caller.msg(f"{target_char.get_display_name(caller)} has no longdesc descriptions set.")
            return

        if target_char == caller:
            caller.msg("|wYour current longdesc descriptions:|n")
        else:
            caller.msg(f"|w{target_char.get_display_name(caller)}'s longdesc descriptions:|n")

        # Show in anatomical order
        from world.combat.constants import ANATOMICAL_DISPLAY_ORDER

        displayed = set()
        for location in ANATOMICAL_DISPLAY_ORDER:
            if location in set_descriptions:
                caller.msg(f"  |c{location}:|n \"{set_descriptions[location]}\"")
                displayed.add(location)

        # Show any extended anatomy
        for location, description in set_descriptions.items():
            if location not in displayed:
                caller.msg(f"  |c{location}:|n \"{description}\"")

    def _clear_specific_location(self, caller, target_char, location):
        """Clear a specific location's longdesc."""
        if not target_char.has_location(location):
            caller.msg(f"'{location}' is not a valid body location.")
            return

        current_desc = target_char.get_longdesc(location)
        if not current_desc:
            if target_char == caller:
                caller.msg(f"No description set for {location}.")
            else:
                caller.msg(f"No description set for {location} on {target_char.get_display_name(caller)}.")
            return

        target_char.set_longdesc(location, None)
        if target_char == caller:
            caller.msg(f"Cleared description for {location}.")
        else:
            caller.msg(f"Cleared description for {location} on {target_char.get_display_name(caller)}.")

    def _clear_all_longdescs(self, caller, target_char=None):
        """Clear all longdescs with confirmation."""
        if not target_char:
            target_char = caller

        longdescs = target_char.longdesc or {}
        set_descriptions = {loc: desc for loc, desc in longdescs.items() if desc}

        if not set_descriptions:
            if target_char == caller:
                caller.msg("You have no longdesc descriptions to clear.")
            else:
                caller.msg(f"{target_char.get_display_name(caller)} has no longdesc descriptions to clear.")
            return

        # Simple confirmation - clear all
        for location in set_descriptions:
            target_char.set_longdesc(location, None)

        count = len(set_descriptions)
        if target_char == caller:
            caller.msg(f"Cleared all {count} longdesc descriptions.")
        else:
            caller.msg(f"Cleared all {count} longdesc descriptions from {target_char.get_display_name(caller)}.")
