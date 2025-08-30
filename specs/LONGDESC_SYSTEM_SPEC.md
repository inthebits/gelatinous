# Long Description System Specification

## Overview

The Long Description (longdesc) system provides players with the ability to set detailed descriptions for specific body parts/locations on their characters. These descriptions appear when other players### Privacy and Content

### Privacy Model
- **Self-modification only**: Players can only set longdescs on their own characters
- **Public visibility**: Longdescs visible to all players via look command
- **Admin moderation**: Staff can modify any character's longdescs for content moderation
- **No consent system**: Players responsible for their own descriptions
- **Optional participation**: Players not required to set longdescs

### Administrative Access
- **Staff override capability**: Admins can use all longdesc commands on any character
- **Same command interface**: Staff use standard commands with character targeting
- **Content moderation**: Standard admin tools apply to longdesc content
- **No special staff commands**: Core commands work for both self and admin targetingt their character, creating rich, personalized character appearances.

## Core Principles

1. **Player Agency**: Players control their character's appearance descriptions
2. **Layered Architecture**: System designed to integrate with future clothing, equipment, and injury systems
3. **Visibility Control**: Only visible body parts show descriptions
4. **Future-Proof**: Foundation for clothing coverage, injuries, cybernetics, tattoos

## Body Location System

### Supported Locations
The system supports distinct body locations with left/right differentiation and extensibility for additional appendages:

#### Core Body Locations
- `head` - Overall head/skull area
- `face` - Facial features and expressions
- `left_eye` / `right_eye` - Individual eye descriptions for asymmetry
- `left_ear` / `right_ear` - Ear shape, piercings, modifications
- `neck` - Neck area, throat
- `chest` - Chest/torso front
- `back` - Back and shoulder blades
- `abdomen` - Stomach/belly area
- `groin` - Lower torso/hip area

#### Paired Appendages (Left/Right Support)
- `left_arm` / `right_arm` - Individual arm descriptions
- `left_hand` / `right_hand` - Hands, fingers, nails
- `left_thigh` / `right_thigh` - Upper leg descriptions
- `left_shin` / `right_shin` - Lower legs/calves
- `left_foot` / `right_foot` - Feet, toes, stance

#### Extensible Appendage System
The system is designed to support additional appendages beyond standard human anatomy:

- **Additional Arms**: `left_arm_2`, `right_arm_2`, `left_hand_2`, `right_hand_2`
- **Prehensile Tails**: `tail`, `tail_2` (for multiple tails)
- **Extra Legs**: `left_leg_3`, `right_leg_3`, `left_foot_3`, `right_foot_3`
- **Wings**: `left_wing`, `right_wing`
- **Tentacles**: `tentacle_1`, `tentacle_2`, etc.
- **Other**: Any anatomically relevant appendage following naming convention

### Location Constants
Body locations are defined as constants (similar to Mr. Hands system) to ensure:
- Consistent referencing across codebase
- Easy validation and error handling
- Support for non-standard anatomies
- Integration with future systems
- **Auto-creation of defaults** like Mr. Hands system
- **Centralized configuration** in constants file
- **High practical limits** with theoretical unlimited support
- **Anatomy source of truth** - foundation for all body-related systems

#### Constants Structure
Following the Mr. Hands pattern, body locations will be defined in `world/combat/constants.py`:

```python
# Default human anatomy (auto-created on character creation)
DEFAULT_LONGDESC_LOCATIONS = {
    "head": None, "face": None, "left_eye": None, "right_eye": None, 
    "left_ear": None, "right_ear": None, "neck": None,
    "chest": None, "back": None, "abdomen": None, "groin": None,
    "left_arm": None, "right_arm": None, "left_hand": None, "right_hand": None,
    "left_thigh": None, "right_thigh": None, "left_shin": None, "right_shin": None,
    "left_foot": None, "right_foot": None
}

# Practical limit for total body locations per character
MAX_LONGDESC_LOCATIONS = 50  # Very high, accommodates extensive modifications

# Individual description character limit
MAX_DESCRIPTION_LENGTH = 1000  # Generous limit, allows detailed descriptions

# Paragraph formatting thresholds
PARAGRAPH_BREAK_THRESHOLD = 400  # Characters before automatic paragraph break
REGION_BREAK_PRIORITY = True     # Prefer breaking between anatomical regions

# Valid location validation set (expandable)
VALID_LONGDESC_LOCATIONS = set(DEFAULT_LONGDESC_LOCATIONS.keys())
```

#### Anatomy Validation System
- **Character anatomy source of truth** - longdesc system serves as foundation for all body-related systems
- **Dynamic validation** - only locations present in character's anatomy dictionary are settable
- **Extensible validation** - supports any anatomy configuration (alien, cybernetic, etc.)
- **Error prevention** - prevents setting descriptions for non-existent body parts

## Command Interface

### Primary Command: `@longdesc`

