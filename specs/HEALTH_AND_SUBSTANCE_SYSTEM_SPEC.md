# Health and Substance System Specification

## Implementation Status

### ✅ COMPLETED (Phase 1 & 2)
**Medical Foundation Complete:**
- Complete anatomical damage system (15 body regions + 6 organs)
- Medical conditions with severity tracking (bleeding, fractures, pain, etc.)
- Vital signs calculation (consciousness, blood level, pain level)
- Death/unconsciousness determination based on organ failure

**Medical Tools & Consumption Complete:**
- 7 medical item prototypes using Evennia's attribute-based system
- Natural language consumption commands (`inject`, `apply`, `bandage`, `eat`, `drink`)
- Medical inventory management commands (`medlist`, `mediteminfo`, `refillmed`)
- Skill-based treatment success using G.R.I.M. stats (Intellect-based medical skill)

**Evennia Integration Complete:**
- Proper attribute-based medical items (no custom typeclass required)
- Integration with built-in `spawn` command
- Medical system integrated with character `take_damage()` and combat
- Persistent medical state storage and retrieval

**Combat-Medical Integration Complete (December 2024):**
- ✅ Combat handler now uses weapon-specific damage types (bullet, cut, stab, blunt, laceration, burn)
- ✅ All weapon prototypes have damage_type attributes for medical integration
- ✅ All apply_damage() calls use proper 4-parameter signature (character, damage, location, injury_type)
- ✅ Fixed location mapping - combat damage to "chest" properly affects heart/lung organs
- ✅ Admin heal command fixed for medical condition list structure
- ✅ Destroyed organ protection - prevents damage to 0 HP organs
- ✅ Limb loss detection when all organs in body part destroyed
- ✅ **Individual bone anatomy system** - hospital-grade anatomical accuracy
- ✅ **Organ naming consistency** - eliminated "unknown" container issues
- ✅ **Enhanced medinfo diagnostics** - comprehensive medical status reporting
- ✅ **Medical system migration tools** - administrative commands for mass updates

### 🔄 CURRENT STATE: ANATOMICALLY ACCURATE MEDICAL SYSTEM
The medical system now features **hospital-grade anatomical accuracy** with individual bone structures:
- Combat damage properly creates medical conditions (bleeding, fractures, organ damage)
- Weapon types create appropriate injury patterns (bullets cause severe bleeding, blunt weapons cause fractures)
- Organ damage occurs realistically (chest hits affect heart/lungs, head hits affect brain/eyes)  
- Medical conditions visible in `medinfo` and treatable with medical items
- Destroyed organs cannot take further damage (prevents unrealistic overkill)
- **Individual bone anatomy** with realistic fracture mechanics

### 🦴 ANATOMICAL BONE SYSTEM (December 2024)
**Individual Bone Structure:**
- **Arms:** `left/right_humerus` (main arm bones) → 40% manipulation each
- **Hands:** `left/right_metacarpals` (hand bones) → 20% manipulation each  
- **Thighs:** `left/right_femur` (thigh bones) → 40% movement each
- **Shins:** `left/right_tibia` (shin bones) → 40% movement each
- **Feet:** `left/right_metatarsals` (foot bones) → 10% movement each

**Medical Benefits:**
- Realistic fractures (can break humerus without affecting other bones)
- Proper orthopedic injury patterns (blunt trauma to leg can fracture femur)
- Anatomically accurate damage distribution
- Enhanced surgical/treatment targeting
- One bone per body location for clean display

### 🏗️ MEDICAL SYSTEM ARCHITECTURE
**Organ Classification System:**
- **Individual Organs** (vital/complex): `brain`, `heart`, `liver`, `left_eye`, etc.
- **Individual Bones** (structural): `left_humerus`, `left_femur`, `left_tibia`, etc.
- **Container Hierarchy**: Organs exist within body location containers (`head`, `chest`, `left_arm`, etc.)

**Critical Integration Points:**
- `ORGANS` constants define available organs with their containers and properties
- `BODY_CAPACITIES` must reference organs that exist in `ORGANS` 
- **Auto-creation Gap**: `get_organ()` creates undefined organs with `container="unknown"`
- **Solution**: All capacity calculations use properly defined organ names

**Capacity Calculation Flow:**
1. Medical state initialized with organs from `ORGANS.keys()`
2. Body capacity calculation references `BODY_CAPACITIES[capacity]["organs"]`
3. Each referenced organ must exist in `ORGANS` or gets auto-created with "unknown" container
4. Bone-specific contributions (femur_contribution, humerus_contribution) provide balanced capacity totals

**Enhanced Medical Commands:**
- `medinfo [target] [organs|conditions|capacities|summary]` - Comprehensive medical diagnostics
- `@resetmedical <character>` - Reset medical states after system updates
- `@medaudit [details]` - Audit medical system health across all characters

