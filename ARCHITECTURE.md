# File Structure & Architecture

## Overview

This document describes the complete file structure and architectural decisions for the Gelatinous MUD project. The organization follows Python best practices, Evennia conventions, and supports AI-driven development.

## Top-Level Directory Structure

```
gelatinous/
├── commands/              # Game commands organized by functionality
├── server/               # Server configuration and settings
├── typeclasses/          # Game object definitions (Evennia typeclasses)
├── web/                  # Web interface components
├── world/                # Game world logic, systems, and data
├── docker-compose.yml    # Docker configuration
└── PROJECT_OVERVIEW.md   # Main project documentation
```

## Commands Directory (`commands/`)

**Purpose**: Contains all game commands organized by functionality.

```
commands/
├── __init__.py           # Package initialization
├── command.py            # Base command classes
├── default_cmdsets.py    # Command set definitions
├── CmdAdmin.py          # Administrative commands
├── CmdCharacter.py      # Character management (stats, appearance, etc.)
├── CmdInventory.py      # Inventory and item manipulation
├── CmdSpawnMob.py       # Mob spawning for testing
└── combat/              # Combat command modules (see below)
```

### Combat Commands Subpackage (`commands/combat/`)

**Purpose**: Modular combat commands organized by tactical function.

```
commands/combat/
├── __init__.py              # Backward compatibility exports
├── cmdset_combat.py         # Combat command set definition
├── core_actions.py          # CmdAttack, CmdStop - fundamental actions
├── movement.py              # CmdFlee, CmdRetreat, CmdAdvance, CmdCharge
├── special_actions.py       # CmdGrapple, CmdEscape, CmdRelease, CmdDisarm, CmdAim
├── info_commands.py         # CmdLook - combat-aware information commands
└── README.md               # Combat commands documentation
```

**Design Rationale**:
- **Logical grouping**: Related commands grouped by tactical purpose
- **Maintainability**: Small, focused modules instead of monolithic files
- **Discoverability**: Clear naming indicates command functionality
- **Extensibility**: Easy to add new command modules

## Server Directory (`server/`)

**Purpose**: Server configuration, settings, and Evennia-specific setup.

```
server/
├── __init__.py
├── conf/                    # Configuration modules
│   ├── settings.py          # Main game settings
│   ├── at_initial_setup.py  # Initial game setup
│   ├── connection_screens.py # Login/logout screens
│   └── [other Evennia config files]
└── __pycache__/            # Python bytecode cache
```

**Design Rationale**:
- **Standard Evennia structure**: Follows platform conventions
- **Centralized configuration**: All settings in one location
- **Environment separation**: Different configs for dev/prod

## Typeclasses Directory (`typeclasses/`)

**Purpose**: Game object definitions using Evennia's typeclass system.

```
typeclasses/
├── __init__.py
├── accounts.py          # Player account objects
├── characters.py        # Character objects (PC/NPC)
├── objects.py          # Generic game objects
├── rooms.py            # Room objects
├── exits.py            # Exit objects
├── items.py            # Item objects
├── scripts.py          # Script objects
├── channels.py         # Communication channels
├── deathscroll.py      # Death/resurrection mechanics
└── README.md           # Typeclasses documentation
```

**Design Rationale**:
- **Evennia compliance**: Uses Evennia's typeclass inheritance system
- **Separation of concerns**: Each object type in its own module
- **G.R.I.M. integration**: Character stats and combat mechanics built in

## World Directory (`world/`)

**Purpose**: Game world logic, systems, and data separate from core mechanics.

```
world/
├── __init__.py
├── batch_cmds.ev        # Batch command definitions
├── help_entries.py      # Game help system
├── namebank.py          # Name generation
├── prototypes.py        # Object prototypes
├── combat/              # Combat system modules (see below)
└── README.md           # World systems documentation
```

### Combat System Subpackage (`world/combat/`)

**Purpose**: Core combat system implementation with modular architecture.

