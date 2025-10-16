# Flash Cloning System Specification

## Document Status
- **Version:** 2.2 PHASE 2 REVISED
- **Date:** October 16, 2025
- **Status:** Phase 1 COMPLETE ✅ | Phase 2 IN PROGRESS 🔄 - Implementation approach revised
- **Priority:** CRITICAL - Core gameplay loop (telnet complete, web in revision)
- **Next Phase:** Phase 2 proper implementation, then Phase 3 (Web-based gameplay)

### Implementation Progress

| Phase | Status | Date | Description | Files | Lines |
|-------|--------|------|-------------|-------|-------|
| **Phase 1** | ✅ COMPLETE | Oct 14, 2025 | Telnet character creation & flash cloning | 4 files | ~1,300 lines |
| **Phase 2** | 🔄 REVISING | Oct 16, 2025 | Web/Django character creation (extend Evennia defaults) | TBD | TBD |
| **Phase 3** | ⏳ PLANNED | TBD | Web-based gameplay (webclient) | TBD | TBD |

**Current Capabilities:**
- ✅ Telnet character creation (EvMenu-based)
- 🔄 Web character creation (implementation approach revised)
- ✅ Flash cloning (telnet only - web pending)
- ✅ Random templates (telnet only - web pending)
- ⏳ Character roster (web - pending)
- ✅ Death → Respawn loop (telnet complete)
- ⏳ Web-based gameplay (planned Phase 3)

---

## Executive Summary

The Flash Cloning System is the core respawn mechanism for Gelatinous Monster. It closes the death loop by seamlessly transitioning dead characters through corporate memory upload into new clone bodies. This system must integrate with the existing death progression, medical system, and account management to create a complete lifecycle: **Creation → Death → Respawn → Death → Respawn...**

**Current State:** ✅ **FUNCTIONAL** - Death loop closes. Characters unpuppet, respawn menu works, flash cloning operational.

**Target State:** ✅ **ACHIEVED** - Death automatically triggers character creation menu. Players can flash clone or select new templates.

**Implementation Date:** October 14, 2025

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

### Implementation Status (October 14, 2025)

**✅ RESOLVED - Bug #1: Zombie Characters in Limbo**
- **Original Issue:** Dead characters teleported to limbo but never unpuppeted
- **Resolution:** `death_progression.py` now properly unpuppets characters and initiates character creation
- **Code Location:** `typeclasses/death_progression.py:548-596` (`_transition_character_to_death()`)
- **Status:** FUNCTIONAL - Characters properly unpuppet and accounts redirected to respawn menu

**✅ RESOLVED - Bug #2: Character Creation System**
- **Original Issue:** No character creation system existed
- **Resolution:** Complete EvMenu-based character creation system implemented
- **Code Location:** `commands/charcreate.py` (1,058 lines)
- **Features Implemented:**
  - First-time character creation (name, sex, GRIM distribution)
  - Respawn menu with 3 random templates
  - Flash clone option (preserves identity, stats, appearance)
  - Roman numeral naming (death_count integration)
  - Template caching and validation
- **Status:** IMPLEMENTED - Needs first-time creation testing

**✅ RESOLVED - Bug #3: Account Login Flow**
- **Original Issue:** AUTO_PUPPET_ON_LOGIN caused conflicts
- **Resolution:** Disabled auto-puppeting, implemented custom `at_post_login()` hook
- **Code Location:** `typeclasses/accounts.py:69-137` (`at_post_login()`)
- **Status:** FUNCTIONAL - Proper character detection and menu triggering