### 🔧 MEDICAL SYSTEM MIGRATION TOOLS
**Administrative Commands (Builder+):**
- `@resetmedical confirm all` - Mass reset all character medical states
- `@resetmedical <character>` - Reset individual character medical state
- `@medaudit` - Quick overview of medical system health across game
- `@medaudit details` - Detailed character-by-character medical state analysis

**Migration Workflow:**
1. `@medaudit` - Assess current medical state distribution
2. `@resetmedical confirm all` - Clean slate migration (recommended)
3. Characters automatically receive current medical structure on next access
4. `@medaudit` - Verify successful migration to new structure

**Use Cases:**
- Medical system updates (new organs, changed mechanics)
- Server maintenance and cleanup
- Development testing and debugging
- Version migration between game updates

### 🎯 FUTURE PHASES: ADVANCED MEDICAL MECHANICS
**Phase 3 - Advanced Features (Future Development):**
- Limb replacement mechanics (prosthetics, cybernetics) 
- Advanced surgical procedures and medical equipment
- Disease and infection progression systems
- Drug addiction and dependency mechanics
- Complex organ transplant procedures

**Phase 4 - Legacy HP Migration (Optional):**
- Consider complete removal of legacy HP system (currently dual system works well)
- All combat systems already use medical model via take_damage() integration
- Legacy HP provides backwards compatibility with existing game mechanics

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

## Current Health System Implementation

### ✅ Implemented Medical System
```python
# MEDICAL STATE SYSTEM (IMPLEMENTED)
class MedicalState:
    """Complete medical state tracking"""
    def __init__(self, character=None):
        self.organs = {}              # Organ health tracking
        self.conditions = []          # Medical conditions (bleeding, fractures, etc.)
        self.blood_level = 100.0      # Current blood percentage
        self.pain_level = 0.0         # Pain accumulation
        self.consciousness = 100.0    # Consciousness level
    
    def is_dead(self):
        """Multi-factor death determination"""
        # Death from vital organ failure
        if self.calculate_body_capacity("blood_pumping") <= 0.0:  # Heart
            return True
        if self.calculate_body_capacity("breathing") <= 0.0:      # Lungs
            return True
        if self.calculate_body_capacity("digestion") <= 0.0:      # Liver
            return True
        # Death from catastrophic blood loss (85%+ loss)
        if self.blood_level <= 15.0:
            return True
        return False
    
    def is_unconscious(self):
        """Multi-factor unconsciousness"""
        consciousness_level = self.calculate_body_capacity("consciousness")
        return consciousness_level < 0.30  # 30% threshold

# CHARACTER INTEGRATION (IMPLEMENTED)
class Character:
    @property
    def medical_state(self):
        """Access persistent medical state"""
        
    def take_damage(self, amount, location="chest", injury_type="generic"):
        """Integrated damage system - applies to BOTH systems"""
        # Legacy HP (backwards compatibility)
        self.hp = max(self.hp - amount, 0)
        
        # New anatomical damage
        from world.medical.utils import apply_anatomical_damage
        damage_results = apply_anatomical_damage(self, amount, location, injury_type)
        
        # Death from EITHER system
        return self.medical_state.is_dead() or self.hp <= 0
    
    def take_anatomical_damage(self, amount, location, injury_type="generic"):
        """Pure medical system damage (preferred method)"""
        damage_results = apply_anatomical_damage(self, amount, location, injury_type)
        
        # Sync legacy HP with medical state
        if self.medical_state.is_dead():
            self.hp = 0
        elif self.medical_state.is_unconscious():
            self.hp = min(self.hp, 1)
            
        return damage_results

# MEDICAL TOOLS SYSTEM (IMPLEMENTED)
# Uses Evennia's attribute-based approach with regular Item typeclass
# Example prototype:
BLOOD_BAG = {
    "key": "blood bag",
    "typeclass": "typeclasses.items.Item",  # Regular Item, not custom
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "blood_restoration"),
        ("uses_left", 1),
        ("effectiveness", {"bleeding": 9, "blood_loss": 10}),
    ]
}

# Accessed via utility functions:
is_medical_item(item)           # Check if item is medical
can_be_used(item)              # Check if item has uses left  
get_medical_type(item)         # Get medical type
apply_medical_effects(...)     # Apply treatment effects
```

