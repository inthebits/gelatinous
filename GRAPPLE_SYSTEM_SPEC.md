# G.R.I.M. Grappling System Specification

## Overview

The G.R.I.M. Grappling System is a comprehensive close-combat mechanism that emphasizes **restraint over violence** while providing tactical depth for complex combat scenarios. It integrates seamlessly with the proximity system, movement mechanics, and yielding philosophy to create dynamic, roleplay-focused grappling encounters.

## Design Philosophy

### 1. **Restraint-First Approach**
- **Default Intent**: Grappling begins as restraint, not violence
- **Escalation Control**: Violence requires explicit choice by participants
- **De-escalation Opportunities**: Multiple chances to avoid harm
- **Roleplay Priority**: Combat serves narrative, not mechanics

### 2. **Tactical Complexity**
- **Movement Integration**: Grappling affects and is affected by positioning
- **Multi-Character Dynamics**: Complex interactions between multiple grapplers
- **State Management**: Rich state system supporting various scenarios
- **Strategic Depth**: Advanced options for experienced players

### 3. **Mechanical Consistency**
- **Attribute-Based**: Uses core G.R.I.M. attributes (primarily Motorics)
- **Contest System**: Opposed rolls determine outcomes
- **State Validation**: Robust error checking and cleanup
- **Integration**: Seamless connection to combat, movement, and social systems

---

## Core Mechanics

### Grapple States

#### **Grappling Relationship States**
1. **Not Grappling**: Character has no grapple involvement
2. **Grappling Someone**: Character is holding/restraining another
3. **Being Grappled**: Character is held/restrained by another
4. **Mutual Grapple**: Two characters grappling each other (rare, contest-based)

#### **Grapple Intent States**
1. **Restraint Mode** (Default): Non-violent holding/control
2. **Violent Mode**: Active struggle with damage potential

#### **Participation States**
1. **Yielding**: Accepting restraint, no resistance
2. **Non-Yielding**: Active resistance, automatic escape attempts

### Primary Attributes
- **Motorics**: Primary attribute for grapple initiation, contests, and escape attempts
- **Grit**: Used for drag resistance during room traversal (physical endurance/willpower)
- **Resonance**: Tertiary for reading intent and de-escalation (future implementation)

---

## Grapple Initiation

### Command: `grapple <target>`

#### **Prerequisites**
- Must be in same room as target
- Target must be valid character
- Cannot grapple self
- Cannot grapple if already grappling someone
- Cannot grapple if being grappled by someone else

#### **Proximity Requirements**
- **Combat Initiation**: Grapple can initiate combat and establish proximity
- **Existing Combat**: Must be in melee proximity with target
- **Rush Mechanics**: Can "rush in" when initiating new combat

#### **Contest Resolution**
```
Grappler Roll: 1d[Motorics]
Defender Roll: 1d[Motorics]

Success: Grappler > Defender
Failure: Defender >= Grappler
```

*Note: All grapple initiation, takeover, and escape attempts use Motorics vs Motorics*

#### **Success Outcomes**
1. **Grapple Established**: Two-way relationship created
   - Grappler: `grappling_dbref` → Target
   - Target: `grappled_by_dbref` → Grappler
2. **State Changes**:
   - Grappler: Auto-yields (restraint intent)
   - Target: Remains non-yielding (auto-resistance)
3. **Proximity**: Both characters enter/maintain proximity
4. **Targeting**: Target auto-targets grappler for potential retaliation

#### **Failure Outcomes**
1. **No Relationship**: No grapple state changes
2. **Yielding Consequences**: 
   - If grappler initiated combat: Auto-yield
   - If defender was pulled into combat: Also auto-yield
3. **Messaging**: Failure messages with narrative context

---

## Grapple Contests (Takeover)

### Multi-Grapple Scenarios

