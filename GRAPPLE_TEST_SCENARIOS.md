# Grapple System Test Scenarios

## Core Mechanics Testing

### 1. Basic Restraint Mode (Default Behavior)
```
Alice: grapple Bob
Expected: Both Alice and Bob auto-yield, restraint mode messages
Alice turn: Maintains gentle hold, no attacks
Bob turn: Doesn't struggle, accepts restraint
Result: Peaceful ongoing restraint
```

### 2. Grappler Goes Violent
```
Alice: grapple Bob (both yielding)
Alice: kill (switches to violent mode)
Alice turn: Can now attack Bob while grappling
Bob turn: Still yielding, doesn't struggle
Expected: Alice damages Bob, Bob accepts violence
```

### 3. Victim Switches to Violent Resistance
```
Alice: grapple Bob (both yielding)
Bob: escape (switches to violent resistance)
Bob turn: Actively attempts escape with messages
Expected: "You fight desperately for your life against Alice's hold!"
```

### 4. Auto-Escape Creates Fighting Spirit
```
Alice: grapple Bob (both yielding)
Bob: escape (now violent)
Combat turn: Bob automatically attempts escape
If Bob succeeds: "Your successful escape fills you with fighting spirit - you're now actively resisting!"
Expected: Bob is no longer yielding after successful auto-escape
```

### 5. Invalid Attack Prevention
```
Alice: grapple Bob
Bob: attack Alice (while grappled)
Expected: "You cannot attack Alice while they are grappling you! Use 'escape' to resist violently."
```

### 6. Peaceful Resolution
```
Alice: grapple Bob (both yielding)
Both remain yielding for several rounds
Expected: Combat eventually ends with "The confrontation ends peacefully as all participants stand down."
```

## Edge Cases Testing

### 7. Death During Grapple
```
Alice: grapple Bob (violent mode)
Alice: kill Bob until death
Expected: Grapple automatically cleared, Alice no longer grappling anyone
```

### 8. Release Mechanics
```
Alice: grapple Bob (yielding)
Alice: release
Expected: Uses "release" message phase, both maintain yielding state
---
Alice: grapple Bob, Alice goes violent
Alice: release  
Expected: Bob becomes non-yielding (defensive after violent grapple)
```

### 9. Multiple Combat Participants
```
Alice: grapple Bob
Charlie: attack Alice (while Alice is grappling)
Expected: Alice can be targeted by others while grappling
```

### 10. Room Changes/Dragging
```
Alice: grapple Bob (yielding)
Alice: north (drag attempt)
Expected: Existing drag mechanics should work with new yielding states
```

## Message Verification

### Key Messages to Verify:
- ✅ Auto-yield on grapple: "You are being grappled and automatically yield (restraint mode). Use 'escape' to resist violently."
- ✅ Escape violent switch: "You fight desperately for your life against {grappler}'s hold!"
- ✅ Auto-escape success: "Your successful escape fills you with fighting spirit - you're now actively resisting!"
- ✅ Restraint hold: "You maintain a restraining hold on {victim} without violence."
- ✅ Attack prevention: "You cannot attack {grappler} while they are grappling you! Use 'escape' to resist violently."

## Stress Testing

### 11. Rapid State Changes
```
Alice: grapple Bob
Bob: escape (violent)
Alice: release
Alice: grapple Bob (should work again)
Bob: stop attacking (yield)
Alice: stop attacking (yield)
Expected: Clean state transitions, peaceful end
```

### 12. Combat Flow Integration
```
Alice: attack Bob (normal combat)
Alice: grapple Bob (mid-combat)
Expected: Smooth transition from normal combat to grapple mechanics
```

## Success Criteria

1. **Intuitive defaults**: Grapples start peaceful (restraint mode)
2. **Clear escalation**: Easy to switch to violent mode when desired  
3. **Realistic mechanics**: Victims can't attack while grappled, must escape
4. **Fighting spirit**: Successful escapes create determination (no longer yielding)
5. **Clean resolution**: Peaceful ending when both parties yield
6. **Proper cleanup**: Death, releases, and room changes handled correctly
7. **Rich messaging**: Clear feedback for all state transitions
8. **Edge case handling**: No broken states or infinite loops

## Notes for Testing

- Test with multiple weapon types during violent grapples
- Verify message phases are correctly used (hit, miss, escape_hit, escape_miss, release)
- Check that proximity system integration still works
- Ensure command availability (grapple should be available globally, escape only in combat)
- Test the "fuck around and find out" progression - peaceful → violent → consequences