### 🔄 Legacy HP System (TO BE DEPRECATED)
```python
# CURRENT LEGACY SYSTEM - MARKED FOR REMOVAL IN PHASE 3
hp = AttributeProperty(10, category='health')           # TO BE REMOVED
hp_max = AttributeProperty(10, category='health')       # TO BE REMOVED
hp_max = 10 + (grit * 2)  # Dynamic max HP based on Grit  # TO BE REMOVED

# Legacy methods that will be removed:
def heal(self, amount):  # Replace with medical treatment only
def is_dead(self): return self.hp <= 0  # Replace with medical_state.is_dead()

# Combat integration now uses medical system:
target.take_damage(damage, location, injury_type)  # Uses medical system with proper injury types
# Phase 3: Replace with target.take_anatomical_damage(damage, location, injury_type)
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

#### 🔧 Current Weapon Implementation Status
As of December 2024, all weapon prototypes have been updated with appropriate damage types:

```python
# IMPLEMENTED WEAPON DAMAGE TYPES:
WEAPON_DAMAGES = {
    # Firearms - high bleeding, hard to treat
    "bullet": ["pistol", "shotgun", "assault_rifle", "sniper_rifle", "heavy_machine_gun"],
    
    # Cutting weapons - moderate bleeding, easy to treat  
    "cut": ["knife", "machete", "sword", "katana", "claymore", "battle_axe", "small_axe"],
    
    # Stabbing weapons - severe bleeding, organ damage risk
    "stab": ["dagger", "spear", "straight_razor", "awl", "ice_pick"],
    
    # Blunt weapons - minimal bleeding, fracture risk
    "blunt": ["club", "hammer", "sledgehammer", "pipe_wrench", "baseball_bat", "crowbar"],
    
    # High-damage ragged weapons - severe bleeding and pain
    "laceration": ["chainsaw", "shuriken", "meat_hook", "rebar", "nailed_board"],
    
    # Chemical/fire weapons - high infection risk  
    "burn": ["spray_can", "solvent_can", "flamethrower"]
}

