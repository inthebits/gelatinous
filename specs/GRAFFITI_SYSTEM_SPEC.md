# Graffiti System Specification

## Overview
Player-driven graffiti system allowing street-level expression through spray paint cans. Provides resource-managed tagging mechanics with finite paint supplies, color selection, and room integration.

## Core Components

### 1. Spray Paint Cans (Item Typeclass)
**Attributes:**
- `paint_level`: Integer (e.g., 256) - remaining paint characters
- `current_color`: String - selected ANSI color
- `max_paint`: Integer - starting paint capacity (prototype-defined)

**Functionality:**
- Color toggle command to cycle through ANSI colors
- Paint depletion tracking (1 character = 1 paint unit)
- Empty cans become unusable until refilled/replaced

### 2. Solvent Cans (Item Typeclass)
**Purpose:** Clean all graffiti from current room
**Functionality:**
- Single-use or multi-use (prototype-defined)
- Removes all graffiti entries from room
- Removes graffiti integration from room description

### 3. Graffiti Storage Object (Room Integration)
**Storage Mechanics:**
- Maximum 7 graffiti entries per room
- FIFO queue - entry 8+ removes oldest entry
- Each entry format: `"Scrawled in <color> paint: <message>"`

**Integration:**
- Appears in room description: "The walls have been daubed with colorful graffiti"
- Becomes examinable object: `look graffiti`
- Persists when empty until solvent applied

### 4. Spray Command
**Syntax:** `spray "message" with <spray_can>`
**Target:** Always current room (implicit)

**Mechanics:**
- Validates spray can has paint
- Enforces maximum message length (quality control)
- Deducts character count from paint_level
- Truncates message if paint runs out mid-spray
- Adds entry to room's graffiti storage
- Creates graffiti integration if first entry

**Paint Depletion:**
- Direct character-to-paint correlation
- Mid-message truncation creates incomplete entries (e.g., "This here...")
- No minimum message length before truncation

### 5. Color System
**Supported Colors:** Standard ANSI color set
- cyan, green, magenta, red, yellow, blue, white, etc.

**Color Toggle:** Command on spray can to cycle through available colors
**Storage:** Current color saved per spray can instance

## Integration with LOOK System

### Room Description Integration
- Graffiti integration triggers: `@integrate Graffiti`
- Adds atmospheric line: "The walls have been daubed with colorful graffiti"
- Integration appears with first graffiti entry
- Persists until solvent removes all entries

### Examination Mechanics
- `look graffiti` displays all stored entries
- Chronological order (newest first or oldest first - TBD)
- Color-coded display using ANSI colors
- Empty graffiti objects show appropriate "clean walls" message

## Resource Economy

### Paint Management
- Finite paint encourages thoughtful messaging
- Character-based depletion prevents spam
- Empty cans create resource scarcity
- Partial messages add realism/immersion

### Cleanup Economics
- Solvent cans provide graffiti removal
- Balances creation vs. cleanup
- Allows property maintenance roleplay
- Creates janitor/cleanup job opportunities

## Quality Control Measures

### Message Length Limits
- Maximum 100 characters per message
- Prevents excessive room description bloat
- Maintains readability in graffiti examinations
- Automatic truncation at limit

### Storage Limits
- 7-entry maximum prevents room spam
- FIFO system keeps content fresh (oldest first display)
- Oldest entries naturally age out
- Encourages active graffiti areas

## Technical Implementation Details

### Color Selection Commands
- `press <color> on <spraycan/red_can/etc>` - Cycle to specified color
- Separate command file (`CmdPress.py`) - expandable for future press mechanics
- Feedback message for command issuer only: "You adjust the nozzle to cyan"
- Works on any spray can object regardless of current color

### Graffiti Object Creation
- Auto-create graffiti objects named simply "graffiti" 
- Use standard item typeclass, locked in place (not takeable/moveable)
- One graffiti object maximum per room (enforce uniqueness)
- Relies on room integration for atmospheric description

### Solvent Usage
- `spray here with <solvent_can>` - Clean graffiti in current room
- Removes random individual characters from random messages
- Vague atmospheric feedback: "Solvent bubbles against the wall as graffiti fades away..."
- 256 uses per solvent can (yin/yang balance with spray paint)
- Error handling: "There's no graffiti here" if room has no graffiti

### Paint Economics
- Starting paint_level: 256 characters per spray can
- All colors cost 1:1 character ratio (color irrelevant for economics)
- Single prototype covers all spray cans (color is toggleable attribute)
- Empty cans: Command destroys can with message "You toss the empty can away"

### Partial Spraying Mechanics
- Mid-message paint depletion creates incomplete entries
- Message truncated at exact paint exhaustion point
- Adds realism and resource management tension

### Integration Timing
- @integrate added: When first graffiti entry created (no existing graffiti object)
- @integrate removed: When solvent removes all characters (graffiti object deleted)
- Clean state: No integration, no graffiti object

### Display Order
- FIFO (oldest first) - entries display in chronological order
- Maintains historical narrative flow

### Integration Method
- Object persistence: Separate graffiti objects in room
- Graffiti object stores all entries as attributes
- Integrates with room's LOOK command via contents

## Implementation Notes

### File Structure
- `commands/CmdPress.py` - Press command for spray can color selection
- `commands/CmdSpray.py` - Spray command implementation
- `typeclasses/items.py` - Spray can and solvent can classes
- `typeclasses/objects.py` - Graffiti storage object class
- Integration with existing LOOK command system

### Dependencies
- LOOK command integration system
- ANSI color support
- Room description @integrate functionality
- Item prototype system

## Future Enhancements
- Gang-specific spray can colors
- Graffiti aging/fading mechanics
- Special effects (drip patterns, fade over time)
- Graffiti quality levels (novice vs. expert artists)
- Paint refill mechanics
- Graffiti removal difficulty levels
