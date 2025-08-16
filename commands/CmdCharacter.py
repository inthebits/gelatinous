from evennia import Command
from evennia.utils.search import search_object
from world.combat.constants import (
    PERM_BUILDER, PERM_DEVELOPER,
    BOX_TOP_LEFT, BOX_TOP_RIGHT, BOX_BOTTOM_LEFT, BOX_BOTTOM_RIGHT,
    BOX_HORIZONTAL, BOX_VERTICAL, BOX_TEE_DOWN, BOX_TEE_UP,
    COLOR_SUCCESS, COLOR_NORMAL
)

class CmdStats(Command):
    """
    View your character's stats, or inspect another character if you're a Builder+.

    Usage:
      @stats
      @stats <target>  (Builder or Developer only)

    Displays your G.R.I.M. attributes and any future derived stats.
    """

    key = "@stats"
    aliases = ["score"]
    locks = "cmd:all()"

    def func(self):
        "Implement the command."

        caller = self.caller
        target = caller

        if self.args:
            if (
                self.account.check_permstring(PERM_BUILDER)
                or self.account.check_permstring(PERM_DEVELOPER)
            ):
                matches = search_object(self.args.strip(), exact=False)
                if matches:
                    target = matches[0]

        grit = target.grit
        resonance = target.resonance
        intellect = target.intellect
        motorics = target.motorics
        vitals_display = f"{target.hp}/{target.hp_max}"

        # Fixed format to exactly 48 visible characters per row
        string = f"""{COLOR_SUCCESS}{BOX_TOP_LEFT}{BOX_HORIZONTAL * 48}{BOX_TOP_RIGHT}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} PSYCHOPHYSICAL EVALUATION REPORT               {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} Subject: {target.key[:38]:<38}{BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} File Reference: GEL-MST/PR-221A                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_TEE_DOWN}{BOX_HORIZONTAL * 48}{BOX_TEE_UP}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Grit:       {grit:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Resonance:  {resonance:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Intellect:  {intellect:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Motorics:   {motorics:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Vitals:     {vitals_display[:7]:>7}                    {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_TEE_DOWN}{BOX_HORIZONTAL * 48}{BOX_TEE_UP}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} Notes:                                         {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_BOTTOM_LEFT}{BOX_HORIZONTAL * 48}{BOX_BOTTOM_RIGHT}{COLOR_NORMAL}"""

        caller.msg(string)


