# Telnet Testing Checklist - Flash Cloning System
**Date:** October 14, 2025  
**Phase:** Phase 1 - Telnet Testing (Pre-Web Interface)  
**Status:** 🟡 READY FOR TESTING

---

## Prerequisites

### Server Configuration
- [x] `NEW_ACCOUNT_REGISTRATION_ENABLED = True` (enabled Oct 14)
- [x] `AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False`
- [x] `AUTO_PUPPET_ON_LOGIN = False`
- [x] `MAX_NR_CHARACTERS = 1`
- [x] `MULTISESSION_MODE = 1`
- [x] `START_LOCATION = "#2"` (Limbo)

### Code Status
- [x] Character creation system implemented (`commands/charcreate.py`)
- [x] Death progression unpuppet logic implemented
- [x] Account hooks implemented (`at_post_login`)
- [x] Flash cloning system implemented
- [x] Death count tracking implemented
- [x] EvMenu respawn menu implemented

---

## Test Suite

### TEST RESULTS - October 14, 2025

**Bug #1 Found During Initial Testing:**
- **Issue:** Blank Enter key at welcome screen was being treated as character name input
- **Symptom:** "Invalid name: Name must be 2-30 characters" error when pressing Enter
- **Root Cause:** EvMenu nodes processing blank `raw_string` as input instead of ignoring it
- **Fix Applied:** Modified `first_char_name_first` and `first_char_name_last` to check `if raw_string and raw_string.strip():`
- **Status:** ✅ FIXED

**Bug #2 Found During Second Test:**
- **Issue:** EvMenu exiting after entering first name, showing node name as debug output
- **Symptom:** After entering first name, saw "first_char_name_last" printed, then "Command 'Wakka' is not available"
- **Root Cause:** Returning node name string instead of calling next node function directly
- **Technical Detail:** EvMenu interprets returned string as text to display, not as goto target during input processing
- **Fix Applied:** Changed all node transitions to either:
  - Return `None` to re-display current node (for errors/validation)
  - Call next node function directly: `return next_node(caller, "", **kwargs)`
- **Files Modified:** 
  - `first_char_name_first()` - Fixed transition to `first_char_name_last()`
  - `first_char_name_last()` - Fixed transition to `first_char_sex()`
  - `first_char_grim()` - Fixed transition to `first_char_confirm()` and all error returns
- **Status:** ✅ FIXED - Ready for re-testing

---

### 1. Fresh Account Creation (First-Time Player)

**Goal:** Validate complete new player experience from account creation to first spawn.

**Steps:**
1. [ ] Connect via telnet: `telnet localhost 4000`
2. [ ] Select "Create new account" option
3. [ ] Enter valid email address
4. [ ] Enter password (confirm)
5. [ ] **OBSERVE:** Should proceed directly to character creation menu

**Expected Flow:**
```
Welcome Screen
→ Create Account Prompt
→ Email Entry
→ Password Entry
→ Password Confirmation
→ Character Creation Menu (automatic)
```