# Combat handler automatically maps weapon.db.damage_type to appropriate injury mechanics
# All apply_damage() calls throughout codebase use 4-parameter signature
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
    
    ### Progressive Condition System
    
    **Core Mechanic: Conditions degrade naturally over time while stacking cumulatively**
    
    #### Progressive Bleeding Degradation
    ```python
    PROGRESSIVE_BLEEDING = {
        "mechanism": "each_round_reduces_severity_by_1",
        "examples": {
            "severe_bleeding_8": "Round 1: 8% → Round 2: 7% → Round 3: 6% → ... → Round 8: 1% → Round 9: stops",
            "moderate_bleeding_3": "Round 1: 3% → Round 2: 2% → Round 3: 1% → Round 4: stops",
            "minor_bleeding_1": "Round 1: 1% → Round 2: stops"
        },
        "cumulative_effect": {
            "description": "Multiple wounds stack their current bleeding rates",
            "example": "Chest severe (6%) + arm moderate (2%) + leg minor (1%) = 9% total blood loss that round"
        }
    }
    ```
    
    #### Script-Based Progression Timer
    ```python
    MEDICAL_PROGRESSION_SYSTEM = {
        "timing_mechanism": {
            "interval": "2-3 combat rounds",
            "real_time": "approximately 4-6 seconds per progression tick",
            "rationale": "Balances urgency with player reaction time and server performance"
        },
        
        "revised_bleeding_duration": {
            "severe_bleeding_8": "16-24 combat rounds total (8-12 minutes)",
            "moderate_bleeding_3": "6-9 combat rounds total (3-4.5 minutes)",
            "minor_bleeding_1": "2-3 combat rounds total (1-1.5 minutes)",
            "survivability": "Much more manageable while maintaining urgency"
        },
        
        "script_triggers": {
            "combat_start": "Activate medical progression if bleeding conditions exist",
            "combat_end": "Continue script until all bleeding stops naturally or treated",
            "medical_treatment": "Interrupt/modify script based on treatment success",
            "character_movement": "Script follows character between locations",
            "logout_persistence": "Script pauses/resumes with character login state"
        },
        
        "evennia_integration": {
            "script_class": "MedicalProgressionScript",
            "script_attachment": "character_with_bleeding_conditions",
            "database_updates": "Batch condition updates every progression tick",
            "cleanup": "Auto-remove script when no progressive conditions remain"
        },
        
        "performance_considerations": {
            "batched_updates": "Update all character conditions in single database write",
            "conditional_activation": "Script only runs when needed (bleeding/poison/burn active)",
            "resource_efficiency": "2-3 round intervals prevent excessive server load"
        }
    }
    ```
    
    #### Multi-Location Treatment
    ```python
    TREATMENT_MECHANICS = {
        "bandages": {
            "effect": "treats_multiple_wounds_per_application",
            "typical_coverage": "2-3_bleeding_sources_per_bandage",
            "requires": "medical_skill_check_for_effectiveness"
        },
        "tourniquets": {
            "effect": "stops_bleeding_in_specific_limb_completely",
            "limitation": "location_specific_only"
        },
        "surgical_intervention": {
            "effect": "treats_severe_bleeding_sources",
            "requires": "high_medical_skill_proper_tools"
        }
    }
    ```
    
    #### Extensible Condition Framework
    ```python
    PROGRESSIVE_CONDITIONS = {
        "toxic_gas_exposure": {
            "initial_damage": "15_poison_per_round",
            "degradation": "14 → 13 → 12 → ... until cleared",
            "cumulative": "multiple_exposures_stack: first(10/round) + second(8/round) = 18/round total"
        },
        "fire_damage": {
            "initial_damage": "20_burn_per_round",
            "degradation": "19 → 18 → 17 → ... until stopped",
            "immediate_remedy": "stop_drop_roll removes condition entirely",
            "cumulative": "multiple_fire_sources_compound"
        },
        "radiation_exposure": {
            "initial_damage": "variable_based_on_exposure_level",
            "degradation": "slow_reduction_over_hours_days",
            "cumulative": "radiation_sickness_compounds_exponentially"
        }
    }
    ```
    
    #### Game Design Benefits
    ```python
    PROGRESSIVE_SYSTEM_ADVANTAGES = {
        "urgency": "conditions_worsen_before_improving_naturally",
        "tactical_depth": "multiple_wounds_require_multiple_treatments",
        "resource_management": "medical_supplies_become_precious_strategic_resource",
        "realistic_progression": "injuries_naturally_degrade_over_time",
        "scalable_difficulty": "environmental_hazards_use_same_framework"
    }
    ```
    
    #### Dynamic Medical Status Messaging
    ```python
    BLEEDING_STATUS_MESSAGES = {
        "self_awareness": {
            "multiple_severe": "Blood runs. Fast.",
            "single_severe": "Your {location} leaks. Badly.",
            "multiple_moderate": "Three holes. Three problems.",
            "single_moderate": "Your {location} drips steadily.",
            "multiple_minor": "Small cuts. They add up.",
            "single_minor": "A nick on your {location}.",
            "deteriorating": "It's getting worse.",
            "improving": "Slowing down. Maybe."
        },
        
        "observer_messages": {
            "multiple_severe": "{character_name} is leaking from everywhere.",
            "single_severe": "{character_name}'s {location} won't stop.",
            "multiple_moderate": "{character_name} has problems. Several.",
            "single_moderate": "{character_name}'s {location} drips.",
            "multiple_minor": "{character_name} is nicked up.",
            "single_minor": "{character_name} has a small cut on their {location}.",
            "deteriorating": "{character_name} is getting worse.",
            "improving": "{character_name}'s bleeding slows."
        },
        
        "medical_status_integration": {
            "stats_display": "Vitals: CRITICAL",
            "medinfo_alerts": "Multiple bleeding sources active",
            "room_descriptions": "Derek is here, bleeding.",
            "combat_status": "Derek fights. Blood follows."
        }
    }
    ```
    
    #### Blood Loss Progression Messaging
    ```python
    BLOOD_LOSS_STAGES = {
        "90-100%": {
            "self": "You feel fine.",
            "observer": "{name} looks steady."
        },
        "70-89%": {
            "self": "Getting light.",
            "observer": "{name} is pale."
        },
        "50-69%": {
            "self": "The world tilts.",
            "observer": "{name} sways slightly."
        },
        "30-49%": {
            "self": "Cold creeps in.",
            "observer": "{name} is very pale. Shaking."
        },
        "15-29%": {
            "self": "Vision narrows. Darkness at the edges.",
            "observer": "{name} can barely stand."
        },
        "0-14%": {
            "self": "Everything fades.",
            "observer": "{name} is unconscious. Dying."
        }
    }
    ```
    
    #### Real-Time Medical Updates
    ```python
    MEDICAL_EVENT_MESSAGING = {
        "round_updates": {
            "bleeding_worsens": "Your {location} opens wider.",
            "bleeding_slows": "Your {location} clots slightly.",
            "multiple_sources": "Blood from your {location1}. Your {location2}. Your {location3}.",
            "treatment_needed": "This won't stop on its own."
        },
        
        "status_changes": {
            "healthy_to_injured": "Something's wrong.",
            "injured_to_serious": "Getting bad.",
            "serious_to_critical": "Very bad.",
            "critical_stabilizing": "Maybe stabilizing.",
            "recovery_progress": "Slowly improving."
        },
        
        "environmental_integration": {
            "room_entry": "Derek enters. Blood trails behind.",
            "examination": "Derek bleeds from chest, arm, leg.",
            "unconscious_bleeding": "Derek lies still. Blood pools.",
            "combat_ongoing": "Derek fights on. Bleeds on."
        }
    }
    ```
    
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

