# Combat System Refactor - Proposed File Structure

## Overview
This structure follows Python best practices, Evennia conventions, and maintains backward compatibility while improving organization and readability.

## Current Structure (what we have now)
```
world/
├── combathandler.py           # Main combat script/handler
├── combat_messages/           # Combat message files by weapon type
│   ├── __init__.py
│   ├── unarmed.py
│   ├── knife.py
│   └── [many weapon files...]
commands/
├── CmdCombat.py              # All combat commands in one file
├── default_cmdsets.py        # Command set definitions
```

## Proposed Refactored Structure

### Phase 1: Extract and Organize (maintain current functionality)
```
world/
├── combat/
│   ├── __init__.py
│   ├── constants.py          # Combat constants (stats, colors, channels, etc.)
│   ├── utils.py              # Utility functions (dice rolls, validation, debug)
│   ├── handler.py            # Refactored combathandler.py
│   ├── proximity.py          # Proximity management logic
│   ├── grappling.py          # Grappling-specific logic
│   ├── attributes.py         # Character attribute helpers (motorics, etc.)
│   └── messages/             # Keep existing structure, improve organization
│       ├── __init__.py       # Import get_combat_message function
│       ├── weapon_messages.py  # Core message loading logic
│       ├── unarmed.py
│       ├── knife.py
│       └── [all existing weapon files...]
commands/
├── combat/
│   ├── __init__.py
│   ├── cmdset_combat.py      # Combat command set
│   ├── core_actions.py       # attack, defend, yield, stop commands
│   ├── movement.py           # flee, retreat, advance, charge commands
│   ├── special_actions.py    # grapple, disarm, aim commands
│   └── info_commands.py      # look (combat-specific behavior)
├── CmdCharacter.py           # Keep existing, maybe enhance
├── default_cmdsets.py        # Updated imports
```

### Phase 2: Service Layer (if needed later)
```
world/
├── combat/
│   ├── services/             # Optional service layer
│   │   ├── __init__.py
│   │   ├── combat_service.py     # High-level combat operations
│   │   ├── proximity_service.py  # Proximity management service
│   │   └── grappling_service.py  # Grappling operations service
```

## Key Principles

### 1. Python Best Practice
- Clear, descriptive module names
- Logical grouping of related functionality
- Proper imports and dependencies
- PEP 8 compliance throughout
- Comprehensive docstrings

### 2. Evennia Best Practice
- Keep main handler as a Script (combat/handler.py)
- Use proper Command and CmdSet patterns
- Follow Evennia's typeclass conventions
- Maintain compatibility with existing Evennia patterns

### 3. AI-Driven Development Best Practice
- Clear separation of concerns
- Predictable file organization
- Self-documenting structure
- Easy to understand module purposes

### 4. Open Source Community Consumption
- README files in each major directory
- Clear examples and documentation
- Logical progression from simple to complex
- Easy to find and modify specific functionality

## Migration Plan

### Step 1: Extract Constants and Utils
- Create `world/combat/constants.py` with all magic numbers/strings
- Create `world/combat/utils.py` with shared utility functions
- Update imports in existing files

### Step 2: Reorganize Commands
- Split `CmdCombat.py` into logical command modules
- Create new cmdset structure
- Maintain all existing command functionality

### Step 3: Refactor Handler
- Move `combathandler.py` to `world/combat/handler.py`
- Extract proximity logic to `world/combat/proximity.py`
- Extract grappling logic to `world/combat/grappling.py`

### Step 4: Reorganize Messages
- Move `combat_messages/` to `world/combat/messages/`
- Improve message loading and organization

## Detailed Constants Breakdown (Based on Your Actual Code)

### 1. Character Attributes & Defaults
```python
# G.R.I.M. system defaults
DEFAULT_GRIT = 1
DEFAULT_RESONANCE = 1  
DEFAULT_INTELLECT = 1
DEFAULT_MOTORICS = 1

# Health system
DEFAULT_HP = 10
HP_GRIT_MULTIPLIER = 2

# Equipment defaults
DEFAULT_HANDS = {"left": None, "right": None}
DEFAULT_WEAPON_TYPE = "unarmed"
FALLBACK_WEAPON_NAME = "your fists"
```