#### **Scenario 1: Contest for Existing Victim**
- **Setup**: A grapples B, then C attempts to grapple B
- **Mechanism**: Contest between A and C for control of B
- **Resolution**: Winner gets B, loser gets nothing
- **Outcome**: B remains grappled by winner

#### **Scenario 2: Grappling an Active Grappler** ⚠️ **NEEDS IMPLEMENTATION**
- **Setup**: A grapples B, then C attempts to grapple A
- **Current Issue**: System blocks this as "A already grappling someone"
- **Needed Behavior**: Force A to release B, then C can grapple A
- **Sequence**: 
  1. C initiates grapple on A
  2. If successful, A releases B automatically
  3. C establishes grapple on A

### Contest Mechanics
```
Challenger Roll: 1d[Motorics]
Current Grappler Roll: 1d[Motorics]

Success: Challenger > Current Grappler → Takeover
Failure: Current Grappler >= Challenger → Maintains control
```

---

## Grapple Maintenance

### Automatic Resistance System

#### **Non-Yielding Victims**
- **Auto-Escape**: Attempt escape every combat round
- **Contest**: Victim Motorics vs Grappler Motorics
- **Success**: Break free, switch to violent mode, target grappler
- **Failure**: Remain grappled, continue struggling

#### **Yielding Victims**
- **No Auto-Escape**: Accept restraint peacefully
- **Manual Escape**: Can use `escape` command to switch to violent mode
- **Roleplay Focus**: Emphasis on negotiation and de-escalation

### Grapple Damage System

#### **Restraint Mode** (Default)
- **No Damage**: Pure control/positioning
- **Messaging**: Restraint-focused descriptions
- **Intent**: Subdue without harm

#### **Violent Mode** (Escalation)
- **Damage Potential**: Both parties can take/deal damage
- **Escalation Triggers**:
  - Victim uses `escape` command
  - Automatic escape success
  - External violence (attacks on grappling pair)
- **Damage Types**:
  - Grapple damage hits: Control damage during struggle
  - Grapple damage misses: Failed attempts to harm

---

## Movement Integration

### Current Implementation ✅

#### **Exit Traversal (Drag System)**
- **Conditions for Dragging**:
  - Grappler is yielding (restraint mode)
  - Grappler not targeted by others (except victim)
  - Victim fails resistance roll (Victim Grit vs Grappler Grit)
- **Successful Drag**:
  - Both characters move to new room
  - Combat state transfers to new handler
  - Grapple relationship preserved
- **Failed Resistance**:
  - Grapple broken automatically
  - Movement blocked

#### **Combat Movement Restrictions**
- **Being Grappled**: Blocks flee, retreat, advance, charge
- **Grappling Someone**: Charge auto-releases grapple if targeting others

### Needed Implementations ⚠️

#### **Advance While Grappling**
- **Current Gap**: No logic for grappler advancing while maintaining hold
- **Needed Behavior**: 
  - Allow advance to new target while holding victim
  - Drag victim along during advance
  - Victim inherits grappler's new proximity relationships
- **Restrictions**: Only if victim is yielding for room traversal

#### **Retreat While Grappling** 
- **Current Gap**: No grapple-specific retreat logic
- **Needed Behavior**:
  - Allow retreat while maintaining grapple
  - Drag victim back with grappler
  - Both maintain proximity after retreat
- **Consistency**: Both should remain in proximity post-retreat

#### **Proximity Inheritance** ⚠️ **CRITICAL IMPLEMENTATION**
- **Principle**: Victim inherits all of grappler's proximity relationships
- **Timing**: After successful movement (advance/retreat/charge)
- **Mechanism**: Copy grappler's proximity set to victim
- **Rationale**: Victim is "dragged along" and gains same positioning

---

## Special Actions

### Escape Grapple: `escape`

#### **Mechanics**
- **State Change**: Victim switches from yielding to non-yielding
- **Immediate Effect**: Violent mode engaged
- **Contest**: Handled on next combat round
- **Targeting**: Auto-target grappler for retaliation

