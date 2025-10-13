# Remote Detonator System Specification

## Status: 📋 SPECIFICATION - NOT YET IMPLEMENTED

## Overview
A handheld remote detonator device that can scan and remotely trigger explosive devices. The detonator maintains a list of up to 20 scanned explosives and can trigger them individually or simultaneously by pulling their pins and starting their normal fuse countdowns. This system integrates with all existing explosive types (sticky grenades, rigged explosives, standard grenades) and respects their unique behaviors.

## Design Philosophy

**Key Principle:** Remote detonation **initiates** the explosive's normal behavior, it doesn't bypass it.

- Remote detonation **pulls the pin** and starts the fuse countdown
- SPDR M9 sticky grenades still get their 6-second countdown to seek/stick
- Rigged explosives still get their 1-second countdown
- Tactical grenades with 5-second fuses give 5 seconds to react
- This maintains explosive type diversity and prevents instant-death scenarios

**Tactical Gameplay:**
- Plan complex multi-stage detonations with timed delays
- Create distractions with long-fuse grenades while rigged traps explode quickly
- Override rigged traps remotely before they're triggered by victims
- Mass detonation creates chaos with staggered explosion timing

---

## 1. Remote Detonator Item

### Item Properties

```python
# New item typeclass: RemoteDetonator
class RemoteDetonator(Item):
    """
    Handheld remote detonator for explosive devices.
    Can scan and remotely trigger up to 20 explosives.
    """
    
    def at_object_creation(self):
        """Set up detonator attributes"""
        self.db.scanned_explosives = []  # List of explosive dbrefs (max 20)
        self.db.max_capacity = 20        # Maximum scanned explosives
        self.db.device_type = "remote_detonator"
```

### Prototype

```python
REMOTE_DETONATOR = {
    "key": "remote detonator",
    "aliases": ["detonator", "remote", "trigger"],
    "typeclass": "typeclasses.items.RemoteDetonator",
    "desc": "A compact military-grade remote detonator with a digital display showing scanned explosive devices. The device can store up to 20 explosive signatures and trigger them remotely with the press of a button. A red safety cover protects the main detonation switch.",
    "attrs": [
        ("scanned_explosives", []),  # List of explosive dbrefs
        ("max_capacity", 20),        # Maximum capacity
        ("device_type", "remote_detonator"),
    ]
}
```

---

## 2. Explosive Tracking

### Bidirectional Relationship

Each explosive can only be scanned by ONE detonator at a time, but detonators can scan multiple explosives:

```python
# On explosive
explosive.db.scanned_by_detonator = detonator_dbref or None

# On detonator  
detonator.db.scanned_explosives = [explosive_dbref1, explosive_dbref2, ...]
```

### Scanning Rules

1. **One Detonator Per Explosive:**
   - An explosive can only be linked to one detonator at a time
   - Scanning with a new detonator **overrides** the previous link
   - Previous detonator automatically removes explosive from its list

2. **Capacity Limit:**
   - Detonators can scan up to 20 explosives
   - Attempting to scan beyond capacity shows error message
   - Must clear explosives to free up slots

3. **No Range Limit:**
   - Once scanned, detonation works from any distance
   - Works across rooms, floors, locations
   - Persistent link until explosive detonates or is cleared

4. **Automatic Cleanup:**
   - Detonated explosives auto-remove from detonator list
   - Destroyed explosives auto-remove from detonator list
   - Detonator validates list on command use

---

## 3. Command System

### Scan Command

**Syntax:** `scan <explosive> with <detonator>`

**Behavior:**
```python
1. Validate both objects exist and in inventory/room
2. Confirm explosive has is_explosive attribute
3. Check detonator capacity (< 20)
4. Check if explosive already scanned by different detonator:
   - If yes: Override old detonator link, add to new detonator
   - If no: Add to detonator
5. Set bidirectional references:
   explosive.db.scanned_by_detonator = detonator.dbref
   detonator.db.scanned_explosives.append(explosive.dbref)
6. Send success messages
```

**Messages:**
```
You: You scan the SPDR M9 grenade with your remote detonator. A soft beep confirms the explosive signature has been registered as e-1234.

Room: {char_name} scans a SPDR M9 grenade with their remote detonator, which emits a soft confirmation beep.
```

