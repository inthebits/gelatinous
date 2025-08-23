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
        spray color <color> on <spray_can>    - Change spray can color
        
    Examples:
        spray "HELLO WORLD" with red_can
        spray "WAKKA WAKKA!" with spray_can
        spray here with solvent_can
        spray color blue on spray_can
        spray color cyan on my_can
        
    Paint cans have finite paint - if you run out mid-message, your graffiti
    will be cut short. Messages are limited to 100 characters.
    
    Solvent cans can clean existing graffiti from the current room.
    """
    
    key = "spray"
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the spray command."""
        if not self.args:
            self.caller.msg("Usage: spray \"<message>\" with <spray_can> OR spray here with <solvent_can> OR spray color <color> on <spray_can>")
            return
        
        # Parse command patterns
        args_lower = self.args.lower()
        
        if args_lower.startswith("color "):
            self._handle_color(self.args[6:].strip())
        elif args_lower.startswith("here with "):
            self._handle_clean(self.args[10:].strip())
        elif " with " in self.args:
            self._handle_spray_paint(self.args)
        else:
            self.caller.msg("Usage: spray \"<message>\" with <spray_can> OR spray here with <solvent_can> OR spray color <color> on <spray_can>")
    
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
        
        # Create the graffiti object
        graffiti = create_object(
            typeclass=GraffitiObject,
            key=f"graffiti: {message}",
            location=self.caller.location
        )
        
        # Set graffiti properties
        graffiti.db.message = message
        graffiti.db.color = current_color
        graffiti.db.creator = self.caller.key
        
        # Add to room's graffiti list
        if not self.caller.location.db.graffiti:
            self.caller.location.db.graffiti = []
        self.caller.location.db.graffiti.append(graffiti)
        
        # Messages - using ANSI color formatting
        colored_message = f"|{current_color}{message}|n"
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
        
        # Check for graffiti in the room
        room_graffiti = self.caller.location.db.graffiti or []
        if not room_graffiti:
            self.caller.msg("There's no graffiti here to clean.")
            return
        
        # Remove random graffiti
        graffiti_to_remove = random.choice(room_graffiti)
        cleaned_message = graffiti_to_remove.db.message
        
        # Remove from room and destroy object
        room_graffiti.remove(graffiti_to_remove)
        self.caller.location.db.graffiti = room_graffiti
        graffiti_to_remove.delete()
        
        # Use solvent
        solvent_can.use_solvent(1)
        
        # Messages
        self.caller.msg(f"You clean '{cleaned_message}' from the wall with {solvent_can.name}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} cleans graffiti from the wall.",
            exclude=self.caller
        )
    
    def _handle_color(self, args):
        """Handle changing spray can color."""
        if " on " not in args:
            self.caller.msg("Usage: spray color <color> on <spray_can>")
            return
        
        # Split color and can name
        color_part, can_part = args.rsplit(" on ", 1)
        new_color = color_part.strip().lower()
        can_name = can_part.strip()
        
        # Find the spray can
        spray_can = self.caller.search(can_name, candidates=self.caller.contents, quiet=True)
        if not spray_can:
            self.caller.msg(f"You don't have a '{can_name}'.")
            return
        
        spray_can = spray_can[0]  # Get first match
        
        # Verify it's a spray can
        if not isinstance(spray_can, SprayCanItem):
            self.caller.msg(f"You can't change colors on {spray_can.name}.")
            return
        
        # Check if color is available
        if not spray_can.set_color(new_color):
            available_colors = spray_can.db.available_colors
            color_list = ", ".join(available_colors)
            self.caller.msg(f"Available colors: {color_list}")
            return
        
        # Messages - color was successfully changed by set_color()
        colored_name = f"|{new_color}{new_color}|n"
        
        self.caller.msg(f"You adjust {spray_can.name} to {colored_name}.")
        self.caller.location.msg_contents(
            f"{self.caller.name} adjusts their spray can.",
            exclude=self.caller
        )
