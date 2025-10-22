# Web-Based Respawn Character Creation Specification

## Overview

Implement the respawn character creation flow (templates + flash clone) on the Django website to match the telnet EvMenu experience. This allows users to respawn characters via the web interface with the same options available in-game.

## Current State

### Telnet Character Creation (commands/charcreate.py)
- **First character**: Custom stat allocation (300 points across GRIM)
- **Respawn**: EvMenu with 3 random templates + flash clone option
- **Flash clone**: Inherits stats, appearance, sex from archived character
- **Roman numerals**: Auto-appends based on death_count (Jorge Jackson → Jorge Jackson II)

### Web Character Creation (web/website/views/characters.py)
- **Current**: Single Django form for manual character creation
- **Limitation**: No respawn flow - always shows the form
- **Problem**: Users can't access flash clone or templates via web

## Desired Behavior

When a user visits the "Decant Sleeve" page:

1. **If `account.db.last_character` exists** (respawn scenario):
   - Display respawn interface with:
     - 3 randomly generated character templates (name, stats)
     - Flash clone option (if archived character exists)
     - Sex selection for chosen option
   - Submit creates character using selected template/clone
   
2. **If no `last_character`** (first character):
   - Display existing manual stat allocation form
   - No changes to current behavior

## Technical Requirements

### 1. View Logic (web/website/views/characters.py)

```python
class CharacterCreateView(EvenniaCharacterCreateView):
    def get(self, request, *args, **kwargs):
        """Determine which character creation flow to show."""
        account = request.user
        
        # Check for respawn scenario
        if account.db.last_character:
            return self.show_respawn_interface(request, account)
        else:
            return self.show_first_character_form(request)
    
    def show_respawn_interface(self, request, account):
        """Display template selection + flash clone options."""
        # Generate 3 random templates (reuse generate_random_template())
        # Pass old character data for flash clone option
        # Render respawn template
        
    def show_first_character_form(self, request):
        """Display existing manual stat allocation form."""
        # Current behavior - no changes
```

### 2. Template Generation

Reuse existing template generation logic from `commands/charcreate.py`:

```python
from commands.charcreate import generate_random_template

templates = [generate_random_template() for _ in range(3)]
```

**Template structure:**
```python
{
    'first_name': str,
    'last_name': str,
    'grit': int,
    'resonance': int,
    'intellect': int,
    'motorics': int
}
```

### 3. Flash Clone Logic

Reuse existing flash clone creation from `commands/charcreate.py`:

```python
from commands.charcreate import create_flash_clone_character

# When user selects flash clone option
character = create_flash_clone_character(account, old_character)
```

**Flash clone behavior:**
- Inherits: GRIM stats, appearance (desc, longdesc), sex, skintone
- Auto-names: Uses `build_name_from_death_count()` for Roman numerals
- Increments: death_count already incremented during archival

### 4. Django Templates

Create new template: `web/templates/website/character_respawn_create.html`

**UI Structure:**
```
Sleeve Decantation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your previous sleeve has been archived.
Stack integrity: 98.7%

Available Sleeves:

┌─────────────────────────────────────────────┐
│ [Radio] Template 1: [Name]                  │
│         Grit: XX  Resonance: XX             │
│         Intellect: XX  Motorics: XX         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ [Radio] Template 2: [Name]                  │
│         Grit: XX  Resonance: XX             │
│         Intellect: XX  Motorics: XX         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ [Radio] Template 3: [Name]                  │
│         Grit: XX  Resonance: XX             │
│         Intellect: XX  Motorics: XX         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ [Radio] FLASH CLONE: [Old Name II]          │
│         Preserves your previous identity    │
│         Grit: XX  Resonance: XX             │
│         Intellect: XX  Motorics: XX         │
└─────────────────────────────────────────────┘

Sex: [Male] [Female] [Ambiguous]

[Decant Sleeve Button]
```

### 5. Form Handling

