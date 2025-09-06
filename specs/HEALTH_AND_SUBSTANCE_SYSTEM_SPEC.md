# Health and Substance System Specification

## Overview

The Gelatinous Monster health and substance system creates tactical medical gameplay that emphasizes realistic injury consequences and meaningful substance interaction choices through detailed anatomical damage modeling, field medical tools, and comprehensive consumption methods.

## Design Philosophy

### Core Principles
- **Anatomical Realism**: Injuries affect specific body parts and organs with logical consequences
- **Tactical Medicine**: Medical tools have specific purposes and limited effectiveness  
- **Consequence-Driven**: Injuries create meaningful gameplay effects, not just HP reduction
- **Resource Management**: Medical supplies are valuable and consumable
- **Skill-Based**: Medical treatment success depends on character abilities

### Integration with Existing Systems
- **Longdesc System**: Medical conditions visible in character descriptions
- **Combat System**: Damage targeting specific anatomical locations
- **G.R.I.M. Stats**: Medical skill primarily based on Intellect (3/4 weight), with Motorics for surgical precision (1/4 weight)
- **Clothing System**: Armor/clothing affects injury locations and severity

## CONFIGURATION CONSTANTS

*All numerical values use constants for easy balance modification during implementation:*

```python
# Death/Unconsciousness Thresholds  
BLOOD_LOSS_DEATH_THRESHOLD = 85        # Placeholder - needs balancing
CONSCIOUSNESS_UNCONSCIOUS_THRESHOLD = 30  # Placeholder - needs balancing

# Hit Weight Distribution (combat handler integration)
HIT_WEIGHT_VERY_RARE = 2              # Brain, spinal cord
HIT_WEIGHT_RARE = 8                   # Eyes, ears, jaw, neck  
HIT_WEIGHT_UNCOMMON = 15              # Heart, lungs, organs, hands
HIT_WEIGHT_COMMON = 25                # Arms, legs, major limbs

# Pain/Consciousness Modifiers
PAIN_UNCONSCIOUS_THRESHOLD = 80       # High pain causes unconsciousness
PAIN_CONSCIOUSNESS_MODIFIER = 0.5     # How much pain affects consciousness

# Treatment Success Modifiers  
BASE_TREATMENT_SUCCESS = 50           # Base % before stat modifiers
STAT_MODIFIER_SCALING = 5             # Points per stat level
TOOL_EFFECTIVENESS_SCALING = 10       # Effectiveness points per tool quality

# Medical Resource Constants
BANDAGE_EFFECTIVENESS = 15            # HP healed per bandage
SURGERY_BASE_DIFFICULTY = 75          # Base difficulty for surgery
INFECTION_CHANCE_BASE = 10            # Base infection chance %

# Medical Treatment Success Constants (Added for Phase 2)
MEDICAL_TREATMENT_BASE_DIFFICULTY = 12  # Base d20 target for medical treatments
PARTIAL_SUCCESS_MARGIN = 3            # How close to success counts as partial
TOOL_EFFECTIVENESS_MODIFIERS = {      # Modifier table - tool appropriateness
    # Example: {"blood_bag": {"bleeding": -2, "fracture": +5}, ...}
    # Negative = easier, Positive = harder
    "placeholder": "to_be_defined_in_phase_2"
}
```

*NOTE: All values are speculative/unbalanced - constants make modification easy*

## Current Health System Foundation

### Existing Components
```python
# LEGACY HP SYSTEM - TO BE REPLACED
# Characters currently have (will be deprecated):
hp = AttributeProperty(10, category='health')
hp_max = AttributeProperty(10, category='health') 
hp_max = 10 + (grit * 2)  # Dynamic max HP based on Grit

# Death mechanics (will be replaced by vital system failure):
def is_dead(self): return self.hp <= 0
def take_damage(self, amount): # Basic damage application
def apply_damage(character, damage_amount): # Combat integration

# NEW SYSTEM: Character health determined by anatomical/organ integrity
# Death occurs when vital systems (consciousness, blood_pumping, breathing) fail
```

### Anatomical Foundation (Dynamic Integration)
```python
# UNIFIED ANATOMY SYSTEM DESIGN:
# 1. Character typeclasses define both longdesc anatomy AND organ mappings
# 2. Medical system adapts to whatever anatomy exists on character
# 3. Creature-type templates provide standard organ-to-location mappings
# 4. NO FALLBACK RULES - all organ-to-location mappings must be explicit per typeclass
# 5. UNIVERSAL INJURY TYPES - fractures, bleeding, infections work on any anatomy

# CROSS-SPECIES FRACTURE COMPATIBILITY:
# - Human: left_arm, right_arm, left_leg, right_leg can be fractured
# - Tentacle Monster: tentacle_1, tentacle_2, tentacle_3, tentacle_4 can be fractured  
# - Spider Creature: leg_1, leg_2, leg_3, leg_4, leg_5, leg_6, leg_7, leg_8 can be fractured
# Same splint mechanics work universally across all appendage types

# Example: Human character (default)
DEFAULT_LONGDESC_LOCATIONS = {
    "head": None, "face": None, "left_eye": None, "right_eye": None,
    "chest": None, "back": None, "abdomen": None, "groin": None,
    "left_arm": None, "right_arm": None, "left_hand": None, "right_hand": None,
    "left_thigh": None, "right_thigh": None, "left_shin": None, "right_shin": None,
    "left_foot": None, "right_foot": None
}

# Example: Tentacle monster character 
TENTACLE_MONSTER_LOCATIONS = {
    "core_mass": None, "feeding_maw": None, "sensory_cluster": None,
    "tentacle_1": None, "tentacle_2": None, "tentacle_3": None, "tentacle_4": None
}

# Organ mapping defined per character type via creature templates
```

## Medical System Architecture

### Organ/Subsystem Model

