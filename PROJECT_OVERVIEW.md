# Gelatinous - Evennia MUD Project

## Overview

**Gelatinous** is a sophisticated text-based multiplayer game (MUD) built on the Evennia platform, featuring the **G.R.I.M. combat system** - a roleplay-focused, turn-based combat engine that emphasizes both violent and non-violent conflict resolution.

## Core Design Philosophy

### The G.R.I.M. System
Our combat system is built around four core character attributes:
- **Grit**: Physical toughness, endurance, and willpower
- **Resonance**: Social awareness, empathy, and emotional intelligence  
- **Intellect**: Mental acuity, problem-solving, and tactical thinking
- **Motorics**: Physical coordination, dexterity, and reflexes

### Design Principles

**1. Roleplay-First Combat**
- Combat enhances narrative rather than dominating it
- Default to non-violent resolution (auto-yielding mechanics)
- Rich, contextual messaging for immersion
- Support for restraint-based conflicts alongside violent encounters

**2. Evennia-Native Development**
- Leverage Evennia's built-in tools and conventions
- Follow platform patterns for Scripts, Handlers, and Commands
- Maintain compatibility with Evennia's core functionality
- Use Evennia's typeclass system effectively

**3. Clean Architecture**
- Modular design with clear separation of concerns
- Python best practices throughout
- AI-friendly development patterns
- Open source community standards

**4. Developer Experience**
- Predictable file organization
- Comprehensive documentation
- Self-documenting code structure
- Easy contribution pathways

## Key Features

### Combat System
- **Turn-based combat** with initiative order
- **Proximity mechanics** (melee vs ranged engagement)
- **Grappling system** with restraint vs violent modes
- **Yielding mechanics** for peaceful resolution
- **Multi-room combat** support
- **Weapon-specific messaging** system

### Technical Features
- **Modular command structure** organized by functionality
- **Comprehensive constants system** (no magic strings)
- **Utility function library** for common operations
- **Robust state management** with NDB attribute handling
- **Extensive debug logging** for troubleshooting
- **Backward compatibility** maintained through refactoring

## Project Structure

```
gelatinous/
├── commands/              # Game commands organized by function
│   ├── combat/           # Combat-specific commands (modular)
│   ├── CmdCharacter.py   # Character management commands
│   ├── CmdInventory.py   # Inventory and item commands
│   └── ...
├── typeclasses/          # Game object definitions
│   ├── characters.py     # Character typeclass
│   ├── objects.py        # Object typeclass
│   ├── rooms.py          # Room typeclass
│   └── ...
├── world/                # Game world logic and systems
│   ├── combat/           # Combat system modules
│   ├── prototypes.py     # Object prototypes
│   └── ...
├── server/               # Server configuration
│   └── conf/            # Settings and configuration
└── web/                  # Web interface components
```

## Development Standards

### Priority Order for Decisions
1. **Python Best Practices** - Clean, readable, maintainable code
2. **Evennia Best Practices** - Platform-native development patterns  
3. **AI-Driven Development** - Predictable structure for AI assistance
4. **Open Source Community** - Easy contribution and understanding

### Code Quality Requirements
- Use centralized constants instead of magic strings/numbers
- Implement comprehensive utility functions to reduce duplication
- Include extensive debug logging for troubleshooting
- Maintain proper error handling throughout
- Ensure type safety and validation

## Getting Started

### For Players
1. Connect to the game server
2. Create your character and allocate G.R.I.M. stats
3. Explore the world and engage in roleplay
4. Use combat commands when conflict arises
5. Remember: combat should enhance story, not replace it

### For Developers
1. Examine the modular structure in `commands/combat/`
2. Review constants and utilities in `world/combat/`
3. Follow established patterns when adding new features
4. Maintain backward compatibility
5. Document your changes thoroughly

### For Contributors
1. Read the documentation in each module
2. Follow the established code style
3. Add appropriate tests for new functionality
4. Update documentation when making changes
5. Preserve the roleplay-first philosophy

## Recent Major Changes

The project recently completed a comprehensive **24-hour system overhaul** that transformed a monolithic combat system into a clean, modular architecture:

- **Combat commands** split into logical modules by functionality
- **Constants system** implemented to eliminate magic strings
- **Utility functions** created to reduce code duplication
- **State management** improved with robust NDB handling
- **Debug infrastructure** enhanced for better troubleshooting

## Future Development

The modular architecture supports easy implementation of:
- Additional combat actions and special abilities
- Environmental effects and terrain impact
- Advanced AI behaviors and dynamic difficulty
- Enhanced UI and visualization features
- Comprehensive tutorial and help systems

## Contributing

We welcome contributions that align with our core tenets:
- Maintain the roleplay-first philosophy
- Follow established architectural patterns
- Preserve Evennia-native development approach
- Ensure code quality and comprehensive documentation
- Test thoroughly and maintain backward compatibility

---

*Last Updated: July 10, 2025*
*Project Status: Active Development - Post-Refactor Stabilization*