**Syntax**: `@longdesc <location> "<description>"`

**Examples**:
```
@longdesc face "weathered features with high cheekbones"
@longdesc left_eye "a piercing blue eye with flecks of gold"
@longdesc right_eye "a cybernetic replacement with a red LED"
@longdesc left_hand "calloused hand with dirt under the fingernails"
@longdesc right_hand "a prosthetic metal hand with intricate engravings"
@longdesc chest "broad shoulders tapering to a narrow waist"
@longdesc tail "a long, serpentine tail ending in a barbed tip"
@longdesc left_wing "a massive feathered wing, midnight black"
```

### Command Behavior
- **Validation**: Location must be valid body location constant
- **Storage**: Description stored in character database
- **Replacement**: New description overwrites existing for that location
- **Removal**: Empty description removes longdesc for location
- **Feedback**: Confirmation of successful setting/removal
- **Self-targeting**: Players can only modify their own longdescs
- **Admin override**: Staff can use commands on third-party characters for moderation

### Command Variations
- `@longdesc <location>` - View current description for location
- `@longdesc/list` - List all available body locations for this character
- `@longdesc` - List all set longdescs for character (only shows non-None values)
- `@longdesc/clear <location>` - Remove description for location (set to None)
- `@longdesc/clear` - Remove all longdescs (reset to defaults with confirmation)

#### Staff Commands (Admin Override)
- `@longdesc <character> <location> "<description>"` - Set longdesc on another character
- `@longdesc/clear <character> <location>` - Clear specific location on another character
- `@longdesc/clear <character>` - Clear all longdescs on another character (with confirmation)

## Integration with Look System

### Character Appearance Display
When a player executes `look <character>`, the system displays:

1. **Base Description**: Character's main description (from Character.db.desc)
2. **Line Break**: Visual separation between base description and longdescs
3. **Visible Longdescs**: All longdescs for uncovered body parts (head-to-toe anatomical order)
4. **Equipment/Clothing**: Future integration point
5. **Status Effects**: Future integration point (injuries, modifications)

#### Smart Paragraph Formatting
- **Automatic line breaks**: System adds paragraph breaks when combined longdescs exceed character threshold
- **Readable flow**: Prevents wall-of-text appearance for verbose descriptions
- **Threshold-based**: Configurable character count triggers paragraph separation
- **Anatomical grouping**: Line breaks respect anatomical regions when possible

#### Display Order (Anatomical Head-to-Toe)
1. **Head region**: head, face, left_eye, right_eye, left_ear, right_ear, neck
2. **Torso region**: chest, back, abdomen, groin  
3. **Arm region**: left_arm, right_arm, left_hand, right_hand
4. **Leg region**: left_thigh, right_thigh, left_shin, right_shin, left_foot, right_foot
5. **Extended appendages**: tail, wings, tentacles (in order of creation/numbering)

#### Paragraph Break Logic
- **Character counting**: System tracks cumulative character count as it builds description
- **Smart breaking**: When threshold reached, insert paragraph break before next anatomical region
- **Region respect**: Avoid breaking within anatomical regions when possible
- **Overflow handling**: If single region exceeds threshold, break at most logical location within region
- **Coverage integration**: Only visible descriptions (body longdescs + clothing longdescs) count toward thresholds
- **Writer freedom**: No forced connecting words or narrative structure - writers control their own style

### Visibility Rules
- **Default**: All body locations are visible
- **Future Coverage**: Clothing/equipment will hide covered locations
- **Unset Locations**: No description shown (invisible)
- **Override System**: Equipment/injuries can override or supplement longdescs

## Data Storage

### Character Database Structure
Following the Mr. Hands AttributeProperty pattern:

```python
# Auto-created on character creation (like Mr. Hands)
character.db.longdesc = {
    "head": None, "face": "weathered features with high cheekbones", 
    "left_eye": "a piercing blue eye with flecks of gold", "right_eye": "a cybernetic replacement with a red LED",
    "left_ear": None, "right_ear": None, "neck": None,
    "chest": "broad shoulders tapering to a narrow waist", 
    "back": None, "abdomen": None, "groin": None,
    "left_arm": None, "right_arm": None,
    "left_hand": "calloused hand with dirt under the fingernails",
    "right_hand": "a prosthetic metal hand with intricate engravings",
    "left_thigh": None, "right_thigh": None,
    "left_shin": None, "right_shin": None,
    "left_foot": None, "right_foot": None,
    # Extended anatomy (when added)
    "tail": "a long, serpentine tail ending in a barbed tip",
    "left_wing": "a massive feathered wing, midnight black"
}
```

#### Implementation Pattern
```python
# In Character typeclass (following Mr. Hands pattern)
longdesc = AttributeProperty(
    DEFAULT_LONGDESC_LOCATIONS.copy(),
    category="appearance", 
    autocreate=True
)
```