#### Core Subsystems
```python
BODY_CAPACITIES = {
    # Vital Capacities - Loss causes death or unconsciousness
    "consciousness": {
        "organs": ["brain"],
        "modifiers": ["pain", "blood_pumping", "breathing", "blood_filtration"],
        "unconscious_threshold": CONSCIOUSNESS_UNCONSCIOUS_THRESHOLD,  # Flag: is_unconscious = True
        "effect": "unconscious_flag",  # Treated as flag for now
        "description": "Difference between functioning PC and unconscious state"
    },
    "blood_pumping": {
        "organs": ["heart"],
        "fatal_threshold": 0.0,
        "directly_fatal": True,
        "affects": ["consciousness", "moving"],
        "description": "Circulation of blood through body - zero equals death"
    },
    "breathing": {
        "organs": ["left_lung", "right_lung"],
        "fatal_threshold": 0.0,  # Death if both lungs lost
        "organ_contribution": 0.5,  # Each lung contributes 50%
        "affects": ["consciousness", "moving"]
    },
    "digestion": {
        "organs": ["liver", "stomach"],
        "liver_contribution": 1.0,   # Liver is primary, stomach is 50%
        "stomach_contribution": 0.5,
        "fatal_threshold": 0.0  # Death if liver lost
    },
    
    # Blood Loss System
    "blood_loss": {
        "source": "bleeding_injuries",
        "fatal_threshold": BLOOD_LOSS_DEATH_THRESHOLD,
        "directly_fatal": True,
        "description": "Blood loss kills - exact threshold uses constants"
    },
    
    # Functional Capacities - Loss reduces effectiveness but not fatal
    "sight": {
        "organs": ["left_eye", "right_eye"],
        "organ_contribution": 0.5,  # Each eye contributes 50% 
        "affects": ["shooting_accuracy", "melee_hit_chance", "work_speed"],
        "total_loss_penalty": "blindness"
    },
    "hearing": {
        "organs": ["left_ear", "right_ear"],
        "organ_contribution": 0.5,
        "affects": ["trade_price_improvement"],
        "total_loss_penalty": "deafness"
    },
    "moving": {
        "organs": ["spine", "pelvis", "left_leg", "right_leg", "left_foot", "right_foot"],
        "spine_contribution": 1.0,    # Spine damage = paralysis
        "pelvis_contribution": 1.0,   # Essential for walking
        "leg_contribution": 0.5,      # Each leg contributes 50%
        "foot_contribution": 0.04,    # Each foot contributes 4%
        "incapacitation_threshold": 0.15,  # Below 15% = cannot move
        "affects": ["movement_speed"]
    },
    "manipulation": {
        "organs": ["left_shoulder", "right_shoulder", "left_arm", "right_arm", 
                  "left_hand", "right_hand", "fingers"],
        "shoulder_contribution": "major",     # Each shoulder = major contribution
        "arm_contribution": "major",          # Each arm = major contribution 
        "hand_contribution": "moderate",      # Each hand = moderate contribution
        "finger_contribution": "minor",       # Each finger = minor contribution
        "affects": ["work_speed", "melee_accuracy"]
        # NOTE: Exact percentages to be calculated during implementation
    },
    "talking": {
        "organs": ["jaw", "tongue"],
        "affects": ["social_impact"],
        "total_loss_effects": ["cannot_negotiate", "social_penalty"]
    },
    "eating": {
        "organs": ["jaw", "tongue"],
        "jaw_primary": True,
        "affects": ["nutrition_efficiency"]
    },
    "blood_filtration": {
        "organs": ["left_kidney", "right_kidney"],
        "organ_contribution": 0.5,  # Each kidney contributes 50%
        "affects": ["disease_resistance", "consciousness"],
        "total_loss_fatal": True
    }
}
```

