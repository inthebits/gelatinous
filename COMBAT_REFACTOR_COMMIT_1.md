"""
COMMIT MESSAGE FOR CONSTANTS EXTRACTION
========================================

feat: Extract combat constants and utilities

**Step 1 of Combat System Refactor - All gas, no brakes!** 🚀

- Created world/combat/ package following Python best practices
- Extracted 50+ constants from scattered magic strings/numbers
- Built comprehensive utils.py with reusable combat functions
- Demonstrated pattern with CmdCharacter.py box drawing constants
- Started migration in CmdCombat.py attack command
- Maintained 100% backward compatibility through re-exports

**Constants organized by category:**
- Character attributes & G.R.I.M. system defaults
- Debug logging prefixes and action types  
- NDB field names (critical for state management)
- Database field names for combat entries
- Permission strings and access types
- Color codes and message formatting
- Weapon types and combat actions
- Common message templates

**Utilities include:**
- Dice rolling with stat validation
- Standardized debug logging
- Character state management (proximity, NDB)
- Weapon detection helpers
- Message formatting with color preservation
- Combat target validation

**Next:** Continue migrating CmdCombat.py to use constants and utils,
then extract proximity.py and grappling.py modules.

Follows priority: Python → Evennia → AI-driven → Open Source best practices
"""