---

## Phase 3 Roadmap: Legacy HP System Elimination

### Goals
Complete the migration from dual HP/medical system to pure medical system, eliminating all legacy HP dependencies while maintaining full backwards compatibility for existing content.

### Recent Improvements (December 2024)

The following critical fixes and enhancements have been implemented:

#### Combat-Medical Integration Fixes
- **Fixed Combat Handler**: Removed invalid `injury_type="combat"`, now uses `weapon.db.damage_type`
- **Weapon Prototypes Updated**: All 25+ weapons have appropriate `damage_type` attributes
- **Location Mapping Fixed**: Changed `location="torso"` to `location="chest"` for proper organ damage
- **Function Signatures**: All `apply_damage()` calls use proper 4-parameter signature

#### Organ Damage Protection  
- **Destroyed Organ Protection**: Prevents damage to organs already at 0 HP
- **Limb Loss Detection**: System detects when all organs in body part destroyed
- **Realistic Damage Flow**: No more "beating a dead horse" with infinite negative HP

#### Admin Tools Fixed
- **Heal Command**: Fixed `AttributeError` for medical conditions list structure  
- **Condition Management**: Proper severity-based healing (minor → moderate → severe → critical)
- **Better Feedback**: Clear messages when damage cannot be applied

#### Code Quality Improvements
- **Comprehensive Audit**: All `apply_damage()` references found and updated
- **Spec Synchronization**: Documentation updated to match implementation
- **Future-Proofing**: Groundwork laid for limb replacement mechanics

### Implementation Tasks

#### 1. Combat System Status ✅ COMPLETE
```python
# CURRENT STATUS: Full integration achieved!
# ✅ Combat handler uses weapon.db.damage_type for proper injury types
# ✅ All apply_damage() calls use (character, damage, location, injury_type) signature  
# ✅ Location mapping fixed (chest damage affects heart/lungs properly)
# ✅ All weapons have damage_type attributes for medical integration

target_died = target.take_damage(damage, location, injury_type)  # WORKING
```

#### 2. Advanced Medical Features (Future Development)
- **Limb Replacement System**: Prosthetics, cybernetics, organ transplants
- **Advanced Surgical Procedures**: Complex medical equipment and operations
- **Disease Progression**: Infections, diseases that spread over time
- **Drug Dependencies**: Addiction mechanics and withdrawal systems

#### 3. Optional Legacy Migration (Future Consideration)
- Consider removing `hp` and `hp_max` attributes (currently provide backwards compatibility)
- Current dual system works well - medical system fully integrated via `take_damage()`
- Legacy HP provides compatibility with existing Evennia systems and player expectations

#### 4. Healing System Replacement
- Replace HP-based healing with medical treatment only
- Convert any existing healing items to medical prototypes
- Update rest/recovery mechanics to work with medical system
- Ensure medical treatment provides equivalent healing power

#### 5. UI/Display Updates
- Replace HP displays with medical status summaries
- Update character sheets to show medical state instead of HP
- Add medical condition displays to relevant interfaces
- Ensure backwards compatibility for HP-checking scripts

#### 6. Testing & Validation
- Comprehensive testing of all combat scenarios
- Verify death/unconsciousness mechanics work correctly
- Test medical treatment effectiveness
- Validate performance with pure medical system

### Benefits of Pure Medical System
- **Realistic Damage:** Location-specific injuries with logical consequences
- **Tactical Combat:** Players must consider where to aim and what weapons to use
- **Medical Gameplay:** Injuries require specific treatment types and skills
- **Immersive Roleplay:** Detailed injury descriptions enhance narrative depth
- **Strategic Resource Management:** Medical supplies become critically important

### Migration Strategy
1. **Gradual Rollout:** Implement changes incrementally to minimize disruption
2. **Extensive Testing:** Test each component thoroughly before removing legacy code
3. **Community Communication:** Inform players about changes and new medical mechanics
4. **Documentation Updates:** Update all player-facing documentation and help files
5. **Backwards Compatibility:** Ensure existing combat content continues to work

### Success Metrics
- [ ] All combat commands use anatomical damage system
- [ ] No references to legacy HP system remain in codebase
- [ ] Medical treatment provides complete healing functionality
- [ ] Performance is equivalent or better than legacy system
- [ ] Player experience is enhanced with richer medical gameplay

This completes the evolution from traditional HP-based health to a sophisticated medical simulation system that enhances both tactical combat and roleplay opportunities.

---

*This specification reflects the current implemented state (Phase 1 & 2 complete) and provides the roadmap for completing the medical system migration in Phase 3.*
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

