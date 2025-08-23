"""
Spray Commands

Unified spray command that handles both spray painting and solvent cleaning
based on the type of can used and syntax provided.
"""

from evennia import Command, create_object
from typeclasses.items import SprayCanItem, SolventCanItem
from typeclasses.objects import GraffitiObject
import random


class CmdGraffiti(Command):
    """
    Spray paint graffiti or clean with solvent.
    
    Usage:
        spray "<message>" with <spray_can>    - Spray paint graffiti
        spray here with <solvent_can>         - Clean graffiti in room
        
    Examples:
        spray "HELLO WORLD" with red_can
        spray "WAKKA WAKKA!" with spray_can
        spray here with solvent_can
        
    Paint cans have finite paint - if you run out mid-message, your graffiti
    will be cut short. Messages are limited to 100 characters.
    
    Solvent cans can clean existing graffiti from the current room, removing
    random characters from graffiti messages. Multiple applications may be
    needed to completely clean walls.
    
    To change spray can colors, use: press <color> on <spray_can>
    """
    
    key = "spray"
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the spray command."""
        if not self.args:
            self.caller.msg("Usage: spray \"<message>\" with <spray_can> OR spray here with <solvent_can>")
            return
        
        # Parse command patterns
        args_lower = self.args.lower()
        
        if args_lower.startswith("here with "):
            self._handle_clean(self.args[10:].strip())
        elif " with " in self.args:
            self._handle_spray_paint(self.args)
        else:
            self.caller.msg("Usage: spray \"<message>\" with <spray_can> OR spray here with <solvent_can>")
    
    def _handle_spray_paint(self, args):
        """Handle spray painting graffiti."""
        if " with " not in args:
            self.caller.msg("Usage: spray \"<message>\" with <spray_can>")
            return
        
        # Split message and can name
        message_part, can_part = args.rsplit(" with ", 1)
        message = message_part.strip().strip('"\'')  # Remove quotes if present
        can_name = can_part.strip()
        
        if not message:
            self.caller.msg("You need to specify a message to spray.")
            return
        
        if len(message) > 100:
            self.caller.msg("Your message is too long! Keep it under 100 characters.")
            return
        
        # Find the spray can
        spray_can = self.caller.search(can_name, candidates=self.caller.contents, quiet=True)
        if not spray_can:
            self.caller.msg(f"You don't have a '{can_name}'.")
            return
        
        spray_can = spray_can[0]  # Get first match
        
        # Verify it's a spray can
        if not isinstance(spray_can, SprayCanItem):
            self.caller.msg(f"You can't spray paint with {spray_can.name}.")
            return
        
        # Check if spray can has paint
        if spray_can.db.aerosol_level <= 0:
            self.caller.msg(f"{spray_can.name} is empty!")
            return
        
        # Calculate paint needed (1 paint per character)
        paint_needed = len(message)
        paint_available = spray_can.db.aerosol_level
        
        # Determine actual message length based on available paint
        if paint_needed > paint_available:
            message = message[:paint_available]
            paint_used = paint_available
            self.caller.msg(f"{spray_can.name} runs out of paint mid-message!")
        else:
            paint_used = paint_needed
        
        # Use the paint
        spray_can.use_paint(paint_used)
        
        # Get the current color
        current_color = spray_can.db.current_color
        
        # Find or create the room's graffiti object
        graffiti_obj = None
        for obj in self.caller.location.contents:
            if isinstance(obj, GraffitiObject):
                graffiti_obj = obj
                break
        
        if not graffiti_obj:
            # Create new graffiti object for this room
            graffiti_obj = create_object(
                typeclass=GraffitiObject,
                key="graffiti",
                location=self.caller.location
            )
        
        # Add the graffiti message to the object
        graffiti_obj.add_graffiti(message, current_color, self.caller)
        
        # Messages - using proper Evennia color formatting
        color_map = {
            'red': 'r', 'blue': 'b', 'green': 'g', 'yellow': 'y',
            'magenta': 'm', 'cyan': 'c', 'white': 'w', 'black': 'x',
            'purple': 'm', 'pink': 'm', 'orange': 'y'
        }
        color_code = color_map.get(current_color.lower(), 'w')
        colored_message = f"|{color_code}{message}|n"
        self.caller.msg(f"You spray '{colored_message}' on the wall with {spray_can.name}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} sprays '{colored_message}' on the wall.",
            exclude=self.caller
        )
    
    def _handle_clean(self, can_name):
        """Handle cleaning graffiti with solvent."""
        if not can_name:
            self.caller.msg("Usage: spray here with <solvent_can>")
            return
        
        # Find the solvent can
        solvent_can = self.caller.search(can_name, candidates=self.caller.contents, quiet=True)
        if not solvent_can:
            self.caller.msg(f"You don't have a '{can_name}'.")
            return
        
        solvent_can = solvent_can[0]  # Get first match
        
        # Verify it's a solvent can
        if not isinstance(solvent_can, SolventCanItem):
            self.caller.msg(f"You can't clean with {solvent_can.name}.")
            return
        
        # Check if solvent can has uses left
        if solvent_can.db.aerosol_level <= 0:
            self.caller.msg(f"{solvent_can.name} is empty!")
            return
        
        # Find the room's graffiti object
        graffiti_obj = None
        for obj in self.caller.location.contents:
            if isinstance(obj, GraffitiObject):
                graffiti_obj = obj
                break
        
        if not graffiti_obj or not graffiti_obj.has_graffiti():
            self.caller.msg("There's no graffiti here to clean.")
            return
        
        # Use solvent to remove random characters from graffiti
        solvent_used = min(10, solvent_can.db.aerosol_level)  # Use up to 10 units of solvent
        chars_removed = graffiti_obj.remove_random_characters(solvent_used)
        
        # Use solvent
        solvent_can.use_solvent(solvent_used)
        
        # Messages
        if chars_removed > 0:
            self.caller.msg(f"You scrub away some graffiti with {solvent_can.name}, removing {chars_removed} characters.")
            self.caller.location.msg_contents(
                f"{self.caller.name} scrubs graffiti from the wall with solvent.",
                exclude=self.caller
            )
        else:
            self.caller.msg(f"You scrub at the wall with {solvent_can.name}, but there's nothing left to clean.")
            self.caller.location.msg_contents(
                f"{self.caller.name} scrubs at the wall with solvent.",
                exclude=self.caller
            )


class CmdPress(Command):
    """
    Press colored buttons on spray cans to change colors.
    
    Usage:
        press <color> on <spray_can>
        
    Examples:
        press blue on spray_can
        press red on my_can
        press cyan on paint_can
        
    Changes the color of paint that comes out of the spray can.
    Available colors depend on the specific spray can.
    """
    
    key = "press"
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the press command."""
        if not self.args:
            self.caller.msg("Usage: press <color> on <spray_can>")
            return
        
        if " on " not in self.args:
            self.caller.msg("Usage: press <color> on <spray_can>")
            return
        
        # Split color and can name
        color_part, can_part = self.args.rsplit(" on ", 1)
        new_color = color_part.strip().lower()
        can_name = can_part.strip()
        
        # Validate color name
        if not new_color:
            self.caller.msg("You need to specify a color to press.")
            return
        
        # Find the spray can
        spray_can = self.caller.search(can_name, candidates=self.caller.contents, quiet=True)
        if not spray_can:
            self.caller.msg(f"You don't have a '{can_name}'.")
            return
        
        spray_can = spray_can[0]  # Get first match
        
        # Verify it's a spray can
        if not isinstance(spray_can, SprayCanItem):
            self.caller.msg(f"You can't press colors on {spray_can.name}.")
            return
        
        # Check if color is available
        if not spray_can.set_color(new_color):
            available_colors = spray_can.db.available_colors
            
            # Color mapping for display
            color_map = {
                'red': 'r', 'blue': 'b', 'green': 'g', 'yellow': 'y',
                'magenta': 'm', 'cyan': 'c', 'white': 'w', 'black': 'x'
            }
            
            # Create colored version of each color name
            colored_names = []
            for color in available_colors:
                color_code = color_map.get(color.lower(), 'w')
                colored_names.append(f"|{color_code}{color}|n")
            
            # Format with proper grammar
            if len(colored_names) > 1:
                color_list = ", ".join(colored_names[:-1]) + f", and {colored_names[-1]}"
            else:
                color_list = colored_names[0] if colored_names else "none"
            
            self.caller.msg(f"Available colors: {color_list}.")
            return
        
        # Messages - color was successfully changed by set_color()
        color_map = {
            'red': 'r', 'blue': 'b', 'green': 'g', 'yellow': 'y',
            'magenta': 'm', 'cyan': 'c', 'white': 'w', 'black': 'x',
            'purple': 'm', 'pink': 'm', 'orange': 'y'
        }
        color_code = color_map.get(new_color.lower(), 'w')
        colored_name = f"|{color_code}{new_color}|n"
        
        self.caller.msg(f"You press the {colored_name} button on {spray_can.name}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} presses a button on their spray can.",
            exclude=self.caller
        )
