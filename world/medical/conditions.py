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
    from evennia.comms.models import ChannelDB
    from world.combat.constants import SPLATTERCAST_CHANNEL
    
    splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
    splattercast.msg(f"MEDICAL_TICK: Callback triggered for {condition_id}")
    
    if condition_id not in _ACTIVE_CONDITIONS:
        # Condition was removed, stop ticker
        TICKER_HANDLER.remove(
            interval=60,  # Default medical interval
            callback=_condition_tick_callback,
            idstring=f"medical_{condition_id}"
        )
        splattercast.msg(f"MEDICAL_TICK: Condition {condition_id} not in registry, stopping ticker")
        return
        
    condition = _ACTIVE_CONDITIONS[condition_id]
    splattercast.msg(f"MEDICAL_TICK: Found condition {condition.condition_type} severity {condition.severity}")
    
    # Get character from condition ID
    try:
        character_id = condition_id.split('_')[0]
        # Find character by ID
        from evennia.objects.models import ObjectDB
        character = ObjectDB.objects.get(id=int(character_id))
        
        if not character or not hasattr(character, 'medical_state'):
            # Character doesn't exist or has no medical state, stop condition
            splattercast.msg(f"MEDICAL_TICK: Character {character_id} invalid, ending condition")
            condition.end_condition(None)
            return
            
        splattercast.msg(f"MEDICAL_TICK: Applying tick effect to {character.key}")
        # Apply tick effect
        condition.tick_effect(character)
        
    except Exception as e:
        # Error occurred, stop condition
        splattercast.msg(f"MEDICAL_TICK_ERROR: {condition_id}: {e}")
        condition.end_condition(None)

import random
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
        
    @property
    def type(self):
        """Backward compatibility property for condition.type access."""
        return self.condition_type
        
    def start_condition(self, character):
        """Begin ticking condition on character if required."""
        from evennia.comms.models import ChannelDB
        from world.combat.constants import SPLATTERCAST_CHANNEL
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not self.requires_ticker:
            splattercast.msg(f"CONDITION_START: {self.condition_type} for {character.key} doesn't require ticker")
            return
            
        # Create unique ticker ID
        self.ticker_id = f"{character.id}_{self.condition_type}_{id(self)}"
        splattercast.msg(f"CONDITION_START: Starting {self.condition_type} ticker {self.ticker_id} for {character.key}")
        splattercast.msg(f"CONDITION_START: Interval={self.tick_interval}s, Severity={self.severity}")
        
        # Register condition in global registry
        _ACTIVE_CONDITIONS[self.ticker_id] = self
        splattercast.msg(f"CONDITION_START: Registered in global registry, total conditions: {len(_ACTIVE_CONDITIONS)}")
        
        # Start ticker with standalone callback
        TICKER_HANDLER.add(
            interval=self.tick_interval,
            callback=_condition_tick_callback,
            idstring=f"medical_{self.ticker_id}",
            persistent=True,
            *[self.ticker_id]  # callback args
        )
        splattercast.msg(f"CONDITION_START: Ticker added to TICKER_HANDLER for {self.ticker_id}")
        
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
            TICKER_HANDLER.remove(
                interval=self.tick_interval,
                callback=_condition_tick_callback,
                idstring=f"medical_{self.ticker_id}"
            )
            self.ticker_id = None
            
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
        
    def get_pain_contribution(self):
        """
        Calculate how much pain this condition contributes.
        
        Returns:
            float: Pain points contributed by this condition
        """
        # Basic pain mapping - to be expanded with constants
        pain_map = {
            "bleeding": {"minor": 2, "moderate": 5, "severe": 10, "critical": 20},
            "burning": {"minor": 8, "moderate": 15, "severe": 30, "critical": 50},
            "acid_exposure": {"minor": 6, "moderate": 12, "severe": 25, "critical": 45},
            "fracture": {"minor": 5, "moderate": 12, "severe": 25, "critical": 40},
            "infection": {"minor": 3, "moderate": 8, "severe": 15, "critical": 30}
        }
        
        # Map numeric severity to pain levels
        if isinstance(self.severity, (int, float)):
            if self.severity >= 20:
                severity_level = "critical"
            elif self.severity >= 10:
                severity_level = "severe"
            elif self.severity >= 5:
                severity_level = "moderate"
            else:
                severity_level = "minor"
        else:
            # String severity
            severity_level = str(self.severity).lower()
        
        return pain_map.get(self.condition_type, {}).get(severity_level, 0)
        
    def get_blood_loss_rate(self):
        """
        Calculate blood loss per round for bleeding conditions.
        
        Returns:
            float: Blood percentage lost per round
        """
        if self.condition_type != "bleeding":
            return 0.0
            
        # Map severity to blood loss rates
        if isinstance(self.severity, (int, float)):
            # Numeric severity - direct percentage
            return max(0.0, float(self.severity) * 0.5)  # 0.5% per severity point
        else:
            # String severity levels
            bleeding_rates = {
                "minor": 1.0,
                "moderate": 3.0,
                "severe": 6.0,
                "critical": 12.0
            }
            return bleeding_rates.get(str(self.severity).lower(), 0.0)
            
    def is_bleeding(self):
        """Returns True if this condition causes bleeding."""
        return self.condition_type == "bleeding"
            
    def stop_condition(self):
        """Alias for end_condition for compatibility."""
        self.end_condition(None)
        
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
        from evennia.comms.models import ChannelDB
        from world.combat.constants import SPLATTERCAST_CHANNEL
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"BLEEDING_TICK: {character.key} {self.location} severity {self.severity}")
        
        if self.severity > 0:
            # Apply blood loss
            blood_loss = self.severity
            if hasattr(character, 'medical_state'):
                old_blood = character.medical_state.blood_level
                character.medical_state.blood_level = max(
                    0.0, 
                    character.medical_state.blood_level - blood_loss
                )
                new_blood = character.medical_state.blood_level
                splattercast.msg(f"BLOOD_LOSS: {character.key} lost {blood_loss}%, {old_blood:.1f}% -> {new_blood:.1f}%")
            
            # Natural clotting - decrease bleeding severity
            old_severity = self.severity
            self.severity = max(0, self.severity - self.decay_rate)
            splattercast.msg(f"CLOTTING: {character.key} {self.location} severity {old_severity} -> {self.severity}")
            
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
