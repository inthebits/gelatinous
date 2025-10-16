# Web Character Creation Alignment Spec

## Overview

This document defines how the web-based character creation should align with the telnet-based character creation system in `commands/charcreate.py`.

## Data Collection Requirements

### Telnet Character Creation Flow

**First Character:**
1. First name (validated, 2-30 chars, letters/hyphens/apostrophes)
2. Last name (validated, same rules)
3. Sex (male/female/ambiguous)
4. GRIM distribution (300 points total)
   - Grit (1-150)
   - Resonance (1-150)
   - Intellect (1-150)
   - Motorics (1-150)

**Respawn (after death):**
- Option 1: Flash clone (copy all stats from previous character)
- Option 2: Choose from 3 random templates (300-point GRIM distributions)

### Character Attributes Set

**From telnet character creation (`first_char_finalize`):**

```python
# Core identity
char.key = f"{first_name} {last_name}"  # Full name
char.sex = sex                           # "male", "female", or "ambiguous"

# GRIM stats (AttributeProperty)
char.grit = grit                         # 1-150
char.resonance = resonance               # 1-150
char.intellect = intellect               # 1-150
char.motorics = motorics                 # 1-150

# Stack/clone tracking
char.db.stack_id = uuid.uuid4()          # Unique consciousness ID
char.db.original_creation = time.time()  # Unix timestamp
char.db.current_sleeve_birth = time.time() # Unix timestamp
char.db.archived = False                 # Death status
char.death_count = 1                     # AttributeProperty default
```

**From flash clone (`create_flash_clone`):**

```python
# Inherited from old character
char.grit = old_character.grit
char.resonance = old_character.resonance
char.intellect = old_character.intellect
char.motorics = old_character.motorics
char.sex = old_character.sex
char.db.desc = old_character.db.desc
char.longdesc = old_character.longdesc   # Dictionary copy
char.db.skintone = old_character.db.skintone
char.death_count = old_character.death_count  # Already incremented at death
char.db.stack_id = old_character.db.stack_id  # Same consciousness
char.db.previous_clone_dbref = old_character.dbref

# New for this sleeve
char.key = build_name_from_death_count(old.key, death_count)  # Roman numeral
char.db.current_sleeve_birth = time.time()
char.db.archived = False
```

## Web Form Requirements

### Phase 1: Minimal Form (Next Step)

**Extend Evennia's CharacterForm with:**
- `grit` (IntegerField, min=1, max=150, initial=75)

**Keep from Evennia default:**
- `db_key` (CharField) - Character name
- `desc` (CharField/TextField) - Description

**Validation:**
- No GRIM total validation yet (just testing single field)

### Phase 2: Basic GRIM Form

**Add all GRIM fields:**
- `grit` (IntegerField, min=1, max=150, initial=75)
- `resonance` (IntegerField, min=1, max=150, initial=75)
- `intellect` (IntegerField, min=1, max=150, initial=75)
- `motorics` (IntegerField, min=1, max=150, initial=75)

**Validation (in `clean()`):**
- Total must equal 300
- Each stat 1-150

### Phase 3: Name Structure

**Split name into fields:**
- `first_name` (CharField, max=30, required, pattern validation)
- `last_name` (CharField, max=30, required, pattern validation)

**Combine to create `db_key`:**
```python
charname = f"{first_name} {last_name}"
```

**Validation:**
- 2-30 characters each
- Regex: `^[a-zA-Z][a-zA-Z\-']*[a-zA-Z]$`
- Check uniqueness of full name

### Phase 4: Sex/Gender

**Add field:**
- `sex` (ChoiceField: "male", "female", "ambiguous")

**Set on character:**
```python
character.sex = form.cleaned_data['sex']
```

### Phase 5: Advanced (Optional)

**Additional fields:**
- `skintone` (CharField/ChoiceField)
- `longdesc` (TextField/FormSet for detailed description)

## Implementation Strategy

### Current State
✅ Template overrides working (`character_form.html`, `_menu.html`)
✅ "Decant Sleeve" / "Manage Sleeves" terminology applied

### Next Steps

