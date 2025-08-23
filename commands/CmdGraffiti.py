"""
Spray Commands

Unified spray command that         # Parse command patterns to determine intent
        args_stripped = self.args.strip()
        args_lower = args_stripped.lower()
        
        if args_lower.startswith("here with "):
            # User wants to clean - get the can name
            can_name = args_stripped[10:].strip()
            intent = "clean"
            message = None
        elif " with " in args_stripped:
            # User wants to spray paint - parse message and can name
            message_part, can_part = args_stripped.rsplit(" with ", 1)
            message = message_part.strip().strip('"'')  # Remove quotes if present
            can_name = can_part.strip()
            intent = "spraypaint"
        else:
            self.caller.msg("Usage: spray "<message>" with <can> OR spray here with <can>")
            return painting and solvent cleaning
based on the type of can used and syntax provided.
"""

from evennia import Command, create_object
from evennia.utils import delay
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
            self.caller.msg("Usage: spray \"<message>\" with <can> OR spray here with <can>")
            return
        
        # Parse command patterns to determine intent
        args_stripped = self.args.strip()
        args_lower = args_stripped.lower()
        
        if args_lower.startswith("here with "):
            # User wants to clean - get the can name
            can_name = args_stripped[10:].strip()
            intent = "clean"
            message = None
        elif " with " in args_stripped:
            # User wants to spray paint - parse message and can name
            message_part, can_part = args_stripped.rsplit(" with ", 1)
            message = message_part.strip().strip('"\'')  # Remove quotes if present
            can_name = can_part.strip()
            intent = "spraypaint"
        else:
            self.caller.msg("Usage: spray \"<message>\" with <can> OR spray here with <can>")
            return
        
        # Find the can object - search inventory and wielded items using standard search
        # First try inventory
        inventory_candidates = list(self.caller.contents)
        can = None
        if inventory_candidates:
            can = self.caller.search(can_name, candidates=inventory_candidates, quiet=True)
        
        # If not found in inventory, try wielded items (Mr. Hands system)
        if not can and hasattr(self.caller, 'hands'):
            hands = self.caller.hands
            held_items = [item for item in hands.values() if item]
            if held_items:
                can = self.caller.search(can_name, candidates=held_items, quiet=True)
        
        if not can:
            self.caller.msg(f"You don't have a '{can_name}'.")
            return
        
        can = can[0]  # Get first match
        
        # Check what type of aerosol contents the can has
        aerosol_contents = getattr(can.db, 'aerosol_contents', None)
        if not aerosol_contents:
            self.caller.msg(f"You can't use {can.name} for spraying.")
            return
        
        # Route to appropriate handler based on can contents AND user intent
        if aerosol_contents == "spraypaint":
            if intent == "spraypaint":
                self._handle_spray_paint_with_spraypaint(can, message)
            else:  # intent == "clean"
                self.caller.msg(f"You can't clean with {can.name} - it contains paint, not solvent.")
        elif aerosol_contents == "solvent":
            if intent == "clean":
                self._handle_clean_with_solvent(can)
            else:  # intent == "spraypaint"
                self.caller.msg(f"You can't spray paint with {can.name} - it contains solvent, not paint.")
        else:
            self.caller.msg(f"You can't use {can.name} for spraying - unknown contents: {aerosol_contents}.")
    
    def _handle_spray_paint_with_spraypaint(self, spray_can, message):
        """Handle spray painting with a spray paint can."""
        if not message:
            self.caller.msg("You need to specify a message to spray.")
            return
        
        if len(message) > 100:
            self.caller.msg("Your message is too long! Keep it under 100 characters.")
            return
        
        # Check if spray can has paint
        if spray_can.db.aerosol_level <= 0:
            self.caller.msg(f"{spray_can.name} is empty!")
            return
        
        # Calculate paint needed (1 paint per character)
        paint_needed = len(message)
        paint_available = spray_can.db.aerosol_level
        
        # Determine actual message length based on available paint
        ran_out_mid_message = False
        if paint_needed > paint_available:
            message = message[:paint_available] + "..."  # Add ellipsis to show it was cut off
            paint_used = paint_available
            ran_out_mid_message = True
        else:
            paint_used = paint_needed
        
        # Get the current color and name before using paint (in case can gets deleted)
        current_color = spray_can.db.current_color or "white"  # Default fallback
        can_name_for_message = spray_can.name
        
        # Use the paint
        spray_can.use_paint(paint_used)
        
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
        color_code = color_map.get(current_color.lower() if current_color else 'white', 'w')
        colored_message = f"|{color_code}{message}|n"
        
        # Create appropriate message based on whether can ran out
        if ran_out_mid_message:
            self.caller.msg(f"You start to spray on the wall with {can_name_for_message}, but it runs out of paint mid-message! You manage to spray '{colored_message}' before the can crumples up and becomes useless.")
            self.caller.location.msg_contents(
                f"{self.caller.name} starts to spray on the wall, but their can runs out of paint mid-message, managing only '{colored_message}' before tossing the empty can aside.",
                exclude=self.caller
            )
        else:
            self.caller.msg(f"You spray '{colored_message}' on the wall with {can_name_for_message}.")
            self.caller.location.msg_contents(
                f"{self.caller.name} sprays '{colored_message}' on the wall.",
                exclude=self.caller
            )
    
    def _handle_clean_with_solvent(self, solvent_can):
        """Handle cleaning graffiti with a solvent can."""
        
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
        chars_affected = graffiti_obj.remove_random_characters(solvent_used)
        
        # Use solvent
        solvent_can.use_solvent(solvent_used)
        
        # Messages
        if chars_affected > 0:
            # Immediate action message
            self.caller.msg("You apply solvent to the |cgraffiti|n, watching the colors dissolve away.")
            self.caller.location.msg_contents(
                f"{self.caller.name} applies solvent to the |cgraffiti|n, watching the colors dissolve away.",
                exclude=self.caller
            )
            
            # Delayed atmospheric message to everyone including the player
            def delayed_message():
                if self.caller.location:  # Make sure location still exists
                    self.caller.location.msg_contents(
                        "The colors break down and the solvent evaporates, taking the |cgraffiti|n with it."
                    )
            
            delay(3, delayed_message)
            
        else:
            self.caller.msg("There's no graffiti here to clean.")
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
        
        # Find the spray can - check inventory and wielded items
        spray_can = self.caller.search(can_name, candidates=self.caller.contents, quiet=True)
        
        # If not found in inventory, check wielded items (Mr. Hands system)
        if not spray_can and hasattr(self.caller, 'hands'):
            hands = self.caller.hands
            for hand_name, held_item in hands.items():
                if held_item:
                    # Check display name, key, and aliases
                    if (can_name.lower() in held_item.get_display_name(self.caller).lower() or
                        can_name.lower() in held_item.key.lower() or
                        (hasattr(held_item, 'aliases') and held_item.aliases.all() and
                         any(can_name.lower() in alias.lower() for alias in held_item.aliases.all()))):
                        spray_can = [held_item]
                        break
        
        if not spray_can:
            self.caller.msg(f"You don't have a '{can_name}'.")
            return
        
        spray_can = spray_can[0]  # Get first match
        
        # Check if it's an aerosol can with color-changing capability (spraypaint)
        aerosol_contents = getattr(spray_can.db, 'aerosol_contents', None)
        if not aerosol_contents:
            self.caller.msg(f"You can't press colors on {spray_can.get_display_name(self.caller)}.")
            return
        
        # Verify it's a spray can (not solvent)
        if aerosol_contents != "spraypaint":
            self.caller.msg(f"You can't press colors on {spray_can.get_display_name(self.caller)}.")
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
        
        self.caller.msg(f"You press the {colored_name} button on {spray_can.get_display_name(self.caller)}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} presses a button on their spray can.",
            exclude=self.caller
        )