### Phase 1: Foundation (Organ System & Data Persistence) - ✅ COMPLETED
- ✅ **Expanded character health model**: Legacy HP system completely eliminated
- ✅ **Advanced anatomical system**: Hospital-grade accuracy with individual bones (humerus, femur, tibia, metacarpals, metatarsals)
- ✅ **Organ/subsystem tracking**: Individual organs with HP, functionality, and anatomical mapping
- ✅ **Body capacities system**: Vital and functional capacities with bone-specific contributions  
- ✅ **Medical condition status effects**: Bleeding, fractures, infections with severity tracking
- ✅ **Advanced injury-to-organ damage mapping**: Location-based damage with organ targeting
- ✅ **Medical data persistence**: Complete medical state stored in `character.db.medical_state`
- ✅ **Migration tools**: Administrative commands for updating existing characters to new anatomy
- ✅ **Death/unconsciousness system**: Based on vital organ failure and blood loss thresholds

#### Implemented Data Storage Architecture
```python
# Character medical state stored persistently in character.db
character.db.medical_state = {
    "organs": {
        "brain": {"current_hp": 8, "max_hp": 10, "conditions": []},
        "heart": {"current_hp": 15, "max_hp": 15, "conditions": []},
        "humerus_left": {"current_hp": 20, "max_hp": 20, "conditions": []},
        # ... all organs and bones
    },
    "conditions": [
        {"type": "fracture", "location": "left_arm", "severity": "moderate", "treated": False},
        {"type": "bleeding", "location": "chest", "severity": "minor", "rate": 1}
    ],
    "blood_level": 85.0,    # Percentage of normal blood volume
    "pain_level": 23.0,     # Current pain accumulation  
    "consciousness": 78.0   # Current consciousness level
}
```

#### Implemented Commands
- ✅ `medical [target]` - Check medical status with detailed health indicators
- ✅ `medinfo [organs|conditions|capacities]` - Detailed medical information system
- ✅ `damagetest <amount> [location] [injury_type]` - Test anatomical damage application
- ✅ `healtest [condition|all]` - Test healing mechanisms (development command)
- ✅ `@resetmedical [character|confirm all]` - Reset character medical states (admin)
- ✅ `@medaudit` - Comprehensive medical system diagnostics (admin)

### Phase 2: Medical Tools & Consumption Method Commands - ✅ COMPLETED
- ✅ **Medical item classes**: Full item management system with usage tracking
- ✅ **Consumption method commands implemented**: `inject`, `apply`, `bandage`, `eat`, `drink` 
- ✅ **Self-administration & third-party administration**: Complete targeting and consent mechanics
- ✅ **Medical item management system**: Item discovery, validation, and usage tracking
- ✅ **G.R.I.M.-based treatment success/failure**: Medical effectiveness calculations implemented
- ✅ **Treatment appropriateness system**: Item-condition matching with success modifiers
- ✅ **Command Integration**: Natural language consumption commands fully functional

#### Implemented Consumption Commands
- ✅ `inject <item> [target]` - Injectable substances with full targeting support
- ✅ `apply <item> [to target]` - Topical treatments with natural language syntax
- ✅ `bandage <body_part> with <item>` - Advanced bandaging with body location targeting  
- ✅ `eat <item>` - Oral consumption of solid substances
- ✅ `drink <item>` - Liquid consumption system
- ✅ `medlist` - List medical items in inventory with status
- 🔲 `inhale/smoke` - Not yet implemented (planned for Phase 2.5)

#### Medical Item Integration
- ✅ **Item type detection**: Automatic medical item classification
- ✅ **Usage tracking**: Items consume uses when applied
- ✅ **Treatment effects**: Medical conditions modified by successful treatments
- ✅ **Success calculation**: `(intellect * 0.75) + (motorics * 0.25)` formula implemented

*Note: Phase 2 consumption method system provides foundation for broader drug/substance system expansion*

### Phase 2.5: Extended Consumption Methods - 🔲 PLANNED
- [ ] **Additional consumption commands**: `inhale`, `smoke`, `huff` with aliasing
- [ ] **Inhalation mechanics**: Respiratory delivery systems for substances  
- [ ] **Combustion consumption**: Smoking/burning substance delivery
- [ ] **Advanced substance interactions**: Multi-method delivery systems

### Phase 3: Combat Integration & Stat Penalties - 🔲 IN PROGRESS
- [ ] **Smart hit location system** based on attack success margin
- [ ] **Organ density-based targeting** - vital organ areas harder to hit precisely
- [ ] **Armor protection layers** - clothing/armor reduces damage to protected organs  
- [ ] **Armor damage system** - protective gear degrades from absorbing hits
- [ ] **Weapon penetration mechanics** - different weapons vs different armor types
- [ ] **Critical hit amplification** - exceptional attacks can bypass armor or hit vital organs directly

