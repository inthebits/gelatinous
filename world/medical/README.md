# Medical System - Phase 1 Implementation

This document describes the Phase 1 implementation of the Gelatinous Monster Health and Substance System.

## What's Implemented

### Core Medical System Foundation
- ✅ **Individual Bone Anatomy**: Hospital-grade anatomical accuracy with specific bones (humerus, femur, tibia, metacarpals, metatarsals)
- ✅ **Organ System**: Individual organs with HP, functionality, and anatomical mapping
- ✅ **Body Capacities**: Vital and functional capacities affected by organ health with bone-specific contributions
- ✅ **Medical Conditions**: Status effects like bleeding, fractures, infections
- ✅ **Medical State**: Complete medical tracking with persistence
- ✅ **Vital Signs**: Blood level, pain level, consciousness tracking
- ✅ **Anatomical Damage**: Location-based damage with organ targeting
- ✅ **Migration Tools**: Administrative commands for updating existing characters to new anatomy

### Character Integration
- ✅ **Medical State Persistence**: Stored in `character.db.medical_state`
- ✅ **Enhanced Damage System**: `take_anatomical_damage()` method with injury types
- ✅ **Death Conditions**: Death from vital organ failure or blood loss
- ✅ **Unconsciousness**: Based on consciousness capacity and vital signs
- ✅ **Legacy Compatibility**: Existing HP system still works alongside medical system

### Available Commands
- ✅ `medical [target]` - Check medical status
- ✅ `medinfo [organs|conditions|capacities]` - Detailed medical information
- ✅ `damagetest <amount> [location] [injury_type]` - Test damage application
- ✅ `healtest [condition|all]` - Test healing (development command)
- ✅ `@resetmedical [character|confirm all]` - Reset character medical states (admin)
- ✅ `@medaudit` - Comprehensive medical system diagnostics (admin)

## System Architecture

### Data Storage
Medical state is persisted in the character database:
```python
character.db.medical_state = {
    "organs": {"brain": {"current_hp": 8, "max_hp": 10, ...}, ...},
    "conditions": [{"type": "bleeding", "location": "chest", ...}, ...],
    "blood_level": 85.0,
    "pain_level": 23.0,
    "consciousness": 78.0
}
```

### Damage Flow
1. `character.take_anatomical_damage(damage, location, injury_type)`
2. Damage distributed to organs in location based on hit weights
3. Medical conditions generated based on injury type and severity
4. Vital signs updated (blood loss, pain, consciousness)
5. Medical state saved to database

### Body Capacities
Organs contribute to body capacities that affect character function:
- **Vital**: `consciousness`, `blood_pumping`, `breathing`, `digestion`
- **Functional**: `sight`, `hearing`, `moving`, `manipulation`, `talking`

Individual bones provide specific capacity contributions:
- **Long Bones**: Femur and tibia each contribute 40% to moving capacity
- **Arm Bones**: Humerus contributes 40% to manipulation capacity
- **Hand/Foot Bones**: Metacarpals (20%) and metatarsals (10%) for fine motor functions

### Death Conditions
Character dies if:
- Heart destroyed (blood_pumping = 0)
- Both lungs destroyed (breathing = 0)  
- Liver destroyed (digestion = 0)
- Blood loss exceeds fatal threshold (85% by default)

## Usage Examples

### Basic Medical Check
```
> medical
Your Medical Status:
CONSCIOUS
Blood Level: 87.3%
Pain Level: 15.2
Consciousness: 92.1%
Active Conditions:
  - Bleeding (moderate) (chest)
  - Fracture (minor) (left_arm)
Damaged Organs:
  - heart: 73.3% functional
  - left_arm_system: 85.0% functional
```

### Applying Anatomical Damage
```python
# In code
results = character.take_anatomical_damage(15, "chest", "stab")
# Creates bleeding condition, damages heart/lungs

# Via command (testing)
> damagetest 12 left_arm blunt
You take 12 blunt damage to your left_arm!
Organs damaged:
  - left_arm_system: 12 damage
New conditions:
  - Fracture (moderate)
```

### Detailed Organ Status
```
> medinfo organs
Organ Status:
┌────────────────────┬─────┬─────────────────┬──────────┐
│ Organ              │ HP  │ Status          │ Location │
├────────────────────┼─────┼─────────────────┼──────────┤
│ Brain              │10/10│ Healthy         │ head     │
│ Heart              │11/15│ Damaged         │ chest    │
│ Left Lung          │15/20│ Damaged         │ chest    │
│ Right Lung         │20/20│ Healthy         │ chest    │
│ Left Humerus       │12/15│ Damaged         │ left_arm │
│ Right Femur        │18/20│ Damaged         │ right_leg│
└────────────────────┴─────┴─────────────────┴──────────┘
```

## Integration Points

### Combat System
The medical system integrates with combat through:
- Location-based damage targeting
- Weapon-specific injury patterns
- Critical hit effects on vital organs

### Longdesc System
Medical conditions automatically appear in character descriptions:
- Visible bleeding, fractures, and disfigurement
- Pain indicators and mobility issues
- Unconsciousness states

### Clothing System
Armor and clothing affect:
- Which body locations can be hit
- Damage reduction to organs
- Medical treatment accessibility

## Migration and Administration

### Character Migration
For existing characters that were created before the individual bone system:

```
# Reset a single character's medical state to current anatomy
> @resetmedical PlayerName

# Reset ALL characters to use individual bones (use with caution)
> @resetmedical confirm all

# Audit the medical system for inconsistencies
> @medaudit
```

The migration process:
1. Updates character medical states to use individual bones (humerus, femur, etc.)
2. Replaces old "system" organs with anatomically accurate bone structure
3. Preserves existing conditions and damage where possible
4. Provides safety confirmation for mass updates

## Testing

Run the integration test to validate the system:
```bash
python world/medical/test_integration.py
```

All tests should pass, validating:
- Organ damage and healing
- Medical condition application
- Vital sign calculation
- Body capacity computation
- Damage distribution logic
- State persistence (serialization)

## What's Next (Phase 2)

The next implementation phase will add:
- **Medical Tools**: Blood bags, surgical kits, bandages, painkillers
- **Consumption Commands**: `inject`, `apply`, `bandage`, `eat`, `drink`, etc.
- **Treatment Mechanics**: G.R.I.M.-based treatment success/failure
- **Medical Skill System**: Training and specialization
- **Tool Appropriateness**: Different tools for different conditions

## Files Added/Modified

### New Files
- `world/medical/__init__.py` - Package initialization
- `world/medical/constants.py` - All medical system constants
- `world/medical/core.py` - Core classes (Organ, MedicalCondition, MedicalState)
- `world/medical/utils.py` - Integration utilities and helper functions
- `world/medical/test_integration.py` - Comprehensive integration tests
- `commands/CmdMedical.py` - Medical system commands

### Modified Files
- `typeclasses/characters.py` - Added medical system integration
- `commands/default_cmdsets.py` - Added medical commands to character cmdset

## Constants and Balance

All numerical values are defined as constants in `world/medical/constants.py` for easy balancing:
- Death/unconsciousness thresholds
- Organ HP values and hit weights
- Treatment success modifiers
- Pain and blood loss rates

This allows for easy adjustment during testing and gameplay balancing.
