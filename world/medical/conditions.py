"""
Medical Conditions System

Ticker-based medical conditions that apply ongoing effects over time.
Uses Evennia's native ticker system for time progression.
"""

from evennia import TICKER_HANDLER
from .constants import (
    CONDITION_INTERVALS, BLEEDING_DAMAGE_THRESHOLDS, CONDITION_TRIGGERS
)

# Global registry to track active conditions for ticker callbacks
_ACTIVE_CONDITIONS = {}

def _condition_tick_callback(condition_id):
    """
    Standalone callback function for condition tickers.
    
    This is required because Evennia's TICKER_HANDLER only accepts
    standalone functions or typeclass methods as callbacks.
    """
    if condition_id not in _ACTIVE_CONDITIONS:
        # Condition was removed, stop ticker
        TICKER_HANDLER.remove(idstring=condition_id)
        return
        
    condition = _ACTIVE_CONDITIONS[condition_id]
    
    # Get character from condition ID
    try:
        character_id = condition_id.split('_')[0]
        # Find character by ID
        from evennia.objects.models import ObjectDB
        character = ObjectDB.objects.get(id=int(character_id))
        
        if not character or not hasattr(character, 'medical_state'):
            # Character doesn't exist or has no medical state, stop condition
            condition.end_condition(None)
            return
            
        # Apply tick effect
        condition.tick_effect(character)
        
    except Exception as e:
        # Error occurred, stop condition
        print(f"Condition tick error for {condition_id}: {e}")
        condition.end_condition(None)

class MedicalCondition:
    """
    Base class for all medical conditions.
    
    Medical conditions are persistent effects that can tick over time,
    applying ongoing damage, healing, or other effects to characters.
    """
    
    def __init__(self, condition_type, severity, location=None, tick_interval=60):
        self.condition_type = condition_type
        self.severity = severity
        self.location = location
        self.tick_interval = tick_interval
        self.requires_ticker = True
        self.ticker_id = None
        
    def start_condition(self, character):
        """Begin ticking condition on character if required."""
        if not self.requires_ticker:
            return
            
        # Create unique ticker ID
        self.ticker_id = f"{character.id}_{self.condition_type}_{id(self)}"
        
        # Register condition in global registry
        _ACTIVE_CONDITIONS[self.ticker_id] = self
        
        # Start ticker with standalone callback
        TICKER_HANDLER.add(
            interval=self.tick_interval,
            callback=_condition_tick_callback,
            idstring=self.ticker_id,
            persistent=True,
            # Pass the condition_id as an argument to the callback
            args=[self.ticker_id]
        )
        
    def tick_effect(self, character):
        """Override in subclasses to implement specific effects."""
        pass
        
    def end_condition(self, character):
        """Stop ticking and clean up."""
        if self.ticker_id:
            # Remove from global registry
            if self.ticker_id in _ACTIVE_CONDITIONS:
                del _ACTIVE_CONDITIONS[self.ticker_id]
                
            # Stop ticker
            TICKER_HANDLER.remove(idstring=self.ticker_id)
            self.ticker_id = None
            
    def stop_condition(self):
        """Alias for end_condition for compatibility."""
        self.end_condition(None)

import random
from evennia import TICKER_HANDLER
from .constants import (
    CONDITION_INTERVALS, COMBAT_TICK_INTERVAL, SEVERE_BLEEDING_INTERVAL, 
    MEDICAL_TICK_INTERVAL, BLEEDING_DAMAGE_THRESHOLDS
)