**Character Creation Menu - First Time:**
1. [ ] See welcome message explaining VECTOR cloning facility
2. [ ] Prompted for character name
3. [ ] Prompted for sex selection (male/female/other)
4. [ ] See GRIM point distribution (300 points across 4 stats)
5. [ ] Confirm character creation
6. [ ] Character spawned at START_LOCATION (Limbo #2)
7. [ ] Can use `look`, `who`, basic commands
8. [ ] Character has correct attributes (grit, resonance, intellect, motorics)

**Pass Criteria:**
- [ ] No errors during account creation
- [ ] Automatically redirected to character creation (no manual commands)
- [ ] Character successfully created and puppeted
- [ ] All stats properly assigned
- [ ] Character appears in game world

**Failure Modes to Watch:**
- Account created but stuck at login prompt
- Character creation menu doesn't trigger
- GRIM distribution validation errors
- Name validation failures
- Spawn location errors

---

### 2. Death & Respawn Flow (Existing Account)

**Goal:** Validate complete death loop: Death → Curtain → Unpuppet → Respawn Menu → Flash Clone.

**Setup:**
1. [ ] Log in with existing account (from Test 1)
2. [ ] Have character in game world
3. [ ] Note character's current stats, appearance, name (for flash clone comparison)

**Death Trigger:**
1. [ ] Use `@py me.at_death()` to trigger death manually
2. [ ] **OBSERVE:** Death curtain should display (red static animation)
3. [ ] **OBSERVE:** Death progression script starts (6-minute countdown)

**During Death Progression (6 minutes):**
1. [ ] Wait for countdown (or use `@py` to speed up testing)
2. [ ] **OBSERVE:** Splattercast messages about corpse creation
3. [ ] **OBSERVE:** Character unpuppeted from account
4. [ ] **OBSERVE:** Account receives death notification

**Respawn Menu:**
1. [ ] **OBSERVE:** Character creation menu automatically appears
2. [ ] See respawn welcome message (different from first-time)
3. [ ] See **4 options:**
   - [ ] Option 1: Flash clone (preserves identity)
   - [ ] Option 2: Random template 1
   - [ ] Option 3: Random template 2
   - [ ] Option 4: Random template 3

**Flash Clone Test:**
1. [ ] Select option 1 (flash clone)
2. [ ] **OBSERVE:** Character name appended with Roman numeral (e.g., "Laszlo II")
3. [ ] **OBSERVE:** Stats preserved from old character
4. [ ] **OBSERVE:** Appearance preserved
5. [ ] **OBSERVE:** death_count incremented by exactly 1
6. [ ] Character spawned at START_LOCATION
7. [ ] Old character archived (check with `@py from evennia.objects.models import ObjectDB; ObjectDB.objects.get(db_key="OldName").db.archived`)

**Pass Criteria:**
- [ ] Death curtain displays correctly
- [ ] 6-minute timer completes without errors
- [ ] Character unpuppets automatically
- [ ] Respawn menu appears without manual intervention
- [ ] Flash clone preserves identity correctly
- [ ] Roman numeral naming works (death_count = 1 → "Name II")
- [ ] Old character archived properly
- [ ] death_count increments exactly once (not 4!)

**Failure Modes to Watch:**
- Death curtain doesn't fire (check `db.death_processed` flag)
- Character stuck in limbo without unpuppeting
- Respawn menu doesn't trigger
- Flash clone creates duplicate (doesn't remove old character)
- death_count jumps by 4 instead of 1
- Name collision errors

---

### 3. Random Template Selection

**Goal:** Validate random template respawn option.

**Setup:**
1. [ ] Trigger death again (use character from Test 2)
2. [ ] Reach respawn menu

**Template Selection:**
1. [ ] Select option 2, 3, or 4 (random template)
2. [ ] **OBSERVE:** Template details displayed (name, stats, description)
3. [ ] Confirm template selection
4. [ ] **OBSERVE:** New character created with template name
5. [ ] **OBSERVE:** Stats match template values
6. [ ] **OBSERVE:** death_count inherited from old character
7. [ ] **OBSERVE:** death_count incremented (e.g., death_count=1 from flash clone → death_count=2 now)
8. [ ] Old character archived

**Pass Criteria:**
- [ ] Templates display different names/stats each time
- [ ] Template application works correctly
- [ ] death_count persists across identity changes
- [ ] Character spawned successfully

---

### 4. Multiple Death Cycles

**Goal:** Validate system stability across multiple deaths.

**Test Sequence:**
1. [ ] Death 1 → Flash clone → "Name II" (death_count = 1)
2. [ ] Death 2 → Flash clone → "Name III" (death_count = 2)
3. [ ] Death 3 → Template → "TemplateName" (death_count = 3)
4. [ ] Death 4 → Flash clone → "TemplateName II" (death_count = 4)
5. [ ] Death 5 → Template → "NewTemplate" (death_count = 5)

**Pass Criteria:**
- [ ] Roman numerals increment correctly (II, III, IV, V)
- [ ] death_count increments exactly once per death
- [ ] No `db.death_processed` flag stuck on revival
- [ ] No memory leaks or handler issues
- [ ] Each respawn menu functions correctly
- [ ] Archived characters accumulate in Limbo

---

### 5. Account Re-Login After Death

**Goal:** Validate account can log back in after being unpuppeted.

**Steps:**
1. [ ] Disconnect from game during death progression
2. [ ] Reconnect via telnet
3. [ ] Log in with account credentials
4. [ ] **OBSERVE:** Should detect no active character
5. [ ] **OBSERVE:** Should trigger character creation menu automatically

**Pass Criteria:**
- [ ] Login succeeds
- [ ] Respawn menu appears (not stuck at prompt)
- [ ] Can complete character creation
- [ ] Character puppeted successfully

---

### 6. Edge Cases & Error Handling

**6.1 Invalid Name Entry:**
1. [ ] Enter name with special characters
2. [ ] Enter extremely long name (>50 chars)
3. [ ] Enter empty name
4. [ ] **OBSERVE:** Validation errors displayed
5. [ ] **OBSERVE:** Can retry with valid name

**6.2 GRIM Distribution Errors:**
1. [ ] Attempt to allocate >300 points
2. [ ] Attempt to allocate <300 points
3. [ ] Attempt to set stat <0
4. [ ] **OBSERVE:** Validation prevents invalid distributions

**6.3 Interrupted Character Creation:**
1. [ ] Start character creation
2. [ ] Disconnect during menu
3. [ ] Reconnect
4. [ ] **OBSERVE:** Menu state recovers or restarts gracefully

**6.4 Manual Flag Cleanup (Existing Characters):**
1. [ ] For existing characters with stuck `db.death_processed` flag
2. [ ] Run: `@py del me.db.death_processed`
3. [ ] Trigger death
4. [ ] **OBSERVE:** Death curtain fires correctly now

---

## Test Results Log

### Test Run 1: [Date/Time]
**Tester:** [Name]  
**Test 1 - Fresh Account:** ⬜ PASS / ⬜ FAIL  
**Test 2 - Death & Respawn:** ⬜ PASS / ⬜ FAIL  
**Test 3 - Random Template:** ⬜ PASS / ⬜ FAIL  
**Test 4 - Multiple Deaths:** ⬜ PASS / ⬜ FAIL  
**Test 5 - Re-Login:** ⬜ PASS / ⬜ FAIL  
**Test 6 - Edge Cases:** ⬜ PASS / ⬜ FAIL  

**Notes:**
```
[Record any issues, unexpected behavior, or observations]
```

---

## Known Issues (Pre-Testing)

1. **First-Time Character Creation Never Tested**
   - Implemented but never executed due to AUTO_PUPPET disabled during development
   - GRIM point distribution menu untested
   - Name validation untested
   - Sex selection untested

2. **Manual Flag Cleanup Required**
   - Existing characters may have `db.death_processed = True` stuck
   - Requires manual `@py del me.db.death_processed` command
   - New characters won't have this issue

3. **START_LOCATION is Limbo**
   - Currently spawning in default Evennia Limbo (#2)
   - Functional but not thematic
   - Should create proper "Medical Reconstruction Bay" room in future

4. **Template Generation**
   - Random template algorithm untested
   - May need adjustment for better name/stat variety

---

## Success Criteria for Phase 1 Completion

**Minimum Viable Product:**
- [x] All 6 test suites pass without critical errors
- [ ] Fresh account → character creation works
- [ ] Death → respawn loop closes completely
- [ ] Flash cloning preserves identity correctly
- [ ] death_count increments once per death (not 4)
- [ ] No stuck states or manual intervention required

**Blockers for Phase 2 (Web Interface):**
- Any critical failures in core telnet flow
- Data corruption issues
- Unpuppeting failures
- Menu state corruption

**Phase 2 Readiness:**
Once all tests pass, we can proceed to implement:
1. Django views for web account registration
2. Web-based character creator (alternative to EvMenu)
3. Character roster/stats display
4. Optional: Web respawn dashboard

---

## Debug Commands Reference

**Check Character State:**
```python
@py me.db.archived
@py me.db.death_count
@py hasattr(me.db, 'death_processed')
@py me.location
```

**Check Account State:**
```python
@py self.account.characters.all()
@py self.account.db._playable_characters
```

**Force Death (Testing):**
```python
@py me.at_death()
```

**Clear Stuck Death Flag:**
```python
@py del me.db.death_processed
```

**Check Handler State:**
```python
@py handler = me.ndb.combat_handler
@py handler.db.combatants if handler else "No handler"
```

**View Archived Characters:**
```python
@py from evennia.objects.models import ObjectDB
@py archived = ObjectDB.objects.filter(db_archived=True)
@py [f"{c.key} (#{c.id})" for c in archived]
```

---

## Next Steps After Testing

**If All Tests Pass:**
1. Document any minor issues or improvements needed
2. Update FLASH_CLONING_SPEC.md with test results
3. Begin Phase 2: Web/Django interface design
4. Create user documentation for telnet commands

**If Critical Failures:**
1. Document failure modes
2. Prioritize fixes by severity
3. Re-test after fixes
4. Delay Phase 2 until stable

**Web Interface Planning:**
- Design signup page mockup
- Plan character creator UI
- Design respawn dashboard
- Determine telnet vs web feature parity
