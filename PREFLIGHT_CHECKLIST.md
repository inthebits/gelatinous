# Pre-Flight Testing Checklist

## ✅ Code Complete

### Core Implementation
- [x] `typeclasses/death_progression.py` - Unpuppet bug fixed, character creation integration
- [x] `commands/charcreate.py` - Full character creation system (1,045 lines)
- [x] `typeclasses/accounts.py` - at_post_login hook with character management
- [x] `server/conf/settings.py` - AUTO_PUPPET_ON_LOGIN disabled, START_LOCATION set

### Dependencies Verified
- [x] `world/namebank.py` - Has FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES
- [x] `typeclasses/characters.py` - Has grit, resonance, intellect, motorics AttributeProperties
- [x] `typeclasses/characters.py` - Has sex AttributeProperty
- [x] `typeclasses/characters.py` - Has death_count AttributeProperty

---

## ⚠️ Critical Settings Changes

### Before Testing, Verify:

**1. AUTO_PUPPET_ON_LOGIN = False** ✅ (Fixed)
- **Why**: Prevents auto-puppeting before character creation menu runs
- **Location**: `server/conf/settings.py` line 79
- **Status**: Changed from `True` to `False`

**2. START_LOCATION = "#2"** ✅ (Added)
- **Why**: Default spawn location for new characters
- **Location**: `server/conf/settings.py` line 82
- **Status**: Added (defaults to Limbo)

**3. MULTISESSION_MODE = 1** ✅ (Already set)
- **Why**: Account-based login with character selection
- **Location**: `server/conf/settings.py` line 75

**4. AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False** ✅ (Already set)
- **Why**: We handle character creation custom
- **Location**: `server/conf/settings.py` line 78

---

## 🧪 Testing Prerequisites

### Before First Test Run:

1. **Server Restart Required** ⚠️
   ```bash
   evennia reload
   # or
   evennia restart
   ```
   - Settings changes require server restart
   - New command module needs to be loaded

2. **Check Splattercast Channel Exists**
   ```python
   # In-game:
   @py from evennia.comms.models import ChannelDB; ChannelDB.objects.get_channel("Splattercast")
   ```
   - Character creation system logs to Splattercast
   - Death system logs to Splattercast

