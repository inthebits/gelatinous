"""
Medical Core Classes

Core classes for tracking organ health, medical conditions, and medical state
persistence. These form the foundation of the medical system.
"""

from .constants import (
    ORGANS, BODY_CAPACITIES, CONTRIBUTION_VALUES, 
    CONSCIOUSNESS_UNCONSCIOUS_THRESHOLD, BLOOD_LOSS_DEATH_THRESHOLD,
    PAIN_CONSCIOUSNESS_MODIFIER, PAIN_UNCONSCIOUS_THRESHOLD
)


class Organ:
    """
    Represents a single organ within a character's anatomy.
    
    Tracks current HP, max HP, and medical conditions affecting this organ.
    Integrates with the body capacity system to determine functional impact.
    """
    
    def __init__(self, organ_name, organ_data=None):
        """
        Initialize an organ instance.
        
        Args:
            organ_name (str): Name of the organ (key in ORGANS dict)
            organ_data (dict, optional): Override organ data, defaults to ORGANS[organ_name]
        """
        self.name = organ_name
        self.data = organ_data or ORGANS.get(organ_name, {})
        
        # Core properties
        self.max_hp = self.data.get("max_hp", 10)
        self.current_hp = self.max_hp  # Start at full health
        self.container = self.data.get("container", "unknown")
        self.hit_weight = self.data.get("hit_weight", "common")
        
        # Functional properties
        self.vital = self.data.get("vital", False)
        self.capacity = self.data.get("capacity", None)
        self.capacities = self.data.get("capacities", [])
        self.contribution = self.data.get("contribution", "minor")
        
        # Medical conditions affecting this organ
        self.conditions = []
        
    def is_destroyed(self):
        """Returns True if organ HP is 0 or below."""
        return self.current_hp <= 0
        
    def is_functional(self):
        """Returns True if organ can perform its function."""
        return not self.is_destroyed() and not self._has_disabling_conditions()
        
    def _has_disabling_conditions(self):
        """Check if any conditions disable this organ's function."""
        # For now, return False - will be expanded in later phases
        return False
        
    def get_functionality_percentage(self):
        """
        Returns the percentage of normal function this organ provides.
        
        Returns:
            float: 0.0 to 1.0 representing functional capacity
        """
        if self.is_destroyed():
            return 0.0
            
        # Base functionality based on current HP
        base_function = self.current_hp / self.max_hp
        
        # TODO: Apply condition modifiers in later phases
        # condition_modifier = self._get_condition_penalty()
        # return max(0.0, base_function * condition_modifier)
        
        return base_function
        
    def take_damage(self, amount, injury_type="generic"):
        """
        Apply damage to this organ.
        
        Args:
            amount (int): Damage amount
            injury_type (str): Type of injury (for future expansion)
            
        Returns:
            bool: True if organ was destroyed by this damage
        """
        if amount <= 0:
            return False
            
        old_hp = self.current_hp
        self.current_hp = max(0, self.current_hp - amount)
        
        # Store the injury type for wound description purposes
        # Only store if this is the first damage or if it's different/more severe
        if not hasattr(self, 'injury_type') or self.injury_type == "generic":
            self.injury_type = injury_type
        
        # Return True if this damage destroyed the organ
        return old_hp > 0 and self.current_hp <= 0
        
    def heal(self, amount):
        """
        Heal damage to this organ.
        
        Args:
            amount (int): Healing amount
            
        Returns:
            int: Actual amount healed
        """
        if amount <= 0:
            return 0
            
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        
        return self.current_hp - old_hp
        
    def add_condition(self, condition):
        """Add a medical condition to this organ."""
        if condition not in self.conditions:
            self.conditions.append(condition)
            
    def remove_condition(self, condition):
        """Remove a medical condition from this organ."""
        if condition in self.conditions:
            self.conditions.remove(condition)
            
    def to_dict(self):
        """
        Serialize organ state for persistence.
        
        Returns:
            dict: Serialized organ state
        """
        return {
            "name": self.name,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "conditions": self.conditions.copy(),
            "container": self.container
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Deserialize organ state from persistence.
        
        Args:
            data (dict): Serialized organ state
            
        Returns:
            Organ: Restored organ instance
        """
        organ = cls(data["name"])
        organ.current_hp = data.get("current_hp", organ.max_hp)
        organ.max_hp = data.get("max_hp", organ.max_hp)
        organ.conditions = data.get("conditions", [])
        return organ


class MedicalCondition:
    """
    Represents a medical condition affecting a character.
    
    Conditions can affect specific organs, body locations, or the entire character.
    They track severity, progression, and treatment status.
    """
    
    def __init__(self, condition_type, location=None, severity="minor", **kwargs):
        """
        Initialize a medical condition.
        
        Args:
            condition_type (str): Type of condition (bleeding, fracture, infection, etc.)
            location (str, optional): Body location affected
            severity (str): Severity level (minor, moderate, severe, critical)
            **kwargs: Additional condition-specific properties
        """
        self.type = condition_type
        self.location = location
        self.severity = severity
        self.treated = False
        self.created_time = None  # TODO: Add timestamp in full implementation
        
        # Store additional properties
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def is_bleeding(self):
        """Returns True if this condition causes bleeding."""
        return self.type == "bleeding"
        
    def get_pain_contribution(self):
        """
        Calculate how much pain this condition contributes.
        
        Returns:
            float: Pain points contributed by this condition
        """
        # Basic pain mapping - to be expanded with constants
        pain_map = {
            "bleeding": {"minor": 2, "moderate": 5, "severe": 10, "critical": 20},
            "fracture": {"minor": 5, "moderate": 12, "severe": 25, "critical": 40},
            "infection": {"minor": 3, "moderate": 8, "severe": 15, "critical": 30},
            "burn": {"minor": 8, "moderate": 15, "severe": 30, "critical": 50}
        }
        
        return pain_map.get(self.type, {}).get(self.severity, 0)
        
    def get_blood_loss_rate(self):
        """
        Calculate blood loss per round for bleeding conditions.
        
        Returns:
            float: Blood percentage lost per round
        """
        if not self.is_bleeding():
            return 0.0
            
        bleeding_rates = {
            "minor": 1.0,     # 1% per round
            "moderate": 3.0,  # 3% per round  
            "severe": 8.0,    # 8% per round
            "arterial": 15.0  # 15% per round
        }
        
        return bleeding_rates.get(self.severity, 0.0)
        
    def to_dict(self):
        """Serialize condition for persistence."""
        return {
            "type": self.type,
            "location": self.location,
            "severity": self.severity,
            "treated": self.treated,
            "created_time": self.created_time
        }
        
    @classmethod
    def from_dict(cls, data):
        """Deserialize condition from persistence."""
        condition = cls(
            data["type"],
            location=data.get("location"),
            severity=data.get("severity", "minor")
        )
        condition.treated = data.get("treated", False)
        condition.created_time = data.get("created_time")
        return condition


class MedicalState:
    """
    Manages the complete medical state of a character.
    
    Coordinates between organs, conditions, vital signs, and body capacities.
    Handles persistence and provides high-level medical queries.
    """
    
    def __init__(self, character=None):
        """
        Initialize medical state.
        
        Args:
            character: Reference to the character this belongs to
        """
        self.character = character
        self.organs = {}
        self.conditions = []
        
        # Vital signs
        self.blood_level = 100.0  # Percentage of normal blood volume
        self.pain_level = 0.0     # Current pain accumulation
        self.consciousness = 1.0  # Current consciousness level (0.0 to 1.0)
        
        # Cache for expensive calculations
        self._capacity_cache = {}
        self._cache_dirty = True
        
        # Initialize default human organs
        self._initialize_default_organs()
        
    def _initialize_default_organs(self):
        """Initialize standard human organ set."""
        for organ_name in ORGANS.keys():
            self.organs[organ_name] = Organ(organ_name)
            
    def get_organ(self, organ_name):
        """Get organ by name, creating if it doesn't exist."""
        if organ_name not in self.organs:
            self.organs[organ_name] = Organ(organ_name)
        return self.organs[organ_name]
        
    def add_condition(self, condition_type, location=None, severity="minor", **kwargs):
        """
        Add a new medical condition.
        
        Args:
            condition_type (str): Type of condition
            location (str, optional): Affected body location
            severity (str): Condition severity
            **kwargs: Additional condition properties
            
        Returns:
            MedicalCondition: The created condition
        """
        condition = MedicalCondition(condition_type, location, severity, **kwargs)
        self.conditions.append(condition)
        self._cache_dirty = True
        return condition
        
    def remove_condition(self, condition):
        """Remove a medical condition."""
        if condition in self.conditions:
            self.conditions.remove(condition)
            self._cache_dirty = True
            
    def get_conditions_by_type(self, condition_type):
        """Get all conditions of a specific type."""
        return [c for c in self.conditions if c.type == condition_type]
        
    def get_conditions_by_location(self, location):
        """Get all conditions affecting a specific body location."""
        return [c for c in self.conditions if c.location == location]
        
    def calculate_total_pain(self):
        """Calculate total pain from all conditions."""
        total_pain = sum(condition.get_pain_contribution() for condition in self.conditions)
        return total_pain
        
    def calculate_blood_loss_rate(self):
        """Calculate total blood loss per round from all bleeding conditions."""
        total_loss = sum(condition.get_blood_loss_rate() for condition in self.conditions)
        return total_loss
        
    def calculate_body_capacity(self, capacity_name):
        """
        Calculate current level of a body capacity.
        
        Args:
            capacity_name (str): Name of capacity to calculate
            
        Returns:
            float: 0.0 to 1.0 representing capacity level
        """
        if not self._cache_dirty and capacity_name in self._capacity_cache:
            return self._capacity_cache[capacity_name]
            
        capacity_data = BODY_CAPACITIES.get(capacity_name, {})
        capacity_organs = capacity_data.get("organs", [])
        
        if not capacity_organs:
            return 1.0  # No organs defined = full capacity
            
        total_capacity = 0.0
        max_possible_capacity = 0.0
        
        for organ_name in capacity_organs:
            organ = self.get_organ(organ_name)
            organ_functionality = organ.get_functionality_percentage()
            
            # Get contribution level - check for organ-specific contributions first
            contribution_value = None
            
            # Check for organ-specific contributions (e.g., liver_contribution, stomach_contribution)
            organ_contribution_key = f"{organ_name}_contribution"
            if organ_contribution_key in capacity_data:
                contribution_value = capacity_data[organ_contribution_key]
            else:
                # Check for bone-specific contributions (e.g., femur_contribution, humerus_contribution)
                bone_type = organ_name.split('_')[-1]  # Get bone name (femur, humerus, etc.)
                if bone_type in ['femur', 'tibia', 'humerus']:
                    bone_contribution_key = f"{bone_type}_contribution"
                elif 'metacarpals' in organ_name:
                    bone_contribution_key = "metacarpal_contribution"
                elif 'metatarsals' in organ_name:
                    bone_contribution_key = "metatarsal_contribution"
                else:
                    bone_contribution_key = None
                    
                if bone_contribution_key and bone_contribution_key in capacity_data:
                    contribution_value = capacity_data[bone_contribution_key]
                else:
                    # Fall back to organ's defined contribution or generic lookup
                    contribution_key = organ.data.get(f"{capacity_name}_contribution", organ.contribution)
                    if isinstance(contribution_key, str):
                        contribution_value = CONTRIBUTION_VALUES.get(contribution_key, 0.05)
                    else:
                        contribution_value = float(contribution_key)
                
            # Add to totals
            total_capacity += organ_functionality * contribution_value
            max_possible_capacity += contribution_value
            
        # Normalize to 0.0-1.0 range based on maximum possible capacity
        if max_possible_capacity > 0:
            capacity_level = total_capacity / max_possible_capacity
        else:
            capacity_level = 1.0
            
        # Clamp to valid range
        capacity_level = max(0.0, min(1.0, capacity_level))
        
        # Cache the result
        self._capacity_cache[capacity_name] = capacity_level
        return capacity_level
        
    def is_unconscious(self):
        """Returns True if character is unconscious."""
        consciousness_level = self.calculate_body_capacity("consciousness")
        return consciousness_level < (CONSCIOUSNESS_UNCONSCIOUS_THRESHOLD / 100.0)
        
    def is_dead(self):
        """Returns True if character should be considered dead."""
        # Death from vital organ failure
        if self.calculate_body_capacity("blood_pumping") <= 0.0:
            return True
        if self.calculate_body_capacity("breathing") <= 0.0:
            return True
        if self.calculate_body_capacity("digestion") <= 0.0:
            return True  # Liver failure
            
        # Death from blood loss
        if self.blood_level <= (100.0 - BLOOD_LOSS_DEATH_THRESHOLD):
            return True
            
        return False
        
    def update_vital_signs(self):
        """Update vital signs based on current conditions and organ state."""
        # Update pain level
        self.pain_level = self.calculate_total_pain()
        
        # Update blood loss
        blood_loss_rate = self.calculate_blood_loss_rate()
        if blood_loss_rate > 0:
            self.blood_level = max(0.0, self.blood_level - blood_loss_rate)
            
        # Update consciousness based on multiple factors
        base_consciousness = self.calculate_body_capacity("consciousness")
        
        # Pain penalty
        pain_penalty = 0.0
        if self.pain_level > PAIN_UNCONSCIOUS_THRESHOLD:
            pain_penalty = (self.pain_level - PAIN_UNCONSCIOUS_THRESHOLD) * PAIN_CONSCIOUSNESS_MODIFIER
            
        # Blood loss penalty
        blood_penalty = max(0.0, (100.0 - self.blood_level) / 100.0)
        
        self.consciousness = max(0.0, base_consciousness - pain_penalty - blood_penalty)
        
        # Mark cache as dirty after vital sign updates
        self._cache_dirty = True
        
    def take_organ_damage(self, organ_name, damage_amount, injury_type="generic"):
        """
        Apply damage to a specific organ.
        
        Args:
            organ_name (str): Name of organ to damage
            damage_amount (int): Amount of damage
            injury_type (str): Type of injury
            
        Returns:
            bool: True if organ was destroyed
        """
        organ = self.get_organ(organ_name)
        was_destroyed = organ.take_damage(damage_amount, injury_type)
        self._cache_dirty = True
        return was_destroyed
        
    def to_dict(self):
        """Serialize medical state for persistence."""
        return {
            "organs": {name: organ.to_dict() for name, organ in self.organs.items()},
            "conditions": [condition.to_dict() for condition in self.conditions],
            "blood_level": self.blood_level,
            "pain_level": self.pain_level,
            "consciousness": self.consciousness
        }
        
    @classmethod 
    def from_dict(cls, data, character=None):
        """Deserialize medical state from persistence."""
        medical_state = cls(character)
        
        # Restore organs
        organ_data = data.get("organs", {})
        for organ_name, organ_dict in organ_data.items():
            medical_state.organs[organ_name] = Organ.from_dict(organ_dict)
            
        # Restore conditions
        condition_data = data.get("conditions", [])
        for condition_dict in condition_data:
            condition = MedicalCondition.from_dict(condition_dict)
            medical_state.conditions.append(condition)
            
        # Restore vital signs
        medical_state.blood_level = data.get("blood_level", 100.0)
        medical_state.pain_level = data.get("pain_level", 0.0)
        
        # Handle consciousness migration: old data stored as percentage (100.0), new as decimal (1.0)
        consciousness_value = data.get("consciousness", 1.0)
        if consciousness_value > 1.0:
            # Old percentage format, convert to decimal
            medical_state.consciousness = consciousness_value / 100.0
        else:
            # New decimal format
            medical_state.consciousness = consciousness_value
        
        return medical_state
