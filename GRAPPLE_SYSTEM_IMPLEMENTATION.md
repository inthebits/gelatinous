# Nuanced Grapple System Implementation

## Overview
I have successfully implemented the robust, nuanced grapple system as per your design specifications. The system now cleanly manages yielding states, restraint vs. violent modes, and automatic behavior for both grapplers and victims.

## Key Features Implemented

### 1. Auto-Yielding on Grapple Establishment
- **Location**: `world/combat/grappling.py` - `establish_grapple()` function
- **Behavior**: When a grapple is established:
  - Both grappler and victim automatically start in yielding/restraint mode
  - Victim receives message: "You are being grappled and automatically yield (restraint mode)"
  - This creates the default "restraint" behavior you specified

### 2. Yielding State Management with `stop attacking`
- **Location**: `commands/combat/core_actions.py` - `CmdStop` class
- **Behavior**: 
  - `stop attacking` sets `is_yielding = True`
  - Different messages for regular combat vs. being grappled
  - Works for both grapplers and victims

### 3. Resume Attacking with Violence Switch
- **Location**: `commands/combat/core_actions.py` - `CmdAttack` class  
- **Behavior**: When someone attacks while yielding:
  - Automatically sets `is_yielding = False`
  - **Important**: Grappled victims CANNOT attack their grappler - they must use `escape`
  - Special message when grappled: "You cannot attack [grappler] while they are grappling you! Use 'escape' to resist violently."
  - General message otherwise: "You steel yourself and resume actively attacking"

### 4. Grappler Restraint vs. Violent Mode
- **Location**: `world/combat/handler.py` - combat turn processing
- **Behavior**:
  - **Yielding grappler (restraint mode)**: Maintains gentle hold, no attacks
    - Message: "You maintain a restraining hold on [victim] without violence"
  - **Non-yielding grappler (violent mode)**: Can attack normally while grappling
  - Grapplers can switch modes with `kill`/`stop attacking`

### 5. Victim Auto-Escape vs. Yielding (Fight for Your Life!)
- **Location**: `world/combat/handler.py` - grapple victim processing
- **Behavior**:
  - **Yielding victim**: No automatic escape attempts, accepts restraint
    - Message: "You remain still in [grappler]'s hold, not resisting"
  - **Non-yielding victim**: Automatically attempts escape each turn
    - **Critical**: Successful auto-escapes switch victim to violent mode (fighting for life)
    - Message on success: "Your successful escape fills you with fighting spirit - you're now actively resisting!"
    - Uses existing escape mechanics with opposed rolls

### 6. Manual Escape Command Enhancement (Proper Violence Switch)
- **Location**: `commands/combat/special_actions.py` - `CmdEscapeGrapple`
- **Behavior**:
  - **This is how grappled victims switch to violent resistance**
  - When someone manually uses `escape`, they automatically stop yielding
  - Message: "You fight desperately for your life against [grappler]'s hold!"
  - Uses proper escape mechanics with message phases

### 7. Combat Ending When All Yielding
- **Location**: `world/combat/handler.py` - `at_repeat()` method
- **Behavior**: 
  - Already implemented: Combat ends peacefully when all participants are yielding
  - Perfect for restraint scenarios where nobody wants to fight

### 8. Proper Message Phases
- **Location**: `world/combat/messages/grapple.py`
- **Behavior**: 
  - Uses correct phases: `hit`, `miss`, `escape_hit`, `escape_miss`, `release`
  - Rich variety of messages for all grapple states and transitions
  - Supports different message types for violent vs. restraint actions

## Code Structure Improvements

### Constants Added
```python
MSG_RESUME_ATTACKING = "|rYou steel yourself and resume actively attacking (no longer yielding).|n"
MSG_GRAPPLE_AUTO_YIELD = "|yYou are being grappled and automatically yield (restraint mode). Use 'escape' to resist violently.|n"
MSG_GRAPPLE_VIOLENT_SWITCH = "|rYou switch to violent resistance against {grappler}!|n"
MSG_GRAPPLE_ESCAPE_VIOLENT_SWITCH = "|rYou fight desperately for your life against {grappler}'s hold!|n"
MSG_GRAPPLE_AUTO_ESCAPE_VIOLENT = "|rYour successful escape fills you with fighting spirit - you're now actively resisting!|n"
MSG_GRAPPLE_RESTRAINT_HOLD = "|gYou maintain a restraining hold on {victim} (non-violent).|n"
MSG_GRAPPLE_VIOLENT_HOLD = "|rYou tighten your grip on {victim} violently!|n"
```

### Enhanced Logic Flow (Fight for Your Life!)
1. **Grapple Initiated** → Both parties auto-yield (restraint mode)
2. **Grappler can**: 
   - `stop attacking` → Gentle restraint hold only
   - `kill`/`attack` → Switch to violent mode, can damage victim
3. **Victim can**:
   - `stop attacking` → Accept restraint peacefully  
   - `escape` → **PROPER WAY** to switch to violent resistance
   - **CANNOT** use `attack [grappler]` while grappled (physically impossible)
4. **Auto-behavior** (Fight for Your Life):
   - Yielding victims don't auto-escape
   - Non-yielding victims auto-escape each turn
   - **Successful auto-escapes switch victims to violent mode** (fighting for life)
   - Yielding grapplers just maintain hold
   - Non-yielding grapplers can attack

## User Experience

### Restraint Scenario (Default)
1. Alice grapples Bob → Both auto-yield
2. Alice maintains gentle restraining hold each turn
3. Bob doesn't struggle, accepts restraint
4. Combat continues peacefully until someone acts or both yield completely

### Violent Grapple Scenario  
1. Alice grapples Bob → Both auto-yield initially
2. Alice uses `kill` → Switches to violent mode, can damage Bob
3. Bob uses `escape` → Switches to violent resistance (proper way for victims)
4. Combat becomes violent with attacks and escape attempts
5. If Bob successfully auto-escapes, he becomes violent (fighting for his life)

### Clean Resolution
1. Both parties use `stop attacking` → Combat ends peacefully
2. Natural end when both are yielding

## Testing Scenarios

The system should now handle these scenarios flawlessly:

1. **Restraint Hold**: Grappler yields, victim yields → Peaceful restraint
2. **Violent Grapple**: Either party attacks → Full combat grapple
3. **Mixed States**: One yielding, one not → Asymmetric behavior
4. **State Transitions**: Clean switching between restraint/violent modes
5. **Combat Ending**: Automatic peaceful resolution when appropriate

## Benefits Achieved

✅ **Cleaned up spaghetti code** - Centralized yielding logic  
✅ **Intuitive commands** - `stop attacking` and `kill`/`attack` for mode switching  
✅ **Nuanced grappling** - Restraint vs. violent modes  
✅ **Auto-yielding** - Sensible defaults for grapple initiation  
✅ **Proper escape mechanics** - Respects yielding states  
✅ **Rich messaging** - Clear feedback for all states and transitions  
✅ **Combat flow** - Peaceful ending when appropriate  

The grapple system is now robust, intuitive, and ready for the future medical/fatigue/bodyshield expansions you mentioned.