#### Individual Organs
```python
# NOTE: Hit chances use relative descriptors - exact percentages to be balanced during implementation
# HIT CHANCE DESCRIPTORS: 
#   very_rare = <1%, rare = 1-3%, uncommon = 3-10%, common = 10%+, guaranteed = always hit
# CONTRIBUTION DESCRIPTORS:
#   total = 100%, major = 40-60%, moderate = 10-40%, minor = 1-10%
# IMPLEMENTATION NOTE: Full organ property complexity maintained - review template before implementation
# HIERARCHY SYSTEM: Hit containers (body locations) → damage redirects to contents (organs/systems)
# EXAMPLE: Hit chest → damage goes to heart/lungs, hit head → damage goes to brain/eyes

ORGANS = {
    # HEAD CONTAINER → ORGANS INSIDE
    "brain": {
        "container": "head", "max_hp": 10, "hit_weight": "very_rare",
        "vital": True, "capacity": "consciousness", "contribution": "total",
        "special": "damage_always_scars", "can_scar": True, "can_heal": False
    },
    "left_eye": {
        "container": "head", "max_hp": 10, "hit_weight": "rare",
        "capacity": "sight", "contribution": "major", "disfiguring_if_lost": True,
        "damage_always_scars": True, "vulnerable_to_blunt": False
    },
    "right_eye": {
        "container": "head", "max_hp": 10, "hit_weight": "rare",
        "capacity": "sight", "contribution": "major", "disfiguring_if_lost": True,
        "damage_always_scars": True, "vulnerable_to_blunt": False
    },
    "left_ear": {
        "container": "head", "max_hp": 12, "hit_weight": "rare",
        "capacity": "hearing", "contribution": "major", "disfiguring_if_lost": True
    },
    "right_ear": {
        "container": "head", "max_hp": 12, "hit_weight": "rare",
        "capacity": "hearing", "contribution": "major", "disfiguring_if_lost": True
    },
    "tongue": {
        "container": "head", "max_hp": 20, "hit_weight": "rare",
        "capacities": ["talking", "eating"], "talking_contribution": "major",
        "eating_contribution": "major", "disfiguring_if_lost": True
    },
    "jaw": {
        "container": "head", "max_hp": 10, "hit_weight": "very_rare",
        "capacities": ["talking", "eating"], "talking_contribution": "major",
        "eating_contribution": "moderate", "disfiguring_if_lost": True, "can_scar": False
    },

    # CHEST CONTAINER → VITAL ORGANS INSIDE  
    "heart": {
        "container": "chest", "max_hp": 15, "hit_weight": "uncommon",
        "vital": True, "capacity": "blood_pumping", "contribution": "total",
        "can_be_harvested": True, "can_be_replaced": True
    },
    "left_lung": {
        "container": "chest", "max_hp": 20, "hit_weight": "uncommon",
        "capacity": "breathing", "contribution": "major", "can_be_harvested": False,
        "backup_available": True  # Can survive with one lung
    },
    "right_lung": {
        "container": "chest", "max_hp": 20, "hit_weight": "uncommon",
        "capacity": "breathing", "contribution": "major", "can_be_harvested": False,
        "backup_available": True
    },

    # ABDOMEN CONTAINER → DIGESTIVE/FILTER ORGANS INSIDE
    "liver": {
        "container": "abdomen", "max_hp": 20, "hit_weight": "uncommon",
        "vital": True, "capacity": "digestion", "contribution": "total",
        "can_be_harvested": True, "can_be_replaced": True
    },
    "left_kidney": {
        "container": "abdomen", "max_hp": 15, "hit_weight": "uncommon",
        "capacity": "blood_filtration", "contribution": "major",
        "can_be_harvested": True, "backup_available": True
    },
    "right_kidney": {
        "container": "abdomen", "max_hp": 15, "hit_weight": "uncommon",
        "capacity": "blood_filtration", "contribution": "major",
        "can_be_harvested": True, "backup_available": True
    },
    "stomach": {
        "container": "abdomen", "max_hp": 20, "hit_weight": "uncommon",
        "capacity": "digestion", "contribution": "moderate", "vital": False,
        "can_survive_loss": True
    },

    # BACK CONTAINER → STRUCTURAL ORGANS INSIDE
    "spine": {
        "container": "back", "max_hp": 25, "hit_weight": "uncommon",
        "capacity": "moving", "contribution": "total", "cannot_be_destroyed": True,
        "causes_pain_when_damaged": True, "paralysis_if_destroyed": True
    },

    # ARM CONTAINERS → MANIPULATION ORGANS INSIDE
    "left_arm_system": {
        "container": "left_arm", "max_hp": 30, "hit_weight": "common",
        "capacity": "manipulation", "contribution": "major", "can_be_destroyed": True
    },
    "right_arm_system": {
        "container": "right_arm", "max_hp": 30, "hit_weight": "common",
        "capacity": "manipulation", "contribution": "major", "can_be_destroyed": True
    },

    # HAND CONTAINERS → FINE MANIPULATION ORGANS INSIDE
    "left_hand_system": {
        "container": "left_hand", "max_hp": 20, "hit_weight": "uncommon",
        "capacity": "manipulation", "contribution": "moderate", "can_be_destroyed": True
    },
    "right_hand_system": {
        "container": "right_hand", "max_hp": 20, "hit_weight": "uncommon",
        "capacity": "manipulation", "contribution": "moderate", "can_be_destroyed": True
    },

    # LEG CONTAINERS → MOVEMENT ORGANS INSIDE
    "left_leg_system": {
        "container": "left_thigh", "max_hp": 30, "hit_weight": "common",
        "capacity": "moving", "contribution": "major", "can_be_destroyed": True
    },
    "right_leg_system": {
        "container": "right_thigh", "max_hp": 30, "hit_weight": "common", 
        "capacity": "moving", "contribution": "major", "can_be_destroyed": True
    },

    # FOOT CONTAINERS → BALANCE/MOBILITY ORGANS INSIDE
    "left_foot_system": {
        "container": "left_foot", "max_hp": 25, "hit_weight": "uncommon",
        "capacity": "moving", "contribution": "minor", "can_be_destroyed": True
    },
    "right_foot_system": {
        "container": "right_foot", "max_hp": 25, "hit_weight": "uncommon",
        "capacity": "moving", "contribution": "minor", "can_be_destroyed": True
    }
```

## CORE MECHANICS CLARIFICATION

### Organ Damage System
- **Organs have HP**: Each organ has max_hp (see ORGANS definition above)  
- **Damage reduces HP**: Incoming damage reduces current HP from max_hp
- **Destruction at 0 HP**: When organ HP reaches 0, organ is destroyed/non-functional
- **Death conditions**: Destruction of vital organs (heart, both lungs, liver) = death
- **Paired organ logic**: Both kidneys/lungs destroyed = death, single destruction = reduced function

### Hit Distribution Formula  
*NOTE: Formula will be based on attack roll/success from combat handler*
```python
# Hit weight distribution (placeholder - needs combat handler integration)
HIT_WEIGHTS = {
    "very_rare": HIT_WEIGHT_VERY_RARE,      # Brain, spinal cord - use constants
    "rare": HIT_WEIGHT_RARE,                # Eyes, ears, jaw, neck
    "uncommon": HIT_WEIGHT_UNCOMMON,        # Heart, lungs, organs, hands
    "common": HIT_WEIGHT_COMMON             # Arms, legs, major limbs
}
```

### Death vs Unconsciousness vs Functionality
- **Blood loss kills**: Tracked separately, reaches fatal threshold = death
- **Blood pumping = 0**: Death (heart destroyed/stopped)
- **Consciousness**: Flag system (is_unconscious = True/False), not death
- **Functionality**: Reduced stats/capabilities, but character remains conscious

### Constants for Balance
*All numerical thresholds use constants for easy modification:*
- CONSCIOUSNESS_UNCONSCIOUS_THRESHOLD  
- BLOOD_LOSS_DEATH_THRESHOLD
- HIT_WEIGHT_* values
- PAIN_MODIFIER_*
- All treatment success rates and failure penalties

### Medical Conditions

