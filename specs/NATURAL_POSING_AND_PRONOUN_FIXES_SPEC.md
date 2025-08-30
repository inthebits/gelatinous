# Pronoun System Integration Specification

## Overview

This specification outlines the integration of Evennia's built-in `$pron()` system into our existing codebase to replace hardcoded pronouns with dynamic, gender-aware alternatives. This will improve inclusivity, grammatical correctness, and maintainability.

## Important: `$pron()` System Limitations

**Key Discovery**: After implementation testing, we learned that `$pron()` functions have specific limitations:

### Where `$pron()` Works
- **msg_contents() calls** - when sending messages to multiple recipients
- **Runtime messaging** - emotes, combat messages, social actions
- **Actor-stance descriptions** - where different players see different text

### Where `$pron()` Does NOT Work
- **Prototype definitions** - `$pron()` is not available in prototype `attrs`
- **Static item descriptions** - stored `desc` attributes
- **AttributeProperty values** - any stored attribute values

### Available Functions by Context
```python
# Available in prototypes (limited set):
from evennia.utils.funcparser import FUNCPARSER_CALLABLES
from evennia.utils.funcparser import SEARCHING_CALLABLES
# Examples: $eval, $toint, $random, $clr, $search, $protkey

# Available in msg_contents() (full set):
from evennia.utils.funcparser import ACTOR_STANCE_CALLABLES  
# Examples: $pron, $You, $conj - requires caller/receiver context

# $pron() requires special kwargs:
parser.parse(string, caller=<obj>, receiver=<obj>, mapping={'key': <obj>, ...})
```

### Correct Implementation Patterns
```python
# CORRECT: Use $pron() in runtime messaging
def send_emote_message(self, actor, message):
    # This works - runtime messaging with proper context
    actor.location.msg_contents(
        f"$You() $conj(lean) against the wall, $pron(your) eyes scanning the area.",
        from_obj=actor
    )

# INCORRECT: Use $pron() in prototypes
CLOTHING_ITEM = {
    "worn_desc": "A jacket that clings to $pron(their) frame",  # This fails!
}

# CORRECT: Use static descriptions in prototypes
CLOTHING_ITEM = {
    "worn_desc": "A jacket that clings to their frame",  # Static "their" works
}
```

## ### Future Considerations

### Emote System Integration

#### Emote Command Design
The `$pron()` system provides perfect integration for a natural first-person pose system. Players write in first person, and the system automatically converts perspectives:

**Primary Pose Command:**
```python
class CmdPose(Command):
    """
    Express actions and dialogue in natural first-person format.
    
    Usage:
        .<action>
        .say "<dialogue>"
        .<action>, "<dialogue>" I .<action>
        
    Write naturally in first person - the system handles perspective conversion.
    
    Examples:
        .lean back and gaze off into the horizon
        .lean back, "It's going to be a hell of a day." I remark
        .scratch my head thoughtfully  
        .draw my sword and salute
        .whisper to bob, "Meet me later."
    """
```

**First-Person to Multi-Perspective Conversion:**
```python
# Player types: .lean back and gaze off into the horizon, "It's going to be a hell of a day." I remark

# You see: "You lean back and gaze off into the horizon, "It's going to be a hell of a day." you remark."
# Others see: "Alice leans back and gazes off into the horizon, "It's going to be a hell of a day." she remarks."
```

**Natural Dialogue Integration:**
- Quoted text remains unchanged for all perspectives
- Actions get converted through `$pron()` system
- Mixed action/dialogue flows naturally