**Edge Cases:**
- Scanning already-scanned explosive: "The SPDR M9 grenade is already scanned by this detonator."
- Capacity full: "Your remote detonator is at maximum capacity (20/20). Clear some explosives first."
- Already scanned by different detonator: Override old link and show message
- Non-explosive item: "The sword is not an explosive device."

---

### Detonate Single Command

**Syntax:** `detonate e-<dbref> with <detonator>`

**Behavior:**
```python
1. Validate dbref is in detonator's scanned list
2. Get explosive object from dbref
3. Validate explosive still exists and is valid
4. Check if pin already pulled:
   - If countdown already active: "e-1234 is already detonating!"
   - If not: Pull pin and start countdown
5. Trigger explosive's normal pin-pull behavior:
   explosive.db.pin_pulled = True
   explosive.ndb.countdown_remaining = explosive.db.fuse_time
   start_fuse_countdown(explosive)
6. Send detonation messages
7. Keep explosive in scanned list (will auto-remove on explosion)
```

**Messages:**
```
You: You press the button for e-1234 on your remote detonator. The SPDR M9 grenade's blue LED begins pulsing rapidly! (6 seconds)

Room: {char_name} presses a button on their remote detonator. A SPDR M9 grenade's blue LED begins pulsing rapidly!

Observer at grenade location (if different room): A SPDR M9 grenade suddenly activates, its blue LED pulsing rapidly!
```

**Edge Cases:**
- Invalid dbref: "e-1234 is not in this detonator's memory."
- Explosive doesn't exist: "e-1234 no longer exists. [Auto-removed from list]"
- Already detonating: "e-1234 is already armed and counting down!"

---

### Detonate All Command

**Syntax:** `detonate all with <detonator>`

**Behavior:**
```python
1. Validate detonator has scanned explosives
2. Iterate through all scanned explosives:
   - Validate explosive exists
   - Check if already detonating
   - Pull pin and start countdown for each valid explosive
3. Track success/failure counts
4. Send summary message
5. Explosives will auto-remove from list as they explode
```

**Messages:**
```
You: You flip open the red safety cover and press the DETONATE ALL button. Your remote detonator confirms: 5 explosives armed, 1 already active, 2 invalid.

Your remote detonator displays:
  e-1234: ARMED (6s) - SPDR M9 grenade
  e-1235: ARMED (8s) - frag grenade  
  e-1236: ARMED (5s) - tactical grenade
  e-1237: ARMED (10s) - demo charge
  e-1238: ARMED (1s) - rigged SPDR M9 grenade
  e-1239: [ALREADY ACTIVE]
  e-1240: [INVALID - REMOVED]
  e-1241: [INVALID - REMOVED]

Room: {char_name} flips open a red safety cover on their remote detonator and presses a large button. Multiple distant beeps echo from various locations!
```

**Edge Cases:**
- Empty list: "Your remote detonator has no scanned explosives."
- All already active: "All scanned explosives are already detonating."
- Mixed results: Show detailed breakdown of successes/failures

---

### List Command

**Syntax:** `detonate list with <detonator>` or `detonator list` (if wielded)

**Behavior:**
```python
1. Validate detonator has scanned explosives
2. Iterate through scanned list:
   - Get explosive object
   - Check if exists and valid
   - Get explosive state (pin_pulled, countdown_remaining, location)
   - Auto-remove invalid explosives
3. Display boxtable with explosive information
```

**Display Format:**
```
╔════════════════════════════════════════════════════════════════════╗
║                   REMOTE DETONATOR - SCANNED DEVICES                ║
║                              Capacity: 8/20                         ║
╠═══════╦══════════════════════╦════════╦═══════════╦════════════════╣
║ ID    ║ Device               ║ Status ║ Fuse      ║ Location       ║
╠═══════╬══════════════════════╬════════╬═══════════╬════════════════╣
║ e-123 ║ SPDR M9 grenade      ║ READY  ║ 6s        ║ Armory         ║
║ e-124 ║ frag grenade         ║ ACTIVE ║ 3s left!  ║ Hallway        ║
║ e-125 ║ tactical grenade     ║ READY  ║ 5s        ║ Your inventory ║
║ e-126 ║ demo charge          ║ READY  ║ 10s       ║ Storage room   ║
║ e-127 ║ rigged SPDR M9       ║ READY  ║ 1s (trap) ║ Doorway        ║
║ e-128 ║ SPDR M9 grenade      ║ STUCK  ║ 4s left!  ║ On Marcia      ║
║ e-129 ║ smoke grenade        ║ READY  ║ 4s        ║ Your inventory ║
║ e-130 ║ flashbang            ║ READY  ║ 6s        ║ Your inventory ║
╚═══════╩══════════════════════╩════════╩═══════════╩════════════════╝

Status Legend:
  READY  - Armed and ready for remote detonation
  ACTIVE - Currently counting down (pin already pulled)
  STUCK  - Sticky grenade adhered to target
  TRAP   - Rigged explosive waiting for trigger
```

