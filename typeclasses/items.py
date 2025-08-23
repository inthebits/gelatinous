from evennia import DefaultObject

class Item(DefaultObject):
    """
    A general-purpose item. In Gelatinous Monster, all items are
    potential weapons. This typeclass ensures that all objects have
    basic combat-relevant properties.
    """

    def at_object_creation(self):
        """
        Called once when the object is created.
        """
        # Core combat attributes
        self.db.damage = 1  # Minimal default damage
        self.db.weapon_type = "melee"  # Most objects default to melee weapons

        # Optional future expansion
        self.db.hands_required = 1  # Assume one-handed for now

        # Generic descriptor
        if not self.db.desc:
            self.db.desc = "It's a thing. Heavy enough to hurt if used wrong."

        # Add a boolean attribute `is_ranged` to the `Item` class
        self.db.is_ranged = False


class SprayCanItem(Item):
    """
    Spray paint can for graffiti system.
    Contains finite paint and selectable colors.
    """
    
    def at_object_creation(self):
        """Initialize spray can with paint and color attributes."""
        super().at_object_creation()
        
        # Graffiti-specific attributes
        self.db.paint_level = 256  # Default paint capacity
        self.db.max_paint = 256    # Starting paint capacity
        self.db.current_color = "red"  # Default color
        
        # Available ANSI colors for cycling
        self.db.available_colors = [
            "red", "green", "yellow", "blue", "magenta", "cyan", "white",
            "boldred", "boldgreen", "boldyellow", "boldblue", 
            "boldmagenta", "boldcyan", "boldwhite"
        ]
        
        # Override default description
        if not self.db.desc:
            self.db.desc = f"A can of spraypaint with a {self.db.current_color} nozzle. It feels {'heavy' if self.db.paint_level > 128 else 'light' if self.db.paint_level > 0 else 'empty'} with paint."
        
        # Combat properties for spray can as weapon
        self.db.damage = 2  # Slightly better than default item
        self.db.weapon_type = "spraycan"  # Specific weapon type for combat messages
        
    def get_display_name(self, looker, **kwargs):
        """
        Display name includes paint level indicator.
        """
        base_name = super().get_display_name(looker, **kwargs)
        if self.db.paint_level <= 0:
            return f"{base_name} (empty)"
        elif self.db.paint_level < 50:
            return f"{base_name} (low)"
        return base_name
    
    def has_paint(self, amount=1):
        """
        Check if spray can has enough paint for operation.
        
        Args:
            amount (int): Paint amount needed
            
        Returns:
            bool: True if enough paint available
        """
        return self.db.paint_level >= amount
    
    def use_paint(self, amount):
        """
        Consume paint from the can.
        
        Args:
            amount (int): Paint amount to consume
            
        Returns:
            int: Actual amount consumed (may be less if running out)
        """
        if amount <= 0:
            return 0
            
        actual_used = min(amount, self.db.paint_level)
        self.db.paint_level -= actual_used
        
        # Update description based on new paint level
        self.db.desc = f"A can of spraypaint with a {self.db.current_color} nozzle. It feels {'heavy' if self.db.paint_level > 128 else 'light' if self.db.paint_level > 0 else 'empty'} with paint."
        
        return actual_used
    
    def set_color(self, color):
        """
        Set the spray can's current color.
        
        Args:
            color (str): Color name to set
            
        Returns:
            bool: True if color was valid and set
        """
        if color.lower() in [c.lower() for c in self.db.available_colors]:
            # Find the properly cased version
            for available_color in self.db.available_colors:
                if available_color.lower() == color.lower():
                    self.db.current_color = available_color
                    # Update description with new color
                    self.db.desc = f"A can of spraypaint with a {self.db.current_color} nozzle. It feels {'heavy' if self.db.paint_level > 128 else 'light' if self.db.paint_level > 0 else 'empty'} with paint."
                    return True
        return False
    
    def get_next_color(self):
        """
        Get the next color in the cycle.
        
        Returns:
            str: Next color name
        """
        try:
            current_index = self.db.available_colors.index(self.db.current_color)
            next_index = (current_index + 1) % len(self.db.available_colors)
            return self.db.available_colors[next_index]
        except ValueError:
            # Current color not in list, return first color
            return self.db.available_colors[0]


class SolventCanItem(Item):
    """
    Solvent can for cleaning graffiti.
    Contains finite solvent for graffiti removal.
    """
    
    def at_object_creation(self):
        """Initialize solvent can with solvent capacity."""
        super().at_object_creation()
        
        # Solvent-specific attributes
        self.db.solvent_level = 256  # Default solvent capacity (matches spray paint)
        self.db.max_solvent = 256    # Starting solvent capacity
        
        # Override default description
        if not self.db.desc:
            self.db.desc = f"A can of solvent for cleaning graffiti. It feels {'heavy' if self.db.solvent_level > 128 else 'light' if self.db.solvent_level > 0 else 'empty'} with solvent."
            
        # Combat properties for solvent can as weapon
        self.db.damage = 2  # Same as spray can
        self.db.weapon_type = "spraycan"  # Same weapon type as spray can
        
    def get_display_name(self, looker, **kwargs):
        """
        Display name includes solvent level indicator.
        """
        base_name = super().get_display_name(looker, **kwargs)
        if self.db.solvent_level <= 0:
            return f"{base_name} (empty)"
        elif self.db.solvent_level < 50:
            return f"{base_name} (low)"
        return base_name
    
    def has_solvent(self, amount=1):
        """
        Check if solvent can has enough solvent for operation.
        
        Args:
            amount (int): Solvent amount needed
            
        Returns:
            bool: True if enough solvent available
        """
        return self.db.solvent_level >= amount
    
    def use_solvent(self, amount):
        """
        Consume solvent from the can.
        
        Args:
            amount (int): Solvent amount to consume
            
        Returns:
            int: Actual amount consumed (may be less if running out)
        """
        if amount <= 0:
            return 0
            
        actual_used = min(amount, self.db.solvent_level)
        self.db.solvent_level -= actual_used
        
        # Update description based on new solvent level
        self.db.desc = f"A can of solvent for cleaning graffiti. It feels {'heavy' if self.db.solvent_level > 128 else 'light' if self.db.solvent_level > 0 else 'empty'} with solvent."
        
        return actual_used
