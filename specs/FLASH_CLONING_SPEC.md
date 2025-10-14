# Flash Cloning System Specification

## Document Status
- **Version:** 1.0 DRAFT
- **Date:** October 13, 2025
- **Status:** Architectural Design Phase
- **Priority:** CRITICAL - Blocks all gameplay progression

---

## Executive Summary

The Flash Cloning System is the core respawn mechanism for Gelatinous Monster. It closes the death loop by seamlessly transitioning dead characters through corporate memory upload into new clone bodies. This system must integrate with the existing death progression, medical system, and account management to create a complete lifecycle: **Creation → Death → Respawn → Death → Respawn...**

**Current State:** 🔴 **BROKEN** - Death loop never closes. Dead characters accumulate in limbo.

**Target State:** ✅ **SEAMLESS** - Death automatically triggers flash cloning. Players respawn with minimal friction.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Thematic Foundation](#thematic-foundation)
3. [Technical Architecture](#technical-architecture)
4. [Data Model](#data-model)
5. [Character Creation Flow](#character-creation-flow)
6. [Death & Respawn Flow](#death--respawn-flow)
7. [Account Management](#account-management)
8. [Integration Points](#integration-points)
9. [Implementation Phases](#implementation-phases)
10. [Testing Requirements](#testing-requirements)
11. [Edge Cases & Error Handling](#edge-cases--error-handling)
12. [Future Enhancements](#future-enhancements)

---

## Problem Statement

### Critical Bugs Identified

**Bug #1: Zombie Characters in Limbo**
- **Location:** `typeclasses/death_progression.py:571-582`
- **Severity:** CRITICAL
- **Description:** Dead characters are teleported to limbo but NEVER unpuppeted from their account. The unpuppeting code is commented out with TODO markers.
- **Impact:** 
  - Accounts remain attached to dead characters
  - Players can't create new characters (still puppeting old one)
  - Dead characters accumulate in limbo indefinitely
  - Blocks all respawn gameplay

**Bug #2: No Character Creation System**
- **Location:** Missing entirely from codebase
- **Severity:** CRITICAL
- **Description:** No command exists to create a character after account login. No character selection menu. No character roster display.
- **Impact:**
  - New accounts have no path to enter the game
  - Dead accounts have no path to respawn
  - `AUTO_PUPPET_ON_LOGIN = True` fails (nothing to puppet)
  - Website and telnet both broken

**Bug #3: Registration Disabled**
- **Location:** `server/conf/settings.py:48`
- **Severity:** HIGH
- **Description:** `NEW_ACCOUNT_REGISTRATION_ENABLED = False` blocks all new account creation
- **Impact:**
  - No new players can join
  - Development/testing requires manual account creation via Django admin
  - Public launch impossible in current state

**Bug #4: Empty Initial Setup**
- **Location:** `server/conf/at_initial_setup.py:16-17`
- **Severity:** MEDIUM
- **Description:** `at_initial_setup()` function is completely empty (just `pass`)
- **Impact:**
  - No starting location created beyond Evennia default Limbo (#2)
  - No default rooms or spawn points
  - No character creation prompts
  - Fresh server has nowhere for players to spawn

**Bug #5: Multisession Mode Mismatch**
- **Location:** `server/conf/settings.py:74,79`
- **Severity:** MEDIUM
- **Description:** `MULTISESSION_MODE = 1` (account-based) with `AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False` and `AUTO_PUPPET_ON_LOGIN = True` creates impossible state
- **Impact:**
  - Settings contradict each other
  - Login attempts auto-puppet but there's no character to puppet
  - Confusing error messages for users

### System Flow Gaps

**Current Death Flow (Broken):**
```
Character Dies → Death Curtain → Death Progression (6 min) → Corpse Created 
→ Character Teleported to Limbo → [STOPS HERE - NEVER UNPUPPETS]
```

**Missing Components:**
- Character unpuppeting from account
- Character archiving/deletion
- Account redirection to character creation
- Character creation menu/interface
- Character roster/selection system
- Respawn location management
- Flash cloning narrative integration

---

## Thematic Foundation

### Setting Context

**World:** Dystopian retrofuture "198█ (ENDLESS BROADCAST)"
- Corporate control
- Memory manipulation
- Body commodification
- Consciousness as data
- Surveillance state
- Flickering reality

**Visual Aesthetic:**
- VHS static and distortion
- Desaturated colors
- Test pattern graphics (connection screen)
- Blood-red violence (death curtain)
- Clinical/corporate language for tech

**Existing World-Building:**
- VECTOR UEM-3 detonator (military-grade corporate weapons)
- Splattercast debug channel (broadcast metaphor)
- Email-based authentication (identity as corporate credential)
- Medical system with granular organ damage (bodies are mechanical)

### Flash Cloning Narrative

**Core Concept:** Corporate Memory Upload & Clone Activation

**The Process:**
1. **Pre-Death:** Consciousness continuously backed up to corporate servers
2. **Death Event:** Original body fails, becomes corpse (evidence)
3. **Upload Window:** 6-minute grace period for manual revival OR automatic upload
4. **Clone Activation:** New body grown/printed by VECTOR Industries
5. **Memory Load:** Consciousness injected into fresh clone
6. **Reentry:** Clone awakens in Medical Reconstruction bay

**Thematic Implications:**
- Death is cheap (you respawn) but *meaningful* (your corpse can be investigated)
- Corporate control over life/death (they own your backup)
- Identity questions (are you the same person after 20 deaths?)
- Economic angle (cloning isn't free - debt? Company scrip?)
- Memory degradation (death_count affects RP, maybe skills?)

**Terminology:**
- **Stack:** The persistent consciousness/data (borrowed from Altered Carbon)
- **Sleeve:** The physical body (temporary, replaceable)
- **Resleeving:** The act of uploading into a new clone
- **Clone Generation:** How many times you've died (death_count)
- **Reconstruction Bay:** The respawn location

**Visual Moments:**
- Death curtain → Static → Test pattern → "SIGNAL REACQUIRED"
- Wake up in medical bay with fluorescent lights
- Vague memories of "the other you" dying
- Clone markers (maybe tattoo? Serial number? Slight appearance shift?)

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    ACCOUNT LAYER                        │
│  (Email-based identity, persistent across clones)      │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼─────────┐
│  CHARACTER 1   │    │  CHARACTER 2     │
│  (Active)      │    │  (Archived)      │
│  Clone Gen 3   │    │  Clone Gen 2     │
└───────┬────────┘    └──────────────────┘
        │
        │ Puppets
        │
┌───────▼─────────────────────────────────────────┐
│              GAME WORLD                         │
│  - Combat System                                │
│  - Medical System                               │
│  - Death Progression                            │
│  - Corpse System                                │
└─────────────────────────────────────────────────┘
```

### Key Design Decisions

**Decision #1: One Active Character Per Account**
- **Rationale:** Simpler to implement, matches single-protagonist narrative
- **Implementation:** Accounts can have multiple archived characters but only one active
- **Future:** Could extend to multiple active characters if needed

**Decision #2: Preserve Character Objects**
- **Rationale:** Investigation RP, admin forensics, player history
- **Implementation:** Dead characters archived rather than deleted
- **Storage:** `character.db.archived = True`, moved to Limbo or Archive room

**Decision #3: Flash Cloning is Automatic**
- **Rationale:** Minimize player downtime, maintain immersion
- **Implementation:** Death progression completion automatically triggers clone creation
- **Player Choice:** Name and appearance can be customized, but respawn is mandatory

**Decision #4: Stack Persistence Model**
- **Rationale:** Define what makes "you" persist across deaths
- **Implementation:** See Data Model section
- **Balancing:** Some progression persists, but death has consequences

### Core Systems Integration

**Existing Systems We Build On:**
1. ✅ **Death Curtain** (`typeclasses/curtain_of_death.py`) - Animation system
2. ✅ **Death Progression** (`typeclasses/death_progression.py`) - 6-minute timer
3. ✅ **Medical System** (`world/medical/*`) - Organ damage, wounds
4. ✅ **Corpse System** (`typeclasses/corpse.py`) - Forensic preservation
5. ✅ **Combat System** (`world/combat/*`) - Damage application
6. ✅ **Email Auth** (`commands/unloggedin_email.py`) - Account creation

**New Systems We Must Build:**
1. ❌ **Character Creation** - Name, appearance, spawn
2. ❌ **Character Selection** - Roster, switching (future)
3. ❌ **Flash Cloning** - Stack preservation, sleeve creation
4. ❌ **Spawn Management** - Respawn locations
5. ❌ **Account Hooks** - Post-login redirection

---

## Data Model

### Account Attributes

**Persistent (Never Reset):**
```python
account.db.email                  # str - Primary identifier (set by auth)
account.db.total_death_count      # int - Sum of all character deaths
account.db.characters_created     # int - Total clones spawned
account.db.first_clone_date       # float - timestamp of first character
account.db.account_flags          # dict - Admin flags, bans, notes
```

**Transient (Session-based):**
```python
account.ndb.in_character_creation # bool - Currently in creation flow
account.ndb.creation_step         # str - Current creation step name
account.ndb.creation_data         # dict - Temp data during creation
```

### Character Attributes (The Stack)

**Core Identity (Persists Across Clones):**
```python
character.db.clone_generation     # int - How many times this identity has died
character.db.stack_id             # str - Unique identifier for this consciousness
character.db.original_creation    # float - timestamp when Stack first created
character.db.current_sleeve_birth # float - timestamp when THIS clone was born
```

**Biological (Persists with Variation):**
```python
character.db.sex                  # str - Biological sex (can change between clones)
character.db.skintone             # str - Skin tone (can drift between clones)
character.db.original_skintone    # str - First clone's skintone (reference)
```

**Cognitive (Degrades with Death):**
```python
character.grit                    # int - Physical resilience
character.resonance               # int - Social/empathic ability  
character.intellect               # int - Mental acuity
character.motorics                # int - Physical coordination
# All start at 1, may increase with XP, may degrade with deaths
```

**Administrative:**
```python
character.db.archived             # bool - Is this an old clone?
character.db.archived_reason      # str - "death", "player_request", etc.
character.db.archived_date        # float - timestamp of archiving
character.db.death_cause          # str - How this clone died (if archived by death)
character.db.previous_clone_dbref # int - Link to previous clone (forensics)
character.db.corpse_dbref         # int - Link to corpse left behind (if died)
```

### Character Attributes (The Sleeve)

**Physical State (Reset on Clone):**
```python
# Medical system handles all of this:
character._medical_state          # MedicalState - Fresh on each clone
# Organs reset to full HP
# No wounds
# No conditions
# Blood at 100%
```

**Possessions (Lost on Death):**
```python
character.contents                # list - Inventory (transferred to corpse)
character.worn_items              # dict - Clothing (transferred to corpse)
character.hands                   # dict - Wielded items (transferred to corpse)
# All reset to empty/default on new clone
```

**Placement (Reset on Clone):**
```python
character.location                # Room - Starts at RESPAWN_ROOM on new clone
character.look_place              # str - "standing here" (default)
character.temp_place              # str - "" (empty)
character.override_place          # str - "" (empty)
```

### Corpse Attributes

**Already Implemented (Keep As-Is):**
```python
corpse.db.original_character_name        # str - Who this was
corpse.db.original_character_dbref       # int - Character object reference
corpse.db.original_account_dbref         # int - Account object reference
corpse.db.death_time                     # float - When they died
corpse.db.death_cause                    # str - How they died
corpse.db.wounds_at_death                # list - Forensic wound data
corpse.db.longdesc_data                  # dict - Physical appearance
corpse.db.original_skintone              # str - For proper rendering
corpse.db.original_gender                # str - For proper rendering
corpse.contents                          # list - All items/clothing from character
```

**New Addition:**
```python
corpse.db.clone_generation               # int - Which clone was this?
corpse.db.stack_id                       # str - Link to consciousness identity
```

### Settings Constants

**New Settings Required:**
```python
# server/conf/settings.py

# Flash Cloning System
RESPAWN_ROOM_DBREF = 3  # Medical Reconstruction Bay
CLONE_SPAWN_MESSAGE = True  # Show atmospheric spawn message
CLONE_MEMORY_DEGRADATION = True  # Each death slightly lowers stats
CLONE_MEMORY_LOSS_PERCENT = 2  # Lose 2% of XP per death (future)

# Character Creation
ENABLE_FLASH_CLONING = True  # Allow respawns
ENABLE_NEW_ACCOUNT_CHARS = True  # Allow first character creation
MAX_CHARACTERS_PER_ACCOUNT = 1  # Only one active character (for now)
ARCHIVE_OLD_CLONES = True  # Keep old clones or delete them?

# Death System
DEATH_CREATES_CORPSE = True  # Already implemented
DEATH_PROGRESSION_DURATION = 360  # 6 minutes (already implemented)
UNPUPPET_ON_FINAL_DEATH = True  # Fix for Bug #1
AUTO_RESPAWN_ON_FINAL_DEATH = True  # Trigger flash cloning automatically
```

---

## Character Creation Flow

### First-Time Account Creation

**Entry Points:**
1. Telnet: `create email@address.com password` (once registration enabled)
2. Website: Django registration form (future enhancement)

**Flow:**
```
1. Account Created
   ↓
2. Login Successful
   ↓
3. at_post_login() hook fires
   ↓
4. Check: account.db.characters_created == 0?
   ↓ YES
5. Start Character Creation
   ↓
6. Character Creation Menu
   ↓
7. Create Character Object
   ↓
8. Initialize Stack attributes
   ↓
9. Spawn at RESPAWN_ROOM
   ↓
10. Puppet character
   ↓
11. Send welcome messages
```

### Flash Cloning (Respawn After Death)

**Entry Point:** Death progression completes (`_complete_death_progression()`)

**Flow:**
```
1. Final Death (6 min expired)
   ↓
2. Create Corpse (already implemented)
   ↓
3. Archive Old Character
   - character.db.archived = True
   - character.db.archived_reason = "death"
   - character.db.death_cause = <from medical system>
   ↓
4. Unpuppet Character
   - account.unpuppet_object(session)
   ↓
5. Initiate Flash Cloning
   - create_flash_clone(account, old_character)
   ↓
6. Clone Creation
   - Copy Stack attributes
   - Increment clone_generation
   - Reset Sleeve attributes (medical, inventory, location)
   ↓
7. Spawn at RESPAWN_ROOM
   ↓
8. Puppet New Clone
   - account.puppet_object(session, new_character)
   ↓
9. Send Respawn Messages
   - Atmospheric "waking up" narrative
   - Stats display
   - Generation number
```

### Character Creation Menu

**OOC Interface Design:**

```
╔════════════════════════════════════════════════════════╗
║        VECTOR INDUSTRIES - CONSCIOUSNESS UPLOAD        ║
║              CLONE GENERATION INITIATED                ║
╚════════════════════════════════════════════════════════╝

SIGNAL ACQUIRED. LOADING STACK DATA...

Your consciousness has been uploaded to VECTOR servers.
A new sleeve is being prepared for you.

Please confirm identity parameters:

[1] Name: _______________________
    (What do people call you?)

[2] Biological Sex: [M]ale / [F]emale / [A]mbiguous
    (Chromosomal configuration of new sleeve)

[3] Appearance: [Randomize] / [Customize]
    (Physical features - skintone, build, distinguishing marks)

[4] Confirm and Deploy
    (Initialize sleeve and transfer consciousness)

Enter your choice [1-4]: _

╔════════════════════════════════════════════════════════╗
║  Type 'help' for more info | 'quit' to disconnect     ║
╚════════════════════════════════════════════════════════╝
```

**Implementation Approach:**
- Use Evennia's `EvMenu` system (built-in menu framework)
- Store choices in `account.ndb.creation_data`
- Validate inputs at each step
- Allow back/forward navigation
- Show preview before final creation

**Menu States:**
```python
# commands/charcreate.py

def node_welcome(caller, raw_string, **kwargs):
    """Entry node - welcome message"""
    
def node_name(caller, raw_string, **kwargs):
    """Name input and validation"""
    
def node_sex(caller, raw_string, **kwargs):
    """Biological sex selection"""
    
def node_appearance(caller, raw_string, **kwargs):
    """Appearance customization or randomization"""
    
def node_skintone(caller, raw_string, **kwargs):
    """Skintone selection (if customizing)"""
    
def node_confirm(caller, raw_string, **kwargs):
    """Final confirmation and character creation"""
    
def node_complete(caller, raw_string, **kwargs):
    """Creation complete - spawn into game"""
```

### Name Validation

**Rules:**
- 3-20 characters
- Letters, spaces, hyphens, apostrophes only
- No numbers or special characters
- Cannot start with space or punctuation
- No profanity (basic filter)
- Must be unique (check existing characters)

**Reserved Names:**
- Admin, Staff, System, Vector, Server, Bot, Guest
- (Import from constants file)

### Appearance System

**Option A: Randomized (Quick Start)**
- System generates random appearance
- Skintone selected from preset list
- Generic "unremarkable" longdesc
- Fast, minimal friction

**Option B: Customized (Full Control)**
- Player selects skintone from list
- Player writes custom longdesc per body part
- More RP flavor, higher engagement
- Slower, may intimidate new players

**Recommendation:** Offer both, default to Randomized
- "Press [R] to randomize and start playing immediately"
- "Press [C] to customize your appearance"

**Skintone Options:**
```python
SKINTONE_OPTIONS = [
    "pale",
    "fair", 
    "light brown",
    "olive",
    "tan",
    "brown",
    "dark brown",
    "deep brown",
    "black"
]
```

---

## Death & Respawn Flow

### Death Trigger Points

**Already Implemented:**
1. Medical system detects `is_dead() == True`
2. Character.at_death() called
3. Death curtain animation plays
4. Death progression script starts

**What We're Adding:**
5. Death progression completes
6. Unpuppet + archive old character
7. Flash cloning triggered
8. New character created and puppeted

### Detailed Death Progression Integration

**File:** `typeclasses/death_progression.py`
**Method:** `_complete_death_progression()`

**Current Code (Lines 331-400):**
```python
def _complete_death_progression(self):
    """Complete the death progression - character is now permanently dead."""
    character = self.obj
    # ... death messages sent ...
    # ... medical script cleanup ...
    
    # Complete death progression - corpse creation and character transition
    self._handle_corpse_creation_and_transition(character)
```

**New Code (Detailed Additions):**
```python
def _complete_death_progression(self):
    """Complete the death progression - character is now permanently dead."""
    character = self.obj
    if not character:
        self.stop()
        self.delete()
        return
    
    # Mark as permanently dead
    self.db.can_be_revived = False
    
    # Send final death messages (already implemented)
    # ... existing message code ...
    
    # Apply final death state (already implemented)
    if hasattr(character, 'apply_final_death_state'):
        character.apply_final_death_state()
    
    # Clean up medical script (already implemented)
    # ... existing cleanup code ...
    
    # NEW: Complete death progression with flash cloning
    self._handle_corpse_creation_and_transition(character)
    
    # Log completion
    try:
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"DEATH_PROGRESSION: {character.key} completed - flash cloning initiated")
        splattercast.msg(f"DEATH_SCRIPT_CLEANUP: Stopping and deleting death progression script")
    except:
        pass
    
    # Stop and delete the script
    self.stop()
    self.delete()
```

**Method:** `_handle_corpse_creation_and_transition()`

**Current Code (Lines 402-438):**
```python
def _handle_corpse_creation_and_transition(self, character):
    """Complete the death progression by creating corpse and transitioning character."""
    try:
        # 1. Create corpse object with forensic data
        corpse = self._create_corpse_from_character(character)
        
        # 2. Get account before unpuppeting
        account = character.account
        
        # 3. Transition character out of play
        self._transition_character_to_death(character)
        
        # 4. TODO: Initiate character creation for account (commented out until character creation ready)
        # if account:
        #     self._initiate_new_character_creation(account)
        
        # ... logging ...
```

**New Code (Flash Cloning Integration):**
```python
def _handle_corpse_creation_and_transition(self, character):
    """Complete death progression: create corpse, archive character, flash clone."""
    try:
        # 1. Create corpse object with forensic data
        corpse = self._create_corpse_from_character(character)
        
        # 2. Get account and session before unpuppeting
        account = character.account
        session = None
        if account and account.sessions.all():
            session = account.sessions.all()[0]
        
        # 3. Archive and unpuppet character
        self._archive_and_unpuppet_character(character, account, session)
        
        # 4. Initiate flash cloning
        if account:
            self._initiate_flash_cloning(account, character, session)
        
        # Log completion
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_COMPLETION: {character.key} -> Corpse created, character archived, flash cloning initiated")
        except:
            pass
            
    except Exception as e:
        # Fallback error handling
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_COMPLETION_ERROR: {character.key if character else 'Unknown'} - {e}")
        except:
            pass
```

**New Method: `_archive_and_unpuppet_character()`**
```python
def _archive_and_unpuppet_character(self, character, account, session):
    """Archive the dead character and unpuppet from account."""
    try:
        # Archive the character
        character.db.archived = True
        character.db.archived_reason = "death"
        character.db.archived_date = time.time()
        character.db.death_cause = getattr(character.db, 'death_cause', 'unknown')
        
        # Link to corpse if available
        if hasattr(self, 'created_corpse_dbref'):
            character.db.corpse_dbref = self.created_corpse_dbref
        
        # Unpuppet character from account
        if account and session:
            account.unpuppet_object(session)
            
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"DEATH_UNPUPPET: {character.key} unpuppeted from {account.key}")
            except:
                pass
        
        # Character remains in database but is archived and unpuppeted
        # This preserves it for admin investigation and forensics
        
    except Exception as e:
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_ARCHIVE_ERROR: Failed to archive {character.key}: {e}")
        except:
            pass
```

**New Method: `_initiate_flash_cloning()`**
```python
def _initiate_flash_cloning(self, account, old_character, session):
    """Initiate flash cloning - create new character from Stack."""
    try:
        from commands.charcreate import create_flash_clone
        
        # Create new clone from old character's Stack
        new_character = create_flash_clone(account, old_character)
        
        if not new_character:
            raise Exception("Flash cloning failed to create character")
        
        # Puppet the new clone
        if session:
            account.puppet_object(session, new_character)
            
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"FLASH_CLONE: {new_character.key} (Gen {new_character.db.clone_generation}) created and puppeted for {account.key}")
            except:
                pass
        
        # Send respawn messages to player
        self._send_respawn_messages(new_character, old_character)
        
    except Exception as e:
        # Fallback: send player to character creation menu instead
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"FLASH_CLONE_ERROR: {e} - Redirecting {account.key} to character creation")
        except:
            pass
        
        # Redirect to manual character creation
        from commands.charcreate import start_character_creation
        start_character_creation(account)
```

**New Method: `_send_respawn_messages()`**
```python
def _send_respawn_messages(self, new_character, old_character):
    """Send atmospheric respawn messages to newly cloned character."""
    
    # Calculate generation
    generation = new_character.db.clone_generation
    
    # Build respawn narrative
    messages = [
        "|x" * 78,  # Static/noise effect
        "",
        "|y>>> SIGNAL REACQUIRED <<<|n",
        "|y>>> CONSCIOUSNESS UPLOAD: COMPLETE <<<|n", 
        "|y>>> SLEEVE INITIALIZATION: COMPLETE <<<|n",
        "",
        f"|gWelcome back, {new_character.key}.|n",
        f"|gClone Generation: |w{generation}|n",
        "",
    ]
    
    # Add generation-specific flavor
    if generation == 1:
        messages.append("|xThis is your first death. The transition was... jarring.|n")
    elif generation < 5:
        messages.append("|xThe memories of your previous body fade like static on old film.|n")
    elif generation < 10:
        messages.append("|xYou've died enough times to know: this never gets easier.|n")
    else:
        messages.append("|rHow many times have you done this? The memories blur together...|n")
    
    messages.extend([
        "",
        f"|xPrevious cause of death: |r{old_character.db.death_cause}|n",
        "",
        "|yYou wake in the Medical Reconstruction Bay.|n",
        "|yFluorescent lights hum overhead. The air tastes like ozone and antiseptic.|n",
        "",
        "|nType |wlook|n to examine your surroundings.",
        ""
    ])
    
    # Send messages with delays for dramatic effect
    from evennia.utils import delay
    for i, msg in enumerate(messages):
        delay(i * 0.3, lambda m=msg: new_character.msg(m))
```

---

## Account Management

### Account Hooks

**File:** `typeclasses/accounts.py`

**Hook: `at_post_login()`**
```python
def at_post_login(self, session=None):
    """
    Called after successful login. Handle character selection or creation.
    
    This is the main entry point for directing accounts to their characters
    or to the character creation flow if they have no active characters.
    """
    # Check if account has any non-archived characters
    from typeclasses.characters import Character
    
    active_characters = Character.objects.filter(
        db_account=self,
        db_attributes__db_key="archived",
        db_attributes__db_value=False
    )
    
    if not active_characters.exists():
        # No active characters - start character creation
        from commands.charcreate import start_character_creation
        start_character_creation(self, session)
    else:
        # Has active character(s) - let AUTO_PUPPET_ON_LOGIN handle it
        # (Evennia will automatically puppet the last-used character)
        pass
```

**Hook: `at_disconnect()`**
```python
def at_disconnect(self, reason=None):
    """
    Called when account disconnects. Clean up any in-progress character creation.
    """
    # If they were in character creation, clean up temp data
    if hasattr(self.ndb, 'in_character_creation'):
        delattr(self.ndb, 'in_character_creation')
    if hasattr(self.ndb, 'creation_step'):
        delattr(self.ndb, 'creation_step')
    if hasattr(self.ndb, 'creation_data'):
        delattr(self.ndb, 'creation_data')
    
    # Call parent disconnect
    super().at_disconnect(reason)
```

### Character Selection (Future Enhancement)

**For MULTISESSION_MODE = 1 with multiple characters:**

**Command:** `@ic <character name>`
```python
class CmdIC(Command):
    """
    Switch to a different character.
    
    Usage:
        @ic <character name>
        @ic
    
    Without arguments, shows your character roster.
    With a character name, switches to that character.
    """
    key = "@ic"
    aliases = ["ic", "puppet"]
    locks = "cmd:all()"
    
    def func(self):
        # ... implementation ...
```

**Command:** `@ooc`
```python
class CmdOOC(Command):
    """
    Return to OOC mode (unpuppet current character).
    
    Usage:
        @ooc
    
    Unpuppets your current character and returns you to account-level.
    """
    key = "@ooc"
    aliases = ["ooc", "unpuppet"]
    locks = "cmd:all()"
    
    def func(self):
        # ... implementation ...
```

**For Phase 1:** Skip this, keep it simple - one character per account only.

---

## Integration Points

### File: `typeclasses/death_progression.py`

**Lines to Modify:**

**Lines 571-582: Uncomment and implement unpuppeting**
```python
# BEFORE:
# TODO: Unpuppet character from account (commented out until character creation ready)
# if account:
#     account.unpuppet_object(character)

# AFTER:
# Unpuppet character from account
if account and session:
    account.unpuppet_object(session)
    character.db.archived = True
    character.db.archived_date = time.time()
```

**Lines 585-595: Replace TODO with flash cloning**
```python
# BEFORE:
def _initiate_new_character_creation(self, account):
    # TODO: Implement character creation system
    account.msg("|yCharacter creation system is under development.|n")

# AFTER:
def _initiate_flash_cloning(self, account, old_character, session):
    """Initiate flash cloning - create new character from Stack."""
    from commands.charcreate import create_flash_clone
    new_character = create_flash_clone(account, old_character)
    if session:
        account.puppet_object(session, new_character)
    self._send_respawn_messages(new_character, old_character)
```

### File: `typeclasses/accounts.py`

**Add New Method:**
```python
def at_post_login(self, session=None):
    """Handle character selection or creation after login."""
    # See Account Management section for full implementation
```

### File: `typeclasses/characters.py`

**Add to `at_object_creation()`:**
```python
def at_object_creation(self):
    """Initialize character with Stack attributes."""
    super().at_object_creation()
    
    # Existing code...
    
    # NEW: Flash cloning Stack attributes
    if not hasattr(self.db, 'clone_generation'):
        self.db.clone_generation = 1
    if not hasattr(self.db, 'stack_id'):
        import uuid
        self.db.stack_id = str(uuid.uuid4())
    if not hasattr(self.db, 'original_creation'):
        self.db.original_creation = time.time()
    self.db.current_sleeve_birth = time.time()
    
    # Archiving flags
    self.db.archived = False
    self.db.archived_reason = ""
    self.db.archived_date = None
```

### File: `typeclasses/corpse.py`

**Add to `_create_corpse_from_character()` in death_progression.py:**
```python
# After line 460 (corpse = create_object(...))
corpse.db.clone_generation = character.db.clone_generation
corpse.db.stack_id = character.db.stack_id
```

### File: `server/conf/settings.py`

**Add New Settings:**
```python
# Flash Cloning System (after line 103)
RESPAWN_ROOM_DBREF = 3  # Medical Reconstruction Bay
ENABLE_FLASH_CLONING = True
MAX_CHARACTERS_PER_ACCOUNT = 1
ARCHIVE_OLD_CLONES = True
```

### File: `server/conf/at_initial_setup.py`

**Implement Respawn Room Creation:**
```python
def at_initial_setup():
    """
    Create essential rooms and objects on first server start.
    """
    from evennia import create_object
    from typeclasses.rooms import Room
    from typeclasses.exits import Exit
    
    # Create Medical Reconstruction Bay (Respawn Room)
    limbo = search_object("#2")[0]  # Default Limbo
    
    recon_bay = create_object(
        Room,
        key="Medical Reconstruction Bay",
        location=None
    )
    recon_bay.db.desc = (
        "Fluorescent lights hum overhead, casting everything in sterile white. "
        "Medical equipment beeps and whirs around you. The air tastes like ozone "
        "and antiseptic. Along the walls, rows of clone vats pulse with dim amber light.\n\n"
        "A digital readout above the exit reads: |yVECTOR INDUSTRIES - CONSCIOUSNESS "
        "RECONSTRUCTION DIVISION|n\n\n"
        "This is where you wake up after dying. Again. And again."
    )
    
    # Create exit from Limbo to Recon Bay (for testing)
    create_object(
        Exit,
        key="recon bay",
        aliases=["recon", "medical"],
        location=limbo,
        destination=recon_bay
    )
    
    # Create exit from Recon Bay to Limbo (for testing)
    create_object(
        Exit,
        key="limbo",
        location=recon_bay,
        destination=limbo
    )
    
    print(f"Created Medical Reconstruction Bay (#{recon_bay.dbref})")
    print(f"Set RESPAWN_ROOM_DBREF = {recon_bay.dbref} in settings.py")
```

### New File: `commands/charcreate.py`

**Create Complete Character Creation System:**
- See Character Creation Flow section for detailed implementation
- Key functions:
  - `start_character_creation(account, session=None)`
  - `create_flash_clone(account, old_character=None)`
  - `create_character_from_data(account, creation_data)`
  - EvMenu nodes for character creation steps

---

## Implementation Phases

### Phase 1: Critical Path (Closes Death Loop)
**Goal:** Dead characters can respawn. New accounts can create first character.
**Duration:** 2-3 days
**Deliverables:**

**1.1 Unpuppet Dead Characters** ✅ Priority 1
- File: `typeclasses/death_progression.py`
- Lines: 571-582
- Uncomment unpuppeting code
- Add archiving flags
- Test: Character death -> unpuppet successful

**1.2 Basic Character Creation Command** ✅ Priority 2
- File: `commands/charcreate.py` (NEW)
- Simple menu: Name input only
- Randomized appearance
- Default stats (1/1/1/1)
- Test: `charcreate` command works from OOC

**1.3 Account Post-Login Hook** ✅ Priority 3
- File: `typeclasses/accounts.py`
- Add `at_post_login()` method
- Check for active characters
- Redirect to character creation if none
- Test: Login -> character creation if no char

**1.4 Flash Cloning Integration** ✅ Priority 4
- File: `typeclasses/death_progression.py`
- Replace `_initiate_new_character_creation()` with `_initiate_flash_cloning()`
- Call `create_flash_clone()` from charcreate
- Copy Stack attributes
- Test: Death -> automatic respawn

**1.5 Respawn Room Setup** ✅ Priority 5
- File: `server/conf/at_initial_setup.py`
- Create Medical Reconstruction Bay
- Set RESPAWN_ROOM_DBREF in settings
- Test: New clones spawn in correct room

**Testing Checklist Phase 1:**
- [ ] New account -> login -> character creation menu
- [ ] Create first character -> spawn in recon bay
- [ ] Character death -> corpse created
- [ ] Character death -> unpuppet successful
- [ ] Character death -> new clone created automatically
- [ ] New clone has incremented generation number
- [ ] Old clone is archived
- [ ] New clone spawns in recon bay
- [ ] Respawn messages display correctly

### Phase 2: Polish & Enhancement
**Goal:** Better UX, atmospheric messaging, appearance customization
**Duration:** 2-3 days
**Deliverables:**

**2.1 Character Creation Menu**
- Full EvMenu implementation
- Name, sex, appearance choices
- Skintone selection
- Preview before creation
- Help text for each step

**2.2 Respawn Messaging**
- Atmospheric "waking up" narrative
- Generation-specific flavor text
- Death cause display
- Stats summary

**2.3 Clone Appearance Variation**
- Slight skintone drift between clones
- Optional "clone markers" (scars, tattoos)
- Physical differences for RP flavor

**2.4 Memory Degradation System**
- Lower stats by 1-2% per death (optional)
- Cap degradation at -20% total
- Display "cognitive drift" messages

**Testing Checklist Phase 2:**
- [ ] Full character creation menu navigation
- [ ] All appearance options work
- [ ] Respawn messages display correctly
- [ ] Clone generation tracking accurate
- [ ] Memory degradation applies (if enabled)

### Phase 3: Account Management
**Goal:** Multiple character support, character roster, switching
**Duration:** 2-4 days
**Deliverables:**

**3.1 Character Roster Command**
- Display all characters (active + archived)
- Show generation, death count, status
- Format with boxtable

**3.2 Character Selection Commands**
- `@ic <name>` to switch
- `@ooc` to unpuppet
- Validation and error handling

**3.3 Increase MAX_CHARACTERS_PER_ACCOUNT**
- Allow 2-3 active characters
- Enforce limits
- Archive management

**Testing Checklist Phase 3:**
- [ ] Character roster displays correctly
- [ ] Switching between characters works
- [ ] Can't exceed character limit
- [ ] Archived characters show properly

### Phase 4: Web Integration
**Goal:** Web-based registration and character creation
**Duration:** 3-5 days
**Deliverables:**

**4.1 Enable Web Registration**
- Django registration view
- Email validation
- Password requirements
- Security (reCAPTCHA?)

**4.2 Web Character Creation**
- HTML/CSS form matching telnet menu
- Same validation as telnet
- Preview rendering

**4.3 Web Character Roster**
- View characters on website
- Can't switch in-game from web (technical limitation)
- Read-only display

**Testing Checklist Phase 4:**
- [ ] Web registration works
- [ ] Web character creation works
- [ ] Web and telnet chars are compatible
- [ ] Security measures in place

---

## Testing Requirements

### Unit Testing

**Test File:** `tests/test_charcreate.py` (NEW)
```python
# Test character creation functions
def test_create_character_from_data()
def test_validate_character_name()
def test_randomize_appearance()
def test_create_flash_clone()
def test_clone_generation_increment()
def test_stack_attribute_preservation()
```

**Test File:** `tests/test_death_respawn.py` (NEW)
```python
# Test death -> respawn cycle
def test_death_unpuppets_character()
def test_death_archives_character()
def test_death_triggers_flash_clone()
def test_respawn_location()
def test_respawn_medical_state_reset()
def test_respawn_inventory_cleared()
```

### Integration Testing

**Test Scenarios:**

**Scenario 1: New Account First Character**
```
1. Create account via telnet
2. Login successful
3. Character creation menu appears
4. Enter name "TestChar"
5. Select sex: Male
6. Randomize appearance
7. Confirm creation
8. Character spawns in recon bay
9. Medical state initialized
10. Inventory empty
11. Stats are 1/1/1/1
```

**Scenario 2: Character Death and Respawn**
```
1. Damage character to death
2. Death curtain plays
3. Death progression starts (6 min)
4. Wait for completion
5. Corpse created in death location
6. Old character unpuppeted
7. Old character archived
8. New clone created automatically
9. New clone generation = old + 1
10. New clone puppeted
11. Respawn messages display
12. New clone in recon bay
```

**Scenario 3: Multiple Deaths**
```
1. Kill character (Generation 1 -> 2)
2. Kill again (Generation 2 -> 3)
3. Kill again (Generation 3 -> 4)
4. Verify each corpse has correct generation
5. Verify only latest character is active
6. Verify old characters are archived
7. Verify generation numbers increment correctly
```

### Stress Testing

**Test Cases:**
- 10 characters dying simultaneously
- Account disconnecting during character creation
- Account disconnecting during death progression
- Character creation with invalid names
- Character creation with duplicate names
- Flash cloning when recon bay doesn't exist
- Flash cloning when account disconnected

---

## Edge Cases & Error Handling

### Edge Case: Account Disconnects During Death Progression

**Problem:** Player loses connection while their character is in the 6-minute death window.

**Solution:**
- Death progression script persists (it's a Script object)
- Continues running even if account disconnected
- When progression completes:
  - Character still archived and unpuppeted
  - Flash clone created
  - When account reconnects: `at_post_login()` detects no active character
  - Redirects to character creation OR automatically puppets new clone

**Implementation:**
```python
# In _initiate_flash_cloning()
if not session:
    # Account disconnected - create clone anyway
    new_character = create_flash_clone(account, old_character)
    # When they log back in, at_post_login() will handle puppeting
```

### Edge Case: Character Creation Menu Abandoned

**Problem:** Player starts character creation but quits/disconnects mid-menu.

**Solution:**
- Menu data stored in `account.ndb.creation_data` (non-persistent)
- On disconnect: `at_disconnect()` clears NDB data
- On reconnect: `at_post_login()` sees no active character, starts fresh creation
- No partial characters created

### Edge Case: Respawn Room Doesn't Exist

**Problem:** RESPAWN_ROOM_DBREF points to deleted/invalid room.

**Solution:**
```python
# In create_flash_clone()
from django.conf import settings
from evennia import search_object

try:
    respawn_room = search_object(f"#{settings.RESPAWN_ROOM_DBREF}")[0]
except (IndexError, AttributeError):
    # Fallback to Limbo
    respawn_room = search_object("#2")[0]
    
    # Log error
    from evennia.comms.models import ChannelDB
    splattercast = ChannelDB.objects.get_channel("Splattercast")
    splattercast.msg(f"RESPAWN_ERROR: Room #{settings.RESPAWN_ROOM_DBREF} not found, using Limbo")

new_character.location = respawn_room
```

### Edge Case: Flash Cloning Fails

**Problem:** `create_flash_clone()` throws exception during character creation.

**Solution:**
```python
# In _initiate_flash_cloning()
try:
    new_character = create_flash_clone(account, old_character)
except Exception as e:
    # Log error
    splattercast.msg(f"FLASH_CLONE_ERROR: {e}")
    
    # Fallback: Send to manual character creation
    from commands.charcreate import start_character_creation
    start_character_creation(account)
    
    # Notify player
    if account and account.sessions.all():
        account.msg("|rAutomatic respawn failed. Please create a new character.|n")
```

### Edge Case: Name Already Taken

**Problem:** Player tries to create character with existing name.

**Solution:**
```python
# In node_name() validation
from typeclasses.characters import Character

def node_name(caller, raw_string, **kwargs):
    if raw_string:
        name = raw_string.strip()
        
        # Check if name already exists
        existing = Character.objects.filter(db_key__iexact=name)
        if existing.exists():
            caller.msg("|rThat name is already taken. Please choose another.|n")
            return "node_name"  # Stay on this node
        
        # Name is valid
        caller.ndb.creation_data['name'] = name
        return "node_sex"
```

### Edge Case: Too Many Characters

**Problem:** Account tries to create more characters than MAX_CHARACTERS_PER_ACCOUNT.

**Solution:**
```python
# In start_character_creation()
from django.conf import settings
from typeclasses.characters import Character

def start_character_creation(account, session=None):
    # Check character limit
    active_chars = Character.objects.filter(
        db_account=account,
        db_attributes__db_key="archived",
        db_attributes__db_value=False
    ).count()
    
    max_chars = getattr(settings, 'MAX_CHARACTERS_PER_ACCOUNT', 1)
    
    if active_chars >= max_chars:
        account.msg(f"|rYou already have {active_chars} active character(s).|n")
        account.msg(f"|rMaximum allowed: {max_chars}|n")
        account.msg("|rPlease archive or delete an existing character first.|n")
        return
    
    # Proceed with creation...
```

---

## Future Enhancements

### Memory System
- Persistent memories across clones
- Memory degradation with deaths
- "Glitches" in recalled memories
- Memory implants/manipulation

### Economic System
- Cloning costs credits
- Debt system for excessive deaths
- Corporate ownership of consciousness
- "Budget" clones vs "Premium" clones

### Clone Variations
- Different body types available
- Genetic modifications purchasable
- Cosmetic options (tattoos, scars, augments)
- "Factory defects" for flavor

### Investigation RP
- Forensic analysis of corpses
- Autopsy commands
- Crime scene preservation
- Evidence collection

### Admin Tools
- Command to manually archive characters
- Command to restore archived characters
- Command to adjust clone generation numbers
- Bulk character management

### Web Dashboard
- Character roster on website
- Death statistics and graphs
- Corpse investigation logs
- Clone history timeline

---

## Appendix A: Command Reference

### Player Commands (Phase 1)

**None** - Character creation is automatic via menu

### Player Commands (Phase 2+)

**`@charcreate`**
- Manually start character creation (if automatic fails)
- Usage: `@charcreate`

**`@ic <character>`** (Phase 3)
- Switch to different character
- Usage: `@ic TestChar`

**`@ooc`** (Phase 3)
- Unpuppet current character
- Usage: `@ooc`

**`@characters`** (Phase 3)
- Show character roster
- Usage: `@characters`

### Admin Commands (Future)

**`@archive <character>`**
- Manually archive a character
- Usage: `@archive TestChar`

**`@unarchive <character>`**
- Restore archived character
- Usage: `@unarchive TestChar`

**`@setgeneration <character>=<number>`**
- Manually set clone generation
- Usage: `@setgeneration TestChar=5`

---

## Appendix B: Database Schema

### Character Attributes (db.*)

```
db.clone_generation     int     1        Clone number (1 = original)
db.stack_id             str     UUID     Unique consciousness ID
db.original_creation    float   time()   When Stack first created
db.current_sleeve_birth float   time()   When THIS clone was born
db.archived             bool    False    Is this an old clone?
db.archived_reason      str     ""       Why archived (death, etc)
db.archived_date        float   None     When archived
db.death_cause          str     ""       How this clone died
db.previous_clone_dbref int     None     Previous clone reference
db.corpse_dbref         int     None     Corpse left behind
```

### Account Attributes (db.*)

```
db.total_death_count    int     0        Total deaths across all clones
db.characters_created   int     0        Total clones spawned
db.first_clone_date     float   None     First character created
```

### Corpse Attributes (db.*) - Additions

```
db.clone_generation     int     Copy from character
db.stack_id             str     Copy from character
```

---

## Appendix C: Settings Reference

### New Settings (server/conf/settings.py)

```python
# Flash Cloning System
RESPAWN_ROOM_DBREF = 3
ENABLE_FLASH_CLONING = True
MAX_CHARACTERS_PER_ACCOUNT = 1
ARCHIVE_OLD_CLONES = True
CLONE_SPAWN_MESSAGE = True
CLONE_MEMORY_DEGRADATION = False  # Future
CLONE_MEMORY_LOSS_PERCENT = 2     # Future

# Character Creation  
ENABLE_NEW_ACCOUNT_CHARS = True
DEFAULT_GRIM_STATS = (1, 1, 1, 1)  # G.R.I.M. starting values
RANDOMIZE_APPEARANCE_DEFAULT = True

# Death System (additions)
UNPUPPET_ON_FINAL_DEATH = True
AUTO_RESPAWN_ON_FINAL_DEATH = True
```

---

## Appendix D: File Structure

### New Files to Create

```
commands/charcreate.py              # Character creation system
tests/test_charcreate.py            # Unit tests
tests/test_death_respawn.py         # Integration tests
web/website/views/charcreate.py     # Web character creation (Phase 4)
web/website/forms.py                # Web forms (Phase 4)
web/website/templates/charcreate/   # Web templates (Phase 4)
```

### Files to Modify

```
typeclasses/death_progression.py   # Unpuppet, flash cloning
typeclasses/accounts.py             # at_post_login() hook
typeclasses/characters.py           # Stack attributes
typeclasses/corpse.py               # Stack ID preservation
server/conf/settings.py             # New settings
server/conf/at_initial_setup.py     # Respawn room creation
```

---

## Appendix E: Glossary

**Stack** - The persistent consciousness/identity across clones (borrowed from Altered Carbon)

**Sleeve** - The physical body, temporary and replaceable

**Resleeving** - The act of uploading consciousness into a new clone body

**Clone Generation** - How many times a Stack has been resleeved (death count + 1)

**Reconstruction Bay** - The respawn location where new clones awaken

**Archived Character** - Old clone that died, kept in database for forensics

**Flash Cloning** - The corporate process of rapid clone creation and consciousness transfer

**VECTOR Industries** - The fictional mega-corporation that owns the cloning tech

**Cognitive Drift** - Memory degradation that occurs with repeated resleeving

**Stack ID** - Unique UUID identifying a consciousness across all its clones

---

## Document Approval

**Author:** AI Assistant (GitHub Copilot)
**Reviewer:** daiimus
**Status:** DRAFT - Awaiting Approval

**Sign-off Required Before Implementation:**
- [ ] Thematic direction approved
- [ ] Technical architecture approved
- [ ] Phase 1 scope approved
- [ ] Data model approved
- [ ] Ready to implement

---

**END OF SPECIFICATION**
