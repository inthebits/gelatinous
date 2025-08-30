from evennia import DefaultObject, AttributeProperty
from world.combat.constants import DEFAULT_CLOTHING_LAYER

class Item(DefaultObject):
    """
    A general-purpose item. In Gelatinous Monster, all items are
    potential weapons. This typeclass ensures that all objects have
    basic combat-relevant properties.
    
    Items become wearable clothing by setting coverage and worn_desc attributes.
    """
    
    # ===================================================================
    # CLOTHING SYSTEM ATTRIBUTES
    # ===================================================================
    
    # Coverage definition - which body locations this item covers (base state)
    # Empty list = not wearable, populated list = clothing item
    coverage = AttributeProperty([], autocreate=True)
    
    # Clothing-specific description that appears when worn (base state)
    # Empty string = not clothing, populated = worn description
    worn_desc = AttributeProperty("", autocreate=True)
    
    # Layer priority for stacking items (higher = outer layer)
    layer = AttributeProperty(DEFAULT_CLOTHING_LAYER, autocreate=True)
    
    # Multiple style properties for combination states
    style_properties = AttributeProperty({}, autocreate=True)
    # Structure: {"adjustable": "rolled", "closure": "zipped"}
    
    # Style configurations defining all possible combinations
    style_configs = AttributeProperty({}, autocreate=True)
    # Structure: {
    #     "adjustable": {
    #         "rolled": {"coverage_mod": [...], "desc_mod": "with sleeves rolled up"},
    #         "normal": {"coverage_mod": [], "desc_mod": ""}
    #     },
    #     "closure": {
    #         "zipped": {"coverage_mod": [...], "desc_mod": "zipped tight"},
    #         "unzipped": {"coverage_mod": [...], "desc_mod": "hanging open"}
    #     }
    # }
    
    # ===================================================================
    # CLOTHING SYSTEM METHODS
    # ===================================================================
    
    def is_wearable(self):
        """Check if this item can be worn as clothing"""
        return bool(self.coverage) and bool(self.worn_desc)
    
    def get_current_coverage(self):
        """Get coverage for current combination of style states"""
        coverage = list(self.coverage)  # Start with base coverage
        
        if not self.style_configs or not self.style_properties:
            return coverage
        
        # Apply modifications from each active style property in deterministic order
        for property_name in sorted(self.style_properties.keys()):
            property_state = self.style_properties[property_name]
            
            if property_name in self.style_configs:
                property_config = self.style_configs[property_name]
                if property_state in property_config:
                    state_config = property_config[property_state]
                    coverage_mod = state_config.get("coverage_mod", [])
                    
                    # Apply coverage modifications
                    for mod in coverage_mod:
                        if mod.startswith("+"):
                            # Add location if not already covered
                            location = mod[1:]
                            if location not in coverage:
                                coverage.append(location)
                        elif mod.startswith("-"):
                            # Remove location if currently covered
                            location = mod[1:]
                            if location in coverage:
                                coverage.remove(location)
        
        return coverage
    
    def get_current_worn_desc(self):
        """Get worn description incorporating all active style states"""
        if not self.style_configs or not self.style_properties:
            return f"{self.worn_desc}." if self.worn_desc else ""
        
        # For multi-property items, we need to handle combinations
        # Priority order: check properties in sorted order, use first non-empty desc_mod
        for property_name in sorted(self.style_properties.keys()):
            property_state = self.style_properties[property_name]
            
            if property_name in self.style_configs:
                property_config = self.style_configs[property_name]
                if property_state in property_config:
                    state_config = property_config[property_state]
                    desc_mod = state_config.get("desc_mod", "").strip()
                    if desc_mod:
                        # First non-empty desc_mod wins - this allows for sophisticated combinations
                        return f"{desc_mod}." if not desc_mod.endswith('.') else desc_mod
        
        # No active desc_mod found, use base worn_desc
        return f"{self.worn_desc}." if self.worn_desc else ""
    
    def can_style_property_to(self, property_name, state_name):
        """Check if item can transition specific property to given state"""
        if property_name not in self.style_configs:
            return False
        if state_name not in self.style_configs[property_name]:
            return False
        
        # Always allow transitions to valid states - the validation is structural, not functional
        return True
    
    def set_style_property(self, property_name, state_name):
        """Set specific style property to given state with validation"""
        if not self.can_style_property_to(property_name, state_name):
            return False
        
        if not self.style_properties:
            self.style_properties = {}
        
        self.style_properties[property_name] = state_name
        return True
    
    def get_style_property(self, property_name):
        """Get current state of specific style property"""
        from world.combat.constants import STYLE_STATE_NORMAL
        return self.style_properties.get(property_name, STYLE_STATE_NORMAL)
    
    def get_available_style_properties(self):
        """Get all available style properties and their states"""
        return {prop: list(states.keys()) for prop, states in self.style_configs.items()}

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
        self.db.aerosol_level = 256  # Default aerosol capacity
        self.db.max_aerosol = 256    # Starting aerosol capacity
        self.db.current_color = "red"  # Default color
        self.db.aerosol_contents = "spraypaint"  # What's inside the can
        
        # Available ANSI colors for cycling
        self.db.available_colors = [
            "red", "green", "yellow", "blue", "magenta", "cyan", "white"
        ]
        
        # Override default description with aerosol level and contents
        if not self.db.desc:
            self.db.desc = f"A can of {self.db.aerosol_contents} with a {self.db.current_color} nozzle. It feels {'heavy' if self.db.aerosol_level > 128 else 'light' if self.db.aerosol_level > 0 else 'empty'} with {self.db.aerosol_contents}."
        
        # Combat properties for spray can as weapon
        self.db.damage = 2  # Slightly better than default item
        self.db.weapon_type = "spraycan"  # Specific weapon type for combat messages
        
    def get_display_name(self, looker, **kwargs):
        """
        Display name based on aerosol contents.
        Since cans self-destruct when empty, no need for state indicators.
        """
        aerosol_contents = self.db.aerosol_contents or "spraypaint"
        return f"can of {aerosol_contents}"
    
    def has_paint(self, amount=1):
        """
        Check if spray can has enough aerosol for operation.
        
        Args:
            amount (int): Aerosol amount needed
            
        Returns:
            bool: True if enough aerosol available
        """
        return self.db.aerosol_level >= amount
    
    def use_paint(self, amount):
        """
        Consume aerosol from the can.
        
        Args:
            amount (int): Aerosol amount to consume
            
        Returns:
            int: Actual amount consumed (may be less if running out)
        """
        if amount <= 0:
            return 0
            
        actual_used = min(amount, self.db.aerosol_level)
        self.db.aerosol_level -= actual_used
        
        # Update description based on new aerosol level
        self.db.desc = f"A can of spraypaint with a {self.db.current_color} nozzle. It feels {'heavy' if self.db.aerosol_level > 128 else 'light' if self.db.aerosol_level > 0 else 'empty'} with paint."
        
        # Delete the can if it's empty
        if self.db.aerosol_level <= 0:
            # If wielded, remove from hands first
            if self.location and hasattr(self.location, 'hands'):
                hands = self.location.hands
                for hand_name, held_item in hands.items():
                    if held_item == self:
                        hands[hand_name] = None
                        self.location.hands = hands
                        break
            
            # Delete silently - let calling code handle messaging
            self.delete()
        
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
                    self.db.desc = f"A can of spraypaint with a {self.db.current_color} nozzle. It feels {'heavy' if self.db.aerosol_level > 128 else 'light' if self.db.aerosol_level > 0 else 'empty'} with paint."
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
        """Initialize solvent can with aerosol capacity."""
        super().at_object_creation()
        
        # Aerosol-specific attributes (standardized)
        self.db.aerosol_level = 256  # Default aerosol capacity (matches spray paint)
        self.db.max_aerosol = 256    # Starting aerosol capacity
        self.db.aerosol_contents = "solvent"  # What's inside the can
        
        # Override default description with contents
        if not self.db.desc:
            self.db.desc = f"A can of {self.db.aerosol_contents} for cleaning graffiti. It feels {'heavy' if self.db.aerosol_level > 128 else 'light' if self.db.aerosol_level > 0 else 'empty'} with {self.db.aerosol_contents}."
            
        # Combat properties for solvent can as weapon
        self.db.damage = 2  # Same as spray can
        self.db.weapon_type = "spraycan"  # Same weapon type as spray can
        
    def get_display_name(self, looker, **kwargs):
        """
        Display name based on aerosol contents.
        Since cans self-destruct when empty, no need for state indicators.
        """
        aerosol_contents = self.db.aerosol_contents or "solvent"
        return f"can of {aerosol_contents}"
    
    def has_solvent(self, amount=1):
        """
        Check if solvent can has enough aerosol for operation.
        
        Args:
            amount (int): Aerosol amount needed
            
        Returns:
            bool: True if enough aerosol available
        """
        return self.db.aerosol_level >= amount
    
    def use_solvent(self, amount):
        """
        Consume aerosol from the can.
        
        Args:
            amount (int): Aerosol amount to consume
            
        Returns:
            int: Actual amount consumed (may be less if running out)
        """
        if amount <= 0:
            return 0
            
        actual_used = min(amount, self.db.aerosol_level)
        self.db.aerosol_level -= actual_used
        
        # Update description based on new aerosol level
        self.db.desc = f"A can of solvent for cleaning graffiti. It feels {'heavy' if self.db.aerosol_level > 128 else 'light' if self.db.aerosol_level > 0 else 'empty'} with solvent."
        
        # Delete the can if it's empty
        if self.db.aerosol_level <= 0:
            # If wielded, remove from hands first
            if self.location and hasattr(self.location, 'hands'):
                hands = self.location.hands
                for hand_name, held_item in hands.items():
                    if held_item == self:
                        hands[hand_name] = None
                        self.location.hands = hands
                        break
            
            # Delete silently - let calling code handle messaging
            self.delete()
        
        return actual_used
