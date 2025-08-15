# Gelatinous Monster

**Gelatinous Monster** is a text-based multiplayer game in development, built on the Evennia platform. It aspires to feature tactical combat, roleplay mechanics, and atmospheric storytelling.

## 🌃 Play in the near to distant future (Closed during Pre-Alpha)

**Live Game**: [play.gel.monster](https://gel.monster) Port 23

Connect with any MUD client.

## ⚔️ The G.R.I.M. System

System based on four core stats:

- **Grit**: Physical toughness and endurance
- **Resonance**: Social awareness and empathy  
- **Intellect**: Mental acuity and tactical thinking
- **Motorics**: Physical coordination and dexterity

Combat features:
- Turn-based encounters with initiative system
- Proximity mechanics for melee vs ranged engagement
- Grappling system with restraint and violence modes
- Multi-room tactical movement
- Yielding mechanics for non-violent resolution

## 🤖 For AI Agents & Developers

**IMPORTANT**: Before working on the combat system, read [`AGENTS.md`](AGENTS.md) - it contains critical architecture information and common patterns.

### Quick Links
- [Combat System Architecture](AGENTS.md#system-architecture)
- [Common Patterns](AGENTS.md#common-patterns)
- [Troubleshooting](AGENTS.md#troubleshooting)

### Key Features
- Clean separation of concerns across combat, commands, and world systems
- 50+ centralized constants eliminate magic values
- Comprehensive debug infrastructure
- Roleplay-first design philosophy

### Getting Started
For development setup, building your own MUD, or contributing to Evennia itself, see the [official Evennia documentation](https://github.com/evennia/evennia).

### Architecture Highlights

```
gelatinous/
├── commands/          # Player commands organized by function
│   └── combat/       # Combat commands (grapple, advance, flee, etc.)
├── typeclasses/      # Game object definitions (characters, rooms, items)
├── world/            # Game world logic and systems
│   └── combat/       # Modular combat engine (G.R.I.M. system)
├── server/           # Evennia server configuration
└── web/              # Web interface customizations
```

## 📚 Documentation

- **[Combat System](COMBAT_SYSTEM.md)** - Deep dive into G.R.I.M. mechanics
- **[Architecture](ARCHITECTURE.md)** - Technical decisions and patterns
- **[Development Guide](DEVELOPMENT_GUIDE.md)** - Contributing guidelines
- **[Project Overview](PROJECT_OVERVIEW.md)** - Design philosophy

## 🤝 Contributing

We welcome pull requests that enhance the atmosphere or improve the codebase:

- Follow established code patterns
- Test thoroughly (the streets are unforgiving)
- Document your changes

For major changes, open an issue first to discuss your ideas.

---

*Gelatinous Monster is a work in progress and I have no idea what I'm doing.*