#### Injury Types
```python
# NOTE: All injury complexity implemented as values - exact mechanics to be balanced during implementation
INJURY_TYPES = {
    "cut": {
        "pain_per_damage": "low",
        "bleed_rate": "moderate", 
        "infection_chance": "low",
        "scar_chance": "low",
        "healing_time": "moderate",
        "treatment_difficulty": "easy",
        "description": "Clean cuts from blades or sharp objects"
    },
    "burn": {
        "pain_per_damage": "high",
        "bleed_rate": "minimal",
        "infection_chance": "high", 
        "scar_chance": "high",
        "healing_time": "slow",
        "treatment_difficulty": "moderate",
        "permanent_damage_chance": "moderate",
        "description": "Fire, heat, or chemical burns"
    },
    "blunt": {
        "pain_per_damage": "moderate",
        "bleed_rate": "minimal",
        "fracture_chance": "moderate",
        "internal_damage_chance": "high",
        "healing_time": "slow",
        "treatment_difficulty": "easy",
        "description": "Crushing, impact, or bludgeoning damage"
    },
    "bullet": {
        "pain_per_damage": "moderate", 
        "bleed_rate": "severe",
        "penetration_chance": "high",
        "fragmentation_chance": "low",
        "infection_chance": "moderate",
        "healing_time": "slow",
        "treatment_difficulty": "hard",
        "description": "Projectile wounds from firearms"
    },
    "stab": {
        "pain_per_damage": "low",
        "bleed_rate": "severe",
        "organ_damage_chance": "high",
        "infection_chance": "moderate", 
        "healing_time": "moderate",
        "treatment_difficulty": "moderate",
        "description": "Deep puncture wounds from thrusting weapons"
    },
    "laceration": {
        "pain_per_damage": "high",
        "bleed_rate": "high",
        "infection_chance": "high",
        "scar_chance": "very_high", 
        "healing_time": "slow",
        "treatment_difficulty": "hard",
        "description": "Ragged tears from claws, shrapnel, or serrated weapons"
    },
    "frostbite": {
        "pain_per_damage": "very_high",
        "bleed_rate": "none",
        "infection_chance": "high",
        "permanent_damage_chance": "high",
        "healing_time": "very_slow",
        "treatment_difficulty": "hard", 
        "amputation_risk": "moderate",
        "description": "Cold damage causing tissue death"
    }
}
```

#### Pain System
```python
# NOTE: Pain system uses descriptive thresholds - exact formulas to be balanced during implementation
PAIN_SYSTEM = {
    "calculation": {
        "base_formula": "sum(injury_severity * pain_per_damage_rating)",
        "creature_size_modifier": True,    # Large creatures have reduced pain sensitivity
        "pain_tolerance_modifier": True,   # Drug effects, traits, training modify pain
        "adrenaline_modifier": True        # Combat/stress can temporarily reduce pain
    },
    
    "pain_levels": {
        # Descriptive pain levels with gameplay effects
        "none": {
            "threshold": "0%", "mood_penalty": 0, "consciousness_penalty": "none",
            "description": "no discomfort", "gameplay_effects": []
        },
        "minor": {
            "threshold": "1-10%", "mood_penalty": "slight", "consciousness_penalty": "none", 
            "description": "a little discomfort", "gameplay_effects": []
        },
        "moderate": {
            "threshold": "10-25%", "mood_penalty": "noticeable", "consciousness_penalty": "minimal",
            "description": "distracting pain", "gameplay_effects": ["concentration_penalty"]
        },
        "severe": {
            "threshold": "25-50%", "mood_penalty": "significant", "consciousness_penalty": "moderate",
            "description": "intense pain", "gameplay_effects": ["action_penalties", "focus_loss"]
        },
        "extreme": {
            "threshold": "50-80%", "mood_penalty": "major", "consciousness_penalty": "severe", 
            "description": "excruciating agony", "gameplay_effects": ["severe_penalties", "periodic_stunning"]
        },
        "unbearable": {
            "threshold": "80%+", "mood_penalty": "overwhelming", "consciousness_penalty": "critical",
            "description": "mind-shattering torture", "gameplay_effects": ["unconsciousness_risk", "shock"]
        }
    },
    
    "consciousness_interaction": {
        # Consciousness is single value affected by multiple factors
        "pain_contribution": "moderate_to_severe",     # Pain reduces consciousness
        "blood_loss_contribution": "severe",           # Blood loss majorly reduces consciousness  
        "organ_damage_contribution": "varies_by_organ", # Brain damage = direct consciousness loss
        "cumulative_effects": True,                    # All factors stack
        "unconscious_threshold": "30% consciousness",
        "death_threshold": "0% consciousness"
    }
}
```

#### Blood System
```python
BLOOD_SYSTEM = {
    "blood_as_resource": {
        "tracked_like_pain": True,
        "max_blood": "100% (varies by creature size)",
        "current_blood": "percentage of maximum", 
        "blood_loss_per_round": "sum of all bleeding wounds",
        "consciousness_impact": "severe at <60% blood"
    },
    
    "blood_loss_effects": {
        "90-100%": {"status": "healthy", "consciousness_penalty": "none"},
        "70-90%": {"status": "light_blood_loss", "consciousness_penalty": "minimal"},
        "50-70%": {"status": "moderate_blood_loss", "consciousness_penalty": "moderate"},
        "30-50%": {"status": "severe_blood_loss", "consciousness_penalty": "major"},
        "10-30%": {"status": "critical_blood_loss", "consciousness_penalty": "severe"},
        "0-10%": {"status": "exsanguination", "consciousness_penalty": "unconscious"}
    }
}
```

