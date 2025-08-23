"""
Graffiti Commands

Consolidated commands for the graffiti system including spray painting,
color selection, and solvent cleaning.
"""

from evennia import Command, create_object
from typeclasses.items import SprayCanItem, SolventCanItem
from typeclasses.objects import GraffitiObject
import random


class CmdGraffiti(Command):
    """
    Graffiti system commands for spray painting and cleaning.
    
    Usage:
        graffiti spray "<message>" with <spray_can>     - Spray graffiti
        graffiti clean with <solvent_can>              - Clean graffiti  
        graffiti color <color> on <spray_can>          - Change spray can color
        
    Examples:
        graffiti spray "HELLO WORLD" with red_can
        graffiti spray "Snake turf!" with spray_can  
        graffiti clean with solvent_can
        graffiti color blue on spray_can
        graffiti color cyan on my_can
        
    Paint cans have finite paint - if you run out mid-message, your graffiti
    will be cut short. Messages are limited to 100 characters.
    """
    
    key = "graffiti"
    aliases = ["tag", "graf"]
    locks = "cmd:all()"
    help_category = "General"
    
    def func(self):
        """Execute the graffiti command."""
        if not self.args:
            self.caller.msg("Usage: graffiti spray \"<message>\" with <spray_can> OR graffiti clean with <solvent_can> OR graffiti color <color> on <spray_can>")
            return
        
        # Parse subcommand
        args_lower = self.args.lower()
        
        if args_lower.startswith("spray "):
            self._handle_spray(self.args[6:].strip())
        elif args_lower.startswith("clean "):
            self._handle_clean(self.args[6:].strip())
        elif args_lower.startswith("color "):
            self._handle_color(self.args[6:].strip())
        else:
            self.caller.msg("Usage: graffiti spray \"<message>\" with <spray_can> OR graffiti clean with <solvent_can> OR graffiti color <color> on <spray_can>")
    
    def _handle_spray(self, args):
        """Handle spray painting graffiti."""
        if not args or " with " not in args:
            self.caller.msg("Usage: graffiti spray \"<message>\" with <spray_can>")
            return
        
        # Parse arguments
        parts = args.split(" with ", 1)
        if len(parts) != 2:
            self.caller.msg("Usage: graffiti spray \"<message>\" with <spray_can>")
            return
        
        message_input = parts[0].strip()
        item_name = parts[1].strip()
        
        # Find the spray can
        item = self.caller.search(item_name, location=self.caller, quiet=True)
        if not item:
            self.caller.msg(f"You don't have a '{item_name}' to spray with.")
            return
        
        item = item[0]  # Take first match
        
        # Check if caller is in a room
        if not self.caller.location:
            self.caller.msg("You need to be somewhere to spray graffiti.")
            return
        
        # Handle spray painting
        if not isinstance(item, SprayCanItem):
            self.caller.msg(f"{item.get_display_name(self.caller)} is not a spray paint can.")
            return
        
        if not item.has_paint(1):
            self.caller.msg("The spray can is empty.")
            # Destroy empty can
            self.caller.msg("You toss the empty can away.")
            item.delete()
            return
        
        # Extract message from quotes if present
        message = message_input.strip()
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        elif message.startswith("'") and message.endswith("'"):
            message = message[1:-1]
        
        if not message:
            self.caller.msg("What do you want to spray? Use: graffiti spray \"<message>\" with <spray_can>")
            return
        
        # Enforce maximum message length
        max_length = 100
        if len(message) > max_length:
            message = message[:max_length]
            self.caller.msg(f"Message too long! Truncated to {max_length} characters.")
        
        # Check available paint for message
        available_paint = item.db.paint_level
        actual_message = message
        
        # Handle partial spraying if running out of paint
        if available_paint < len(message):
            actual_message = message[:available_paint]
            if available_paint > 3:  # Add "..." if there's room
                actual_message = actual_message[:-3] + "..."
        
        if not actual_message:
            self.caller.msg("Not enough paint left to spray anything.")
            return
        
        # Use paint
        paint_used = item.use_paint(len(actual_message))
        
        # Find or create graffiti object in room
        graffiti_obj = None
        for obj in self.caller.location.contents:
            if isinstance(obj, GraffitiObject):
                graffiti_obj = obj
                break
        
        # Create graffiti object if it doesn't exist
        if not graffiti_obj:
            graffiti_obj = create_object(
                GraffitiObject,
                key="graffiti",
                location=self.caller.location
            )
            
            # Add room integration
            if hasattr(self.caller.location, 'db'):
                if not hasattr(self.caller.location.db, 'integrate'):
                    self.caller.location.db.integrate = []
                if not self.caller.location.db.integrate:
                    self.caller.location.db.integrate = []
                    
                # Add graffiti integration if not already present
                integration_found = False
                for integration in self.caller.location.db.integrate:
                    if 'graffiti' in str(integration).lower():
                        integration_found = True
                        break
                        
                if not integration_found:
                    self.caller.location.db.integrate.append("The walls have been daubed with colorful graffiti.")
        
        # Add graffiti entry
        entry = graffiti_obj.add_graffiti(actual_message, item.db.current_color, self.caller)
        
        # Feedback to player
        if paint_used < len(message):
            self.caller.msg(f"You spray on the wall but run out of paint partway through: {entry}")
            self.caller.msg("You toss the empty can away.")
            item.delete()
        else:
            self.caller.msg(f"You spray on the wall: {entry}")
        
        # Message to room (excluding the sprayer)
        self.caller.location.msg_contents(
            f"{self.caller.get_display_name(None)} sprays graffiti on the wall.",
            exclude=self.caller
        )
    
    def _handle_clean(self, args):
        """Handle cleaning graffiti with solvent."""
        if not args or not args.startswith("with "):
            self.caller.msg("Usage: graffiti clean with <solvent_can>")
            return
        
        item_name = args[5:].strip()  # Remove "with "
        
        # Find the solvent can
        item = self.caller.search(item_name, location=self.caller, quiet=True)
        if not item:
            self.caller.msg(f"You don't have a '{item_name}' to clean with.")
            return
        
        item = item[0]  # Take first match
        
        if not isinstance(item, SolventCanItem):
            self.caller.msg(f"{item.get_display_name(self.caller)} is not a solvent can.")
            return
        
        if not item.has_solvent(1):
            self.caller.msg("The solvent can is empty.")
            # Destroy empty can
            self.caller.msg("You toss the empty can away.")
            item.delete()
            return
        
        # Find graffiti object in room
        graffiti_obj = None
        for obj in self.caller.location.contents:
            if isinstance(obj, GraffitiObject):
                graffiti_obj = obj
                break
        
        if not graffiti_obj or not graffiti_obj.has_graffiti():
            self.caller.msg("There's no graffiti here to clean.")
            return
        
        # Use solvent to remove characters
        amount_to_remove = random.randint(15, 25)  # Random cleaning effectiveness
        solvent_used = min(amount_to_remove, item.db.solvent_level)
        
        # Remove characters from graffiti
        chars_removed = graffiti_obj.remove_random_characters(solvent_used)
        item.use_solvent(solvent_used)
        
        # Atmospheric feedback
        feedback_messages = [
            "The solvent bubbles against the wall as graffiti begins to fade away...",
            "Chemical fumes rise as the solvent eats through layers of paint...",
            "The solvent hisses softly, dissolving random patches of graffiti...",
            "Streams of dissolved paint run down the wall as the solvent works...",
            "The harsh chemical smell fills your nostrils as paint dissolves..."
        ]
        
        self.caller.msg(random.choice(feedback_messages))
        
        # If no graffiti left, remove the graffiti object and integration
        if not graffiti_obj.has_graffiti():
            # Delete empty graffiti object
            graffiti_obj.delete()
            self.caller.msg("The walls are now completely clean.")
        
        # Check if solvent can is empty
        if not item.has_solvent(1):
            self.caller.msg("You toss the empty solvent can away.")
            item.delete()
    
    def _handle_color(self, args):
        """Handle color selection for spray cans."""
        if not args or " on " not in args:
            self.caller.msg("Usage: graffiti color <color> on <spray_can>")
            return
            
        parts = args.split(" on ", 1)
        if len(parts) != 2:
            self.caller.msg("Usage: graffiti color <color> on <spray_can>")
            return
            
        color_name = parts[0].strip().lower()
        item_name = parts[1].strip()
        
        # Find the target item
        item = self.caller.search(item_name, location=self.caller, quiet=True)
        if not item:
            self.caller.msg(f"You don't have a '{item_name}' to adjust.")
            return
        
        item = item[0]  # Take the first match
        
        # Check if it's a spray can
        if not isinstance(item, SprayCanItem):
            self.caller.msg(f"You can't change colors on {item.get_display_name(self.caller)}.")
            return
        
        # Handle color selection
        if color_name:
            # Try to set the specific color
            if item.set_color(color_name):
                self.caller.msg(f"You adjust the nozzle on {item.get_display_name(self.caller)} to |{item.db.current_color}{item.db.current_color}|n.")
            else:
                # Show available colors if invalid color provided
                available = ", ".join(item.db.available_colors)
                self.caller.msg(f"That's not a valid color. Available colors: {available}")
        else:
            # No color specified, cycle to next color
            next_color = item.get_next_color()
            if item.set_color(next_color):
                self.caller.msg(f"You adjust the nozzle on {item.get_display_name(self.caller)} to |{item.db.current_color}{item.db.current_color}|n.")
            else:
                self.caller.msg("Something went wrong with the color adjustment.")