**⚠️ PARTIAL - Bug #4: Empty Initial Setup**
- **Original Issue:** No starting location or spawn points
- **Resolution:** START_LOCATION set to Limbo (#2) in settings
- **Code Location:** `server/conf/settings.py:82`
- **Status:** FUNCTIONAL - Using Evennia default Limbo as spawn point
- **Future:** Create proper starting room when world building begins

**✅ RESOLVED - Bug #5: Settings Configuration**
- **Original Issue:** Contradictory multisession settings
- **Resolution:** Proper configuration applied
- **Settings Applied:**
  - `MULTISESSION_MODE = 1` (account-based login)
  - `AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False`
  - `AUTO_PUPPET_ON_LOGIN = False`
  - `MAX_NR_CHARACTERS = 1` (enforces single character limit)
- **Status:** FUNCTIONAL - Clean account-based flow

### System Flow - Current Implementation

**✅ FUNCTIONAL Death & Respawn Flow:**
```
Character Dies → Death Curtain → Death Progression (6 min) → Corpse Created 
→ Character Moved to Limbo → Character Unpuppeted from Account 
→ Account Receives Death Notification → Character Creation Menu Launched
→ [Flash Clone OR Random Template] → New Character Created → Puppeted → Spawned
```

**✅ IMPLEMENTED Components:**
- ✅ Character unpuppeting from account
- ✅ Character archiving (db.archived = True, db.archived_reason = "death")
- ✅ Account redirection to character creation
- ✅ Character creation menu (EvMenu-based)
- ✅ Flash cloning with identity preservation
- ✅ Random template generation (3 options)
- ✅ Respawn location management (START_LOCATION)
- ✅ Death count tracking with Roman numerals
- ✅ Character-account cleanup (removes old char from account.characters)

**⚠️ UNTESTED Components:**
- ⚠️ First-time character creation flow (never triggered with existing accounts)
- ⚠️ GRIM point distribution validation
- ⚠️ Name uniqueness validation
- ⚠️ Fresh account login without existing character

**❌ NOT IMPLEMENTED (Deferred to Future):**
- ❌ Web/Django registration interface (telnet-only approach)
- ❌ Character roster/selection menu (not needed with MAX_NR_CHARACTERS=1)
- ❌ Multiple character management
- ❌ Character deletion UI (handled automatically on death)

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
- **Implementation:** `MAX_NR_CHARACTERS = 1` enforces single character limit
- **Status:** ✅ IMPLEMENTED - Old character removed from account before new clone created
- **Future:** Could extend to multiple active characters if needed

**Decision #2: Preserve Character Objects**
- **Rationale:** Investigation RP, admin forensics, player history
- **Implementation:** Dead characters archived rather than deleted
- **Status:** ✅ IMPLEMENTED - Characters marked `db.archived = True` and moved to Limbo
- **Storage:** `character.db.archived = True`, `character.db.archived_reason = "death"`

**Decision #3: Flash Cloning Menu-Driven**
- **Rationale:** Player agency, respawn choices, identity preservation
- **Implementation:** EvMenu-based character creation with flash clone option
- **Status:** ✅ IMPLEMENTED - Respawn menu offers flash clone or 3 random templates
- **Player Choice:** Full control over name, appearance, stats, or use flash clone

**Decision #4: Stack Persistence Model**
- **Rationale:** Define what makes "you" persist across deaths
- **Implementation:** Death count tracks number of deaths, used for Roman numeral naming
- **Status:** ✅ IMPLEMENTED - Single increment location prevents race conditions
- **Balancing:** Death count visible, affects narrative but not hard mechanics

**Decision #5: Phased Implementation Approach**
- **Rationale:** Test core functionality via telnet before adding web complexity
- **Phase 1:** Telnet-only character creation and respawn - ✅ COMPLETE (Oct 14, 2025)
- **Phase 2:** Web/Django signup and character creation interface - ✅ COMPLETE (Oct 16, 2025)
- **Phase 3:** Web-based gameplay (webclient integration) - ⏳ PLANNED
- **Status:** Phase 2 complete and ready for testing
- **Benefits:** 
  - Validates game logic independently of web layer
  - Simpler debugging and iteration
  - Web UI adds convenience without replacing telnet
  - Telnet remains functional as fallback/admin tool

### Core Systems Integration

**Existing Systems We Build On:**
1. ✅ **Death Curtain** (`typeclasses/curtain_of_death.py`) - Animation system - FUNCTIONAL
2. ✅ **Death Progression** (`typeclasses/death_progression.py`) - 6-minute timer - FUNCTIONAL
3. ✅ **Medical System** (`world/medical/*`) - Organ damage, wounds - FUNCTIONAL
4. ✅ **Corpse System** (`typeclasses/corpse.py`) - Forensic preservation - FUNCTIONAL
5. ✅ **Combat System** (`world/combat/*`) - Damage application - FUNCTIONAL
6. ✅ **Email Auth** (`commands/unloggedin_email.py`) - Account creation - FUNCTIONAL

**Systems We Built - Phase 1 (October 14, 2025):**
1. ✅ **Character Creation** (`commands/charcreate.py:1-1058`) - IMPLEMENTED (telnet)
2. ✅ **Flash Cloning** (`commands/charcreate.py:622-758`) - IMPLEMENTED (telnet)
3. ✅ **Spawn Management** (`typeclasses/death_progression.py:548-596`) - IMPLEMENTED
4. ✅ **Account Hooks** (`typeclasses/accounts.py:69-137`) - IMPLEMENTED
5. ✅ **Character Archiving** (`typeclasses/death_progression.py:575-587`) - IMPLEMENTED
6. ✅ **Death Count System** (`typeclasses/death_progression.py:556-563`) - IMPLEMENTED

**Systems To Build - Phase 2 (Revised Approach - October 16, 2025):**

**Core Principle:** EXTEND Evennia's default character creation system, don't replace it.

**Implementation Strategy:**
1. 🔄 **Extend CharacterForm** - Add GRIM stat fields to Evennia's default form
2. 🔄 **Extend CharacterCreateView** - Override `form_valid()` for GRIM validation
3. 🔄 **Modify character_form.html** - Add GRIM input section to existing template
4. 🔄 **Add CharacterRespawnView** - New class-based view for flash cloning
5. 🔄 **Integrate Telnet Functions** - Reuse `generate_random_template()`, `create_flash_clone()`

**Files to Modify (Not Create):**
- `web/website/forms.py` - Extend existing `CharacterForm` class
- `web/website/views/characters.py` - Add `CharacterRespawnView` class
- `web/templates/website/character_form.html` - Add GRIM fields section
- `web/website/urls.py` - Add respawn route to existing `/characters/` namespace

**What We're Building On:**
- Evennia's `CharacterCreateView(CharacterMixin, ObjectCreateView)`
- Evennia's `CharacterForm(ObjectForm)` with `db_key` and `desc` fields
- Evennia's `character_form.html` template
- Evennia's `/characters/create/` URL route (already exists)
- Evennia's class-based view architecture with mixins

**What We're Adding:**
- GRIM stat fields: `grit`, `resonance`, `intellect`, `motorics` (IntegerFields)
- 300-point validation in `form_valid()` override
- JavaScript for live stat total display
- Flash clone respawn route: `/characters/respawn/`
- Template selection interface

**Phase 3 (Future - Web-Based Gameplay):**
1. ⏳ **Web Client Integration** - Play via browser instead of telnet
2. ⏳ **Real-Time Updates** - WebSocket integration for live character updates
3. ⏳ **Advanced Appearance** - Full body description customization via web
4. ⏳ **Account Dashboard** - Death statistics, achievements, settings

**Deferred to Future:**
1. ❌ **Character Selection Roster** - Not needed with MAX_NR_CHARACTERS=1
2. ❌ **Multiple Character Management** - Single character enforced
3. ❌ **Character Deletion UI** - Automatic on death

---

## October 14, 2025 Implementation Summary

### Bugs Fixed

**Bug #1: EvMenu Auto-Generated Numbered Lists**
- **Symptom:** Respawn menu showed "1 2 3 4" auto-generated lines
- **Root Cause:** Returning bare dict instead of tuple for options
- **Solution:** Changed options return from `dict` to `(dict,)` tuple format
- **Pattern:** Created `_respawn_process_choice()` goto-callable following Evennia canonical pattern
- **Files Modified:** `commands/charcreate.py`

**Bug #2: Death Count Incrementing by 4**
- **Symptom:** Character names jumped from "Laszlo VII" to "Laszlo XI" (4 instead of 1)
- **Root Cause:** `at_death()` called from multiple locations (combat, medical, manual)
- **Solution:** Moved death_count increment to single definitive location in `_transition_character_to_death()`
- **Architectural Win:** Instead of preventing multiple calls with flags, increment only at guaranteed-once location
- **Files Modified:** 
  - `typeclasses/characters.py` (removed increment from `at_death()`)
  - `typeclasses/death_progression.py` (added increment before limbo teleport)

**Bug #3: Death Curtain Not Firing**
- **Symptom:** Death curtain and progression script not running on subsequent deaths
- **Root Cause:** Changed to persistent `db.death_processed` flag but forgot to clear on revival
- **Solution:** Added `db.death_processed` cleanup to `remove_death_state()`
- **Manual Fix Required:** Existing characters need `@py del me.db.death_processed`
- **Files Modified:** `typeclasses/characters.py:1093-1096`

**Bug #4: Stale Handler References**
- **Original Issue:** NDB attributes not cleaned up properly
- **Solution:** Comprehensive state cleanup in character removal
- **Files Modified:** Multiple cleanup functions across combat system

**Bug #5: Complete Death Loop**
- **Original Issue:** Death loop never closed, characters stuck in limbo
- **Solution:** Implemented complete flow from death to respawn
- **Components:** Unpuppet → Character creation menu → Flash clone/template → Respawn
- **Files Modified:** `typeclasses/death_progression.py`, `commands/charcreate.py`

### Testing Status

**✅ Tested and Verified:**
- Death curtain display and timing
- Death progression script (6-minute countdown)
- Corpse creation with inventory transfer
- Character unpuppeting on death
- Character archiving system
- Respawn menu display (clean, no auto-formatting)
- Flash clone option (identity preservation, stat inheritance)
- Random template generation (3 options)
- Death count increment (exactly once per death)
- Roman numeral naming system
- Character-account cleanup (removes old char from account.characters)

**⚠️ Implemented But Untested:**
- First-time character creation flow (never triggered due to AUTO_PUPPET disabled during dev)
- GRIM point distribution validation (300 points across 4 stats)
- Name uniqueness validation
- Fresh account login without existing character
- Sex selection system
- Character description generation
- Starting equipment assignment

**❌ Known Limitations:**
- Manual flag cleanup needed for existing characters with `db.death_processed=True`
- START_LOCATION set to Limbo (#2) - proper starting room needed for world building
- No multi-character support (by design - MAX_NR_CHARACTERS=1)
- No web interface (by design - telnet-only approach)

### Code Changes Summary

**Files Created:**
- None (all modifications to existing files)

**Files Modified:**
- `commands/charcreate.py` - Complete refactor of respawn menu system
  - Added `_respawn_process_choice()` goto-callable
  - Fixed EvMenu options tuple format
  - Improved error handling and state management
  
- `typeclasses/characters.py`
  - Changed `at_death()` to use persistent `db.death_processed` flag
  - Removed death_count increment from `at_death()`
  - Added `db.death_processed` cleanup to `remove_death_state()`
  
- `typeclasses/death_progression.py`
  - Added death_count increment in `_transition_character_to_death()`
  - Implemented proper character archiving
  - Added unpuppet and character creation menu trigger
  
- `typeclasses/accounts.py`
  - Implemented `at_post_login()` hook for character detection
  - Added respawn menu triggering for dead accounts
  
- `server/conf/settings.py`
  - Set `MULTISESSION_MODE = 1`
  - Set `AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False`
  - Set `AUTO_PUPPET_ON_LOGIN = False`
  - Set `MAX_NR_CHARACTERS = 1`
  - Set `START_LOCATION = "#2"` (Limbo)

**Lines of Code:**
- Character Creation System: ~1,085 lines (new)
- Account Hooks: ~69 lines (new)
- Death Progression: ~100 lines (modified)
- Character Type: ~50 lines (modified)

### EvMenu Implementation Bugs Fixed

During telnet testing (October 14, 2025), we discovered and fixed 4 critical EvMenu bugs:

**Bug #1: Blank Input Validation**
- **Issue:** Pressing Enter triggered "Invalid name" errors
- **Fix:** Changed `if raw_string:` to `if raw_string and raw_string.strip():`
- **Pattern:** Always validate stripped non-empty input only

**Bug #2: Node Transitions Exiting Menu**
- **Issue:** Returning node name string printed it as text and exited menu
- **Fix:** Call next node function directly: `return next_node(caller, "", **kwargs)`
- **Pattern:** Never return node name strings during input processing

**Bug #3: Leftover Input from Previous Node**
- **Issue:** Previous node's selection ("1", "2", "3") processed as command in next node
- **Fix:** Added command whitelist - only process known commands, ignore invalid input
- **Pattern:** Validate commands before processing when transitioning with kwargs

**Bug #4: Return None Exits Menu**
- **Issue:** `return None` exits menu instead of re-displaying current node
- **Fix:** Use recursive call: `return current_node(caller, "", **kwargs)`
- **Pattern:** CRITICAL - `return None` = exit, not re-display!

**Documentation:** See `specs/EVMENU_PATTERNS_SPEC.md` for complete EvMenu reference guide.

**Testing Status:**
- ✅ Full character creation flow works end-to-end
- ✅ Name validation functional
- ✅ Sex selection functional
- ✅ GRIM stat distribution functional (300 points across 4 stats)
- ✅ Menu stays active during multi-command input
- ✅ Confirmation and finalization tested successfully
- ✅ Death → Respawn flow tested successfully
- ✅ Flash cloning preserves identity correctly
- ✅ Roman numeral naming works correctly
- ✅ Complete death loop closes properly

**Phase 1 Status:** ✅ COMPLETE - All core functionality tested and working

---

## October 16, 2025 Phase 2 Implementation (REVISED)

### Web/Django Interface Implementation

**Goal:** Extend Evennia's default character creation system with GRIM stats and flash cloning

**Status:** ✅ COMPLETE - Smart single-page implementation

### Implementation Approach: EXTEND, Don't Replace

**Critical Principle:** Evennia already has a complete character creation system. We EXTEND it, not replace it.

**What Evennia Provides (Default):**
- `CharacterCreateView` - Class-based view at `/characters/create/`
- `CharacterForm` - Form with `db_key` (name) and `desc` (description)
- `character_form.html` - Template for character creation
- `CharacterManageView` - View at `/characters/manage/` for character management
- `CharacterListView` - View at `/characters/` for browsing characters
- URL routing under `/characters/` namespace

**What We Built:**
1. ✅ **GRIM Stat Fields** - Extended `CharacterForm` with 4 IntegerFields
2. ✅ **Smart Context Detection** - `get_context_data()` checks for archived characters
3. ✅ **Unified Template** - Single `character_form.html` adapts to first-time or respawn
4. ✅ **Three Creation Paths** - Flash clone, template selection, or custom
5. ✅ **Integration Functions** - Reuses telnet's `generate_random_template()`, `create_flash_clone()`

### Implementation: Smart Single-Page Approach

**Architecture Decision (Oct 16, 2025):**
Instead of separate pages for first-time creation and respawn, we implemented a **context-aware single page** that adapts based on account state. This matches Evennia's philosophy and provides better UX.

**User Experience Flow:**
1. **First-Time Player** → `/characters/create/` → Standard creation form
2. **Veteran Player (Dead Character)** → `/characters/create/` → Respawn options (flash clone + templates + custom)

**Files Created:**

**1. `web/website/forms.py` (102 lines)**
```python
from django import forms
from django.core.exceptions import ValidationError
from evennia.web.website.forms import CharacterForm as EvenniaCharacterForm

GRIM_TOTAL_POINTS = 300

class CharacterForm(EvenniaCharacterForm):
    """Extend Evennia's default form with GRIM stats"""
    
    grit = forms.IntegerField(min_value=1, max_value=150, initial=75)
    resonance = forms.IntegerField(min_value=1, max_value=150, initial=75)
    intellect = forms.IntegerField(min_value=1, max_value=150, initial=75)
    motorics = forms.IntegerField(min_value=1, max_value=150, initial=75)
    
    def clean(self):
        """Validate 300-point GRIM total"""
        cleaned_data = super().clean()
        grim_total = sum([
            cleaned_data.get('grit', 0),
            cleaned_data.get('resonance', 0),
            cleaned_data.get('intellect', 0),
            cleaned_data.get('motorics', 0)
        ])
        
        if grim_total != GRIM_TOTAL_POINTS:
            raise ValidationError(f"GRIM stats must total {GRIM_TOTAL_POINTS} points (currently {grim_total})")
        
        return cleaned_data
```

**2. `web/website/views/characters.py` (178 lines)**
```python
from django.contrib import messages
from django.shortcuts import redirect
from evennia.web.website.views.characters import CharacterCreateView as EvenniaCharacterCreateView
from commands.charcreate import generate_random_template, create_flash_clone

class CharacterCreateView(EvenniaCharacterCreateView):
    """Smart character creation view - adapts to first-time vs respawn"""
    
    form_class = forms.CharacterForm
    
    def get_context_data(self, **kwargs):
        """Add respawn context if account has archived characters"""
        context = super().get_context_data(**kwargs)
        account = self.request.user
        
        # Check for archived (dead) characters
        archived_chars = account.db_characters_all.filter(
            db_archived=True
        ).order_by('-db_date_created')
        
        if archived_chars.exists():
            # RESPAWN MODE: Show flash clone + template options
            context['is_respawn'] = True
            context['last_character'] = archived_chars.first()
            context['random_templates'] = [generate_random_template() for _ in range(3)]
        else:
            # FIRST-TIME MODE: Standard creation form
            context['is_respawn'] = False
        
        return context
    
    def form_valid(self, form):
        """Handle three creation paths: flash clone, template, or custom"""
        respawn_choice = self.request.POST.get('respawn_choice')
        
        # PATH 1: Flash Clone
        if respawn_choice == 'flash_clone':
            # Use telnet's flash clone function
            archived_chars = self.request.user.db_characters_all.filter(
                db_archived=True
            ).order_by('-db_date_created')
            
            if archived_chars.exists():
                new_character = create_flash_clone(self.request.user, archived_chars.first())
                messages.success(self.request, f"Flash clone '{new_character.name}' activated")
                return redirect('character-detail', pk=new_character.id)
        
        # PATH 2: Template Selection
        elif respawn_choice and respawn_choice.startswith('template_'):
            template_index = int(respawn_choice.split('_')[1])
            templates = [generate_random_template() for _ in range(3)]
            
            if template_index < len(templates):
                template = templates[template_index]
                response = super().form_valid(form)
                character = self.object
                
                # Apply template stats
                character.db.grit = template['grit']
                character.db.resonance = template['resonance']
                character.db.intellect = template['intellect']
                character.db.motorics = template['motorics']
                # ... set other template attributes
                
                return response
        
        # PATH 3: Custom Character (default)
        response = super().form_valid(form)
        character = self.object
        
        # Set GRIM stats from form
        character.db.grit = form.cleaned_data['grit']
        character.db.resonance = form.cleaned_data['resonance']
        character.db.intellect = form.cleaned_data['intellect']
        character.db.motorics = form.cleaned_data['motorics']
        
        return response
```

**3. `web/templates/website/character_form.html` (366 lines)**
```html
{% extends "website/base.html" %}

{% block content %}
<div class="container mt-5">
  {% if is_respawn %}
    {# RESPAWN MODE: Flash Clone + Templates + Custom #}
    <h1>Stack Recovery - VECTOR Industries Respawn Protocol</h1>
    
    <form method="post">
      {% csrf_token %}
      
      <!-- Flash Clone Option -->
      <div class="template-card flash-clone-card">
        <input type="radio" name="respawn_choice" value="flash_clone" id="choice_flash">
        <label for="choice_flash">
          <h3>Flash Clone (Recommended)</h3>
          <p>Restore original Stack configuration</p>
          <div>Stack: {{ last_character.db.stack_name_first }}</div>
          <div>Stats: G{{ last_character.db.grit }} R{{ last_character.db.resonance }} 
                      I{{ last_character.db.intellect }} M{{ last_character.db.motorics }}</div>
        </label>
      </div>
      
      <!-- 3 Random Templates -->
      {% for template in random_templates %}
      <div class="template-card">
        <input type="radio" name="respawn_choice" value="template_{{ forloop.counter0 }}">
        <label>Template {{ forloop.counter }}: {{ template.name_first }}</label>
      </div>
      {% endfor %}
      
      <!-- Custom Character Option -->
      <div class="template-card">
        <input type="radio" name="respawn_choice" value="custom" checked>
        <label>Custom Sleeve Configuration</label>
      </div>
      
      <!-- Custom form fields (shown when custom selected) -->
      <div id="custom-form-fields">
        {{ form.db_key }}
        {{ form.grit }} {{ form.resonance }} {{ form.intellect }} {{ form.motorics }}
        <div id="points-display">Points Used: <span id="points-used">300</span> / 300</div>
      </div>
      
      <button type="submit">Respawn Character</button>
    </form>
    
  {% else %}
    {# FIRST-TIME MODE: Standard Creation Form #}
    <h1>Create Your Character - VECTOR Industries</h1>
    
    <form method="post">
      {% csrf_token %}
      {{ form.db_key }}
      {{ form.desc }}
      {{ form.grit }} {{ form.resonance }} {{ form.intellect }} {{ form.motorics }}
      
      <div id="points-display">Points Used: <span id="points-used">300</span> / 300</div>
      <button type="submit">Create Character</button>
    </form>
  {% endif %}
</div>

<script>
  // Live GRIM points calculator
  function calculatePoints() {
    const total = parseInt($('#id_grit').val() || 0) +
                 parseInt($('#id_resonance').val() || 0) +
                 parseInt($('#id_intellect').val() || 0) +
                 parseInt($('#id_motorics').val() || 0);
    $('#points-used').text(total);
    // Color coding: green=300, yellow<300, red>300
  }
  
  $('#id_grit, #id_resonance, #id_intellect, #id_motorics').on('input', calculatePoints);
  
  // Toggle custom fields visibility based on radio selection
  $('input[name="respawn_choice"]').on('change', function() {
    $('#custom-form-fields').toggle($(this).val() === 'custom');
  });
</script>

**4. `web/website/urls.py` - Override character-create route**
```python
# mygame/web/website/urls.py
from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns
from web.website.views import characters

# Override Evennia's default CharacterCreateView with our GRIM-enabled version
urlpatterns = [
    path("characters/create/", characters.CharacterCreateView.as_view(), name="character-create"),
] + evennia_website_urlpatterns
```

### What This Smart Single-Page Approach Achieves

**✅ Better User Experience:**
- Players always go to `/characters/create/` regardless of context
- System automatically detects first-time vs respawn scenario
- No confusing separate URLs for different situations
- Single entry point reduces navigation complexity

**✅ Follows Evennia Patterns:**
- Uses class-based views (CBV) with proper Django patterns
- Extends existing forms, doesn't replace them
- Uses Evennia's URL namespace (`/characters/`)
- Overrides only what's needed, reuses everything else

**✅ Maintains Compatibility:**
- Evennia's character management (`/characters/manage/`) works unchanged
- Character list (`/characters/`), update, delete all work normally
- Navbar "Create Character" link points to single URL
- Web changes don't break telnet system

**✅ Code Reuse:**
- Imports `generate_random_template()` from telnet (DRY principle)
- Imports `create_flash_clone()` from telnet (shared logic)
- Same validation rules as telnet (300-point GRIM total)
- Same character structure both interfaces

### Implementation History

**Phase 2.0 (Discarded):**
- ❌ Created parallel system instead of extending Evennia
- ❌ Used function-based views instead of class-based
- ❌ Separate `/characters/respawn/` URL for respawn flow
- ❌ Two templates: `character_form.html` and `character_respawn.html`
- ❌ Would have been unmaintainable and inconsistent with Evennia

**Phase 2.1 (Current - October 16, 2025):**
- ✅ Smart single-page approach with context detection
- ✅ Single URL `/characters/create/` adapts to scenario
- ✅ Uses `get_context_data()` to check for archived characters
- ✅ Template conditionally renders respawn or first-time interface
- ✅ Three creation paths in one unified flow

### Current Status (October 16, 2025)

**Phase 2 Status:** ✅ COMPLETE - Implementation finished, ready for testing

**Files Created:**
- `web/website/forms.py` (102 lines) - CharacterForm extension with GRIM fields
- `web/website/views/characters.py` (178 lines) - Smart CharacterCreateView
- `web/templates/website/character_form.html` (366 lines) - Unified template
- `web/website/urls.py` (modified) - Override character-create route

**Key Features:**
- Context-aware page (detects first-time vs respawn automatically)
- Flash clone option with stats display
- 3 random template options
- Custom character with GRIM stat allocation
- JavaScript live point calculator
- Radio button selection for respawn methods
- Form validation (server-side and client-side)

**Integration Points:**
- Reuses `generate_random_template()` from `commands/charcreate.py`
- Reuses `create_flash_clone()` from `commands/charcreate.py`
- Works alongside Evennia's `/characters/manage/` interface
- Compatible with telnet character creation

### Testing Checklist (Phase 2)

**First-Time Character Creation (Web):**
- [ ] New account logs in
- [ ] Navigate to `/characters/create/`
- [ ] Page shows "Create Your Character" (not respawn interface)
- [ ] Form shows name, description, AND GRIM fields
- [ ] GRIM point calculator works (live JavaScript update)
- [ ] Color coding: green=300, yellow<300, red>300
- [ ] Submitting form with total != 300 shows validation error
- [ ] Submitting valid form creates character with GRIM stats
- [ ] Character appears in `/characters/manage/`
- [ ] Character can be puppeted via telnet
- [ ] Character has `db.grit`, `db.resonance`, `db.intellect`, `db.motorics` set

**Respawn Character Creation (Web):**
- [ ] Character dies in telnet → `db.archived = True`
- [ ] Account logs into website
- [ ] Navigate to `/characters/create/` (same URL)
- [ ] Page shows "Stack Recovery - Respawn Protocol"
- [ ] Flash clone card shows last character's stats
- [ ] 3 random template cards display
- [ ] Custom option available (default selected)
- [ ] Selecting flash clone → custom form hidden
- [ ] Selecting template → custom form hidden
- [ ] Selecting custom → custom form shown
- [ ] Submitting flash clone creates character with preserved stats
- [ ] Submitting template creates character with template stats
- [ ] Submitting custom creates character with form stats
- [ ] New character has incremented death count
- [ ] Roman numeral appended to name correctly

**Character Creation (Telnet - Regression Test):**
- [ ] Telnet character creation still works (unchanged)
- [ ] Characters created via telnet have GRIM stats
- [ ] Both web and telnet create compatible character structures
- [ ] Death → respawn flow works in telnet
- [ ] Characters created in web can be used in telnet

**Evennia Integration:**
- [ ] `/characters/manage/` still works (list your characters)
- [ ] `/characters/` still works (list all characters)
- [ ] Character update/edit still works
- [ ] Character delete still works
- [ ] Navbar "Create Character" link works
- [ ] Dropdown "Manage Characters" link works

**Integration:**
- [ ] Web-created characters work in telnet
- [ ] Telnet-created characters visible in web views
- [ ] Archived characters show in character list
- [ ] Flash cloning works same in telnet and web

### Known Limitations

1. **No Web Puppeting**: Must use telnet to play (Phase 3 feature)
2. **No Real-Time Updates**: Page refresh required to see changes
3. **Single Character**: Assumes `MAX_NR_CHARACTERS = 1`
4. **Basic Appearance**: Only description field (no detailed body parts yet)

### Future Enhancements (Phase 3+)

- Web-based gameplay (Evennia webclient integration)
- Real-time character updates (WebSocket)
- Advanced appearance customization (separate form)
- Account dashboard with death statistics
- Multiple active characters support (if MAX_NR_CHARACTERS changed)

---

---

## Research Notes: Evennia Default Character System

### What Evennia Provides Out-of-the-Box

**Discovered:** October 16, 2025 via GitHub repository research

**Character Management System (`evennia/web/website/`):**

**1. Views (`views/characters.py`):**
- `CharacterMixin` - Configures views for Character objects
- `CharacterListView` - Browse all characters (`/characters/`)
- `CharacterCreateView(CharacterMixin, ObjectCreateView)` - Create characters (`/characters/create/`)
- `CharacterManageView` - Manage owned characters (`/characters/manage/`)
- `CharacterDetailView` - View character details (`/characters/detail/<slug>/<pk>/`)
- `CharacterUpdateView` - Edit character attributes (`/characters/update/<slug>/<pk>/`)
- `CharacterDeleteView` - Delete characters (`/characters/delete/<slug>/<pk>/`)
- `CharacterPuppetView` - Switch active character (for web sessions)

**2. Forms (`forms.py`):**
- `CharacterForm(ObjectForm)` - Django form for character creation
  - Default fields: `db_key` (name), `desc` (description)
  - Meta class specifies Character model and field configuration
  - Help text and validation built-in
- `CharacterUpdateForm(CharacterForm)` - For editing (can restrict fields)
- Extends `ObjectForm` which extends `EvenniaForm, ModelForm`

**3. Templates (`templates/website/`):**
- `character_form.html` - Character creation/edit form
  - Bootstrap styling
  - CSRF protection
  - Error display
  - Field iteration with help text
- `character_list.html` - Browse characters (public)
- `character_manage_list.html` - Manage owned characters
  - Character cards with thumbnails
  - Edit/Delete links
  - Date created display
- `character_detail.html` - View single character details

**4. URL Routes (`urls.py`):**
```python
urlpatterns = [
    path("characters/", CharacterListView.as_view(), name="characters"),
    path("characters/create/", CharacterCreateView.as_view(), name="character-create"),
    path("characters/manage/", CharacterManageView.as_view(), name="character-manage"),
    path("characters/detail/<str:slug>/<int:pk>/", CharacterDetailView.as_view(), name="character-detail"),
    path("characters/puppet/<str:slug>/<int:pk>/", CharacterPuppetView.as_view(), name="character-puppet"),
    path("characters/update/<str:slug>/<int:pk>/", CharacterUpdateView.as_view(), name="character-update"),
    path("characters/delete/<str:slug>/<int:pk>/", CharacterDeleteView.as_view(), name="character-delete"),
]
```

**5. Character Creation Flow (Default):**
```python
class CharacterCreateView(CharacterMixin, ObjectCreateView):
    template_name = "website/character_form.html"
    
    def form_valid(self, form):
        """Called when form passes validation"""
        account = self.request.user
        
        # Extract form data
        self.attributes = {k: form.cleaned_data[k] for k in form.cleaned_data.keys()}
        charname = self.attributes.pop("db_key")
        description = self.attributes.pop("desc")
        
        # Create character using typeclass.create()
        character, errors = self.typeclass.create(charname, account, description=description)
        
        if character:
            # Assign any additional attributes from form
            for key, value in self.attributes.items():
                setattr(character.db, key, value)
            
            messages.success(self.request, f"Your character '{character.name}' was created!")
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(self.request, "Your character could not be created.")
            return self.form_invalid(form)
```

### Key Design Patterns

**1. Class-Based Views (CBV) with Mixins:**
```python
# Evennia uses Django's CBV pattern extensively
class CharacterCreateView(CharacterMixin, ObjectCreateView):
    # CharacterMixin configures for Character objects
    # ObjectCreateView provides create functionality
    pass
```

**2. Typeclass-Based Model Access:**
```python
# Model determined by settings
model = class_from_module(
    settings.BASE_CHARACTER_TYPECLASS, 
    fallback=settings.FALLBACK_CHARACTER_TYPECLASS
)
```

**3. Form-Based Validation:**
```python
# Django forms handle validation and cleaning
class CharacterForm(ObjectForm):
    class Meta:
        model = Character  # From settings
        fields = ("db_key",)  # Database fields to expose
        labels = {"db_key": "Name"}  # Human-readable labels
    
    # Add custom fields as form fields
    desc = forms.CharField(
        label="Description",
        max_length=2048,
        widget=forms.Textarea(attrs={"rows": 3})
    )
```

**4. Attribute Storage Pattern:**
```python
# Core fields stored in database (db_key, db_typeclass_path)
# Custom attributes stored in Evennia's attribute system
character.db.custom_stat = value  # Sets an Attribute object
```

**5. Template Extension Pattern:**
```html
<!-- Evennia templates use Django template inheritance -->
{% extends "website/base.html" %}

{% block content %}
    <!-- Page-specific content -->
{% endblock %}
```

### What This Means for Our Implementation

**✅ We MUST:**
- Extend `CharacterForm` with GRIM fields (not create parallel form)
- Override `CharacterCreateView.form_valid()` for custom logic
- Modify `character_form.html` template (not create new template)
- Use existing `/characters/` URL namespace
- Follow class-based view patterns with mixins
- Store GRIM stats in `character.db.*` attributes

**❌ We MUST NOT:**
- Create function-based views (breaks Evennia patterns)
- Create parallel URL structure (`/character/` vs `/characters/`)
- Create entirely new templates when existing ones can be extended
- Create forms that don't extend Evennia's base forms
- Store data in ways incompatible with Evennia's attribute system

**Key Learning:**
Evennia already has a **complete, production-ready** character creation system. Our job is to ADD GRIM stats and flash cloning to it, not build a new system from scratch. This is done through:
1. Form extension (add fields)
2. View override (add validation)
3. Template modification (add UI)
4. New view addition (add respawn)

**Reference Materials:**
- Evennia Web Character Generation Tutorial: https://github.com/evennia/evennia/tree/main/docs/source/Howtos/Web-Character-Generation.md
- Evennia's CharacterCreateView source: `evennia/web/website/views/characters.py`
- Evennia's CharacterForm source: `evennia/web/website/forms.py`
- Evennia's templates: `evennia/web/templates/website/character_*.html`

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