#### Status Effects (Medical Conditions)
```python
MEDICAL_CONDITIONS = {
    "bleeding": {
        "description": "Contributes to blood loss per round - multiple wounds stack",
        "severity_levels": {
            "minor": {"blood_loss_per_round": "1%", "visible": "small bloodstains"},
            "moderate": {"blood_loss_per_round": "3%", "visible": "steady bleeding"}, 
            "severe": {"blood_loss_per_round": "8%", "visible": "heavy blood loss"},
            "arterial": {"blood_loss_per_round": "15%", "visible": "spurting blood"}
        },
        "stacking": "multiple_wounds_add_blood_loss",
        "treatments": {
            "basic_bandage": {"success_rate": "moderate", "requirements": ["bandage"], "stops": ["minor", "moderate"]},
            "surgical_kit": {"success_rate": "high", "requirements": ["surgical_kit", "medical_skill"], "stops": ["all_levels"]},
            "blood_bag": {"success_rate": "guaranteed", "requirements": ["blood_bag"], "restores": "blood_volume"}
        },
        "progression": "stable_until_treated"
    },
    "infection": {
        "description": "Develops over time from untreated wounds",
        "severity_levels": {
            "minor": {"pain_increase": "slight", "healing_slowdown": "moderate"},
            "major": {"pain_increase": "significant", "system_effects": "fever_weakness"}
        },
        "treatments": {
            "basic_cleaning": {"success_rate": "moderate", "requirements": ["basic_supplies"], "stat_requirement": "intellect_1"},
            "surgical_kit": {"success_rate": "high", "requirements": ["surgical_kit"], "stat_requirement": "intellect_2_motorics_1"}
        },
        "failure_consequences": "chronic_infection_permanent_pain"
    },
    
    "fracture": {
        "description": "Universal injury type - can affect any appendage regardless of species",
        "affected_anatomy": "any_moveable_appendage",  # arms, legs, tentacles, wings, tails, etc.
        "effects": {
            "appendage_unusable": True,
            "constant_pain": "moderate", 
            "movement_impaired": "if_locomotion_appendage"
        },
        "examples": {
            "human": "left_arm_fractured, right_leg_fractured",
            "tentacle_monster": "tentacle_2_fractured, tentacle_5_fractured",
            "spider": "leg_3_fractured, leg_7_fractured"
        },
        "treatments": {
            "splint": {"success_rate": "moderate", "requirements": ["splint"], "stat_requirement": "intellect_1"},
            "surgical_kit": {"success_rate": "high", "requirements": ["surgical_kit"], "stat_requirement": "intellect_3_motorics_2"}
        },
        "failure_consequences": "permanent_reduced_function_chronic_pain"
    }
            "spreading": {"pain": 0.08, "fever": True, "stat_penalties": {"grit": -1}},
            "systemic": {"pain": 0.15, "sepsis_risk": 0.20, "stat_penalties": {"all": -2}}
        },
        "treatments": ["surgical_kit", "disinfectant", "antibiotics"],
        "environmental_factors": ["cleanliness", "humidity", "wound_care"],
        "mortality_risk": {"localized": 0.0, "spreading": 0.05, "systemic": 0.25}
    }
}
```

## Field Medical Tools

### Medical Equipment

#### Blood Bag
```python
BLOOD_BAG = {
    "name": "Blood Bag",
    "uses": 1,
    "time_to_use": "3 rounds",
    "effects": {
        "restores_blood": "25% of maximum",
        "stops_bleeding": "minor_to_moderate",
        "reduces_shock": True
    },
    "stat_requirement": "intellect >= 2",  # Basic medical knowledge needed
    "success_formula": "(intellect * 0.75) + (motorics * 0.25)",
    "failure_consequences": "infection_risk_scar_tissue",
    "description": "Emergency blood transfusion kit"
}
```

#### Painkiller
```python
PAINKILLER = {
    "name": "Painkiller",
    "uses": 1,
    "time_to_use": "1 round",
    "effects": {
        "reduces_pain": "significant_temporary",
        "temporary_stat_boost": {"grit": +1},
        "duration": "10 rounds"
    },
    "side_effects": "dulled_awareness_after_effect",
    "stat_requirement": None,  # Anyone can inject
    "failure_consequences": "overdose_risk_addiction_chance",
    "description": "Military-grade analgesic injection"
}
```

#### Gauze/Bandages
```python
GAUZE = {
    "name": "Gauze Bandages",
    "uses": 3,  # Multiple applications
    "time_to_use": "2 rounds",
    "effects": {
        "stops_bleeding": "minor_to_moderate",
        "prevents_infection": "basic_protection",
        "stabilizes_wounds": True
    },
    "stat_requirement": "intellect >= 1",  # Basic first aid knowledge
    "success_formula": "(intellect * 0.75) + (motorics * 0.25)",
    "failure_consequences": "incomplete_bleeding_control_infection_risk",
    "description": "Sterile bandages and gauze pads for wound care"
}
```

#### Splint
```python
SPLINT = {
    "name": "Splint",
    "uses": 1,
    "time_to_use": "2 rounds", 
    "effects": {
        "stabilizes_fractures": True,
        "restores_partial_function": "50%_of_normal",
        "prevents_further_damage": True,
        "reduces_pain": "moderate"
    },
    "targets": "any_fractured_appendage",  # Universal - works on arms, legs, tentacles, wings, etc.
    "cross_species_examples": {
        "human": "left_arm, right_leg, left_hand",
        "tentacle_monster": "tentacle_1, tentacle_3, tentacle_7", 
        "spider": "leg_2, leg_5, leg_8",
        "winged_creature": "left_wing, right_wing"
    },
    "stat_requirement": "intellect >= 1",
    "success_formula": "(intellect * 0.75) + (motorics * 0.25)",
    "failure_consequences": "improper_healing_permanent_reduced_function",
    "description": "Universal immobilization device - adapts to any appendage type"
}
```

#### Surgical Kit
```python
SURGICAL_KIT = {
    "name": "Surgical Kit", 
    "uses": 3,  # Multiple procedures
    "time_to_use": "5 rounds",  # Lengthy procedure
    "effects": {
        "repairs_organs": True,
        "stops_internal_bleeding": True,
        "removes_foreign_objects": True,
        "restores_function": 0.8  # 80% restoration
    },
    "stat_requirement": "intellect >= 4",  # High stat needed
    "failure_effects": ["organ_damage", "massive_bleeding", "death"],
    "success_modifiers": {
        "sterile_environment": +2,
        "assistant_present": +1,
        "time_pressure": -3
    },
    "description": "Portable surgical suite with micro-instruments and nano-sutures"
}
```

## Consumption Method System

### Overview
The medical system serves as the foundation for a broader consumable substance system that encompasses both medical treatments and recreational substances. All consumable items utilize natural language commands that reflect realistic delivery methods.

### Core Philosophy
- **Realistic Delivery Methods**: Commands reflect how substances are actually consumed in reality
- **Universal System**: Medical items, drugs, and other consumables use the same underlying mechanics
- **Self-Administration & Third-Party**: Items can be used on oneself or administered to others
- **Natural Language**: Commands use familiar terminology (inject, apply, eat, drink, smoke, inhale, etc.)

### Consumption Commands