#### Pre-built Emote Templates (Action-Format Style)
```python
EMOTE_TEMPLATES = {
    # Solo emotes (no target required)
    "nod": "%N %<nods> thoughtfully.",
    "shrug": "%N %<shrugs> %p shoulders.", 
    "laugh": "%N %<laughs> heartily.",
    "sigh": "%N %<lets> out a deep sigh.",
    "smile": "%N %<smiles> warmly.",
    "frown": "%N %<frowns> deeply.",
    "stretch": "%N %<stretches> and %<yawns>.",
    "yawn": "%N %<yawns> loudly.",
    
    # Social interaction emotes (require target)
    "pat": "%N %<pats> %d gently on the shoulder.",
    "hug": "%N %<hugs> %d warmly.",
    "wave": "%N %<waves> at %d.",
    "bow": "%N %<bows> respectfully to %d.",
    "salute": "%N %<salutes> %d crisply.",
    "glare": "%N %<glares> at %d menacingly.",
    "wink": "%N %<winks> at %d playfully.",
    
    # Object interaction emotes  
    "lean": "%N %<leans> against %p %t.",
    "examine": "%N %<examines> %p %t carefully.",
    "polish": "%N %<polishes> %p %t with care.",
    "hand": "%N %<hands> %p %t to %d.",
    "show": "%N %<shows> %p %t to %d.",
    "offer": "%N %<offers> %p %t to %d.",
}

# Usage Examples with action-format perspective:
# @emote nod 
#   You: "You nod thoughtfully."
#   Others: "Alice nods thoughtfully."

# @emote/to bob pat
#   You: "You pat Bob gently on the shoulder."
#   Bob: "Alice pats you gently on the shoulder." 
#   Others: "Alice pats Bob gently on the shoulder."

# @emote/to charlie hand sword
#   You: "You hand your sword to Charlie."
#   Charlie: "Alice hands her sword to you."
#   Others: "Alice hands her sword to Charlie."
```

#### First-Person Pose Parser
```python
class FirstPersonParser:
    """Converts first-person poses to multi-perspective using $pron() system"""
    
    def parse_pose(self, pose_text, actor):
        """
        Convert first-person pose to $pron() format
        
        Args:
            pose_text: "lean back and gaze off, "Hello!" I remark"
            actor: Character performing the pose
            
        Returns:
            String with $pron() substitutions for perspective handling
        """
        # Examples of conversion:
        # "I lean back" → "$pron(I) lean back"
        # "my sword" → "$pron(my) sword"  
        # "I draw my sword" → "$pron(I) draw $pron(my) sword"
        
        return self.convert_first_person_to_pron(pose_text)
    
    def convert_first_person_to_pron(self, text):
        """Convert first-person pronouns to $pron() equivalents"""
        conversions = {
            r'\bI\b': '$pron(I)',           # "I" → "$pron(I)"  
            r'\bme\b': '$pron(me)',         # "me" → "$pron(me)"
            r'\bmy\b': '$pron(my)',         # "my" → "$pron(my)"
            r'\bmine\b': '$pron(mine)',     # "mine" → "$pron(mine)"
            r'\bmyself\b': '$pron(myself)', # "myself" → "$pron(myself)"
        }
        
        # Apply regex substitutions while preserving quoted dialogue
        return self.apply_conversions_preserve_quotes(text, conversions)
```

#### Command Implementation
```python
class CmdPose(Command):
    """
    Natural first-person posing with automatic perspective conversion
    
    Usage:
        .<action>
        
    Examples:
        .lean back against the wall
        .scratch my head and frown
        .draw my sword, "En garde!" I shout
        .whisper softly, "The plan is ready."
    """
    
    key = "."
    locks = "cmd:all()"
    help_category = "Social"
    
    def func(self):
        if not self.args:
            self.caller.msg("Pose what?")
            return
            
        # Parse first-person pose into $pron() format
        parser = FirstPersonParser()
        converted_pose = parser.parse_pose(self.args.strip(), self.caller)
        
        # Send message to room with perspective handling
        self.caller.location.msg_contents(
            converted_pose,
            from_obj=self.caller
        )
```

