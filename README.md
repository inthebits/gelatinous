# Welcome to the G.E.L. M.O.N.S.T.E.R. Program

## *Genetic Engineering Laboratory - Manufactured Organism for Nuclear/Synthetic Testing and Experimental Research*

**Congratulations, Subject!** You've been selected to participate in our cutting-edge text-based multiplayer *experience* built on the Evennia platform. Our scientists assure us this experiment in tactical combat, roleplay mechanics, and atmospheric storytelling is completely voluntary and mostly safe.*

*\*Side effects may include existential dread, spontaneous combat encounters, and an inexplicable urge to check your inventory repeatedly.*

## 🧪 Join Our Elite Test Facility (Currently Decontaminating During Pre-Alpha)

**Live Testing Environment**: [play.gel.monster](https://gel.monster) Port 23  
*Temporarily offline while our research team "figures things out." No subjects were harmed in the making of this downtime.*

Connect with any MUD client when our containment protocols are restored!

## 🧬 The G.R.I.M. Enhancement Protocol

*Our proprietary enhancement system* based on four rigorously tested genetic modifications:

- **Grit**: Physical toughness and endurance *(Warning: May cause stubborn behavior)*
- **Resonance**: Social awareness and empathy *(Side effects include caring about others)*
- **Intellect**: Mental acuity and tactical thinking *(Subjects may experience "smart mouth syndrome")*
- **Motorics**: Physical coordination and dexterity *(Reduces likelihood of walking into walls)*

### Laboratory Testing Features (Recently Enhanced):
- Turn-based encounter simulations with initiative protocols
- **Advanced Proximity System** - Close-quarters vs ranged engagement with tactical movement
- **Complete Grappling Protocols** - Multi-participant restraint with contest mechanics, dragging, and human shield functionality  
- **Medical Trauma System** - Wound tracking, bleeding, pain management, and recovery protocols
- **Projectile Research Division** - Cross-room throwing mechanics with flight timing and interception
- **Environmental Trapping** - Exit rigging with defusal mechanics and chain reactions
- **Object Wrestling** - Grit-based contests for equipment acquisition
- **Clothing Integration** - Layered equipment system with armor mechanics
- **Consumption Protocols** - Substance intake and metabolic effects
- Multi-room tactical movement evaluations with proximity inheritance
- Peaceful resolution yielding mechanics *(Our legal department insists we mention this)*
- Natural language command processing with ordinal number recognition ("get 2nd chainsaw")
- Inventory consolidation algorithms for identical test materials
- Persistent targeting system with visual feedback indicators
- **Environmental Documentation** - Graffiti system for facility wall writings

*Results may vary. The G.E.L. facility is not responsible for any unintended mutations, tactical disadvantages, medical complications, or existential crises resulting from participation in our enhanced testing protocols.*

## 🔬 For Our Distinguished Research Partners & Code Archaeologists

**CLASSIFIED NOTICE**: Before conducting any modifications to our combat testing protocols, consult [`AGENTS.md`](AGENTS.md) - it contains vital containment procedures and approved research methodologies.

*Unauthorized tampering with the combat system may result in unexpected subject behavior, facility-wide incidents, or strongly worded memos from management.*

### Research Quick Access
- [Combat Testing Architecture](AGENTS.md#system-architecture)
- [Approved Research Patterns](AGENTS.md#common-patterns)
- [Incident Response Procedures](AGENTS.md#troubleshooting)

### Facility Features & Amenities
- Meticulously engineered separation of concerns across combat, medical, and environmental systems
- **Comprehensive Medical Division** - Trauma tracking, bleeding mechanics, pain management, and healing protocols
- **Advanced Combat Architecture** - Multi-participant grappling, proximity systems, and tactical positioning
- **Projectile Ballistics Lab** - Cross-room throwing with flight physics and interception mechanics
- 50+ centralized constants to eliminate "magic values" *(Our accounting department loves this)*
- State-of-the-art debug infrastructure *(Success rate improving with recent proximity fixes)*
- Roleplay-first design philosophy *(Subject immersion is our priority)*
- Atmospheric three-perspective combat messaging system *(Witnesses included at no extra charge)*
- Universal ordinal number support for intuitive command processing *(Because "get sword" is so primitive)*
- **Environmental Systems** - Weather effects, crowd dynamics, and facility documentation protocols

### New Researcher Orientation
For facility setup, constructing your own testing environment, or contributing to the Evennia research foundation, consult the [official Evennia documentation](https://github.com/evennia/evennia).

*The G.E.L. facility recommends all researchers complete proper safety training before handling experimental subjects.*

### Facility Architecture *(Actual Directory Structure)*

```
gelatinous/
├── commands/          # Subject command interface (various operational states)
│   ├── combat/       # Combat testing commands (grapple, advance, flee, aim, etc.)
│   ├── CmdInventory.py # Enhanced inventory with consolidation protocols
│   ├── CmdCharacter.py # Subject evaluation and statistics
│   ├── CmdThrow.py   # Projectile research mechanics (complete system)
│   ├── CmdMedical.py # Medical intervention and treatment protocols
│   ├── CmdClothing.py # Equipment layering and armor systems
│   ├── CmdConsumption.py # Substance intake and metabolic protocols
│   └── CmdGraffiti.py # Environmental documentation system
├── typeclasses/      # Experimental organism definitions
│   ├── objects.py    # Base protocols with ordinal number processing
│   ├── characters.py # Subject profiles and G.R.I.M. modifications
│   ├── items.py      # Research materials and interaction behaviors
│   └── rooms.py      # Testing environments and chamber features
├── world/            # Core facility operations
│   ├── combat/       # G.R.I.M. testing engine modules
│   │   ├── handler.py    # Combat state coordination
│   │   ├── constants.py  # Testing parameters
│   │   ├── messages/     # 95+ atmospheric interaction message files
│   │   ├── proximity.py  # Tactical positioning systems
│   │   ├── grappling.py  # Restraint and contest mechanics
│   │   └── utils.py      # Combat support algorithms
│   ├── medical/      # Trauma and recovery systems
│   │   ├── core.py       # Medical state management
│   │   ├── conditions.py # Wound and status tracking
│   │   ├── script.py     # Automated medical processes
│   │   └── wounds/       # Injury classification and effects
│   ├── crowd/        # Population dynamics simulation
│   └── weather/      # Environmental controls and atmospheric effects
├── server/           # Administrative configuration (Evennia)
├── specs/            # Research proposals and expansion plans (20+ detailed specs)
└── docs/             # Comprehensive facility documentation
```

## � Research Documentation & Safety Manuals

### Primary Research Documents
- **[Combat Testing Protocols](COMBAT_SYSTEM.md)** - Comprehensive G.R.I.M. methodology
- **[Facility Architecture](ARCHITECTURE.md)** - Engineering decisions and structural patterns
- **[Research Guidelines](DEVELOPMENT_GUIDE.md)** - Contribution protocols and safety procedures
- **[Project Charter](PROJECT_OVERVIEW.md)** - Core mission and design philosophy
- **[Research Partner Guide](AGENTS.md)** - AI development and integration handbook

### Current Project Status
- 🧪 **Combat Response System** - Message protocols converted *(Performance within acceptable parameters)*
- 🧪 **Advanced Grappling Protocols** - Multi-participant restraint with contest mechanics *(Recently enhanced)*
- 🩸 **Medical Trauma Division** - Wound tracking, bleeding, and recovery systems *(Operational)*
- 💉 **Projectile Ballistics Lab** - Complete throwing system with flight physics *(Production ready)*
- 🔒 **Proximity Enforcement** - Tactical positioning with recent bypass vulnerability patches *(Security enhanced)*
- 🧠 **Natural Language Processing** - Ordinal number recognition *(Subjects report improved usability)*
- 📦 **Equipment Organization** - Identical item consolidation with clothing layers *(Storage efficiency optimized)*
- 🎯 **Targeting Enhancement** - Persistent visual feedback systems *(Accuracy metrics improving)*
- ⚠️ **Environmental Expansion** - See [Research Proposals](specs/) for 20+ ambitious development plans

*Quality assurance ongoing. Individual results may vary. Recent security patches have eliminated proximity bypass exploits.*

---

**DISCLAIMER**: *The G.E.L. M.O.N.S.T.E.R. Program is an experimental research initiative. Participation is voluntary and subjects are free to leave at any time.* 

*\*Facility exit procedures may require completion of standard decontamination protocols. Management is not responsible for any lingering effects of genetic modification or tactical combat training. For questions, complaints, or mutation reports, please contact our Customer Relations department at your earliest convenience.*

**WARNING**: *This facility is a work in progress and our research team is still figuring things out. Side effects of exposure may include uncontrollable urges to optimize combat strategies and an inexplicable fondness for turn-based tactical planning.*