**State Information:**
- **READY**: Pin not pulled, ready for remote detonation
- **ACTIVE**: Pin pulled, countdown in progress
- **STUCK**: Sticky grenade adhered to armor/character
- **TRAP**: Rigged explosive set up as trap

**Location Information:**
- Room name if in a room
- "Your inventory" if carried by user
- "On {character_name}" if stuck to character
- "Dropped at {room}" if on ground

**Edge Cases:**
- Empty list: "Your remote detonator has no scanned explosives."
- All invalid: Auto-clear and show: "All previously scanned explosives are invalid. List cleared."

---

### Clear Single Command

**Syntax:** `clear e-<dbref> from <detonator>`

**Behavior:**
```python
1. Validate dbref is in detonator's scanned list
2. Get explosive object (if exists)
3. Remove bidirectional references:
   detonator.db.scanned_explosives.remove(explosive_dbref)
   explosive.db.scanned_by_detonator = None (if explosive exists)
4. Send success message
```

**Messages:**
```
You: You clear e-1234 (SPDR M9 grenade) from your remote detonator's memory.

Room: {char_name} presses several buttons on their remote detonator.
```

**Edge Cases:**
- Invalid dbref: "e-1234 is not in this detonator's memory."
- Explosive doesn't exist: Auto-remove and confirm: "e-1234 no longer exists. Removed from memory."

---

### Clear All Command

**Syntax:** `clear all from <detonator>` or `detonator clear`

**Behavior:**
```python
1. Iterate through all scanned explosives
2. For each valid explosive:
   explosive.db.scanned_by_detonator = None
3. Clear detonator's list:
   detonator.db.scanned_explosives = []
4. Send success message with count
```

**Messages:**
```
You: You clear all 8 explosive signatures from your remote detonator's memory.

Room: {char_name} holds down a button on their remote detonator, which emits a series of beeps before going silent.
```

**Edge Cases:**
- Empty list: "Your remote detonator has no scanned explosives to clear."

---

## 4. Integration with Existing Explosion Logic

### Pin Pull Mechanism

Remote detonation uses the **same pin-pull logic** as manual grenade usage:

```python
def remote_detonate_explosive(explosive):
    """
    Remotely detonate an explosive by pulling its pin.
    Starts normal fuse countdown - does NOT bypass explosive behavior.
    """
    from world.combat.utils import start_fuse_countdown  # Or wherever this lives
    
    # Check if already detonating
    if getattr(explosive.db, 'pin_pulled', False):
        return False, "already_active"
    
    # Pull the pin (same as manual pull)
    explosive.db.pin_pulled = True
    
    # Get fuse time from explosive
    fuse_time = getattr(explosive.db, 'fuse_time', 8)
    
    # Set countdown
    explosive.ndb.countdown_remaining = fuse_time
    
    # Start countdown using existing system
    start_fuse_countdown(explosive)
    
    return True, fuse_time
```

### Explosive Type Behaviors

**Standard Grenades (frag, tactical, demo):**
```python
# Remote detonation → Pin pulled → Countdown starts → Explosion at location
# Uses existing explosion logic from CmdThrow.py
```

**SPDR M9 Sticky Grenades:**
```python
# Remote detonation → Pin pulled → 6s countdown
# During countdown: If thrown, still seeks magnetic targets
# If stuck: Explodes stuck to armor (existing behavior)
# If on ground: Explodes at ground location (existing behavior)
```

**Rigged Explosives:**
```python
# Remote detonation → Pin pulled → 1s countdown → Explosion
# Bypasses trap trigger logic (remote override)
# Uses existing rigged explosive explosion logic
# Respects proximity system for damage calculation
```

**Thrown Grenades (in flight or countdown):**
```python
# If grenade is thrown and countdown already started:
# Remote detonation attempt → "already active" message
# Cannot re-trigger already-counting explosives
```

### Explosion Function Integration

The detonator calls existing explosion paths:

```python
# Standard explosive explosion
# Located in: CmdThrow.py or world/combat/utils.py
def explode_grenade(grenade):
    """Existing explosion logic"""
    # Get location (room or armor hierarchy)
    # Get proximity list
    # Calculate damage
    # Apply damage to all in proximity
    # Check human shield mechanics
    # Destroy grenade object
    # Send explosion messages

# Remote detonation simply triggers this:
remote_detonate(explosive) → pull_pin(explosive) → start_countdown(explosive) → explode_grenade(explosive)
```

---

## 5. Edge Cases and Special Scenarios

### Sticky Grenades

**Scenario 1: Stuck to Armor**
```python
# SPDR M9 is magnetically stuck to character's plate mail
# Remote detonation pulls pin → 6s countdown
# Grenade explodes while stuck to armor (existing behavior)
# Damage applied to wearer and proximity
```

**Scenario 2: In Inventory**
```python
# SPDR M9 in character's inventory
# Remote detonation pulls pin → 6s countdown
# Character holding live grenade (existing behavior)
# Can drop before explosion
```

**Scenario 3: On Ground**
```python
# SPDR M9 on ground in room
# Remote detonation pulls pin → 6s countdown
# Explodes at ground location
# Damages everyone in proximity (existing logic)
```

### Rigged Explosives

**Scenario 1: Trap Override**
```python
# Rigged explosive set up as trap in doorway
# Remote detonation pulls pin → 1s countdown
# Explodes BEFORE anyone triggers trap
# Useful for clearing your own traps safely
```

**Scenario 2: Trap + Remote**
```python
# Rigged explosive scanned by detonator
# Someone triggers trap → 1s countdown starts
# Remote detonation attempt → "already active"
# Cannot re-trigger during countdown
```

### Multiple Detonators

**Scenario: Override Behavior**
```python
# Detonator A scans grenade → grenade.db.scanned_by_detonator = A
# Detonator B scans same grenade:
#   - Remove from Detonator A's list
#   - Add to Detonator B's list  
#   - grenade.db.scanned_by_detonator = B
# Detonator A can no longer detonate it
```

### Automatic Cleanup

**Scenario: Explosive Detonated**
```python
# Explosive explodes (any method: manual, remote, trap)
# On explosion completion:
#   - explosive.db.scanned_by_detonator → get detonator
#   - detonator.db.scanned_explosives.remove(explosive_dbref)
#   - Cleanup happens automatically in explosion function
```

**Scenario: Explosive Destroyed**
```python
# Explosive destroyed (taken from corpse, destroyed object, etc)
# On object destruction:
#   - Check explosive.db.scanned_by_detonator
#   - Remove from detonator's list
#   - Or validate on next list command
```

**Scenario: Detonator Destroyed**
```python
# Detonator destroyed/taken
# Iterate through detonator.db.scanned_explosives
# Clear explosive.db.scanned_by_detonator for each
# Explosives no longer remotely detonable
```

---

## 6. Implementation Checklist

### New Code Required

**1. RemoteDetonator Typeclass** (`typeclasses/items.py`)
```python
class RemoteDetonator(Item):
    """Remote detonator for explosive devices"""
    def at_object_creation(self):
        # Initialize attributes
    
    def validate_scanned_list(self):
        # Clean up invalid explosives
    
    def add_explosive(self, explosive):
        # Add to scanned list with validation
    
    def remove_explosive(self, explosive):
        # Remove from scanned list
    
    def detonate_explosive(self, explosive):
        # Trigger single explosive
    
    def detonate_all(self):
        # Trigger all explosives
```

**2. New Commands** (`commands/combat/detonator.py` - new file)
```python
class CmdScan(Command):
    """Scan explosive with detonator"""
    
class CmdDetonate(Command):
    """Detonate single or all explosives"""
    
class CmdDetonateList(Command):
    """List scanned explosives"""
    
class CmdClearDetonator(Command):
    """Clear single or all explosives from detonator"""

class DetonatorCmdSet(CmdSet):
    """Command set for detonator commands"""
```

**3. Integration Hooks** (Modify existing explosion code)
```python
# In existing explosion functions:
def explode_grenade(grenade):
    # ... existing explosion logic ...
    
    # NEW: Auto-cleanup detonator reference
    if hasattr(grenade.db, 'scanned_by_detonator'):
        detonator_dbref = grenade.db.scanned_by_detonator
        if detonator_dbref:
            detonator = search_object(f"#{detonator_dbref}")
            if detonator:
                remove_explosive_from_detonator(detonator, grenade)
    
    # ... rest of explosion logic ...
```