#### Natural Pose Examples
```python
# Player Input → System Processing → Final Output

# Example 1: Simple action
".lean back and gaze off into the horizon"
# You see: "You lean back and gaze off into the horizon."
# Others see: "Alice leans back and gazes off into the horizon."

# Example 2: Action with dialogue  
'.lean back, "It\'s going to be a hell of a day." I remark'
# You see: 'You lean back, "It\'s going to be a hell of a day." you remark.'
# Others see: 'Alice leans back, "It\'s going to be a hell of a day." she remarks.'

# Example 3: Complex action sequence
".draw my sword and salute, then I sheathe it again"
# You see: "You draw your sword and salute, then you sheathe it again."
# Others see: "Alice draws her sword and salutes, then she sheathes it again."

# Example 4: Possessive interactions
".scratch my head and adjust my coat"
# You see: "You scratch your head and adjust your coat."  
# Others see: "Bob scratches his head and adjusts his coat." (male character)
# Others see: "Sam scratches their head and adjusts their coat." (nonbinary character)
```

#### Verb Conjugation Handling
```python
# The system needs to handle verb conjugation automatically:
# "I lean" → "you lean" (to actor) / "Alice leans" (to others)
# "I gaze" → "you gaze" (to actor) / "Alice gazes" (to others)  
# "I remark" → "you remark" (to actor) / "Alice remarks" (to others)

# Integration with Evennia's $conj() system:
class VerbConjugator:
    """Handle automatic verb conjugation in poses"""
    
    def conjugate_pose(self, pose_with_pron):
        """
        Convert verbs to work with $pron() perspectives
        
        "I draw" → "$pron(I) $conj(draw)"
        "I lean" → "$pron(I) $conj(lean)"  
        "I remark" → "$pron(I) $conj(remark)"
        """
        # This requires parsing sentence structure to identify verbs
        # and applying $conj() appropriately
        return pose_with_pron
```

#### Social Targeting Integration
```python
# For directed poses, we can extend the system:

# Directed pose with target
".whisper to bob, \"The plan is ready.\""
# You see: "You whisper to Bob, \"The plan is ready.\""
# Bob sees: "Alice whispers to you, \"The plan is ready.\""  
# Others see: "Alice whispers to Bob, \"The plan is ready.\""

# The parser would need to detect target references:
class TargetedPoseParser(FirstPersonParser):
    """Handle poses with explicit targets"""
    
    def parse_targeted_pose(self, pose_text, actor):
        """
        Detect and handle targeted actions like "whisper to bob"
        Convert to appropriate $pron() format with target awareness
        """
        # Detect patterns like "to <name>" or "at <name>"
        # Convert to $pron() with target context
        pass
```

#### Integration with Existing Systems
The pose system integrates seamlessly with our existing features:

```python
# Combat integration - poses during combat
".draw my sword and enter a defensive stance"
# Integrates with combat system, shows weapon state

# Clothing integration - poses referencing worn items  
".adjust my hoodie and roll up my sleeves"
# References clothing items, respects style states

# Inventory integration - poses with held items
".polish my sword while I wait"
# References wielded/held items naturally
```

#### Implementation Architecture
```python
class EmoteParser:
    """Handles MOO-style + action-format substitutions with Evennia integration"""
    
    def parse_emote(self, emote_string, actor, targets=None, objects=None):
        """
        Parse emote string with substitutions and perspective handling
        
        Args:
            emote_string: Raw emote with %substitutions and %<verbs>
            actor: Character performing emote
            targets: List of target characters (for /to emotes)  
            objects: Dict of object substitutions
            
        Returns:
            Dict of messages for different audiences with proper perspective
        """
        # Phase 1: Replace %substitutions with $pron() equivalents
        substituted = self.substitute_placeholders(emote_string, actor, targets, objects)
        
        # Phase 2: Handle verb conjugation with $conj()
        conjugated = self.conjugate_verbs(substituted, actor)
        
        # Phase 3: Generate perspective-specific messages
        return self.generate_perspectives(conjugated, actor, targets)
    
    def generate_perspectives(self, message, actor, targets):
        """
        Generate different message versions for actor, targets, and observers
        Uses Evennia's FuncParser viewpoint system
        """
        return {
            'actor_msg': message,    # $pron() automatically shows "you" to actor
            'target_msg': message,   # $pron() shows target as "you", actor as name
            'room_msg': message      # $pron() shows all names to observers
        }

    def conjugate_verbs(self, text, actor):
        """Convert %<verb> patterns to $conj(verb) for Evennia"""
        import re
        verb_pattern = r'%<(\w+)>'
        return re.sub(verb_pattern, r'$conj(\1)', text)
```