#### Hit Location Mechanics
```python
# Attack success determines hit precision
attack_roll = d20 + attacker_skill
defense_roll = d20 + defender_skill
success_margin = attack_roll - defense_roll

if success_margin >= 15:  # Exceptional success
    target_location = attacker_chooses_location()  # Deliberate targeting
elif success_margin >= 5:   # Good success  
    target_location = weighted_random(prefer_large_areas=True)  # Chest, torso likely
else:  # Marginal success
    target_location = weighted_random(prefer_extremities=True)  # Arms, legs likely

# Organ targeting within location based on hit precision
organs_in_location = get_organs_by_location(target_location)
if success_margin >= 10:
    # Can target specific vital organs
    target_organ = weighted_random(organs_in_location, allow_vital=True)
else:
    # Random organ in location, bias away from vital organs
    target_organ = weighted_random(organs_in_location, avoid_vital=True)
```

#### Armor Integration System
```python
# Layered protection check
worn_items = character.get_worn_items_for_location(hit_location)
protection_layers = []

for item in worn_items:
    if item.armor_rating and protects_location(item, hit_location):
        protection_layers.append({
            'item': item,
            'armor_rating': item.armor_rating,
            'armor_type': item.armor_type,  # 'leather', 'kevlar', 'plate', etc.
            'condition': item.condition      # 100% = perfect, 0% = destroyed
        })

# Calculate damage reduction
total_protection = 0
penetrating_damage = initial_damage

for layer in protection_layers:
    # Weapon vs armor type effectiveness
    penetration = get_penetration_value(weapon_type, layer['armor_type'])
    effective_armor = layer['armor_rating'] * (layer['condition'] / 100.0)
    
    damage_stopped = min(penetrating_damage, effective_armor * (1.0 - penetration))
    penetrating_damage -= damage_stopped
    
    # Damage the armor
    armor_damage = calculate_armor_damage(damage_stopped, weapon_type)
    layer['item'].take_armor_damage(armor_damage)
    
    if penetrating_damage <= 0:
        break  # Completely stopped by armor

# Apply remaining damage to organs
if penetrating_damage > 0:
    target_organ.take_damage(penetrating_damage, injury_type)
```

#### Weapon vs Armor Matrix
```python
PENETRATION_VALUES = {
    # weapon_type: { armor_type: penetration_percentage }
    'bullet': {
        'cloth': 0.95,      # Bullets easily penetrate cloth
        'leather': 0.80,    # Some protection vs bullets
        'kevlar': 0.30,     # Designed to stop bullets
        'plate': 0.60       # Depends on caliber vs thickness
    },
    'stab': {
        'cloth': 0.90,      # Knives cut through cloth
        'leather': 0.50,    # Leather provides good stab protection
        'kevlar': 0.70,     # Kevlar weak vs stabbing
        'plate': 0.20       # Plate excellent vs stabs
    },
    'cut': {
        'cloth': 0.85,      # Slashing cuts cloth easily  
        'leather': 0.60,    # Moderate protection
        'kevlar': 0.40,     # Good vs cuts
        'plate': 0.15       # Excellent protection
    },
    'blunt': {
        'cloth': 0.95,      # No protection vs blunt force
        'leather': 0.80,    # Minimal padding
        'kevlar': 0.70,     # Some cushioning
        'plate': 0.30       # Distributes impact well
    }
}
```

#### Integration with Existing Combat System
The tactical hit location system builds on the existing combat architecture:

**Current State**: Combat system calls `target.take_anatomical_damage(damage, "chest", injury_type)`
- All hits currently default to "chest" location
- Damage is distributed among chest organs (heart, lungs) by hit weights

**Phase 3 Enhancement**: 
```python
# In combat handler, replace current location targeting:
# OLD: target.take_anatomical_damage(damage, "chest", weapon.damage_type)

# NEW: Smart location targeting
attack_success_margin = attacker_roll - defender_roll  
hit_location = calculate_hit_location(attack_success_margin, attacker_intent)
final_damage = apply_armor_protection(damage, hit_location, target, weapon)
target.take_anatomical_damage(final_damage, hit_location, weapon.damage_type)
```

**Combat Command Integration**:
```python
# Enhanced attack commands with targeting options
> attack bandit             # Normal attack (success determines location)  
> attack bandit head        # Deliberate headshot (harder roll, -4 penalty)
> attack bandit center      # Aim for center mass (+2 bonus, chest/abdomen)
> attack bandit limbs       # Target extremities (+1 bonus, arms/legs only)
```

**Clothing/Armor System Integration**:
- Extends existing `clothing.py` system with armor ratings
- Uses current wear/remove mechanics  
- Builds on location-based coverage already in clothing system