```
world/combat/
├── __init__.py              # Package initialization with exports
├── constants.py             # All combat constants (50+ definitions)
├── utils.py                 # Utility functions for combat operations
├── handler.py               # Main combat handler (refactored from legacy)
├── proximity.py             # Proximity relationship management
├── grappling.py             # Grappling system implementation
└── messages/               # Combat message templates
    ├── __init__.py
    ├── unarmed.py
    ├── knife.py
    └── [weapon-specific message files]
```

**Design Rationale**:
- **Modular architecture**: Each aspect of combat in focused modules
- **Constants centralization**: No magic strings throughout system
- **Utility functions**: Reusable code reduces duplication
- **Message organization**: Weapon-specific templates for rich narrative

## Web Directory (`web/`)

**Purpose**: Web interface components for browser-based interaction.

```
web/
├── __init__.py
├── urls.py              # URL routing
├── admin/               # Admin interface
├── api/                 # API endpoints
├── templates/           # HTML templates
├── webclient/           # Web client interface
└── website/             # Main website
```

**Design Rationale**:
- **Django integration**: Leverages Evennia's Django foundation
- **Separation of concerns**: API, admin, and client interfaces separated
- **Template organization**: Structured for maintainability

## Architecture Principles

### 1. **Modular Design**
- **Single Responsibility**: Each module has a clear, focused purpose
- **Loose Coupling**: Modules interact through well-defined interfaces
- **High Cohesion**: Related functionality grouped together

### 2. **Python Best Practices**
- **PEP 8 Compliance**: Consistent code style throughout
- **Clear Naming**: Descriptive names for modules, classes, and functions
- **Proper Documentation**: Comprehensive docstrings and comments
- **Type Safety**: Appropriate type hints and validation

### 3. **Evennia Integration**
- **Platform Patterns**: Uses Evennia's Script, Handler, and Command patterns
- **Typeclass System**: Leverages Evennia's object inheritance model
- **Database Integration**: Proper use of Evennia's ORM and attribute systems

### 4. **AI-Driven Development**
- **Predictable Structure**: Consistent organization aids AI understanding
- **Self-Documenting**: File names and structure indicate purpose
- **Pattern Consistency**: Similar patterns across all modules

## Key Design Decisions

### Combat System Refactoring
**Decision**: Split monolithic combat files into focused modules.
**Rationale**: Improved maintainability, easier debugging, clearer responsibilities.
**Impact**: Reduced complexity, enhanced extensibility, better testing.

### Constants Centralization
**Decision**: Extract all magic strings and numbers into constants.py.
**Rationale**: Eliminates typos, improves consistency, easier maintenance.
**Impact**: More reliable code, easier localization, better debugging.

### Utility Function Library
**Decision**: Create reusable utility functions for common operations.
**Rationale**: Reduces code duplication, improves consistency, easier testing.
**Impact**: Cleaner code, fewer bugs, faster development.

### Backward Compatibility
**Decision**: Maintain compatibility during refactoring through re-exports.
**Rationale**: Allows gradual migration, reduces risk, preserves existing code.
**Impact**: Smooth transition, no breaking changes, confidence in updates.

## Migration History

The current structure is the result of a comprehensive **24-hour system overhaul** that transformed:

### Before (Monolithic)
- Single 2000+ line `CmdCombat.py` file
- Scattered magic strings and hardcoded values
- Duplicated code across multiple functions
- Difficult to maintain and extend

### After (Modular)
- 8 focused combat command modules
- 50+ centralized constants
- Comprehensive utility function library
- Clear separation of concerns
- Maintainable and extensible architecture

## Future Considerations

### Planned Enhancements
- **Service Layer**: High-level service classes for complex operations
- **Event System**: Decoupled event handling for better modularity
- **Caching Layer**: Performance optimization for frequently accessed data
- **Testing Framework**: Comprehensive test suite for all modules

### Architectural Evolution
- **Domain Models**: Rich domain objects for complex game entities
- **Repository Pattern**: Abstracted data access for better testability
- **Plugin System**: Dynamic loading of game features and content
- **Microservices**: Potential separation of major subsystems

---

*This architecture balances immediate needs with long-term maintainability, following our core tenets of Python best practices, Evennia conventions, AI-friendly development, and open source community standards.*