#### Advanced Emote Features with Action-Format
```python
class CmdEmote(Command):
    """
    Enhanced emote system with action-format support
    
    Usage:
        emote <freeform text>           # Freeform emoting
        emote <template> [object]       # Template-based emoting  
        emote/to <target> <template>    # Directed template emoting
        emote/at <target> <freeform>    # Directed freeform emoting
        
    Templates use action-format substitutions:
        wiggle, pat, hand, show, point, nod, shrug, etc.
        
    Advanced substitutions:
        %N = your name, %<verb> = conjugated verb, %d = direct object
        %p = possessive, %s = subject pronoun, %o = object pronoun
        
    Examples:
        emote nods thoughtfully         # Template: "%N %<nods> thoughtfully."
        emote/to bob pat                # Template: "%N %<pats> %d on shoulder."
        emote scratches %p head         # Freeform with substitution
        emote/at alice %N %<waves> at %d # Freeform directed emote
    """
    
    def func(self):
        # Parse command for template vs freeform
        # Handle /to and /at switches for targeting
        # Process through EmoteParser
        # Send appropriate messages to all audiences
        pass
```

#### Character Placement Integration
Our existing `@look_place` and `@temp_place` commands can adopt the same first-person approach:

**Current:**
```
@look_place sitting on a rock
# Others see: "Alice is sitting on a rock"
```

**With First-Person + $pron() Enhancement:**
```
@look_place I am sitting on a rock, my eyes scanning the horizon  
# Others see: "Alice is sitting on a rock, her eyes scanning the horizon"

@temp_place I am crouched behind my shield
# Others see: "Bob is crouched behind his shield"
```

#### Advantages of This Natural Approach

**1. Intuitive Writing**: Players write exactly how they think - "I do this"
**2. Powerful Backend**: Leverages Evennia's `$pron()` for automatic perspective conversion
**3. Dialogue Integration**: Natural mixing of actions and speech  
**4. System Integration**: Works seamlessly with combat, clothing, inventory systems
**5. Minimal Learning Curve**: Just type what your character does, system handles the rest

#### Advanced Emote Features
1. **Pose System**: Persistent character stances with pronoun awareness
2. **Mood System**: Emotional states that modify emote displays
3. **Social Memory**: Remember how characters typically interact
4. **Cultural Emotes**: Location or faction-specific social actions

### Potential Enhancementsrent State Analysis

### Hardcoded Pronouns Found
- **Combat Messages**: `their`, `they`, `them` in weapon attack descriptions
- **Clothing Descriptions**: Generic pronouns in atmospheric descriptions
- **Character System**: `sex` attribute not connected to pronoun system
- **Future Risk**: Any new content may continue hardcoding patterns

### Technical Debt
1. All combat message files use `"their rifle"` instead of `"$pron(their) rifle"`
2. Clothing descriptions assume neutral pronouns
3. No standardized pronoun usage guidelines for developers
4. Character gender/sex not integrated with Evennia's pronoun system

## Goals

### Primary Objectives
1. **Fix Existing `$pron()` Integration Gaps**: Replace hardcoded pronouns in combat messages, clothing descriptions, and other systems
2. **Implement Natural First-Person Posing**: Create intuitive `.` command for natural roleplay
3. **Establish Pronoun Foundation**: Set up character gender system and `@gender` command
4. **Consistency**: Standardized pronoun handling across all game systems

### Secondary Benefits  
- Improved immersion through personalized messaging
- Foundation for future identity/disguise systems
- Reduced development overhead for pronoun management
- Better integration with Evennia's messaging framework