#### Location Difficulty Modifiers
```python
HIT_LOCATION_DIFFICULTY = {
    # Higher values = harder to hit precisely
    'head': {
        'difficulty': 8,     # Small target, vital organs
        'organs': ['brain', 'left_eye', 'right_eye'],
        'vital_density': 'very_high'
    },
    'chest': {
        'difficulty': 4,     # Large target, but vital organs
        'organs': ['heart', 'left_lung', 'right_lung'],  
        'vital_density': 'high'
    },
    'abdomen': {
        'difficulty': 5,     # Medium target, some vital organs
        'organs': ['liver', 'stomach', 'left_kidney', 'right_kidney'],
        'vital_density': 'medium'
    },
    'left_arm': {
        'difficulty': 2,     # Easier to hit, no vital organs
        'organs': ['left_humerus', 'left_metacarpals'],
        'vital_density': 'none'
    },
    'right_leg': {
        'difficulty': 3,     # Large target, structural bones only
        'organs': ['right_femur', 'right_tibia', 'right_metatarsals'],
        'vital_density': 'none'  
    }
}
```

#### Technical Implementation Plan
**Phase 3.1: Hit Location System**
1. Create `world/combat/hit_location.py` module
2. Add `calculate_hit_location(success_margin, targeting_intent)` function
3. Define location difficulty constants and organ targeting weights
4. Update combat handler to use smart location targeting

**Phase 3.2: Armor Protection Layer** 
1. Extend `typeclasses/items.py` with armor properties:
   ```python
   # Add to clothing items
   armor_rating = 0         # Protection points
   armor_type = "none"      # 'leather', 'kevlar', 'plate', etc.
   max_condition = 100      # Durability when new
   current_condition = 100  # Current condition (damaged = less protection)
   protects_locations = []  # ['chest', 'abdomen'] etc.
   ```

2. Create `world/medical/armor_system.py` module:
   ```python
   def apply_armor_protection(damage, location, character, weapon):
       """Calculate damage after armor protection"""
       
   def damage_armor(item, damage_amount, weapon_type):
       """Apply wear and tear to protective equipment"""
   ```

**Phase 3.3: Integration Points**
1. Update `world/combat/handler.py` damage application
2. Extend weapon definitions with penetration characteristics  
3. Add armor condition display to clothing commands
4. Create armor repair mechanics (future: crafting system integration)

**Phase 3.4: Balancing and Testing**
1. Define penetration values through combat testing
2. Balance armor degradation rates vs availability
3. Tune hit location probabilities for tactical depth vs playability
4. Test integration with existing medical condition system

### Phase 4: Combat Integration & Stat Penalties
- [ ] Location-based damage system in combat
- [ ] Weapon-specific injury patterns  
- [ ] Critical injury immediate effects
- [ ] **Pain/injury penalties affecting dice rolls**: Unified with existing stat calculation systems
- [ ] **Medical condition modifiers**: Integration with combat, skill checks, and other game mechanics
- [ ] Medical emergency scenarios

*Note: Penalty mechanics will be unified with existing stat vs health calculations*

### Phase 5: Advanced Systems
- [ ] Long-term healing and recovery
- [ ] Infection and complication systems
- [ ] Prosthetics and permanent disabilities
- [ ] Advanced surgical procedures

## Example Medical Scenarios

### Tactical Combat Scenario (Phase 3)
```
Alice attacks Bob with a pistol. 
Attack roll: 18, Defense roll: 12 → Success margin: 6

Hit Location Calculation:
- Success margin 6 = "good success"  
- Weighted random favors large areas → chest selected
- Organs in chest: heart, left_lung, right_lung
- Success margin 6 < 10 → bias away from vital organs → right_lung targeted

Armor Check:
Bob wears: Kevlar vest (armor_rating: 15, condition: 85%, type: 'kevlar')
- Bullet vs kevlar penetration: 30%
- Effective armor: 15 × 0.85 = 12.75
- Damage stopped: 8 points (from 12 bullet damage)
- Penetrating damage: 4 points
- Kevlar vest takes 2 armor damage (now 83% condition)

Result:
- Bob's right_lung takes 4 bullet damage
- Develops "punctured_lung" condition (minor bleeding)
- Kevlar vest damaged but still functional
- Bob suffers breathing penalty (-1 to physical rolls)
```

### Armor Degradation Scenario
```
Charlie's leather jacket (condition: 60%) gets hit by knife attack.
- Stab vs leather penetration: 50%
- Effective armor: 8 × 0.60 = 4.8 protection
- Damage: 10 stab → 5 penetrates, 5 stopped
- Leather takes 3 armor damage
- New condition: 45% (getting worn down)

After several more hits:
- Leather condition drops to 20%
- Protection now only 1.6 points
- Next hit will likely penetrate fully
- Charlie needs to repair or replace armor
```

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
