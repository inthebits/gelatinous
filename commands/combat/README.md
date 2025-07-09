# Combat Commands Package

This package contains the refactored combat commands system, organized into logical modules following Python best practices and Evennia conventions.

## Structure

```
commands/combat/
├── __init__.py              # Package initialization with backward compatibility exports
├── cmdset_combat.py         # Combat command set definition
├── core_actions.py          # CmdAttack, CmdStop - fundamental combat actions
├── movement.py              # CmdFlee, CmdRetreat, CmdAdvance, CmdCharge - movement commands
├── special_actions.py       # CmdGrapple, CmdEscape, CmdRelease, CmdDisarm, CmdAim - special actions
├── info_commands.py         # CmdLook - information and awareness commands
└── README.md               # This file
```

## Design Principles

### 1. Python Best Practices
- Clear, descriptive module names that indicate functionality
- Logical grouping of related commands
- Proper imports and dependency management
- Comprehensive docstrings for all modules and classes

### 2. Evennia Best Practices
- Maintains proper Command and CmdSet patterns
- Follows Evennia's typeclass conventions
- Compatible with existing Evennia command system
- Proper use of locks and permissions

### 3. AI-Driven Development Best Practices
- Predictable file organization for easy navigation
- Self-documenting code structure
- Clear separation of concerns
- Consistent naming patterns

### 4. Open Source Community Best Practices
- README documentation in each major directory
- Clear examples and usage patterns
- Easy to understand module purposes
- Gradual progression from simple to complex concepts

## Module Descriptions

### core_actions.py
Contains the fundamental combat commands that initiate or control combat flow:
- **CmdAttack**: Primary combat initiation command with proximity and weapon validation
- **CmdStop**: Stop attacking/aiming commands for controlling aggressive actions

These commands form the core of the combat system and are used most frequently by players.

### movement.py
Contains commands related to movement and positioning in combat:
- **CmdFlee**: Attempt to flee from combat or aiming situations
- **CmdRetreat**: Disengage from melee proximity within the same room
- **CmdAdvance**: Close distance with a target for melee engagement
- **CmdCharge**: Recklessly charge at a target with potential bonuses/penalties

These commands handle tactical movement aspects, allowing strategic positioning.

### special_actions.py
Contains specialized combat commands that add tactical depth:
- **CmdGrapple**: Initiate a grapple with a target
- **CmdEscapeGrapple**: Attempt to escape from being grappled
- **CmdReleaseGrapple**: Release a grapple you have on someone
- **CmdDisarm**: Attempt to disarm a target's weapon
- **CmdAim**: Aim at a target or direction for ranged attacks

These provide advanced tactical options for experienced combatants.

### info_commands.py
Contains commands that provide information during combat:
- **CmdLook**: Enhanced look command with combat-specific information

Helps players understand the current combat situation for informed decisions.

## Integration with New Modular Structure

This commands package integrates seamlessly with the new combat system modules:

### Constants Integration
All commands use constants from `world.combat.constants` instead of hardcoded strings:
```python
from world.combat.constants import (
    MSG_ATTACK_WHO, MSG_SELF_TARGET, MSG_NOT_IN_COMBAT,
    DEBUG_PREFIX_ATTACK, COLOR_SUCCESS, COLOR_FAILURE
)
```

### Utilities Integration
Commands leverage utility functions from `world.combat.utils`:
```python
from world.combat.utils import (
    get_numeric_stat, get_highest_opponent_stat, filter_valid_opponents,
    initialize_proximity_ndb, validate_combat_target
)
```

### Proximity Management
Uses the proximity module for all proximity-related operations:
```python
from world.combat.proximity import (
    establish_proximity, break_proximity, is_in_proximity
)
```

### Grappling Integration
Integrates with the grappling module for grapple state management:
```python
from world.combat.grappling import (
    establish_grapple, break_grapple, is_grappling, is_grappled
)
```

## Backward Compatibility

The package maintains full backward compatibility through:

1. **Re-exports in __init__.py**: All commands are re-exported so existing imports continue to work
2. **Preserved Command Names**: All command keys and aliases remain unchanged
3. **Same Functionality**: Core behavior is preserved while improving organization
4. **Gradual Migration**: Old monolithic file can coexist during transition

## Usage Examples

### In Command Sets
```python
from commands.combat import CombatCmdSet

class CharacterCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CombatCmdSet)
```

### Individual Command Import
```python
from commands.combat.core_actions import CmdAttack
from commands.combat.movement import CmdFlee, CmdRetreat
```

### Using New Utilities
```python
from world.combat.utils import get_numeric_stat, opposed_roll
from world.combat.constants import MSG_ATTACK_WHO, DEBUG_PREFIX_ATTACK

# Example in a command
def func(self):
    if not self.args:
        self.caller.msg(MSG_ATTACK_WHO)
        return
        
    caller_motorics = get_numeric_stat(self.caller, "motorics")
    result = opposed_roll(self.caller, target, "motorics")
```

## Migration Status

### Completed
✅ Created modular package structure
✅ Extracted constants to `world.combat.constants`
✅ Created utility functions in `world.combat.utils`
✅ Migrated CmdAttack to use new constants and utilities
✅ Migrated CmdRetreat to use new constants and utilities
✅ Created proximity and grappling modules
✅ Started migration of CmdAdvance and CmdCharge

### In Progress
🔄 Complete migration of all commands to new modules
🔄 Finish extracting all hardcoded strings to constants
🔄 Complete utility function migration

### Pending
⏳ Move remaining commands to appropriate modules
⏳ Complete CmdSet integration testing
⏳ Update default_cmdsets.py to use new structure
⏳ Add comprehensive unit tests for each module
⏳ Performance testing and optimization

## Benefits Achieved

1. **Improved Maintainability**: Related commands are now grouped logically
2. **Better Testability**: Each module can be tested independently
3. **Enhanced Readability**: Clear file names indicate purpose and content
4. **Easier Extension**: New commands can be added to appropriate modules
5. **AI-Friendly Structure**: Predictable organization aids AI-assisted development
6. **Community Contribution**: Clear structure makes it easier for contributors to understand and modify

## Next Steps

1. Continue migrating remaining commands from monolithic CmdCombat.py
2. Complete the extraction of all magic strings to constants
3. Add comprehensive error handling and validation
4. Create unit tests for each command module
5. Update documentation with usage examples
6. Performance profiling and optimization