#### **Outcomes**
- **Success**: Break free, remain in proximity, target grappler
- **Failure**: Remain grappled but now in violent mode

### Release Grapple: `release`

#### **Mechanics**
- **Voluntary Action**: Grappler chooses to let go
- **No Contest**: Automatic success
- **State Preservation**: Yielding states maintained
- **Proximity**: Both remain in proximity

#### **Strategic Use**
- **De-escalation**: Peaceful resolution option
- **Tactical**: Free up for other actions
- **Roleplay**: Character development opportunities

---

## State Management

### Database Fields

#### **Combat Entry Fields**
```python
{
    "char": Character object,
    "grappling_dbref": int or None,      # Who this character is grappling
    "grappled_by_dbref": int or None,    # Who is grappling this character
    "is_yielding": bool,                 # Yielding state
    "target_dbref": int or None,         # Combat target
    # ... other combat fields
}
```

#### **Validation Rules**
1. **Mutual Exclusivity**: Can't grapple multiple people
2. **Relationship Consistency**: Cross-references must match
3. **Combat Participation**: All grapple participants must be in combat
4. **Proximity Requirement**: Grappling requires proximity

### State Cleanup System

#### **Automatic Validation** (`validate_and_cleanup_grapple_state`)
- **Stale References**: Remove references to non-existent characters
- **Cross-Reference Validation**: Ensure bidirectional consistency
- **Combat State Sync**: Align with combat handler state
- **Self-Grapple Prevention**: Block impossible relationships

#### **Cleanup Triggers**
- Every combat round (proactive)
- Character removal from combat
- Handler shutdown
- Error conditions

---

## Integration Points

### Combat System Integration

#### **Handler Processing Order**
1. **Validation**: Check and clean grapple states
2. **Auto-Resistance**: Process non-yielding victim escapes
3. **Special Actions**: Handle grapple/escape/release commands
4. **Movement Actions**: Process advance/retreat/charge with grapple logic
5. **Standard Combat**: Regular attacks with grapple considerations

#### **Action Restrictions**
- **Being Grappled**: Limited to escape, talk, yielding actions
- **Grappling Someone**: Can advance/retreat (with victim), limited other actions
- **Attack Restrictions**: Can't attack your grappler while being grappled

### Proximity System Integration

#### **Establishment Rules**
- **Grapple Creation**: Always establishes proximity
- **Maintenance**: Grappling maintains proximity automatically
- **Release**: Proximity persists after grapple ends
- **Movement**: Proximity inherited during movement

#### **Movement Interactions**
- **Room Changes**: Drag system handles proximity transfer
- **Within Room**: Advance/retreat maintains grapple proximity
- **Multiple Targets**: Victim gains grappler's proximity to others

### Yielding System Integration

#### **State Relationships**
- **Default Grappler**: Auto-yields (restraint intent)
- **Default Victim**: Remains non-yielding (resistance mode)
- **Manual Override**: Both can change yielding state independently
- **Escalation**: Non-yielding victims auto-attempt escape

#### **Combat Mode Interactions**
- **Peaceful Mode**: Both yielding, no auto-resistance
- **Mixed Mode**: Yielding grappler, non-yielding victim
- **Violent Mode**: Neither yielding, active struggle

---

## Implementation Priorities

### High Priority ⚠️

1. **Multi-Grapple Chain Logic**: 
   - Fix scenario where C tries to grapple A (who is grappling B)
   - Implement forced release mechanism
   - Test edge cases thoroughly

2. **Proximity Inheritance**:
   - Implement victim proximity copying during grappler movement
   - Ensure consistency across advance/retreat/charge
   - Handle multi-character scenarios

3. **Advance While Grappling**:
   - Add grapple check to advance command
   - Implement victim dragging during advance
   - Maintain grapple state through movement

### Medium Priority