### 2. Debug & Logging
```python
# Channel names
SPLATTERCAST_CHANNEL = "Splattercast"

# Debug message templates
DEBUG_TEMPLATE = "{prefix}_{action}: {message}"
DEBUG_PREFIXES = {
    "attack": "ATTACK_CMD",
    "flee": "FLEE_CMD", 
    "retreat": "RETREAT",
    "advance": "ADVANCE",
    "grapple": "GRAPPLE",
}

# Debug action types
DEBUG_ACTIONS = {
    "valid": "VALID",
    "invalid": "INVALID", 
    "success": "SUCCESS",
    "fail": "FAIL",
    "error": "ERROR",
    "failsafe": "FAILSAFE",
}
```

### 3. NDB Field Names (Critical for State Management)
```python
# Combat state fields
NDB_COMBAT_HANDLER = "combat_handler"
NDB_PROXIMITY = "in_proximity_with"
NDB_SKIP_ROUND = "skip_combat_round"

# Aiming state fields  
NDB_AIMING_AT = "aiming_at"
NDB_AIMED_AT_BY = "aimed_at_by"
NDB_AIMING_DIRECTION = "aiming_direction"
```

### 4. Combat Entry Database Fields
```python
# Handler database fields
DB_COMBATANTS = "combatants"
DB_COMBAT_RUNNING = "combat_is_running"
DB_MANAGED_ROOMS = "managed_rooms"

# Combatant entry fields
DB_CHAR = "char"
DB_TARGET_DBREF = "target_dbref"
DB_GRAPPLING_DBREF = "grappling_dbref" 
DB_GRAPPLED_BY_DBREF = "grappled_by_dbref"
DB_IS_YIELDING = "is_yielding"
```

### 5. Permission & Access
```python
# Permission strings
PERM_BUILDER = "Builder"
PERM_DEVELOPER = "Developer"

# Access types
ACCESS_TRAVERSE = "traverse"
ACCESS_VIEW = "view"
```

### 6. Color Codes & Message Formatting
```python
# Your existing color system
COLOR_SUCCESS = "|g"
COLOR_FAILURE = "|r" 
COLOR_WARNING = "|y"
COLOR_COMBAT = "|R"
COLOR_NORMAL = "|n"

# Box drawing characters (from your @stats command)
BOX_TOP_LEFT = "╔"
BOX_TOP_RIGHT = "╗"
BOX_BOTTOM_LEFT = "╚"
BOX_BOTTOM_RIGHT = "╝"
BOX_HORIZONTAL = "═"
BOX_VERTICAL = "║"
BOX_TEE_DOWN = "╠"
BOX_TEE_UP = "╣"
```

## Benefits

1. **Readability**: Clear file names indicate purpose
2. **Maintainability**: Related code is grouped together
3. **Testability**: Each module has clear responsibilities
4. **Extensibility**: Easy to add new combat features
5. **AI-Friendly**: Predictable structure for AI tools
6. **Community-Friendly**: Easy for contributors to navigate

## Backward Compatibility

All existing imports will be maintained through:
- `__init__.py` files with re-exports
- Gradual migration with deprecation warnings
- No breaking changes to existing API

This structure allows us to improve organization while maintaining the working combat system you've built.

---

## Commit Message Suggestion

```
docs: Add comprehensive combat system refactor plan

- Analyzed existing codebase patterns and extracted constants
- Designed Python/Evennia best practice structure preserving working code
- Planned incremental migration maintaining backward compatibility
- Prioritized readability, maintainability, and AI-driven development
- Documented detailed constants breakdown from actual code analysis
- Established clear phases for gradual refactor without breaking changes

Follows priority order: Python → Evennia → AI-driven → Open Source best practices
Ready for Step 1: Extract constants.py and utils.py
```
---
