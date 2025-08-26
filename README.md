# Gelatinous Monster

**Gelatinous Monster** is a text-based multiplayer game experiment in early development, built on the Evennia platform. It's attempting to blend tactical combat, roleplay mechanics, and atmospheric storytelling.

## 🌃 Play in the near to distant future (Closed during Pre-Alpha)

**Live Game**: [play.gel.monster](https://gel.monster) Port 23  
*Currently offline while we figure things out.*

Connect with any MUD client when it's actually running.

## ⚔️ The G.R.I.M. System

An experimental system based on four core stats:

- **Grit**: Physical toughness and endurance
- **Resonance**: Social awareness and empathy  
- **Intellect**: Mental acuity and tactical thinking
- **Motorics**: Physical coordination and dexterity

Combat features (in various states of working):
- Turn-based encounters with initiative system
- Proximity mechanics for melee vs ranged engagement
- Grappling system with restraint and violence modes
- Multi-room tactical movement
- Yielding mechanics for non-violent resolution
- Natural language commands with ordinal number support ("get 2nd sword")
- Inventory consolidation for identical items
- Persistent aim system with visual feedback

## 🤖 For AI Agents & Developers

**IMPORTANT**: Before working on the combat system, read [`AGENTS.md`](AGENTS.md) - it contains critical architecture information and common patterns.

### Quick Links
- [Combat System Architecture](AGENTS.md#system-architecture)
- [Common Patterns](AGENTS.md#common-patterns)
- [Troubleshooting](AGENTS.md#troubleshooting)

### Key Features
- Attempts at clean separation of concerns across combat, commands, and world systems
- 50+ centralized constants to eliminate magic values (probably)
- Debug infrastructure that sometimes helps
- Roleplay-first design philosophy (in theory)
- Combat message system with atmospheric three-perspective messaging
- Universal ordinal number support for natural language commands

### Getting Started
For development setup, building your own MUD, or contributing to Evennia itself, see the [official Evennia documentation](https://github.com/evennia/evennia).

### Architecture Highlights

```
gelatinous/
├── commands/          # Player commands (various states of working)
│   ├── combat/       # Combat commands (grapple, advance, flee, aim, etc.)
│   ├── CmdInventory.py # Enhanced inventory with consolidation attempts
│   ├── CmdCharacter.py # Character sheet and stats
│   ├── CmdThrow.py   # Throwing mechanics
│   └── CmdGraffiti.py # Environmental writing system
├── typeclasses/      # Game object definitions
│   ├── objects.py    # ObjectParent with ordinal number support
│   ├── characters.py # Character classes and G.R.I.M. stats
│   ├── items.py      # Item definitions and behaviors
│   └── rooms.py      # Room types and features
├── world/            # Game world systems
│   ├── combat/       # G.R.I.M. combat engine modules
│   │   ├── handler.py    # Combat state management
│   │   ├── constants.py  # Combat configuration
│   │   ├── messages/     # 95+ atmospheric combat message files
│   │   └── utils.py      # Combat utility functions
│   ├── crowd/        # Dynamic crowd system
│   └── weather/      # Weather effects
├── server/           # Evennia configuration
└── specs/            # Design documents and future plans
```

## 📚 Documentation

### Core Documentation
- **[Combat System](COMBAT_SYSTEM.md)** - Deep dive into G.R.I.M. mechanics
- **[Architecture](ARCHITECTURE.md)** - Technical decisions and patterns
- **[Development Guide](DEVELOPMENT_GUIDE.md)** - Contributing guidelines
- **[Project Overview](PROJECT_OVERVIEW.md)** - Design philosophy
- **[Agent Reference](AGENTS.md)** - AI development guide

### System Status
- ✅ **Combat Message System** - Messages converted (probably working)
- ✅ **Ordinal Number Support** - Natural language commands seem to work
- ✅ **Inventory Consolidation** - Identical items grouped (mostly)
- ✅ **Aim System Enhancement** - Persistent visual feedback attempts
- 🚧 **Everything Else** - See [specs/](specs/) for ambitious plans

---

*Gelatinous Monster is a work in progress and I have no idea what I'm doing.*

