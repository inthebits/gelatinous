# Character Cleanup Guide

## Problem

During testing of the character creation and death systems, multiple instances of characters (particularly "Laszlo") were created with inconsistent states. This can cause issues with:

- Character selection at login
- Archived vs active character detection
- Multiple characters with similar names
- Missing or incorrect attributes (clone_generation, archived, etc.)

## Diagnostic Tools

### @inspect_chars [account_name]

Inspect all characters for an account and their states.

```
@inspect_chars Laszlo
@inspect_chars
```

Shows:
- Character ID and name
- Location
- Archived status and reason
- Clone generation
- Death count
- Stack ID
- Status summary (ACTIVE/ARCHIVED/LEGACY)

**Use this first** to understand what characters exist and their states.

## Cleanup Tools

### @archive_char <character_name> [reason]

Mark a character as inactive without deleting them.

```
@archive_char Laszlo "old test character"
@archive_char "Laszlo II" testing
```

**Use this for:**
- Old test characters you want to keep but not use
- Characters with broken states
- Duplicate characters from failed tests

### @unarchive_char <character_name>

Restore an archived character to active status.

```
@unarchive_char Laszlo
@unarchive_char #12345
```

**Use this for:**
- Restoring accidentally archived characters
- Reactivating characters after fixing their state

### @delete_char <character_name> /confirm

**PERMANENTLY** delete a character (cannot be undone).

```
@delete_char Laszlo /confirm
@delete_char #12345 /confirm
```

**Use this for:**
- Completely removing unwanted test characters
- Cleaning up duplicate characters
- Removing corrupted characters that can't be fixed

⚠️ **WARNING:** This is permanent! Use @archive_char instead if you're unsure.

## Recommended Cleanup Process

### 1. Inspect Current State

```
@inspect_chars Laszlo
```

Review all characters and note:
- Which ones are legacy (no archived attribute)
- Which ones are test characters
- Which one is the "real" active character

### 2. Archive Test Characters

For each old/test character you want to keep but not use:

```
@archive_char "Old Laszlo" "testing - before flash clone system"
@archive_char "Laszlo Test" "early test character"
```

### 3. Delete Unwanted Characters

For characters you don't need at all:

```
@delete_char "Laszlo Duplicate" /confirm
@delete_char #12345 /confirm
```

### 4. Verify Clean State

```
@inspect_chars Laszlo
```

Should show only:
- One active character (the one you want to use)
- Any archived characters (for records)
- No legacy characters with missing attributes

### 5. Test Login

Log out and back in. You should:
- See the OOC menu with character list
- NOT see the character creation menu (if you have active characters)
- Be able to use `ic <character>` to puppet your character

## Example Cleanup Session

```
> @inspect_chars
Character Inspection for Account: Laszlo
----------------------------------------------------------------------

Character: Laszlo (#12340)
  Location: Limbo
  Archived: None 
  Clone Generation: None
  Death Count: 2
  Stack ID: None
  Status: LEGACY (no archived attribute)

Character: Laszlo II (#12345)
  Location: Limbo
  Archived: None 
  Clone Generation: 2
  Death Count: 1
  Stack ID: 1
  Status: LEGACY (no archived attribute)

Character: Laszlo III (#12350)
  Location: Braddock Avenue
  Archived: False
  Clone Generation: 3
  Death Count: 2
  Stack ID: 1
  Status: ACTIVE

Total characters: 3

> @archive_char Laszlo "original test character"
Archived character: Laszlo (#12340)
Reason: original test character

> @archive_char "Laszlo II" "second test character"
Archived character: Laszlo II (#12345)
Reason: second test character

> @inspect_chars
Character Inspection for Account: Laszlo
----------------------------------------------------------------------

Character: Laszlo (#12340)
  Location: Limbo
  Archived: True (original test character)
  Clone Generation: None
  Death Count: 2
  Stack ID: None
  Status: ARCHIVED

Character: Laszlo II (#12345)
  Location: Limbo
  Archived: True (second test character)
  Clone Generation: 2
  Death Count: 1
  Stack ID: 1
  Status: ARCHIVED

Character: Laszlo III (#12350)
  Location: Braddock Avenue
  Archived: False
  Clone Generation: 3
  Death Count: 2
  Stack ID: 1
  Status: ACTIVE

Total characters: 3

> quit
[...logs out and back in...]

> Available character(s) (1/1, ic <name> to play):
 - Laszlo III [player]

> ic Laszlo III
You become Laszlo III.
```

## Debugging Login Issues

If you're still seeing the character creation menu when you shouldn't:

1. Check Splattercast channel for debug messages:
   ```
   AT_POST_LOGIN: Account Laszlo - all_chars=3, active_chars=1
   AT_POST_LOGIN: Active characters: [('Laszlo III', 12350)]
   AT_POST_LOGIN: Has 1 active characters, using default OOC menu
   ```

2. If active_chars is 0 but you have characters:
   - They might all be archived
   - Use @unarchive_char on the one you want active

3. If you're seeing multiple EvMenu prompts:
   - An old EvMenu might be stuck
   - Try: `@py caller.ndb._evmenu = None` then reconnect

4. If none of this works:
   - Delete all test characters with @delete_char
   - Keep only ONE active character
   - Restart server with `evennia reload`

## Prevention

Going forward:
- Use @archive_char instead of leaving dead characters around
- The flash clone system properly manages clone_generation now
- Death system archives old bodies automatically
- Login system only triggers character creation if NO active characters exist

## Notes

- Archived characters are kept in the database for records
- You can always unarchive a character later
- Deletion is permanent and cannot be undone
- All tools require Builder or Developer permissions
- Character IDs can be used instead of names to avoid ambiguity