## Technical Specification

### Character System Integration

#### Phase 1: Character Gender Property
```python
# typeclasses/characters.py
class Character(DefaultCharacter):
    sex = AttributeProperty("ambiguous")  # Existing attribute
    
    @property
    def gender(self):
        """Convert sex attribute to gender for Evennia's pronoun system."""
        gender_mapping = {
            "male": "male",
            "female": "female", 
            "ambiguous": "plural",  # they/them pronouns
            "neutral": "neutral",   # it/its pronouns (rarely used)
            "nonbinary": "plural",  # they/them pronouns
        }
        return gender_mapping.get(self.sex, "plural")
```

#### Phase 2: Player Commands
```python
# commands/CmdCharacter.py  
class CmdGender(Command):
    """
    Set your character's gender/pronouns
    
    Usage:
      @gender <male|female|nonbinary|ambiguous>
      @pronouns <male|female|nonbinary|ambiguous>
      
    Sets your character's pronouns for how others see your actions.
    - male: he/him/his
    - female: she/her/hers  
    - nonbinary/ambiguous: they/them/their
    """
```

### Message Format Standards

#### Combat Messages
**Before:**
```python
"victim_msg": "{attacker_name} loads their weapon with practiced efficiency."
```

**After (Correct Usage):**
```python  
"victim_msg": "$You(attacker) $conj(load, attacker) $pron(their, attacker) weapon with practiced efficiency."
```

**Note**: Combat messages are sent via `msg_contents()` which supports `$pron()` system.

#### Clothing Descriptions (Static Approach)
**Current Implementation (Correct):**
```python
"worn_desc": "Battle-tested jeans that show their urban scars"
```

**Why Not `$pron()`**: Clothing descriptions are stored in prototypes where `$pron()` is not available. The static "their" approach works well for atmospheric descriptions.

#### Emote System (Dynamic Approach)
**Implementation Target:**
```python
# Player input: .lean back against the wall
# Processed message with $pron() for perspective:
msg = "$You() $conj(lean) back against the wall, $pron(your) eyes scanning the area."
actor.location.msg_contents(msg, from_obj=actor)
```

#### General Messaging
**Standard Pattern:**
- `$pron(I)` → "I" (to actor) / "he/she/they" (to others)
- `$pron(me)` → "me" (to actor) / "him/her/them" (to others)
- `$pron(my)` → "my" (to actor) / "his/her/their" (to others)
- `$pron(mine)` → "mine" (to actor) / "his/hers/theirs" (to others)
- `$pron(myself)` → "myself" (to actor) / "himself/herself/themselves" (to others)

### Implementation Phases

#### Phase 1: Character System Foundation
**Priority: High**
**Estimated Time: 2-3 hours**

**Tasks:**
1. Add `gender` property to Character class
2. Create `@gender` command for players
3. Update character creation to set default pronouns
4. Test pronoun resolution in simple messages

**Files Modified:**
- `typeclasses/characters.py`
- `commands/CmdCharacter.py` 
- `commands/default_cmdsets.py`

**Acceptance Criteria:**
- Players can set their pronouns with `@gender` command
- `Character.gender` property returns correct values
- Simple `$pron()` usage works in `say` command

#### Phase 2: Combat Message Retrofit
**Priority: High**  
**Estimated Time: 4-6 hours**

**Tasks:**
1. Update combat message files to use `$pron()` in `msg_contents()` calls
2. Ensure proper context (caller/receiver) is provided to combat messages
3. Test combat messages with different character genders
4. Verify message clarity and grammatical correctness
5. Update combat message format documentation

**Files Modified:**
- Combat message sending functions (not the message data files)
- Combat message format specification

**Acceptance Criteria:**
- All combat messages sent via `msg_contents()` can use `$pron()` system
- Messages display correctly for all supported genders
- No grammatical errors or awkward phrasing

**Note**: Focus on the message sending mechanism, not the stored message strings.

