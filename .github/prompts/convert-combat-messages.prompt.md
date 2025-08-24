---
mode: agent
description: "Convert Evennia MUD combat message files from old {attacker}/{target} format to new three-perspective dictionary structure"
---

# Combat Message Format Conversion

Convert an Evennia MUD combat message file from the old string-based format using `{attacker}` and `{target}` placeholders to the new three-perspective dictionary structure with `attacker_msg`, `victim_msg`, and `observer_msg` keys.

## Current Format (Old)
```python
MESSAGES = {
    "initiate": [
        "{attacker} draws the sword, ready to strike {target}.",
        # ... more messages
    ],
    "hit": [
        "The blade cuts {target}'s arm, and {attacker} grins.",
        # ... more messages  
    ],
    # ... other categories
}
```

## Target Format (New)
```python
MESSAGES = {
    "initiate": [
        {
            'attacker_msg': "You draw the sword, ready to strike {target_name}.",
            'victim_msg': "{attacker_name} draws the sword, ready to strike you.",
            'observer_msg': "{attacker_name} draws the sword, ready to strike {target_name}."
        },
        # ... more message dictionaries
    ],
    "hit": [
        {
            'attacker_msg': "The blade cuts {target_name}'s arm, and you grin.",
            'victim_msg': "The blade cuts your arm, and {attacker_name} grins.",
            'observer_msg': "The blade cuts {target_name}'s arm, and {attacker_name} grins."
        },
        # ... more message dictionaries
    ],
    # ... other categories
}
```

## Conversion Rules

### Placeholder Transformation
- `{attacker}` → `{attacker_name}` in victim_msg and observer_msg
- `{attacker}` → "you/your" (first person) in attacker_msg
- `{target}` → `{target_name}` in attacker_msg and observer_msg  
- `{target}` → "you/your" (first person) in victim_msg

### Perspective Grammar Adjustments
- **attacker_msg**: Convert third person to first person
  - "The attacker swings" → "You swing"
  - "{attacker} raises the weapon" → "You raise the weapon"
  - "their" → "your" when referring to attacker
  - "them" → "you" when referring to attacker

- **victim_msg**: Convert third person to first person for victim
  - "{target} screams" → "You scream"  
  - "their" → "your" when referring to target
  - "them" → "you" when referring to target

- **observer_msg**: Keep third person for both parties
  - Use `{attacker_name}` and `{target_name}`
  - Maintain original perspective and grammar

### Atmospheric Content Preservation
- **CRITICAL**: Preserve all atmospheric, visceral, and poetic language exactly
- Maintain the unique voice and tone of each weapon type
- Keep all sound effects, visual descriptions, and emotional content
- Preserve punctuation, capitalization, and formatting details
- Do NOT simplify or sanitize the dramatic descriptions

### Structure Requirements  
- Each message becomes a dictionary with exactly 3 keys
- Maintain original message order within each category
- Keep all original categories (initiate, hit, miss, kill, etc.)
- Ensure consistent indentation and formatting

## Systematic Conversion Approach for Large Files
When working with files containing 80+ messages (like flamethrower.py with 120+ messages):

1. **Assessment Phase**: Count total messages and categories first
2. **Incremental Building**: Create file structure, then build category by category
3. **Category-by-Category**: Convert initiate → hit → miss → kill in separate operations  
4. **Quality Focus**: Preserve every atmospheric detail, sound effect, and visceral description
5. **Validation Checkpoints**: Test syntax after each major category addition
6. **Patience Over Speed**: Take time to maintain the horror and drama of each message

**Never sacrifice the atmospheric quality for conversion speed - these messages define the weapon's character!**

## Process Steps
1. **Read** the entire source file to understand structure and count
2. **Create** a new file with "_converted" suffix  
3. **Convert** systematically by category (initiate, hit, miss, kill) - DO ONE CATEGORY AT A TIME
4. **Take time** - avoid rushing through large files that may hit response length limits
5. **Build incrementally** - start with file structure, then add each converted category section by section
6. **Validate** syntax with Python compilation test after each major section
7. **Replace** original file only after successful complete conversion
8. **Verify** message count and structure integrity

## Large File Handling Strategy
- **CRITICAL**: For files with 100+ messages, work in smaller chunks
- Convert one category at a time (initiate → hit → miss → kill)
- Use multiple edit operations rather than trying to create the entire file at once
- Always preserve the exact atmospheric language and dramatic descriptions
- Take breaks between categories to avoid response length limits
- Verify each section compiles before moving to the next

## Quality Checklist
- [ ] File analyzed for size and message count before conversion
- [ ] Large files handled in systematic chunks (category by category)
- [ ] All messages converted to dictionary format
- [ ] Three perspectives (attacker_msg, victim_msg, observer_msg) for each message
- [ ] Proper first/second/third person grammar for each perspective
- [ ] All atmospheric and dramatic language preserved exactly
- [ ] Placeholder names updated correctly ({attacker_name}, {target_name})
- [ ] Python syntax valid (no compilation errors) after each section
- [ ] Message count matches original (verify with count check)
- [ ] File structure and categories intact
- [ ] No rushed conversions that sacrifice quality for speed

## Response Length Management
- **IMPORTANT**: Take time with large files - better to work systematically than hit limits
- If a file has 80+ messages, expect to need multiple conversion steps
- Focus on quality and accuracy over speed
- Use incremental building approach for files with 4+ categories
- Always preserve the atmospheric and visceral language completely

Convert the file: ${file}