**4. Utility Functions** (`world/combat/utils.py`)
```python
def validate_detonator_list(detonator):
    """Clean up invalid explosives from detonator list"""

def format_detonator_display(detonator):
    """Generate boxtable display for scanned explosives"""
    
def get_explosive_state_string(explosive):
    """Return state string (READY/ACTIVE/STUCK/TRAP)"""
    
def get_explosive_location_string(explosive):
    """Return location string for display"""
```

### Modified Code

**1. Explosive Items** (`world/prototypes.py` or existing explosives)
```python
# Add to all explosive prototypes:
"attrs": [
    # ... existing attrs ...
    ("scanned_by_detonator", None),  # Detonator dbref or None
]
```

**2. Explosion Functions** (Wherever they currently live)
```python
# Add cleanup hook to explosion completion
# Ensure sticky grenades, rigged explosives, standard explosives all clean up
```

### Testing Priorities

1. ✅ Scan explosive with detonator
2. ✅ Display detonator list with boxtable
3. ✅ Remote detonate single explosive → countdown starts
4. ✅ Remote detonate all → multiple countdowns
5. ✅ SPDR M9 remote detonation → still seeks/sticks during countdown
6. ✅ Rigged explosive remote detonation → 1s countdown
7. ✅ Explosive override (scan with second detonator)
8. ✅ Auto-cleanup after explosion
9. ✅ Clear single explosive from detonator
10. ✅ Clear all explosives from detonator

---

## 7. Command Reference Summary

```
scan <explosive> with <detonator>
  - Scan explosive device into detonator memory
  - Max 20 explosives per detonator
  - Overrides previous detonator link

detonate e-<dbref> with <detonator>
  - Remotely detonate specific explosive
  - Pulls pin and starts fuse countdown
  - Respects explosive type behavior

detonate all with <detonator>
  - Remotely detonate all scanned explosives
  - Pulls pins and starts countdowns for all
  - No confirmation required (embrace chaos)

detonate list with <detonator>
  - Display boxtable of scanned explosives
  - Shows ID, type, status, fuse time, location
  - Auto-validates and cleans invalid entries

clear e-<dbref> from <detonator>
  - Remove single explosive from detonator
  - Breaks bidirectional link
  - Explosive no longer remotely detonable

clear all from <detonator>
  - Remove all explosives from detonator
  - Breaks all bidirectional links
  - Frees all 20 capacity slots
```

---

## 8. Future Enhancements (Not in Initial Implementation)

**Range Limitations:**
- Add signal strength system
- Require line-of-sight or proximity
- Interference from walls/materials

**Security Features:**
- Encrypted detonators with passcodes
- Anti-tamper mechanisms
- Signal jamming devices

**Advanced Features:**
- Timed/delayed remote detonation
- Sequential detonation patterns
- Multi-detonator synchronization
- Abort/disarm capabilities

**UI Improvements:**
- Sort detonator list by type/location/status
- Filter active vs ready explosives
- Highlight explosives in current room

---

## 9. Design Notes

**Why No Instant Detonation:**
- Maintains explosive type diversity (sticky vs standard vs rigged)
- Creates tactical timing windows
- Prevents instant-death griefing
- Allows counterplay (flee during countdown)
- Respects existing explosion code paths

**Why One Detonator Per Explosive:**
- Prevents detonator conflicts
- Clear ownership model
- Simplifies state tracking
- Makes override behavior intuitive

**Why No Range Limit:**
- Simpler implementation
- More cinematic gameplay
- Prevents frustrating "out of range" edge cases
- Can add range limits later if needed

**Why 20 Capacity:**
- High enough for tactical complexity
- Low enough to require planning
- Reasonable to display in UI
- Can adjust based on gameplay testing

---

## Conclusion

The remote detonator adds a powerful tactical tool for explosive management while respecting all existing explosive behaviors. By triggering normal pin-pull and countdown logic rather than bypassing it, the system maintains the unique characteristics of each explosive type (SPDR M9 magnetic seeking, rigged explosive trap mechanics, varied fuse times) while enabling complex multi-stage detonation plans.

The bidirectional tracking system ensures clean state management, and the override mechanics prevent conflicts while allowing detonator theft/takeover gameplay. Combined with the boxtable display and capacity management, this creates a robust foundation for explosive-focused tactical gameplay.