#### Primary Consumption Methods
```python
CONSUMPTION_METHODS = {
    # Injectable substances
    "inject": {
        "aliases": ["inject", "shot", "jab"],
        "self_syntax": "inject <item>",
        "other_syntax": "inject <item> <target>",
        "examples": ["inject painkiller", "inject stimpak Alice"],
        "time_required": "1-2 rounds",
        "stat_requirements": "varies by substance",
        "applicable_to": ["painkillers", "stimpaks", "adrenal boosters", "toxins", "vaccines"]
    },
    
    # Topical applications
    "apply": {
        "aliases": ["apply", "rub", "spread"],
        "self_syntax": "apply <item>",
        "other_syntax": "apply <item> to <target>",
        "examples": ["apply burn gel", "apply antiseptic to Bob's wound"],
        "time_required": "1-3 rounds",
        "stat_requirements": "basic motorics for precise application",
        "applicable_to": ["burn gel", "antiseptic", "healing salves", "contact toxins", "medicated patches"]
    },
    
    # Oral consumption - solids
    "eat": {
        "aliases": ["eat", "consume", "swallow"],
        "self_syntax": "eat <item>",
        "other_syntax": "feed <item> to <target>",
        "examples": ["eat ration bar", "feed medicine to Charlie"],
        "time_required": "1 round",
        "stat_requirements": None,
        "applicable_to": ["pills", "tablets", "food", "edible drugs", "emergency rations"]
    },
    
    # Oral consumption - liquids
    "drink": {
        "aliases": ["drink", "sip", "gulp"],
        "self_syntax": "drink <item>",
        "other_syntax": "give <item> to <target> to drink",
        "examples": ["drink medical brew", "give water to Dana"],
        "time_required": "1 round",
        "stat_requirements": None,
        "applicable_to": ["liquid medicines", "water", "alcohol", "liquid drugs", "nutritional drinks"]
    },
    
    # Inhalation methods
    "inhale": {
        "aliases": ["inhale", "huff", "breathe"],
        "self_syntax": "inhale <item>",
        "other_syntax": "help <target> inhale <item>",
        "examples": ["inhale oxygen", "inhale anesthetic gas"],
        "time_required": "1-2 rounds",
        "stat_requirements": "conscious target required",
        "applicable_to": ["inhalers", "oxygen tanks", "anesthetic gases", "vaporized drugs"]
    },
    
    # Smoking/burning consumption
    "smoke": {
        "aliases": ["smoke", "light", "burn"],
        "self_syntax": "smoke <item>",
        "other_syntax": "help <target> smoke <item>",
        "examples": ["smoke medicinal herb", "smoke pain-relief cigarette"],
        "time_required": "3-5 rounds",
        "stat_requirements": "fire source required",
        "applicable_to": ["medicinal herbs", "cigarettes", "pipes", "combustible drugs"]
    }
}
```

#### Special Consumption Cases
```python
SPECIAL_CONSUMPTION_METHODS = {
    # Suppository/rectal administration (boof)
    "boof": {
        "aliases": ["boof", "insert"],
        "self_syntax": "boof <item>",
        "other_syntax": "administer <item> to <target>",
        "examples": ["boof suppository", "administer rectal medication to patient"],
        "time_required": "2-3 rounds",
        "stat_requirements": "medical knowledge for third-party administration",
        "applicable_to": ["suppositories", "rectal medications", "emergency drugs"],
        "privacy_considerations": "requires consent for third-party administration"
    },
    
    # Combination methods
    "bandage": {
        "aliases": ["bandage", "wrap", "dress"],
        "self_syntax": "bandage <body_part> with <item>",
        "other_syntax": "bandage <target>'s <body_part> with <item>",
        "examples": ["bandage arm with gauze", "bandage Alice's leg with medicated bandage"],
        "time_required": "2-3 rounds",
        "stat_requirements": "basic first aid knowledge",
        "applicable_to": ["gauze", "bandages", "medicated wraps", "splints"]
    }
}
```

### Administration Mechanics

#### Self-Administration vs Third-Party
```python
def administer_substance(administrator, target, substance, method):
    """
    Universal substance administration system.
    Handles both self-administration and third-party scenarios.
    """
    is_self_admin = (administrator == target)
    
    # Base requirements
    base_requirements = substance.consumption_requirements
    method_modifiers = CONSUMPTION_METHODS[method]
    
    if is_self_admin:
        # Self-administration: simpler, faster, more private
        difficulty_modifier = 0
        time_modifier = 1.0
        consent_required = False
    else:
        # Third-party administration: more complex, requires consent/cooperation
        difficulty_modifier = +2  # Slightly harder
        time_modifier = 1.2       # Takes 20% longer
        consent_required = True
        
        # Check consciousness/cooperation of target
        if not target.conscious and method not in ["inject", "apply", "bandage"]:
            return "target_unconscious_method_inappropriate"
    
    # Calculate success based on administrator's stats
    admin_skill = calculate_medical_skill(administrator)
    success_chance = admin_skill + base_requirements + difficulty_modifier
    
    return execute_consumption(administrator, target, substance, method, success_chance)
```

#### Medical vs Recreational Substances
```python
SUBSTANCE_CATEGORIES = {
    "medical": {
        "priority": "healing",
        "side_effects": "minimal_therapeutic",
        "legal_status": "regulated_legal",
        "examples": ["painkillers", "antibiotics", "blood_bags", "burn_gel"]
    },
    "recreational": {
        "priority": "psychological_effect", 
        "side_effects": "varied_unpredictable",
        "legal_status": "varies_by_jurisdiction",
        "examples": ["alcohol", "stimulants", "hallucinogens", "depressants"]
    },
    "performance": {
        "priority": "stat_enhancement",
        "side_effects": "temporary_crash",
        "legal_status": "controlled_military",
        "examples": ["combat_stims", "focus_enhancers", "strength_boosters"]
    },
    "toxic": {
        "priority": "harm",
        "side_effects": "damage_death",
        "legal_status": "restricted_illegal",
        "examples": ["poisons", "nerve_agents", "corrosives"]
    }
}
```

### Command Integration Examples