### Storage Principles
- **AttributeProperty Pattern**: Following Mr. Hands system architecture
- **Auto-Creation**: All default locations created with None values on character creation
- **Dictionary Format**: Easy lookup and modification
- **None as Unset**: Only locations with string values are "set" (None = invisible)
- **Persistent Storage**: AttributeProperty handles automatic database persistence
- **Unicode Support**: Full character set support for descriptions

## Layered System Architecture

### Current Layer: Base Longdescs
- Player-set descriptions stored in database
- Direct display when location is visible
- Manual setting via @longdesc command

### Future Layer Integration Points

#### Clothing/Equipment Coverage
- Items define coverage areas: `coverage = ["chest", "arms"]`
- **Coverage uses same location constants** as longdesc system for consistency
- **Covered longdescs hidden** - base body descriptions not shown when covered
- **Clothing longdescs displayed** - clothing items have their own appearance descriptions
- **Coverage longdescs count toward paragraph thresholds** - clothing descriptions participate in formatting
- Transparent/partial coverage rules
- Layered clothing system support

#### Custom Fitting System (Future)
- **Tailor fitting command** for custom clothing adjusted to unique anatomies
- **Adaptive coverage** - clothing automatically maps to available body locations
- **Custom measurements** - items fitted to specific character's appendage configuration
- **Coverage validation** - ensures clothing coverage matches character's anatomy

#### Injury/Medical System
- Injuries override or supplement base descriptions
- Temporary modifications (bandages, casts)
- Permanent modifications (scars, prosthetics)
- Medical condition visibility

#### Cybernetic/Modification System
- Cybernetic implants as location overrides
- Tattoo system integration
- Body modification descriptions
- Enhancement visibility rules

#### Equipment Integration
- Worn equipment affects appearance
- Weapon/tool integration
- Armor and protection display
- Magical item effects

## Technical Implementation Notes

### Validation System
- **Location validation against character's actual anatomy** (anatomy source of truth)
- **Description length limits (1000 characters max per location)**
- **Paragraph formatting validation (400 character break threshold)**
- Content filtering capabilities
- Input sanitization
- **Anatomical order preservation** for display consistency
- **Dynamic anatomy checking** - only allow longdescs for locations character actually possesses

### Performance Considerations
- Efficient dictionary lookups
- **Minimal database queries** (AttributeProperty handles persistence)
- **No caching needed** (Evennia's scale makes real-time assembly efficient)
- Lazy loading of complex descriptions
- **Direct database access** for optimal performance

### Error Handling
- Invalid location handling
- Database storage failures
- Malformed input protection
- Graceful degradation

## Privacy and Content

### Privacy Model
- **No Consent System**: Players responsible for their own descriptions
- **No Censorship**: Player agency in description content
- **Optional Participation**: Players not required to set longdescs
- **Admin Override**: Standard admin moderation capabilities

### Content Guidelines
- Player responsibility for appropriate content
- Standard server rules apply
- Admin tools for content moderation
- Appeal/modification processes

## Future Expansion

### Planned Integrations
1. **Clothing System**: Coverage-based visibility using shared location constants
2. **Equipment System**: Worn item integration
3. **Injury System**: Medical condition display
4. **Modification System**: Cybernetics, tattoos, piercings
5. **Pronoun System**: Dynamic pronoun integration (separate feature)
6. **Tailor System**: Custom fitting commands for unique anatomies

### Architectural Considerations
- **Modular Design**: Each layer independent
- **Plugin Architecture**: Easy system addition/removal
- **Configuration Options**: Server-specific customization
- **API Consistency**: Uniform interface across systems

## Testing Requirements

### Unit Tests
- Command parsing and validation
- Database storage and retrieval
- Location constant validation
- Error condition handling

### Integration Tests
- Look command integration
- Character appearance assembly
- Multi-layer description building
- Performance under load

### User Acceptance Tests
- Player workflow validation
- Description setting/viewing
- Integration with existing systems
- Error message clarity

## Migration Strategy

### Initial Implementation
1. Body location constants definition
2. @longdesc command implementation
3. Character appearance integration
4. Basic testing and validation

### Development Migration
- **No automatic migration needed** - system is additive to existing descriptions
- **Existing Character.db.desc preserved** - appears before longdescs with line break
- **Clean development environment** - new system doesn't affect existing characters
- **Gradual adoption** - players can adopt longdescs at their own pace

### Incremental Enhancement
1. Clothing coverage integration
2. Equipment system integration
3. Injury/modification systems
4. Advanced features and optimizations

## Success Criteria

### Functional Requirements
- Players can set/view/modify longdescs
- Descriptions appear in character appearance
- System integrates with existing look command
- Validation prevents invalid inputs

### Quality Requirements
- Performance impact minimal
- Error handling comprehensive
- User interface intuitive
- Code maintainable and extensible

### Integration Requirements
- Compatible with existing character system
- Ready for clothing/equipment integration
- Supports future medical/injury systems
- Maintains game balance and immersion