class MedicalCondition:
    """
    Base class for all medical conditions with ticker support.
    
    Conditions can be static (just impose penalties) or dynamic (tick over time).
    Dynamic conditions use Evennia's ticker system for time-based progression.
    """
    
    def __init__(self, condition_type, severity, location=None, duration=None, requires_ticker=False):
        """
        Initialize a medical condition.
        
        Args:
            condition_type (str): Type of condition (bleeding, burning, etc.)
            severity (int/str): Current condition strength
            location (str): Body location affected (optional)
            duration (int): Maximum ticks before auto-resolve (None = unlimited)
            requires_ticker (bool): Whether this condition needs time-based progression
        """
        self.condition_type = condition_type
        self.severity = severity
        self.location = location
        self.max_duration = duration
        self.current_tick = 0
        self.requires_ticker = requires_ticker
        self.treated = False
        self.auto_resolve = True
        self.created_time = None  # TODO: Add timestamp when time system implemented
        
        # Get ticker interval for this condition type
        self.tick_interval = CONDITION_INTERVALS.get(condition_type, MEDICAL_TICK_INTERVAL)
        
        # Unique identifier for ticker system
        self.ticker_id = None
        
    def start_condition(self, character):
        """Begin ticking condition on character if required."""
        if not self.requires_ticker:
            return
            
        # Create unique ticker ID
        self.ticker_id = f"{character.id}_{self.condition_type}_{id(self)}"
        
        # Start ticker
        TICKER_HANDLER.add(
            interval=self.tick_interval,
            callback=self.tick_callback,
            idstring=self.ticker_id,
            persistent=True
        )
        
    def tick_callback(self, *args, **kwargs):
        """Ticker callback - find character and apply effect."""
        # Get character from ticker ID
        character_id = self.ticker_id.split('_')[0]
        character = self._get_character_by_id(character_id)
        
        if not character:
            self.end_condition(None)  # Character doesn't exist, stop ticker
            return
            
        # Apply tick effect
        self.tick_effect(character)
        
    def tick_effect(self, character):
        """
        Apply condition effect each tick.
        
        This method should be overridden by subclasses.
        Default behavior: increment tick counter and check for resolution.
        """
        self.current_tick += 1
        
        # Check for natural resolution
        if self.should_resolve():
            self.end_condition(character)
            
    def should_resolve(self):
        """Check if condition should end naturally."""
        if not self.auto_resolve:
            return False
        if self.max_duration and self.current_tick >= self.max_duration:
            return True
        if isinstance(self.severity, (int, float)) and self.severity <= 0:
            return True
        return False
        
    def end_condition(self, character):
        """Stop ticking and clean up."""
        if self.ticker_id and self.requires_ticker:
            TICKER_HANDLER.remove(
                interval=self.tick_interval,
                callback=self.tick_callback,
                idstring=self.ticker_id
            )
            
        # Remove from character's conditions
        if character and hasattr(character, 'medical_state'):
            medical_state = character.medical_state
            if self in medical_state.conditions:
                medical_state.conditions.remove(self)
                
    def apply_treatment(self, treatment_quality="adequate"):
        """Apply medical treatment to this condition."""
        self.treated = True
        # Subclasses should override for specific treatment effects
        
    def get_effect_message(self):
        """Get message describing current effect. Override in subclasses."""
        return f"Your {self.condition_type} condition continues."
        
    def _get_character_by_id(self, character_id):
        """Helper to get character object by ID."""
        try:
            from evennia import ObjectDB
            return ObjectDB.objects.get(id=int(character_id))
        except:
            return None
            
    def to_dict(self):
        """Serialize condition for persistence."""
        return {
            "condition_type": self.condition_type,
            "severity": self.severity,
            "location": self.location,
            "current_tick": self.current_tick,
            "treated": self.treated,
            "created_time": self.created_time
        }
        
    @classmethod
    def from_dict(cls, data):
        """Deserialize condition from persistence."""
        condition = cls(
            data["condition_type"],
            data["severity"],
            location=data.get("location"),
            duration=None,  # Will be set by subclass if needed
            requires_ticker=True  # Assume ticker conditions when deserializing
        )
        condition.current_tick = data.get("current_tick", 0)
        condition.treated = data.get("treated", False)
        condition.created_time = data.get("created_time")
        return condition