class CmdLookPlace(Command):
    """
    Set your default room positioning description.
    
    Usage:
        @look_place <description>
        @look_place me is <description>
        @look_place me are <description>
        @look_place me is "<description>"
        @look_place is <description>
        @look_place are <description>
        @look_place "<description>"
        @look_place clear
    
    Examples:
        @look_place standing here.
        @look_place me is "sitting on a rock"
        @look_place me are "lounging lazily"
        @look_place me is "is lounging lazily"
        @look_place are crouched in the shadows
        @look_place clear
    
    This sets your default positioning that others see when they look at a room.
    Instead of appearing in a separate "Characters:" section, you'll appear naturally
    in the room description as "YourName is <your description>".
    
    Use 'clear' to remove your look_place and return to default display.
    """
    
    key = "@look_place"
    aliases = ["@lookplace"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        caller = self.caller
        
        if not self.args:
            # Show current setting
            current = caller.look_place or "standing here."
            caller.msg(f"Your current look_place: '{current}'")
            return
        
        # Handle 'clear' command
        if self.args.strip().lower() in ('clear', 'none', 'remove'):
            caller.look_place = "standing here."
            caller.msg("Your look_place has been cleared and reset to 'standing here.'")
            return
        
        # Parse the description with smart 'is' handling
        description = self.parse_placement_description(self.args)
        
        if not description:
            caller.msg("Please provide a description for your look_place.")
            return
        
        # Check length limit to prevent abuse while allowing creativity
        if len(description) > 200:
            caller.msg(f"Your look_place description is too long ({len(description)} characters). Please keep it under 200 characters.")
            return
        
        # Ensure description ends with proper punctuation
        if not description.endswith(('.', '!', '?')):
            description += '.'
        
        # Set the look_place
        caller.look_place = description
        caller.msg(f"Your look_place is now: '{description}'")
        caller.msg("Others will see: '|c" + caller.get_display_name(caller) + f"|n is {description}'")
    
    def parse_placement_description(self, raw_input):
        """
        Parse various input formats to extract the placement description.
        
        Handles patterns like:
        - "standing here"
        - "me is standing here"  
        - "me is \"standing here\""
        - "is standing here"
        - "\"standing here\""
        - "me is \"is standing here\""
        
        Args:
            raw_input (str): The raw command arguments
            
        Returns:
            str: The cleaned placement description
        """
        text = raw_input.strip()
        
        # Remove outer quotes if present
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        
        # Handle "me is ..." pattern
        if text.lower().startswith('me is '):
            text = text[6:].strip()  # Remove "me is "
            
            # Remove inner quotes if present after "me is"
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                text = text[1:-1]
        
        # Handle "is ..." pattern (without "me")
        elif text.lower().startswith('is '):
            text = text[3:].strip()  # Remove "is "
        
        # Clean up redundant "is" at the beginning
        # Handle cases like "me is \"is standing here\""
        if text.lower().startswith('is '):
            text = text[3:].strip()
        
        return text.strip()


class CmdTempPlace(Command):
    """
    Set a temporary room positioning description.
    
    Usage:
        @temp_place <description>
        @temp_place me is <description>
        @temp_place me are <description>
        @temp_place me is "<description>"
        @temp_place is <description>
        @temp_place are <description>
        @temp_place "<description>"
        @temp_place clear
    
    Examples:
        @temp_place hiding behind a tree.
        @temp_place me is "examining the wall closely"
        @temp_place me are "investigating something"
        @temp_place me is "is investigating something"
        @temp_place are crouched and ready to spring
        @temp_place clear
    
    This sets a temporary positioning that overrides your @look_place.
    It will be automatically cleared when you move to a different room.
    
    Use 'clear' to remove your temp_place immediately.
    """
    
    key = "@temp_place"
    aliases = ["@tempplace"]
    locks = "cmd:all()"
    help_category = "Character"
    
    def func(self):
        """Execute the command."""
        caller = self.caller
        
        if not self.args:
            # Show current setting
            current = caller.temp_place or ""
            if current:
                caller.msg(f"Your current temp_place: '{current}'")
            else:
                caller.msg("You have no temp_place set.")
            return
        
        # Handle 'clear' command
        if self.args.strip().lower() in ('clear', 'none', 'remove'):
            caller.temp_place = ""
            caller.msg("Your temp_place has been cleared.")
            return
        
        # Parse the description with smart 'is' handling
        description = self.parse_placement_description(self.args)
        
        if not description:
            caller.msg("Please provide a description for your temp_place.")
            return
        
        # Check length limit to prevent abuse while allowing creativity
        if len(description) > 200:
            caller.msg(f"Your temp_place description is too long ({len(description)} characters). Please keep it under 200 characters.")
            return
        
        # Ensure description ends with proper punctuation
        if not description.endswith(('.', '!', '?')):
            description += '.'
            description += '.'
        
        # Set the temp_place
        caller.temp_place = description
        caller.msg(f"Your temp_place is now: '{description}'")
        caller.msg("Others will see: '|c" + caller.get_display_name(caller) + f"|n is {description}'")
        caller.msg("This will be cleared when you move to a different room.")
    
    def parse_placement_description(self, raw_input):
        """
        Parse various input formats to extract the placement description.
        
        Same logic as CmdLookPlace for consistency.
        """
        text = raw_input.strip()
        
        # Remove outer quotes if present
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        
        # Handle "me is ..." pattern
        if text.lower().startswith('me is '):
            text = text[6:].strip()  # Remove "me is "
            
            # Remove inner quotes if present after "me is"
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                text = text[1:-1]
        
        # Handle "is ..." pattern (without "me")
        elif text.lower().startswith('is '):
            text = text[3:].strip()  # Remove "is "
        
        # Clean up redundant "is" at the beginning
        # Handle cases like "me is \"is standing here\""
        if text.lower().startswith('is '):
            text = text[3:].strip()
        
        return text.strip()