**POST data structure:**
```python
{
    'sleeve_choice': 'template_0' | 'template_1' | 'template_2' | 'flash_clone',
    'sex': 'male' | 'female' | 'ambiguous'
}
```

**Processing:**
```python
def post(self, request, *args, **kwargs):
    choice = request.POST.get('sleeve_choice')
    sex = request.POST.get('sex')
    
    if choice == 'flash_clone':
        character = create_flash_clone_character(account, old_character)
    else:
        template_idx = int(choice.split('_')[1])
        template = templates[template_idx]
        character = create_character_from_template(account, template, sex)
    
    # Redirect to character detail or management page
```

## Data Flow

### Respawn Flow
```
User Archives Character (web or death)
  ↓
archive_character() sets:
  - account.db.last_character = character
  - character.death_count += 1
  ↓
User Visits "Decant Sleeve"
  ↓
View Detects account.db.last_character exists
  ↓
Generate 3 Random Templates
  ↓
Display Respawn Interface:
  - Template Option 1
  - Template Option 2  
  - Template Option 3
  - Flash Clone Option (shows Roman numeral name)
  ↓
User Selects Option + Sex
  ↓
POST Handler Creates Character:
  - Template: create_character_from_template()
  - Flash Clone: create_flash_clone_character()
  ↓
Redirect to Character Management
```

## Implementation Checklist

### Phase 1: View Logic
- [ ] Add `get()` method to detect respawn vs first character
- [ ] Create `show_respawn_interface()` method
- [ ] Import and use `generate_random_template()` function
- [ ] Pass context data to template (templates, old_character, sex options)

### Phase 2: Template Creation
- [ ] Create `character_respawn_create.html`
- [ ] Style respawn interface to match game theme (dark, dissolution aesthetic)
- [ ] Add radio buttons for template selection
- [ ] Add sex selection buttons
- [ ] Add flash clone option display

### Phase 3: Form Processing
- [ ] Create respawn form handler in `post()` method
- [ ] Import `create_flash_clone_character()` function
- [ ] Import `create_character_from_template()` function
- [ ] Handle template selection + creation
- [ ] Handle flash clone selection + creation
- [ ] Add error handling and user feedback messages

### Phase 4: Testing
- [ ] Test first character creation (should still show form)
- [ ] Archive a character, verify respawn interface appears
- [ ] Test template selection and character creation
- [ ] Test flash clone selection and character creation
- [ ] Verify Roman numeral naming works (Jorge → Jorge II)
- [ ] Test sex selection for both templates and flash clone
- [ ] Verify stat inheritance for flash clones
- [ ] Test appearance inheritance (desc, longdesc) for flash clones

### Phase 5: Polish
- [ ] Add loading states for form submission
- [ ] Style to match Gelatinous Monster aesthetic
- [ ] Add helpful tooltips/descriptions
- [ ] Ensure mobile responsiveness
- [ ] Add confirmation messages on success

## Edge Cases

1. **Template generation fails**: Show error, fallback to manual form
2. **No last_character but all characters archived**: Treat as first character
3. **last_character deleted from DB**: Handle gracefully, show manual form
4. **Concurrent creation attempts**: Django form validation should handle
5. **Invalid sex selection**: Validate and default to 'ambiguous'

## Success Criteria

- [ ] Users with archived characters see respawn interface on web
- [ ] Templates generate correctly with random stats (300 point total)
- [ ] Flash clone inherits all data from archived character
- [ ] Roman numeral naming works correctly
- [ ] Sex selection applies to created character
- [ ] First-time users still see manual stat allocation form
- [ ] All creation paths persist character correctly to database
- [ ] UI matches game's dissolution/body-horror aesthetic

## Future Enhancements

- [ ] Allow regenerating templates without page refresh (AJAX)
- [ ] Preview character appearance before decanting
- [ ] Add "Randomize All" button for template generation
- [ ] Allow editing template stats before decanting (within 300 point limit)
- [ ] Add character comparison view (side-by-side stats)