#### Medical Scenarios
```
> inject painkiller
You inject the painkiller into your arm. The sharp pain in your chest begins to fade.

> apply burn gel to Alice
You carefully apply the cooling gel to Alice's burned arm. She winces but looks relieved.

> bandage Bob's leg with gauze  
You wrap Bob's wounded leg with sterile gauze, stemming the bleeding.
```

#### Cross-Category Usage
```
> drink whiskey
You take a swig of whiskey. The alcohol burns as it goes down, dulling the edge of your pain.

> smoke medicinal herb
You light the dried herb and inhale deeply. Your breathing becomes easier and the pain subsides.

> inhale stimpak vapor
You breathe in the aerosolized stimpak. Energy surges through your body as your wounds begin to close.
```

### Implementation Notes
- **Unified Backend**: All consumption methods use the same core mechanics with method-specific modifiers
- **Natural Language**: Commands reflect real-world familiarity with consumption methods
- **Scalability**: System supports easy addition of new substances and consumption methods
- **Medical Foundation**: Medical system provides the underlying health/condition framework for all substances

### Medical Tool Interactions

### Treatment Effectiveness (Simplified)
```python
# Simple tool appropriateness for conditions
TOOL_APPROPRIATENESS = {
    "bleeding": {
        "gauze": "highly_effective_for_minor_moderate",
        "blood_bag": "restores_blood_volume_only",
        "surgical_kit": "effective_for_severe_internal", 
        "splint": "ineffective",
        "painkiller": "counter_productive"
    },
    "fracture": {
        "splint": "highly_effective",
        "surgical_kit": "effective_but_complex",
        "gauze": "ineffective",
        "blood_bag": "ineffective",
        "painkiller": "helps_with_pain_only"
    },
    "infection": {
        "surgical_kit": "effective_with_cleaning",
        "gauze": "basic_prevention_only",
        "blood_bag": "ineffective",
        "splint": "ineffective", 
        "painkiller": "ineffective"
    }
    # Note: Exact effectiveness mechanics to be determined during implementation
}
```

## Medical Skill System

### G.R.I.M. Integration (Current Implementation)
- **Intellect (75%)**: Medical knowledge, diagnosis ability, understanding of anatomy and treatment
- **Motorics (25%)**: Steady hands for precise procedures, dexterity with medical tools

### G.R.I.M. Integration (Future Potential)  
- **Grit**: Pain tolerance during self-treatment, ability to work while injured
- **Resonance**: Bedside manner, patient stabilization, calming effect on others

### Medical Treatment Formula
```python
medical_effectiveness = (intellect * 0.75) + (motorics * 0.25)
treatment_success = d20_roll + medical_effectiveness vs difficulty_threshold
```

### Medical Actions

#### Diagnosis
```python
def diagnose_patient(medic, patient):
    """
    Determine what medical conditions affect the patient.
    Success reveals hidden conditions and treatment requirements.
    """
    intellect_roll = roll_d20() + medic.intellect
    difficulty = {
        "obvious_injuries": 8,    # Visible wounds
        "internal_injuries": 14,  # Requires examination  
        "systemic_conditions": 18 # Hidden organ damage
    }
```

#### Treatment Application
```python
def apply_medical_treatment(medic, patient, tool, condition):
    """
    Use medical tool to treat specific condition.
    Success based on G.R.I.M. stats and tool appropriateness.
    """
    medical_skill = (medic.intellect * 0.75) + (medic.motorics * 0.25)
    base_roll = roll_d20() + medical_skill
    
    # Tool appropriateness modifies difficulty
    base_difficulty = MEDICAL_TREATMENT_BASE_DIFFICULTY  # Constant for balance
    tool_modifier = TOOL_EFFECTIVENESS_MODIFIERS[tool.type][condition.type]  # Constant table
    actual_difficulty = base_difficulty + tool_modifier
    
    # Success determination
    if base_roll >= actual_difficulty:
        return "success"
    elif base_roll >= (actual_difficulty - PARTIAL_SUCCESS_MARGIN):  # Constant
        return "partial_success" 
    else:
        return "failure"
    
    # NOTE: All difficulty values use constants for easy balance adjustment
```

## Integration Points

### Combat System Integration

#### Damage Location Targeting
```python
def apply_anatomical_damage(character, damage, location):
    """
    Apply damage to specific body part, affecting relevant organs/systems.
    """
    # Determine which organs/systems are affected
    affected_systems = get_systems_for_location(location)
    
    # Distribute damage across systems
    for system in affected_systems:
        system_damage = calculate_system_damage(damage, system)
        apply_system_damage(character, system, system_damage)
        
    # Check for immediate effects
    check_critical_system_failure(character, affected_systems)
```

#### Weapon-Specific Injury Patterns
```python
WEAPON_INJURY_PATTERNS = {
    "blade": {"primary": "laceration", "secondary": "organ_damage"},
    "blunt": {"primary": "fracture", "secondary": "internal_bleeding"}, 
    "projectile": {"primary": "organ_damage", "secondary": "internal_bleeding"},
    "explosive": {"primary": "multiple_trauma", "secondary": "burns"}
}
```

### Longdesc System Integration

#### Medical Condition Visibility (Automatic Longdesc Appending)
```python
MEDICAL_DESCRIPTIONS = {
    "bleeding": {
        "obvious": "blood soaking through their clothing",
        "severe": "leaving a trail of blood behind them",
        "critical": "pale and trembling from blood loss"
    },
    "fracture_arm": {
        "splinted": "their arm held in a makeshift splint",
        "unsplinted": "cradling their obviously broken arm"
    },
    "vision_impaired": {
        "partial": "squinting as if having trouble seeing",
        "severe": "feeling around carefully with their hands"
    }
    # These descriptions automatically append to character longdesc when conditions are present
    # NOTE: Longdesc system is already designed to support this - implementation will use existing append hooks
}
```

### Integration Implementation Notes
- **Longdesc Appending**: Will interface with existing longdesc system's append functionality
- **Condition Detection**: Medical conditions stored in `character.db.medical_conditions` will trigger appropriate descriptions
- **Priority System**: More severe conditions override less severe ones for the same body part

## Implementation Architecture

### Core Design Decisions