#### Phase 3: Static Description Consistency
**Priority: Medium**
**Estimated Time: 1-2 hours**

**Tasks:**
1. Audit existing static descriptions (clothing, items, rooms) for pronoun consistency
2. Standardize on "their" for atmospheric descriptions where perspective isn't needed
3. Document static vs. dynamic description approach
4. Update style guide for future content creation

**Files Modified:**
- `world/prototypes.py` (review existing descriptions)
- Style guide documentation

**Acceptance Criteria:**
- Consistent pronoun usage in static descriptions
- Clear guidelines for when to use static vs. dynamic pronouns
- All existing descriptions reviewed and standardized

**Note**: This phase accepts that static descriptions use "their" and focuses on consistency rather than `$pron()` conversion.

#### Phase 4: Natural First-Person Posing System  
**Priority: High**
**Estimated Time: 6-8 hours**

**Tasks:**
1. Create natural `.` pose command with first-person input parsing
2. Implement first-person to `$pron()` conversion system
3. Integrate with character placement commands (@look_place, @temp_place)
4. Add emote templates that work with `$pron()` system
5. Test comprehensive pose system with various character genders

**Files Modified:**
- `commands/CmdSocial.py` (new pose system)
- `commands/CmdCharacter.py` (placement command updates)
- `commands/default_cmdsets.py`

**Acceptance Criteria:**
- Natural `.lean back against the wall` syntax works
- First-person input automatically converts to proper `$pron()` format
- Character placement descriptions use appropriate pronouns
- Players can write intuitively while system handles perspective
- All gender pronouns display correctly for all participants

#### Phase 5: Developer Guidelines
**Priority: Medium**
**Estimated Time: 2 hours**

**Tasks:**
1. Create pronoun usage guidelines document
2. Add pronoun examples to development standards
3. Update contribution guidelines
4. Create testing checklist for new content

**Files Created:**
- `docs/PRONOUN_USAGE_GUIDELINES.md`
- Updates to `DEVELOPMENT_GUIDE.md`

#### Phase 5: Developer Guidelines
**Priority: Medium**
**Estimated Time: 2 hours**

**Tasks:**
1. Create pronoun usage guidelines document
2. Add pronoun examples to development standards
3. Update contribution guidelines
4. Create testing checklist for new content

**Files Created:**
- `docs/PRONOUN_USAGE_GUIDELINES.md`
- Updates to `DEVELOPMENT_GUIDE.md`

#### Phase 6: Comprehensive Audit
**Priority: Low**
**Estimated Time: 3-4 hours**

**Tasks:**
1. Search entire codebase for hardcoded pronouns
2. Update any remaining instances
3. Add pronoun validation to code review process
4. Create automated tests for pronoun consistency

## Testing Strategy

### Unit Tests
```python
class TestPronounSystem(BaseEvenniaTest):
    def test_character_gender_property(self):
        """Test gender property returns correct values"""
        
    def test_pronoun_resolution_male(self):
        """Test $pron() with male characters"""
        
    def test_pronoun_resolution_female(self):
        """Test $pron() with female characters"""
        
    def test_pronoun_resolution_nonbinary(self):
        """Test $pron() with nonbinary characters"""
```

### Integration Tests
- Combat messages with mixed-gender participants
- Clothing descriptions on characters of various genders
- Multi-character scenarios (group combat, social interactions)
- Emote system integration with character pronouns
- Character placement and social positioning

### Manual Testing Checklist
- [ ] Create characters with different genders
- [ ] Test all combat weapon types
- [ ] Test all clothing style combinations
- [ ] Test emote system with various character genders
- [ ] Test character placement (@look_place, @temp_place) with pronouns
- [ ] Verify messages to self vs. others
- [ ] Check edge cases (no gender set, invalid values)

## Developer Guidelines

### New Content Standards
1. **Always use `$pron()` for character references**
2. **Never hardcode he/she/they pronouns**
3. **Test content with multiple character genders**
4. **Follow established pronoun patterns**

