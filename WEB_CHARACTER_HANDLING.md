# Web Character Creation & Handling

## Problem
Characters created via the web interface were appearing as unpuppeted NPCs in the game world. When archived via web, they remained in their last location instead of being properly removed from active play.

## Solution
Implemented proper character lifecycle management:
1. **Archived characters** are moved to Limbo (#2) to remove them from the game world
2. **Web-created characters** are left unpuppeted at START_LOCATION (they are invisible until puppeted)
3. **Telnet-created characters** are immediately puppeted upon creation

## Key Insight
Characters in Evennia are **invisible and non-interactive until puppeted**. An unpuppeted character:
- Does not appear in room descriptions
- Cannot be interacted with by other players
- Is effectively "offline" despite existing in the database
- Only becomes "active" when `account.puppet_object(session, character)` is called

This means web-created characters don't need special handling - they simply remain unpuppeted until the player logs in via telnet.

## Implementation Details

### 1. Archived Characters → Limbo
**File:** `typeclasses/characters.py` (archive_character method)
- All archived characters are moved to Limbo (#2)
- Uses `quiet=True` and `move_hooks=False` to prevent notifications
- Includes Splattercast logging for debugging
- Prevents archived characters from appearing as NPCs

### 2. Web-Created Characters → Stay Unpuppeted
**File:** `web/website/views/characters.py`

#### Respawn Flow (handle_respawn_submission):
- Flash clone or template-based character creation
- Character remains at START_LOCATION, unpuppeted
- Debug logging: `WEB_CHAR_CREATE: {char.key} created via web (respawn), left unpuppeted`

#### First-Time Creation (form_valid):
- New character creation with GRIM stats
- Character remains at START_LOCATION, unpuppeted
- Debug logging: `WEB_CHAR_CREATE: {char.key} created via web (first-time), left unpuppeted`

### 3. Telnet Login → Auto-Puppet
**File:** `typeclasses/accounts.py` (at_post_login method)

When a player logs in via telnet:
1. Checks for active (non-archived) characters
2. If exactly one character exists, auto-puppets it
3. Character becomes visible and interactive in the game world
4. No special handling needed for web-created vs telnet-created characters

## Flow Diagram

### Web Character Creation Flow
```
User creates character via web
    ↓
Character created at START_LOCATION (unpuppeted)
    ↓
Character is INVISIBLE (not puppeted)
    ↓
User logs in via telnet
    ↓
at_post_login auto-puppets the character
    ↓
Character becomes VISIBLE and active
    ↓
Player enters game
```

### Telnet Character Creation Flow
```
User logs in via telnet
    ↓
start_character_creation called
    ↓
Character created at START_LOCATION
    ↓
Character immediately puppeted by telnet session
    ↓
Character is VISIBLE and active
    ↓
Player enters game
```

### Character Archival Flow
```
Character archived (death or manual)
    ↓
archive_character() called
    ↓
Character moved to Limbo (#2)
    ↓
Character unpuppeted (sessions disconnected)
    ↓
Character marked as archived
    ↓
last_character reference stored on account
```

## Key Technical Details

### Puppeting States
- **Unpuppeted:** Character exists in database but is invisible/non-interactive
- **Puppeted:** Character is controlled by a session, visible and interactive
- Puppeting is what makes a character "appear" in the game world

### Character Visibility
Evennia characters are only visible when **puppeted**. An unpuppeted character:
- Does not appear in room descriptions (`look`)
- Cannot be targeted by other players
- Does not trigger presence-based game mechanics
- Exists only as a database object

This is why web-created characters don't appear as NPCs - they're unpuppeted.

### Session Types
- **Web sessions:** Django web login (request.user) - can create characters but not puppet them
- **Telnet sessions:** Game session - can puppet characters and interact with game world
- Web-created characters remain unpuppeted until player connects via telnet

### Limbo (#2)
- Storage location for inactive/archived characters
- Characters in Limbo are:
  - Unpuppeted (no active sessions)
  - Marked as archived (excluded from active character count)
  - Not participating in game mechanics

### Character States
1. **Active & Puppeted:** At game location, controlled by player session, visible
2. **Active & Unpuppeted (Web-Created):** At START_LOCATION, invisible until puppeted
3. **Archived:** In Limbo, marked as archived, excluded from active character count

## Testing Checklist

- [ ] Create character via web → verify unpuppeted, invisible in game
- [ ] Login via telnet with web-created character → verify auto-puppets and becomes visible
- [ ] Create character via telnet → verify immediately puppeted and visible
- [ ] Archive character via death → verify moves to Limbo
- [ ] Archive character manually via web → verify moves to Limbo
- [ ] Respawn via web (flash clone) → verify new character unpuppeted at START_LOCATION
- [ ] Respawn via web (template) → verify new character unpuppeted at START_LOCATION
- [ ] Check Splattercast logs for proper debug messages
- [ ] Verify unpuppeted characters don't appear in `look` command
- [ ] Verify unpuppeted characters cannot be targeted by other players

## Debug Messages

All operations log to Splattercast channel:

- `WEB_CHAR_CREATE: {char.key} created via web (respawn), left unpuppeted at {location.key}`
- `WEB_CHAR_CREATE: {char.key} created via web (first-time), left unpuppeted at {location.key}`
- `ARCHIVE: Moved {char.key} from {old_location.key} to Limbo`

## Files Modified

1. `typeclasses/characters.py` - archive_character method (moves to Limbo)
2. `web/website/views/characters.py` - Added debug logging for web character creation
3. ~~`typeclasses/accounts.py`~~ - No changes needed (at_post_login already handles auto-puppeting)

---

*Last Updated: 2025-01-27*