class BleedingCondition(MedicalCondition):
    """
    Bleeding condition with natural clotting over time.
    
    Severe bleeding (>20 damage): 12-second ticks, requires treatment
    Minor bleeding (10-20 damage): 60-second ticks, stops naturally
    """
    
    def __init__(self, initial_severity, location, decay_rate=1):
        """
        Initialize bleeding condition.
        
        Args:
            initial_severity (int): Initial blood loss per tick
            location (str): Body location bleeding from
            decay_rate (int): How much severity decreases per tick (natural clotting)
        """
        # Determine if severe or minor bleeding
        is_severe = initial_severity >= BLEEDING_DAMAGE_THRESHOLDS["severe"]
        condition_type = "severe_bleeding" if is_severe else "minor_bleeding"
        
        super().__init__(
            condition_type=condition_type,
            severity=initial_severity,
            location=location,
            requires_ticker=True,
            duration=None  # No max duration - stops when severity reaches 0
        )
        
        self.decay_rate = decay_rate
        self.auto_resolve = True
        
        # Severe bleeding doesn't naturally clot as quickly
        if is_severe:
            self.decay_rate = max(1, decay_rate // 2)  # Half decay rate
            
    def tick_effect(self, character):
        """Apply blood loss and natural clotting each tick."""
        if self.severity > 0:
            # Apply blood loss
            blood_loss = self.severity
            if hasattr(character, 'medical_state'):
                character.medical_state.blood_level = max(
                    0.0, 
                    character.medical_state.blood_level - blood_loss
                )
            
            # Natural clotting - decrease bleeding severity
            self.severity = max(0, self.severity - self.decay_rate)
            
        # Check for natural resolution
        super().tick_effect(character)
        
    def apply_treatment(self, treatment_quality="adequate"):
        """Treat bleeding condition."""
        super().apply_treatment(treatment_quality)
        
        if treatment_quality == "poor":
            # Poor treatment reduces bleeding by half
            self.severity = max(1, self.severity // 2)
        elif treatment_quality in ["adequate", "professional", "surgical"]:
            # Good treatment stops bleeding immediately
            self.severity = 0
            
    def get_effect_message(self):
        """Get bleeding effect message."""
        if self.severity >= 8:
            return f"blood flows heavily from your {self.location}"
        elif self.severity >= 4:
            return f"blood seeps from your {self.location}"
        elif self.severity >= 1:
            return f"blood slowly drips from your {self.location}"
        else:
            return f"the bleeding from your {self.location} has stopped"


class BurningCondition(MedicalCondition):
    """
    Fire condition that causes damage over time and can spread.
    
    Ticks every 6 seconds (combat speed) for immediate tactical threat.
    Must be extinguished with treatment - doesn't resolve naturally.
    """
    
    def __init__(self, intensity, spread_chance=0.1):
        """
        Initialize burning condition.
        
        Args:
            intensity (int): Burn damage per tick
            spread_chance (float): Chance per tick for fire to spread/intensify
        """
        super().__init__(
            condition_type="burning",
            severity=intensity,
            requires_ticker=True,
            duration=None
        )
        
        self.spread_chance = spread_chance
        self.auto_resolve = False  # Must be extinguished
        
    def tick_effect(self, character):
        """Apply burn damage and check for spreading."""
        if self.severity > 0:
            # Apply burn damage through medical system
            if hasattr(character, 'medical_state'):
                # Choose random organ/location for burn damage
                medical_state = character.medical_state
                organs = list(medical_state.organs.keys())
                if organs:
                    random_organ = random.choice(organs)
                    medical_state.take_organ_damage(random_organ, self.severity, "burn")
            
            # Chance for fire to spread/intensify
            if random.random() < self.spread_chance:
                self.severity += 1
                
        # Burning doesn't resolve naturally - must be extinguished
        
    def apply_treatment(self, treatment_quality="adequate"):
        """Extinguish fire."""
        super().apply_treatment(treatment_quality)
        # Any treatment extinguishes fire
        self.severity = 0
        
    def get_effect_message(self):
        """Get burning effect message."""
        if self.severity >= 8:
            return "flames engulf your body, searing your flesh"
        elif self.severity >= 4:
            return "fire burns across your skin"
        elif self.severity >= 1:
            return "small flames flicker on your body"
        else:
            return "the flames have been extinguished"


class AcidCondition(MedicalCondition):
    """
    Acid exposure that causes ongoing damage and equipment degradation.
    
    Ticks every 6 seconds (combat speed) for immediate tactical threat.
    Duration-based - acid neutralizes over time.
    """
    
    def __init__(self, concentration, duration_ticks=10):
        """
        Initialize acid condition.
        
        Args:
            concentration (int): Acid damage per tick
            duration_ticks (int): How many ticks before acid neutralizes
        """
        super().__init__(
            condition_type="acid_exposure",
            severity=concentration,
            requires_ticker=True,
            duration=duration_ticks
        )
        
        self.auto_resolve = True  # Neutralizes over time
        
    def tick_effect(self, character):
        """Apply acid damage to character and equipment."""
        if self.severity > 0:
            # Apply acid damage through medical system
            if hasattr(character, 'medical_state'):
                medical_state = character.medical_state
                organs = list(medical_state.organs.keys())
                if organs:
                    # Acid affects external organs more
                    external_organs = [org for org in organs if "skin" in org or "muscle" in org]
                    target_organs = external_organs if external_organs else organs
                    
                    random_organ = random.choice(target_organs)
                    medical_state.take_organ_damage(random_organ, self.severity, "acid")
            
            # TODO: Add equipment damage when equipment system exists
            # for item in character.equipment:
            #     if hasattr(item, 'take_acid_damage'):
            #         item.take_acid_damage(self.severity)
        
        # Continue with normal tick progression
        super().tick_effect(character)
        
    def apply_treatment(self, treatment_quality="adequate"):
        """Neutralize acid."""
        super().apply_treatment(treatment_quality)
        
        if treatment_quality in ["adequate", "professional", "surgical"]:
            # Good treatment neutralizes acid immediately
            self.current_tick = self.max_duration
        else:
            # Poor treatment reduces duration by half
            self.current_tick = min(self.current_tick + self.max_duration // 2, self.max_duration)
            
    def get_effect_message(self):
        """Get acid effect message."""
        if self.severity >= 8:
            return "acid burns through your flesh with a sizzling sound"
        elif self.severity >= 4:
            return "acid eats away at your skin"
        elif self.severity >= 1:
            return "weak acid stings your flesh"
        else:
            return "the acid has been neutralized"


def create_condition_from_damage(damage_amount, injury_type, location):
    """
    Factory function to create appropriate conditions based on damage.
    
    Args:
        damage_amount (int): Amount of damage dealt
        injury_type (str): Type of injury (bullet, burn, acid, etc.)
        location (str): Body location affected
        
    Returns:
        list: List of medical conditions to add
    """
    conditions = []
    
    if injury_type in ["bullet", "stab", "cut"]:
        # Create bleeding condition if damage exceeds threshold
        if damage_amount >= BLEEDING_DAMAGE_THRESHOLDS["minor"]:
            bleeding = BleedingCondition(
                initial_severity=damage_amount // 5,  # 1 blood loss per 5 damage
                location=location
            )
            conditions.append(bleeding)
            
    elif injury_type == "burn":
        # Create burning condition - low initial damage, fire does real damage
        burning = BurningCondition(
            intensity=max(3, damage_amount // 3),  # Ongoing fire damage
            spread_chance=0.1
        )
        conditions.append(burning)
        
    elif injury_type == "acid":
        # Create acid condition - moderate ongoing damage
        acid = AcidCondition(
            concentration=max(2, damage_amount // 4),
            duration_ticks=8  # 48 seconds at combat speed
        )
        conditions.append(acid)
        
    return conditions