**Step 1: Single GRIM Field Test**
- Create `web/website/forms.py`
- Extend `CharacterForm` with just `grit` field
- No custom view needed (use Evennia's default)
- Verify field appears in form
- Create test character with grit value
- Confirm `character.grit` is set correctly

**Step 2: Full GRIM Fields**
- Add `resonance`, `intellect`, `motorics` to form
- Add `clean()` method to validate 300-point total
- Add client-side JavaScript for live point calculator
- Test character creation end-to-end

**Step 3: Name Structure**
- Add `first_name`, `last_name` fields to form
- Override `save()` or view's `form_valid()` to combine names
- Remove or hide `db_key` field from user input
- Test name validation and uniqueness

**Step 4: Sex Field**
- Add `sex` ChoiceField
- Set `character.sex` in view
- Test all three options

**Step 5: Respawn Interface**
- Extend view with `get_context_data()` to detect archived characters
- Update template to show flash clone + template options
- Handle respawn choices in `form_valid()`
- Integrate `create_flash_clone()` function

## Form Example (Phase 2)

```python
# web/website/forms.py
from django import forms
from evennia.web.website.forms import CharacterForm as EvenniaCharacterForm

class CharacterForm(EvenniaCharacterForm):
    """Extended character form with GRIM stats."""
    
    grit = forms.IntegerField(
        min_value=1, max_value=150, initial=75,
        label="Grit",
        help_text="Physical power and endurance (1-150)",
        widget=forms.NumberInput(attrs={'class': 'form-control grim-stat'})
    )
    
    resonance = forms.IntegerField(
        min_value=1, max_value=150, initial=75,
        label="Resonance",
        help_text="Psychic affinity and willpower (1-150)",
        widget=forms.NumberInput(attrs={'class': 'form-control grim-stat'})
    )
    
    intellect = forms.IntegerField(
        min_value=1, max_value=150, initial=75,
        label="Intellect",
        help_text="Logic, memory, and reasoning (1-150)",
        widget=forms.NumberInput(attrs={'class': 'form-control grim-stat'})
    )
    
    motorics = forms.IntegerField(
        min_value=1, max_value=150, initial=75,
        label="Motorics",
        help_text="Dexterity, reflexes, and coordination (1-150)",
        widget=forms.NumberInput(attrs={'class': 'form-control grim-stat'})
    )
    
    class Meta(EvenniaCharacterForm.Meta):
        fields = EvenniaCharacterForm.Meta.fields + (
            'grit', 'resonance', 'intellect', 'motorics'
        )
    
    def clean(self):
        """Validate GRIM total equals 300."""
        cleaned_data = super().clean()
        
        grit = cleaned_data.get('grit', 0)
        resonance = cleaned_data.get('resonance', 0)
        intellect = cleaned_data.get('intellect', 0)
        motorics = cleaned_data.get('motorics', 0)
        
        total = grit + resonance + intellect + motorics
        
        if total != 300:
            raise forms.ValidationError(
                f"GRIM stats must total exactly 300 points. Current total: {total} points."
            )
        
        return cleaned_data
```

## View Example (Phase 2)

```python
# web/website/views/characters.py
from django.contrib import messages
from django.http import HttpResponseRedirect
from evennia.web.website.views.characters import CharacterCreateView as EvenniaCharacterCreateView
from web.website import forms

class CharacterCreateView(EvenniaCharacterCreateView):
    """Extended character creation with GRIM stats."""
    
    form_class = forms.CharacterForm
    
    def form_valid(self, form):
        """Handle character creation with GRIM stats."""
        account = self.request.user
        
        # Extract form data
        charname = form.cleaned_data['db_key']
        description = form.cleaned_data.get('desc', '')
        
        # Create character (Evennia pattern)
        character, errors = self.typeclass.create(
            charname, account, description=description
        )
        
        if errors:
            [messages.error(self.request, x) for x in errors]
            return self.form_invalid(form)
        
        if character:
            # Set GRIM stats
            character.grit = form.cleaned_data['grit']
            character.resonance = form.cleaned_data['resonance']
            character.intellect = form.cleaned_data['intellect']
            character.motorics = form.cleaned_data['motorics']
            
            messages.success(
                self.request,
                f"Character '{character.name}' created with GRIM stats!"
            )
            return HttpResponseRedirect(self.success_url)
        else:
            messages.error(self.request, "Character creation failed.")
            return self.form_invalid(form)
```

## URL Override (Phase 2)

```python
# web/website/urls.py
from django.urls import path
from evennia.web.website.urls import urlpatterns as evennia_website_urlpatterns
from web.website.views.characters import CharacterCreateView

urlpatterns = [
    path("characters/create/", CharacterCreateView.as_view(), name="character-create"),
]

urlpatterns = urlpatterns + evennia_website_urlpatterns
```

## Testing Checklist

### Phase 1 (Single Field)
- [ ] Form displays with grit field
- [ ] Can enter value 1-150
- [ ] Value is saved to `character.grit`
- [ ] Can retrieve value with `character.grit`

### Phase 2 (Full GRIM)
- [ ] All four GRIM fields appear
- [ ] JavaScript calculator shows total
- [ ] Cannot submit if total ≠ 300
- [ ] All four stats saved correctly
- [ ] Can create multiple characters with different distributions

### Phase 3 (Name Structure)
- [ ] First/last name fields appear
- [ ] Name validation works (regex, length)
- [ ] Names combined into `character.key`
- [ ] Uniqueness check works

### Phase 4 (Sex)
- [ ] Sex dropdown appears with 3 options
- [ ] Selection saved to `character.sex`
- [ ] Gender property returns correct value

### Phase 5 (Respawn)
- [ ] Flash clone option appears for accounts with dead characters
- [ ] Templates display correctly
- [ ] Flash clone preserves all attributes
- [ ] Roman numeral increments correctly
- [ ] Death count carries forward

## Notes

- **Incremental approach:** Each phase builds on previous, with testing at each step
- **Code reuse:** Import functions from `commands/charcreate.py` where possible
- **Consistency:** Web and telnet should create identical character states
- **Safety:** Always test on development before production deployment
