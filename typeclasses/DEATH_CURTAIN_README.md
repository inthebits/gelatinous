# Death Curtain Animation System

## Overview

The `curtain_of_death.py` module provides an elegant "dripping blood" death animation for characters in the Evennia MUD. This system creates a sophisticated visual effect by centering a death message in a "sea" of characters and progressively removing characters to create a dripping effect.

## Design Philosophy

This animation system is based on a beautiful and subtle design:

1. **Message-Centered**: Places a meaningful death message at the center of the animation
2. **Progressive Decay**: Characters "drip away" from the message in a planned sequence
3. **Visual Poetry**: Creates a sense of fading consciousness and dissolving reality
4. **Flexible**: Works with any death message, making it reusable
5. **Elegant**: The effect is subtle and artistic, not overwhelming

## Features

### Visual Effects
- **Dripping Animation**: Characters progressively disappear from the message in a randomized sequence
- **Color Variation**: Uses Evennia's color system with red variations for blood-like effect
- **Dynamic Timing**: Animation starts fast and slows down over time for dramatic effect
- **Centered Layout**: Message is centered in a "sea" of block characters

### Technical Features
- **Evennia-Native**: Uses Evennia's built-in `delay()` function and color system
- **Message Flexibility**: Can animate any text message
- **Character Messaging**: Integrates with standard Evennia character messaging
- **Observer Support**: Provides different messages for dying character vs. room observers
- **Configurable**: Timing, colors, and characters can be easily adjusted

## Usage

### Basic Usage

```python
from typeclasses.curtain_of_death import show_death_curtain

# Use default death message
show_death_curtain(character)

# Use custom death message
show_death_curtain(character, "Your vision fades to black...")
```

### Integration with Character Death

```python
def at_death(self):
    from .curtain_of_death import show_death_curtain
    show_death_curtain(self)
```

### Testing with Various Messages

```
testdeathcurtain
testdeathcurtain You feel your strength ebbing away...
testdeathcurtain The darkness consumes you
testdeathcurtain A red haze blurs your vision as the world slips away...
```

## Implementation Details

### Core Algorithm

The animation works through these steps:

1. **Center the Message**: Place the death message in the center of a line filled with block characters (`▓`)
2. **Create Removal Plan**: Generate a randomized sequence for removing characters
3. **Progressive Removal**: Remove characters one by one according to the plan
4. **Color Enhancement**: Apply random red-spectrum colors to remaining characters
5. **Final Frame**: Show the complete message one last time

### Key Functions

**`curtain_of_death(text, width=None)`**: Core animation generator
- Creates the sequence of frames for the dripping effect
- Handles message centering and character removal planning
- Applies Evennia color codes

**`DeathCurtain`**: Animation controller class
- Manages timing and frame display
- Handles character messaging
- Provides observer notifications

**`show_death_curtain(character, message=None)`**: Convenience function
- Easy integration point for character death
- Supports custom messages

### Animation Characteristics

```python
# Default message
"A red haze blurs your vision as the world slips away..."

# Frame progression example:
"▓▓▓▓▓▓A red haze blurs your vision as the world slips away...▓▓▓▓▓▓"
"▓▓▓▓▓▓A red h ze blurs your vision as the world slips away...▓▓▓▓▓▓"
"▓▓▓▓▓▓A red h ze blur  your vision as the world slips away...▓▓▓▓▓▓"
"▓▓▓▓▓▓A red h ze blur  your vision as the world slip  away...▓▓▓▓▓▓"
# ... continues until message dissolves
```

## Configuration

### Timing Parameters

```python
self.frame_delay = 0.015        # Starting delay between frames
self.delay_multiplier = 1.01    # Acceleration factor (gets slower)
```

### Visual Parameters

```python
_get_terminal_width()           # Width of animation area (default 78)
sea_char = "▓"                  # Character surrounding the message
replacement_char = "█"          # Character used during dripping
```

### Color Customization

```python
colors = ["|r", "|R", "|y", "|Y"]  # Evennia color codes for effect
```

## Evennia Integration

### Color System Compatibility
- Uses Evennia's native color codes (`|r`, `|R`, `|y`, `|Y`, `|n`)
- Avoids conflicts with color parsing
- Properly terminates color sequences

### Messaging Patterns
- Standard `character.msg()` for dying character
- `location.msg_contents()` for observers
- Proper exclusion handling for room messaging

### Performance Considerations
- Pre-generates all frames for smooth playback
- Limits observer messages to reduce spam
- Uses efficient string operations

## Best Practices

### Message Design
- Keep messages under 60 characters for best visual effect
- Use evocative, atmospheric language
- Consider the pacing of the animation

### Integration Tips
- Test with various message lengths
- Consider context-specific death messages
- Integrate with existing death handling systems

### Performance Guidelines
- Monitor animation performance on slower connections
- Adjust timing for different server loads
- Consider client capabilities

## Examples

### Default Death Message
```python
show_death_curtain(character)
# Uses: "A red haze blurs your vision as the world slips away..."
```

### Custom Death Messages
```python
# Dramatic
show_death_curtain(character, "The darkness claims your soul...")

# Peaceful
show_death_curtain(character, "You drift away into eternal rest...")

# Violent
show_death_curtain(character, "Your blood pools beneath you...")

# Mystical
show_death_curtain(character, "Your essence fades into the void...")
```

## Future Enhancements

- **Multiple Sea Characters**: Different background patterns for different death types
- **Color Themes**: Ice (blue), fire (red/orange), nature (green), etc.
- **Speed Variations**: Different timing profiles for different death causes
- **Sound Integration**: Audio cues synchronized with visual effects
- **Multi-line Support**: Animate longer death messages across multiple lines

## Technical Notes

### Algorithm Beauty
The core algorithm elegantly balances:
- **Randomness**: Unpredictable character removal creates organic feel
- **Structure**: Planned sequence ensures complete message dissolution
- **Timing**: Progressive slowdown creates dramatic pacing
- **Flexibility**: Same system works for any message length

### Performance Characteristics
- **Memory Efficient**: Generates frames on-demand
- **Network Friendly**: Sends complete frames, not incremental changes
- **Server Optimized**: Uses Evennia's delay system for proper scheduling

---

*This system transforms character death from a simple event into a poetic, visual experience that enhances the storytelling aspect of the game while maintaining technical excellence.*
