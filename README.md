# Gelatinous - Evennia MUD

Welcome to **Gelatinous**, a sophisticated text-based multiplayer game (MUD) built on the Evennia platform, featuring the **G.R.I.M. Combat System** - a roleplay-focused, turn-based combat engine.

## Quick Start

### Prerequisites
- Python 3.8+
- Evennia framework
- Virtual environment (recommended)

### Installation
1. Clone this repository
2. Activate your virtual environment
3. Install dependencies: `pip install evennia`
4. Initialize database: `evennia migrate`
5. Start the server: `evennia start`

### Connection
- **MUD Client**: Connect to `localhost:4000`
- **Web Client**: Open `http://localhost:4001` in your browser

## Core Features

### G.R.I.M. Combat System
- **Grit**: Physical toughness and endurance
- **Resonance**: Social awareness and empathy
- **Intellect**: Mental acuity and tactical thinking
- **Motorics**: Physical coordination and dexterity

### Combat Features
- Turn-based combat with initiative system
- Proximity-based engagement (melee vs ranged)
- Sophisticated grappling with restraint vs violent modes
- Yielding mechanics for non-violent resolution
- Multi-room combat support
- Rich narrative messaging system

## Documentation

### Essential Reading
- **[Project Overview](PROJECT_OVERVIEW.md)** - Core philosophy and features
- **[Architecture](ARCHITECTURE.md)** - File structure and technical decisions
- **[Combat System](COMBAT_SYSTEM.md)** - Complete G.R.I.M. system documentation
- **[Development Guide](DEVELOPMENT_GUIDE.md)** - Developer guidelines and best practices

### Additional Resources
- **[Changelog](CHANGELOG.md)** - Version history and release notes
- **[Evennia Documentation](https://www.evennia.com/docs/)** - Platform documentation
- **[Commands README](commands/README.md)** - Command system overview
- **[Combat Commands](commands/combat/README.md)** - Combat command details

## Project Structure

```
gelatinous/
├── commands/          # Game commands (modular structure)
│   └── combat/       # Combat commands by function
├── typeclasses/      # Game object definitions
├── world/            # Game world systems
│   └── combat/       # Combat system modules
├── server/           # Server configuration
└── web/              # Web interface components
```

## Development Philosophy

### Core Tenets
1. **Roleplay-First**: Combat enhances story, doesn't replace it
2. **Evennia-Native**: Leverage platform tools and conventions
3. **Clean Architecture**: Modular, maintainable, extensible code
4. **AI-Friendly**: Predictable structure for AI-assisted development

### Code Standards
- Python best practices (PEP 8, type hints, documentation)
- Centralized constants (no magic strings/numbers)
- Comprehensive error handling and logging
- Modular design with clear separation of concerns

## Recent Updates

The project recently completed a major **24-hour system overhaul** that transformed the combat system from a monolithic structure to a clean, modular architecture:

- ✅ **Modular Commands**: Split into focused modules by function
- ✅ **Constants System**: 50+ centralized constants eliminate magic values
- ✅ **Utility Functions**: Reusable code reduces duplication
- ✅ **Enhanced Grappling**: Nuanced restraint vs violent modes
- ✅ **Debug Infrastructure**: Comprehensive logging and error handling
- ✅ **Backward Compatibility**: No breaking changes during refactor

## Contributing

We welcome contributions that align with our core philosophy:
- Maintain roleplay-first approach
- Follow established architectural patterns
- Ensure comprehensive documentation
- Preserve Evennia-native development style

See [Development Guide](DEVELOPMENT_GUIDE.md) for detailed contribution guidelines.

## Support

### Getting Help
- Review the documentation files listed above
- Check the [Evennia documentation](https://www.evennia.com/docs/)
- Examine existing code for patterns and examples
- Use the comprehensive debug logging for troubleshooting

### Bug Reports
- Include detailed reproduction steps
- Provide relevant debug log output
- Describe expected vs actual behavior
- Test with the latest version

---

*Gelatinous is designed to be a platform for compelling storytelling through sophisticated roleplay mechanics. The combat system serves the narrative, providing depth and consequence while maintaining focus on character development and compelling stories.*