#### State Persistence Strategy
- **Pattern**: Use `character.db` entries following the combat handler persistence model
- **Benefits**: Survives disconnections, server restarts, and maintains treatment timers
- **Implementation**: Medical state, ongoing treatments, and substance effects stored in persistent database attributes
- **Consistency**: Mid-treatment interruptions handled gracefully with state recovery on reconnection

#### Organ Template System  
- **Approach**: Dictionary-based organ mapping system in character typeclasses
- **Template Storage**: Pre-generated organ templates for each creature type (human, tentacle_monster, spider, etc.)
- **Dynamic Creation**: Templates support dynamic character creation with varied anatomy
- **Inspiration**: Similar to existing systems like "Mr. Hands" location mapping
- **Flexibility**: New creature types easily added via typeclass definitions

#### Command Architecture
- **Structure**: Separate command classes for each consumption method (`InjectCommand`, `ApplyCommand`, etc.)
- **Shared Logic**: Common handler/utility classes for substance effects and medical calculations
- **Aliases**: Evennia's native command-level alias system (e.g., `inhale`/`huff` aliases)
- **Best Practices**: Follows Evennia command architecture patterns for maintainability

#### NPC Integration
- **Consistency**: NPCs use identical medical modeling and typeclasses as player characters
- **Benefits**: NPCs can be meaningfully injured, treated, and interact with substance system
- **Complexity**: Avoids maintaining separate/simplified systems for NPCs
- **Gameplay**: Enables realistic medical scenarios with NPC patients and medics

#### Substance Interaction System (Long-term)
- **Toxicity Framework**: Substances contribute to cumulative toxicity levels
- **Stacking Effects**: Multiple substances with interaction modifiers and duration overlaps
- **Metabolic Modeling**: Clearance rates and effectiveness curves over time
- **Complexity Scaling**: Start simple, evolve into detailed pharmacological interactions

#### Performance Considerations
- **Lazy Loading**: Inactive/resolved medical conditions cleaned up automatically
- **Template Caching**: Organ templates cached at typeclass level for performance
- **State Optimization**: Medical state only tracks active conditions and damaged organs

## Implementation Phases

### Phase 1: Foundation (Organ System & Data Persistence)
- [ ] Expand character health model beyond simple HP
- [ ] Add organ/subsystem tracking to Character class
- [ ] Implement medical condition status effects
- [ ] Basic injury-to-organ damage mapping
- [ ] **Medical data persistence**: Store medical state in `character.db` for session persistence

#### Data Storage Architecture
```python
# Character medical state stored persistently in character.db
character.db.medical_state = {
    "organs": {
        "brain": {"current_hp": 8, "max_hp": 10, "conditions": []},
        "heart": {"current_hp": 15, "max_hp": 15, "conditions": []},
        # ... all organs
    },
    "conditions": [
        {"type": "fracture", "location": "left_arm", "severity": "moderate", "treated": False},
        {"type": "bleeding", "location": "chest", "severity": "minor", "rate": 1}
    ],
    "blood_level": 85,  # Percentage of normal blood volume
    "pain_level": 23,   # Current pain accumulation
    "consciousness": 78 # Current consciousness level
}

# Ongoing treatments/timers: Use Evennia's built-in timer system
# - Short term (rounds): Use delayed calls for bandaging, injections
# - Long term (days): Use Scripts for healing, recovery, infections
```

*Note: Ongoing treatment timers will use Evennia's timer/script system for persistence across server restarts*

### Phase 2: Medical Tools & Consumption Method Commands
- [ ] Create medical item classes (BloodBag, Painkiller, etc.)
- [ ] **Implement consumption method commands**: `inject`, `apply`, `eat`, `drink`, `inhale`, `smoke`, `bandage`
- [ ] **Self-administration & third-party administration mechanics**
- [ ] **Unified consumable substance system**: Foundation for medical items, drugs, and other consumables
- [ ] Add G.R.I.M.-based treatment success/failure with method-specific modifiers
- [ ] Tool appropriateness system integrated with consumption methods
- [ ] **Command Integration**: Natural language consumption commands interface with substance effects and patient conditions

*Note: Consumption method system serves as foundation for broader drug/substance system beyond medical items*

### Phase 3: Combat Integration & Stat Penalties
- [ ] Location-based damage system in combat
- [ ] Weapon-specific injury patterns  
- [ ] Critical injury immediate effects
- [ ] **Pain/injury penalties affecting dice rolls**: Unified with existing stat calculation systems
- [ ] **Medical condition modifiers**: Integration with combat, skill checks, and other game mechanics
- [ ] Medical emergency scenarios

*Note: Penalty mechanics will be unified with existing stat vs health calculations*

### Phase 4: Advanced Systems
- [ ] Long-term healing and recovery
- [ ] Infection and complication systems
- [ ] Prosthetics and permanent disabilities
- [ ] Advanced surgical procedures

## Example Medical Scenarios

### Combat Medic Scenario
```
During combat, Alice takes a blade hit to the chest (internal damage to lungs).
She develops "punctured_lung" condition - breathing difficulty, gradual HP loss.
Bob, with high Intellect, diagnoses the condition successfully.
He uses Surgical Kit (requiring 5 rounds of uninterrupted work) to repair the lung.
Success: Alice's breathing stabilizes, HP loss stops.
Failure: Alice develops "pneumothorax" - more severe breathing failure.
```

### Field Medicine Scenario  
```
Charlie has a fractured arm from explosion damage.
Without treatment: arm is unusable, constant pain penalties.
Dana applies Splint: requires Intellect roll, takes 2 rounds.
Success: arm partially functional (50%), pain reduced.
Later, Surgical Kit can provide full repair (80% function restored).
```

### Resource Management Scenario
```
Multiple wounded characters, limited medical supplies.
Player must choose: use Blood Bag on critically wounded ally, or save it?
Painkiller: give to heavily injured fighter to keep them combat-effective?
Surgical Kit: attempt difficult organ repair, or save uses for emergencies?
```

---

*"In space, a medical emergency doesn't wait for convenient timing. Every blood bag, every splint, every steady hand could mean the difference between coming home or floating in the void."*
- Dr. Sarah Chen, Frontier Medical Corps, 2387 TST
