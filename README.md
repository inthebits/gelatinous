# Gelatinous Monster

**Gelatinous Monster** is a MUD (Multi-User Dungeon) built on the [Evennia](https://www.evennia.com/) engine. It blends 1980s urban realism, cyberpunk noir, and eldritch sci-fi into a richly immersive text-based world. Inspired by works like *Chinatown*, *Disco Elysium*, *They Cloned Tyrell*, and *Fear and Loathing in Las Vegas*, this project focuses on roleplay-heavy interaction, emergent storytelling, and tactical, round-based combat. Our website is available at https://gel.monster

---

## Core Concepts

### 🎭 Roleplay and Atmosphere
- **Immersive scripting**: Uses scripting syntax to guide reactive storytelling.
- **No forced emotes**: NPCs suggest or respond—never override player agency.
- **Ambient world**: Street descriptions, weather, and crowd noise will eventually be ambient systems layered over basic rooms.

### 🧠 Character Stats: G.R.I.M.
- `Grit` – Physical endurance and brute strength.
- `Resonance` – Mental/spiritual attunement, empathy, and psionic sensitivity.
- `Intellect` – Problem-solving and technical know-how.
- `Motorics` – Reaction speed, finesse, and reflexes.

Stat displays follow a strict 52-character ASCII box format with 48-character interior rows.

---

## ⚔️ Combat System

- **Round-Based (DIKU-style)**: Each participant takes actions in initiative order.
- **Initiative**: Determined once per combat based on a Motorics roll.
- **Auto-Attacks**: Characters attack unless they've taken another action.
- **Commands**:
  - `kill <target>` – Initiate combat.
  - `flee` – Attempt to escape room.
  - `heal` – Admin command to restore HP.
- **Upcoming**:
  - Support for weapon hands (right/left)
  - Posture and range mechanics (guarded/offensive/retreat/etc.)
  - Cover and terrain bonuses

---

## 🧪 Developer Guidelines

### ✅ Design Philosophy
- Use **Evennia-native tools** (`delay()`, `repeat()`, `DefaultScript`, etc.)
- Avoid `Twisted` unless modifying Telnet/web protocols.
- Keep combat logic modular—avoid hardcoding single-use actions.

### 🚫 Avoid
- Duplicate imports in multiple scopes.
- Starting combat loops before both combatants are registered.
- Relying on `.db` for attributes that can be real properties.

---

## 🧙 Staff Workflow

- Rooms can have duplicate names (e.g. *Braddock Avenue*) for immersion; staff should use `@examine` or object IDs.
- `CmdAdmin` houses admin-only commands like `heal`.
- Combat debugging is verbose by design, but will be toggleable in production.

---

## 📂 Repository Structure (Highlights)

```
world/
├── combathandler.py   # Main combat system logic
├── CmdCombat.py       # Combat command set (kill, flee, etc)
├── CmdAdmin.py        # Admin commands (heal, etc)
├── characters.py      # Player and NPC character typeclass
└── namebank.py        # Names for random generation
```

---

## 🤝 Contributions

While this project is not currently open to outside contributors, if you're exploring MUD development with Evennia or a fan of interactive fiction, feel free to poke around.

