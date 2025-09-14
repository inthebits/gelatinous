"""
Medical condition classes for the health system.

This module defines the base MedicalCondition class and specific condition types
like bleeding. Conditions are managed by per-character MedicalScript instances.
"""

import random
from evennia.comms.models import ChannelDB
from .constants import (
    INJURY_SEVERITY_MULTIPLIERS,
    BLOOD_LOSS_PER_SEVERITY,
    HEALING_EFFECTIVENESS,
    CONDITION_INTERVALS, 
    BLEEDING_DAMAGE_THRESHOLDS, 
    CONDITION_TRIGGERS
)


class MedicalCondition:
    """
    Base class for all medical conditions.
    
    Medical conditions are now managed by per-character MedicalScript instances
    instead of individual TICKER_HANDLER subscriptions.
    """
    
    def __init__(self, condition_type, severity, location=None, tick_interval=60):
        self.condition_type = condition_type
        self.severity = severity
        self.max_severity = severity  # Track original severity
        self.location = location
        self.tick_interval = tick_interval  # Not used directly anymore, but kept for compatibility
        self.requires_ticker = True
        self.treated = False
        
    def start_condition(self, character):
        """Begin condition management for character."""
        from world.medical.script import start_medical_script
        from evennia.comms.models import ChannelDB
        from world.combat.constants import SPLATTERCAST_CHANNEL
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not self.requires_ticker:
            splattercast.msg(f"CONDITION_START: {self.condition_type} for {character.key} doesn't require ticker")
            return
            
        splattercast.msg(f"CONDITION_START: Adding {self.condition_type} severity {self.severity} to {character.key}")
        
        # Ensure character has medical script running
        medical_script = start_medical_script(character)
        if medical_script:
            splattercast.msg(f"CONDITION_START: Medical script active for {character.key}")
        else:
            splattercast.msg(f"CONDITION_START: Failed to start medical script for {character.key}")
            
    def tick_effect(self, character):
        """Override in subclasses to implement specific effects."""
        pass
        
    def should_end(self):
        """Check if condition should be removed. Override in subclasses."""
        return self.severity <= 0
        
    def get_pain_contribution(self):
        """Return pain contribution from this condition. Override in subclasses."""
        return 0  # Base conditions don't contribute pain by default
        
    def get_blood_loss_rate(self):
        """Return blood loss rate from this condition. Override in subclasses."""
        return 0  # Base conditions don't cause blood loss by default
        
    @property
    def type(self):
        """Alias for condition_type for backward compatibility."""
        return self.condition_type
        
    def to_dict(self):
        """Serialize condition for persistence."""
        return {
            "condition_type": self.condition_type,
            "severity": self.severity,
            "max_severity": self.max_severity,
            "location": self.location,
            "tick_interval": self.tick_interval,
            "requires_ticker": self.requires_ticker,
            "treated": self.treated
        }
        
    @classmethod
    def from_dict(cls, data):
        """Deserialize condition from persistence."""
        condition = cls(
            data.get("condition_type", "unknown"),
            data.get("severity", 1),
            data.get("location")
        )
        condition.max_severity = data.get("max_severity", condition.severity)
        condition.tick_interval = data.get("tick_interval", 60)
        condition.requires_ticker = data.get("requires_ticker", True)
        condition.treated = data.get("treated", False)
        return condition
        
    def end_condition(self, character):
        """Clean up when condition ends."""
        # No ticker cleanup needed - script handles lifecycle
        pass
        
    def apply_treatment(self, treatment_quality="adequate"):
        """Apply medical treatment to this condition."""
        self.treated = True
        # Subclasses should override for specific treatment effects