4. **Retreat Grapple Logic**:
   - Add grapple awareness to retreat command
   - Implement victim dragging during retreat
   - Ensure proximity maintenance

5. **Enhanced Contest System**:
   - Add modifiers for different situations
   - Implement fatigue mechanics for extended grapples
   - Add environmental factors

### Low Priority

6. **Advanced Grapple Moves**:
   - Submission attempts
   - Position-based modifiers
   - Team grappling mechanics

7. **Grapple Specialization**:
   - Character-specific grappling styles
   - Equipment modifiers
   - Training-based improvements

---

## Edge Cases and Considerations

### Multi-Character Scenarios

#### **Chain Grapples**
- **A→B→C**: Multiple dependency chains
- **Circular References**: Prevention and detection
- **Cascade Releases**: When one grapple affects others

#### **Team Grappling**
- **Multiple Grapplers**: Two people trying to grapple same target
- **Assistance**: Helping teammate with grapple
- **Interference**: Attacking grappling pairs

### Room Transition Edge Cases

#### **Handler Boundaries**
- **Cross-Handler Grapples**: When characters end up in different handlers
- **Handler Merging**: When grapple brings handlers together
- **Handler Cleanup**: When handlers shut down during grapples

#### **Movement Restrictions**
- **Yielding Requirements**: Room traversal requiring victim consent
- **Failed Drags**: What happens when drag fails
- **Escape During Movement**: Mid-transition escapes

### Error Recovery

#### **State Corruption**
- **Orphaned References**: Cleanup strategies
- **Inconsistent States**: Recovery mechanisms
- **Data Loss**: Graceful degradation

#### **System Failures**
- **Handler Crashes**: Grapple preservation
- **Network Issues**: State synchronization
- **Resource Limits**: Performance under load

---

## Testing Scenarios

### Basic Functionality
1. **Simple Grapple**: A grapples B successfully
2. **Grapple Failure**: A fails to grapple B
3. **Escape Success**: B escapes from A
4. **Escape Failure**: B fails to escape from A
5. **Voluntary Release**: A releases B voluntarily

### Contest Scenarios
6. **Grapple Contest**: A grapples B, C contests for B
7. **Chain Grapple**: A grapples B, C grapples A
8. **Multiple Contesters**: A grapples B, both C and D contest

### Movement Integration
9. **Room Drag Success**: A drags B to new room
10. **Room Drag Failure**: B resists A's drag attempt
11. **Advance While Grappling**: A advances to C while holding B
12. **Retreat While Grappling**: A retreats while holding B

### Edge Cases
13. **Handler Transitions**: Grapple across room boundaries
14. **Combat Initiation**: Grapple starting new combat
15. **State Corruption**: Recovery from invalid states
16. **Multi-Grapple Chains**: Complex relationship webs

---

## Conclusion

The G.R.I.M. Grappling System provides a sophisticated, roleplay-focused framework for close combat scenarios that emphasizes restraint while maintaining tactical depth. The system's integration with movement, proximity, and yielding mechanics creates a cohesive combat experience that serves narrative goals while providing meaningful strategic choices.

The specification identifies key implementation gaps that need addressing to complete the system's vision, particularly around proximity inheritance and multi-grapple scenarios. Once these elements are implemented, the grappling system will provide a robust foundation for complex, engaging combat encounters that prioritize character development and story progression.

## Implementation Roadmap

### Phase 1: Core Fixes (High Priority)
- Fix multi-grapple chain logic
- Implement proximity inheritance
- Add advance-while-grappling support

### Phase 2: Movement Integration (Medium Priority)  
- Complete retreat-while-grappling logic
- Enhance contest system
- Add environmental factors

### Phase 3: Advanced Features (Low Priority)
- Specialized grapple moves
- Character customization
- Performance optimization

This roadmap ensures the grappling system evolves systematically while maintaining backwards compatibility and system stability.