3. **Verify Limbo (#2) Exists**
   ```python
   # In-game:
   @py from evennia import search_object; print(search_object("#2"))
   ```
   - START_LOCATION points to #2
   - Fallback location if custom room not set

4. **Test Account with No Characters**
   - Need a fresh account OR
   - Archive all existing characters for test account
   ```python
   # Archive all characters for account:
   @py self.account.characters.all().update(db_archived=True)
   ```

---

## 🎯 Test Scenarios

### Test 1: First Character Creation Flow
**Objective**: Verify first-time character creation works

**Steps**:
1. Log in with account that has no characters
2. Should immediately see character creation menu
3. Enter first name (test validation: too short, too long, special chars)
4. Enter last name (test uniqueness check)
5. Select sex (male/female/androgynous)
6. Distribute GRIM points:
   - Try `grit 100`
   - Try `resonance 50`
   - Try `reset`
   - Try `done` before reaching 300 (should fail)
   - Distribute to 300 total
   - Try `done` (should succeed)
7. Confirm character creation
8. Should spawn in START_LOCATION with welcome message

**Expected Results**:
- ✅ Character created with correct name
- ✅ GRIM stats match distribution (total 300)
- ✅ Sex correctly set
- ✅ Character spawned in correct location
- ✅ clone_generation = 1
- ✅ archived = False
- ✅ Stack ID created

**Validation Commands**:
```python
@stats
@examine me
```

---

### Test 2: Death and Respawn Flow
**Objective**: Verify death → character creation → respawn works

**Steps**:
1. Have a character (from Test 1 or create manually)
2. Set custom desc/longdesc for testing inheritance:
   ```
   @desc me = A weathered clone with tired eyes.
   @longdesc/head This clone's face shows signs of previous trauma.
   ```
3. Kill the character (use admin command or medical system)
4. Wait 6 minutes for death progression to complete
5. Should see unpuppet message in Splattercast
6. Should see character creation menu with 3 templates + flash clone
7. Note the 3 template names and GRIM distributions
8. Select option 4 (flash clone)
9. Should see name incremented (e.g., "John Doe" → "John Doe II")
10. Should spawn with inherited stats

**Expected Results**:
- ✅ Old character unpuppeted
- ✅ Old character archived with reason="death"
- ✅ 3 random templates shown with 300 GRIM each
- ✅ Flash clone shows old character name and stats
- ✅ New character has incremented Roman numeral
- ✅ New character inherits: GRIM, desc, longdesc, sex
- ✅ clone_generation incremented
- ✅ death_count incremented
- ✅ Same Stack ID preserved
- ✅ previous_clone_dbref points to old character

**Validation Commands**:
```python
@stats
@examine me
@py print(f"Generation: {self.db.clone_generation}, Deaths: {self.db.death_count}")
@py print(f"Stack ID: {self.db.stack_id}")
@py print(f"Previous: {self.db.previous_clone_dbref}")
```

---

### Test 3: Template Selection
**Objective**: Verify template selection works

**Steps**:
1. Kill character again (or use test account)
2. In respawn menu, select option 1 (first template)
3. Note the template's name and GRIM stats
4. Select sex
5. Confirm creation
6. Check character stats match template

**Expected Results**:
- ✅ Character created with template name
- ✅ GRIM stats match template exactly
- ✅ Sex correctly set
- ✅ clone_generation = 1 (new identity)
- ✅ No Stack ID from previous character

---

### Test 4: Name Validation
**Objective**: Verify name validation works

**In first character creation:**
1. Try names too short: "A" → should reject
2. Try names too long: "A" * 31 → should reject
3. Try special characters: "John@Doe" → should reject
4. Try numbers: "John123" → should reject
5. Try existing name: (name of another character) → should reject
6. Try profanity: "Fuck Smith" → should reject
7. Try valid name: "John Doe" → should accept

---

### Test 5: GRIM Distribution Validation
**Objective**: Verify GRIM validation works

**In first character creation:**
1. Try `grit 0` → should reject (min 1)
2. Try `grit 151` → should reject (max 150)
3. Try `grit 100`, `resonance 100`, `intellect 100`, `motorics 100` → total 400, `done` should reject
4. Try `grit 1`, `resonance 1`, `intellect 1`, `motorics 297` → total 300, `done` should accept

---

### Test 6: Re-login After Character Creation
**Objective**: Verify at_post_login handles existing characters

**Steps**:
1. Have a character created
2. Quit game (`@quit`)
3. Log back in
4. Should auto-puppet last character (no menu)

**Expected Results**:
- ✅ No character creation menu
- ✅ Automatically puppeted into last character
- ✅ Character state preserved

---

### Test 7: Multiple Deaths (Roman Numeral Incrementation)
**Objective**: Verify Roman numerals increment correctly

**Steps**:
1. Create character "Test Subject"
2. Kill and flash clone → "Test Subject II"
3. Kill and flash clone → "Test Subject III"
4. Kill and flash clone → "Test Subject IV"
5. Continue to test higher numerals

**Expected Roman Numerals**:
- I → II → III → IV → V
- IX → X → XI
- XIX → XX → XXI

---

## 🐛 Known Issues to Watch For

### Potential Bugs:
1. **EvMenu not exiting properly** - Menu might stay open after character creation
2. **Session lost during creation** - Disconnect during menu might orphan character
3. **Template generation extremes** - Random templates might be unbalanced
4. **Roman numeral parsing** - Edge cases with existing numerals
5. **Duplicate name race condition** - Two accounts creating same name simultaneously

### Debug Commands:
```python
# Check active handlers
@py from evennia.scripts.models import ScriptDB; print(ScriptDB.objects.filter(db_key="combat_handler_script"))

# Check character state
@py print(f"Archived: {self.db.archived}, Death count: {self.db.death_count}")

# Check account characters
@py print(self.account.characters.all())

# Force character creation menu
@py from commands.charcreate import start_character_creation; start_character_creation(self.account, is_respawn=False)

# Archive current character
@py self.db.archived = True

# Check Stack ID
@py print(self.db.stack_id)
```

---

## ✅ Testing Complete Checklist

- [ ] Test 1: First Character Creation Flow
- [ ] Test 2: Death and Respawn Flow  
- [ ] Test 3: Template Selection
- [ ] Test 4: Name Validation
- [ ] Test 5: GRIM Distribution Validation
- [ ] Test 6: Re-login After Character Creation
- [ ] Test 7: Multiple Deaths (Roman Numerals)

---

## 🚀 Ready to Test?

**Final Checklist Before Testing:**
1. [ ] Server restarted with new code
2. [ ] Splattercast channel exists
3. [ ] Test account has no non-archived characters
4. [ ] Limbo (#2) exists and is accessible
5. [ ] Ready to monitor Splattercast for debug output

**If all checked, you're ready to test!** 🎉