class BleedingCondition(MedicalCondition):
    """Bleeding condition that causes blood loss over time."""
    
    def __init__(self, severity, location=None):
        super().__init__("minor_bleeding", severity, location, tick_interval=60)
        self.blood_loss_rate = BLOOD_LOSS_PER_SEVERITY.get(severity, 1)
        
    def tick_effect(self, character):
        """Apply blood loss and potentially reduce severity."""
        from world.combat.constants import SPLATTERCAST_CHANNEL
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not hasattr(character, 'medical_state'):
            return
            
        medical_state = character.medical_state
        
        # Calculate blood loss
        blood_loss = self.blood_loss_rate
        if self.treated:
            blood_loss = int(blood_loss * 0.3)  # Treated bleeding loses less blood
            
        # Apply blood loss
        old_blood = medical_state.blood_level
        medical_state.blood_level = max(0, medical_state.blood_level - blood_loss)
        
        splattercast.msg(f"BLOOD_LOSS: {character.key} loses {blood_loss} blood ({old_blood} -> {medical_state.blood_level})")
        
        # Check for natural healing (random chance to reduce severity)
        if not self.treated and random.randint(1, 100) <= 10:  # 10% chance per tick
            self.severity = max(0, self.severity - 1)
            splattercast.msg(f"BLEEDING_HEAL: {character.key} bleeding severity reduced to {self.severity}")
            
        # Notify character of blood loss
        if blood_loss > 0:
            if self.location:
                character.msg(f"|rYou feel blood seeping from your {self.location}.|n")
            else:
                character.msg(f"|rYou feel blood loss from your injuries.|n")
                
    def should_end(self):
        """Bleeding ends when severity reaches 0."""
        return self.severity <= 0
        
    def get_pain_contribution(self):
        """Return pain contribution from bleeding."""
        # Bleeding causes pain proportional to severity
        return max(1, self.severity // 2)  # Half severity as pain
        
    def get_blood_loss_rate(self):
        """Return blood loss rate per tick."""
        blood_loss = self.blood_loss_rate
        if self.treated:
            blood_loss = int(blood_loss * 0.3)  # Treated bleeding loses less blood
        return blood_loss
        
    def apply_treatment(self, treatment_quality="adequate"):
        """Apply medical treatment to bleeding."""
        super().apply_treatment(treatment_quality)
        
        # Treatment effectiveness
        effectiveness = HEALING_EFFECTIVENESS.get(treatment_quality, 0.5)
        severity_reduction = max(1, int(self.severity * effectiveness))
        
        self.severity = max(0, self.severity - severity_reduction)
        
        # Reduce blood loss rate for treated bleeding
        self.blood_loss_rate = max(1, int(self.blood_loss_rate * 0.3))
        
    def to_dict(self):
        """Serialize bleeding condition for persistence."""
        data = super().to_dict()
        data["blood_loss_rate"] = self.blood_loss_rate
        return data
        
    @classmethod
    def from_dict(cls, data):
        """Deserialize bleeding condition from persistence."""
        condition = cls(
            data.get("severity", 1),
            data.get("location")
        )
        condition.max_severity = data.get("max_severity", condition.severity)
        condition.tick_interval = data.get("tick_interval", 60)
        condition.requires_ticker = data.get("requires_ticker", True)
        condition.treated = data.get("treated", False)
        condition.blood_loss_rate = data.get("blood_loss_rate", condition.blood_loss_rate)
        return condition


class PainCondition(MedicalCondition):
    """Pain condition that affects character abilities."""
    
    def __init__(self, severity, location=None):
        super().__init__("pain", severity, location, tick_interval=120)  # Longer interval
        
    def tick_effect(self, character):
        """Pain naturally diminishes over time."""
        from world.combat.constants import SPLATTERCAST_CHANNEL
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Natural pain reduction
        if random.randint(1, 100) <= 20:  # 20% chance per tick
            self.severity = max(0, self.severity - 1)
            splattercast.msg(f"PAIN_HEAL: {character.key} pain severity reduced to {self.severity}")
            
        # Pain messages
        if self.severity > 5:
            character.msg(f"|rIntense pain throbs from your {self.location or 'injuries'}.|n")
        elif self.severity > 2:
            character.msg(f"|yAching pain persists in your {self.location or 'injuries'}.|n")
            
    def should_end(self):
        """Pain ends when severity reaches 0."""
        return self.severity <= 0
        
    def get_pain_contribution(self):
        """Return pain contribution from this condition."""
        return self.severity  # Pain conditions contribute their full severity to total pain
        
    def apply_treatment(self, treatment_quality="adequate"):
        """Apply medical treatment to pain."""
        super().apply_treatment(treatment_quality)
        
        # Pain treatment is very effective
        effectiveness = HEALING_EFFECTIVENESS.get(treatment_quality, 0.5)
        severity_reduction = max(1, int(self.severity * effectiveness * 1.5))  # Extra effective
        
        self.severity = max(0, self.severity - severity_reduction)


class InfectionCondition(MedicalCondition):
    """Infection condition that can worsen over time if untreated."""
    
    def __init__(self, severity, location=None):
        super().__init__("infection", severity, location, tick_interval=300)  # 5 minute interval
        self.progression_chance = 15  # % chance to worsen per tick if untreated
        
    def tick_effect(self, character):
        """Infection can worsen if untreated, or improve if treated."""
        from world.combat.constants import SPLATTERCAST_CHANNEL
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if self.treated:
            # Treated infection improves
            if random.randint(1, 100) <= 30:  # 30% chance to improve
                self.severity = max(0, self.severity - 1)
                splattercast.msg(f"INFECTION_HEAL: {character.key} infection severity reduced to {self.severity}")
        else:
            # Untreated infection can worsen
            if random.randint(1, 100) <= self.progression_chance:
                self.severity = min(10, self.severity + 1)  # Cap at 10
                splattercast.msg(f"INFECTION_WORSEN: {character.key} infection severity increased to {self.severity}")
                character.msg(f"|rYour {self.location or 'wound'} feels hot and inflamed.|n")
                
        # Infection effects
        if self.severity > 7:
            character.msg(f"|rFever burns through you as infection spreads.|n")
            # Could add fever effects here
        elif self.severity > 4:
            character.msg(f"|yYour {self.location or 'wound'} throbs with infection.|n")
            
    def should_end(self):
        """Infection ends when severity reaches 0."""
        return self.severity <= 0
        
    def apply_treatment(self, treatment_quality="adequate"):
        """Apply medical treatment to infection."""
        super().apply_treatment(treatment_quality)
        
        # Treatment is crucial for infections
        effectiveness = HEALING_EFFECTIVENESS.get(treatment_quality, 0.5)
        severity_reduction = max(1, int(self.severity * effectiveness))
        
        self.severity = max(0, self.severity - severity_reduction)
        
        # Stop progression when treated
        self.progression_chance = 0


def create_condition_from_damage(damage_amount, damage_type, location=None):
    """
    Create appropriate medical conditions based on damage dealt.
    
    Args:
        damage_amount: Amount of damage dealt
        damage_type: Type of damage (bullet, blade, blunt, etc.)
        location: Body location affected
        
    Returns:
        list: List of MedicalCondition instances
    """
    conditions = []
    
    # Always create bleeding for significant damage
    threshold = BLEEDING_DAMAGE_THRESHOLDS.get('minor', 5)
    
    if damage_amount >= threshold:
        bleeding_severity = min(10, max(1, damage_amount // 3))
        conditions.append(BleedingCondition(bleeding_severity, location))
    
    # Add pain for any damage
    if damage_amount > 0:
        pain_severity = min(8, max(1, damage_amount // 2))
        conditions.append(PainCondition(pain_severity, location))
    
    # Add infection risk for penetrating wounds
    if damage_type in ['bullet', 'blade', 'pierce'] and damage_amount >= 8:
        if random.randint(1, 100) <= 25:  # 25% chance
            infection_severity = random.randint(1, 3)
            conditions.append(InfectionCondition(infection_severity, location))
    
    return conditions


def remove_condition_by_type(character, condition_type):
    """
    Remove all conditions of a specific type from character.
    
    Args:
        character: Character to remove conditions from
        condition_type: Type of condition to remove
    """
    if not hasattr(character, 'medical_state'):
        return
        
    medical_state = character.medical_state
    conditions_to_remove = [c for c in medical_state.conditions if c.condition_type == condition_type]
    
    for condition in conditions_to_remove:
        medical_state.conditions.remove(condition)
        condition.end_condition(character)