### Code Review Checklist
- [ ] No hardcoded pronouns (search for: he, she, they, their, his, her, him, them)
- [ ] Proper `$pron()` usage and syntax
- [ ] Messages tested with different genders
- [ ] Grammatically correct for all pronoun types

### Common Patterns
```python
# Actor-focused messages (character doing something)
"$pron(I) swing $pron(my) sword at the target"

# Observer messages (watching someone else)  
"{actor_name} swings $pron(their, actor) sword at the target"

# Victim messages (something happening to you)
"{actor_name} swings $pron(their, actor) sword at $pron(you)"
```

## Migration Strategy

### Rollout Plan
1. **Week 1**: Phase 1 - Character system foundation
2. **Week 2**: Phase 2 - Combat message system (enable `$pron()` in messaging)
3. **Week 3**: Phase 3 - Static description consistency audit
4. **Week 4**: Phase 4 - Natural first-person posing system implementation
5. **Week 5**: Phase 5 - Guidelines and comprehensive audit

### Focus Areas
**Primary Focus**: Implement natural first-person posing with proper `$pron()` integration
**Secondary Focus**: Enable `$pron()` in combat messaging system where appropriate
**Foundation**: Establish proper character gender system and static description standards

### Backwards Compatibility
- Existing characters with `sex` attribute will automatically work
- Default gender remains "ambiguous" (they/them) for inclusivity
- No breaking changes to existing save data

### Risk Mitigation
- Phase-by-phase implementation reduces integration risks
- Comprehensive testing at each phase
- Rollback plan: revert specific files if issues arise
- Player communication about new pronoun options

## Success Metrics

### Technical Metrics
- [ ] Character gender system connects existing `sex` attribute to Evennia's pronoun system
- [ ] Natural first-person posing system implemented with `.` command
- [ ] Combat messaging system properly supports `$pron()` where applicable  
- [ ] Static descriptions consistently use appropriate neutral pronouns
- [ ] Zero inappropriate `$pron()` usage in prototypes or static content
- [ ] Foundation ready for future identity/disguise systems

### Player Experience Metrics
- [ ] Players can successfully set their preferred pronouns with `@gender`
- [ ] Natural posing with `.lean back` syntax works intuitively
- [ ] Combat and social messages display grammatically correct pronouns
- [ ] Posing system works seamlessly across all gender identities
- [ ] No player reports of incorrect pronoun usage
- [ ] Smooth foundation for future roleplay enhancement systems

## Future Considerations

### Potential Enhancements
1. **Custom Pronouns**: Allow players to set custom pronoun sets
2. **Multiple Characters**: Different pronouns per character for same account
3. **NPC Genders**: Assign genders to NPCs for consistent messaging
4. **Localization**: Support for non-English pronoun systems

### Integration Opportunities
1. **Natural First-Person Posing**: Core `.` command system for intuitive roleplay (PRIMARY FOCUS)
2. **Combat Message Enhancement**: Enable `$pron()` in combat messaging where contextually appropriate
3. **Static Description Standards**: Consistent neutral pronoun usage in prototypes and stored descriptions  
4. **Character Placement Enhancement**: Integrate posing with @look_place/@temp_place using `$pron()` system
5. **Identity System Foundation**: Prepare gender system for future disguise mechanics
6. **Admin Tools**: Admin commands that reference players by pronoun (using `$pron()` in messages)

## Implementation Notes

### Evennia-Specific Considerations
- `$pron()` requires FuncParser-enabled strings (most game messages)
- Gender detection looks for `.gender` property on referenced objects
- Case sensitivity: `$Pron()` for capitalization, `$pron()` for lowercase
- Performance: Minimal overhead, resolved at message send time

### Edge Cases to Handle
- Characters without gender set (fallback to "plural")
- Messages with multiple character references
- Complex grammatical constructions
- Non-standard message formats

---

**Document Version**: 1.0  
**Author**: Development Team  
**Date**: August 30, 2025  
**Status**: Draft - Pending Review
