"""
Character Creation System for Gelatinous Monster

This module handles both first-time character creation and respawn/flash cloning
after death. It uses Evennia's EvMenu system for the interactive interface.

Flow:
1. First Character: Name input → Sex selection → GRIM distribution (300 points)
2. Respawn: Choose from 3 random templates OR flash clone previous character
"""

from evennia import create_object
from evennia.utils.evmenu import EvMenu
from django.conf import settings
import random
import time
import re


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_random_template():
    """
    Generate a random character template with 300 GRIM points distributed.
    
    Returns:
        dict: Template with 'grit', 'resonance', 'intellect', 'motorics', 
              'first_name', 'last_name'
    """
    from world.namebank import FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES
    
    # Randomly pick gender for name selection
    use_male = random.choice([True, False])
    first_name = random.choice(FIRST_NAMES_MALE if use_male else FIRST_NAMES_FEMALE)
    last_name = random.choice(LAST_NAMES)
    
    # Generate GRIM distribution totaling 300 points
    # Use weighted random distribution to create varied but viable templates
    points_left = 300
    stats = []
    
    # Assign 3 stats randomly, then give remainder to 4th
    for i in range(3):
        # Each stat gets between 25-100 points (avoid extremes)
        min_points = max(25, points_left - (150 * (3 - i)))  # Ensure enough left
        max_points = min(100, points_left - (25 * (3 - i)))  # Ensure minimum for others
        
        if max_points > min_points:
            points = random.randint(min_points, max_points)
        else:
            points = min_points
            
        stats.append(points)
        points_left -= points
    
    # Give remainder to 4th stat (clamped to max 150)
    stats.append(min(150, points_left))
    
    # Shuffle so variance isn't predictable by position
    random.shuffle(stats)
    
    return {
        'first_name': first_name,
        'last_name': last_name,
        'grit': stats[0],
        'resonance': stats[1],
        'intellect': stats[2],
        'motorics': stats[3]
    }


def increment_roman_numeral(name):
    """
    Increment the Roman numeral at the end of a name, or add ' II' if none exists.
    
    Examples:
        "Brock" → "Brock II"
        "Brock II" → "Brock III"
        "Marcus X" → "Marcus XI"
    
    Args:
        name (str): Character name possibly ending in Roman numeral
        
    Returns:
        str: Name with incremented Roman numeral
    """
    # Roman numeral pattern at end of string
    pattern = r'^(.*?)\s*([IVXLCDM]+)$'
    match = re.match(pattern, name.strip(), re.IGNORECASE)
    
    if match:
        base_name = match.group(1).strip()
        roman = match.group(2).upper()
        
        # Convert Roman to int
        roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        value = 0
        prev_value = 0
        
        for char in reversed(roman):
            current_value = roman_values.get(char, 0)
            if current_value < prev_value:
                value -= current_value
            else:
                value += current_value
            prev_value = current_value
        
        # Increment
        value += 1
        
        # Convert back to Roman
        new_roman = int_to_roman(value)
        return f"{base_name} {new_roman}"
    else:
        # No Roman numeral found, add II
        return f"{name} II"


def int_to_roman(num):
    """Convert integer to Roman numeral."""
    values = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    
    result = ''
    for value, numeral in values:
        count = num // value
        if count:
            result += numeral * count
            num -= value * count
    return result


def validate_name(name):
    """
    Validate a character name.
    
    Rules:
    - 2-30 characters
    - Letters, spaces, hyphens, apostrophes only
    - Cannot start/end with space or punctuation
    - No profanity (basic filter)
    
    Args:
        name (str): Name to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    name = name.strip()
    
    if len(name) < 2:
        return (False, "Name must be at least 2 characters long.")
    
    if len(name) > 30:
        return (False, "Name must be 30 characters or less.")
    
    # Check allowed characters
    if not re.match(r"^[a-zA-Z][a-zA-Z\s\-']*[a-zA-Z]$", name):
        return (False, "Name can only contain letters, spaces, hyphens, and apostrophes.")
    
    # Basic profanity filter (expandable)
    profanity_list = ['fuck', 'shit', 'damn', 'bitch', 'ass', 'cunt', 'dick', 'cock', 'pussy']
    name_lower = name.lower()
    for word in profanity_list:
        if word in name_lower:
            return (False, "That name is not allowed.")
    
    # Check uniqueness
    from typeclasses.characters import Character
    if Character.objects.filter(db_key__iexact=name).exists():
        return (False, "That name is already taken.")
    
    return (True, None)


def validate_grim_distribution(grit, resonance, intellect, motorics):
    """
    Validate GRIM stat distribution.
    
    Rules:
    - All stats between 1 and 150
    - Total equals 300
    
    Args:
        grit, resonance, intellect, motorics (int): Stat values
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    stats = [grit, resonance, intellect, motorics]
    
    # Check range
    for stat in stats:
        if stat < 1:
            return (False, "All stats must be at least 1.")
        if stat > 150:
            return (False, "No stat can exceed 150.")
    
    # Check total
    total = sum(stats)
    if total != 300:
        return (False, f"Stats must total 300 (current total: {total}).")
    
    return (True, None)


def create_character_from_template(account, template, sex="androgynous"):
    """
    Create a character from a template (for respawn).
    
    Args:
        account: Account object
        template (dict): Template with name and GRIM stats
        sex (str): Biological sex
        
    Returns:
        Character: New character object
    """
    from typeclasses.characters import Character
    
    # Get spawn location
    start_location = get_start_location()
    
    # Create full name
    full_name = f"{template['first_name']} {template['last_name']}"
    
    # Create character
    char = create_object(
        Character,
        key=full_name,
        location=start_location,
        home=start_location
    )
    
    # Set account
    char.db.account = account
    account.db._last_puppet = char
    
    # Set GRIM stats
    char.grit = template['grit']
    char.resonance = template['resonance']
    char.intellect = template['intellect']
    char.motorics = template['motorics']
    
    # Set sex
    char.sex = sex
    
    # Set defaults
    char.db.clone_generation = 1
    char.db.archived = False
    
    return char


def create_flash_clone(account, old_character):
    """
    Create a flash clone from a dead character.
    Inherits: GRIM stats, longdesc, desc, sex, skintone
    Increments: name (with Roman numeral), death_count
    
    Args:
        account: Account object
        old_character: Dead character to clone from
        
    Returns:
        Character: New cloned character
    """
    from typeclasses.characters import Character
    
    # Get spawn location
    start_location = get_start_location()
    
    # Increment name
    new_name = increment_roman_numeral(old_character.key)
    
    # Create character
    char = create_object(
        Character,
        key=new_name,
        location=start_location,
        home=start_location
    )
    
    # Set account
    char.db.account = account
    account.db._last_puppet = char
    
    # INHERIT: GRIM stats (with fallback defaults)
    char.grit = old_character.grit if old_character.grit is not None else 1
    char.resonance = old_character.resonance if old_character.resonance is not None else 1
    char.intellect = old_character.intellect if old_character.intellect is not None else 1
    char.motorics = old_character.motorics if old_character.motorics is not None else 1
    
    # INHERIT: Appearance
    char.db.desc = old_character.db.desc
    if hasattr(old_character, 'longdesc') and old_character.longdesc:
        char.longdesc = dict(old_character.longdesc)  # Copy dictionary
    
    # INHERIT: Biology
    char.sex = old_character.sex
    if hasattr(old_character.db, 'skintone'):
        char.db.skintone = old_character.db.skintone
    
    # INCREMENT: Generation and death count
    old_generation = getattr(old_character.db, 'clone_generation', None)
    if old_generation is None:
        old_generation = 1
    char.db.clone_generation = old_generation + 1
    
    old_death_count = getattr(old_character.db, 'death_count', None)
    if old_death_count is None:
        old_death_count = 0
    char.db.death_count = old_death_count + 1
    
    # Link to previous incarnation
    char.db.previous_clone_dbref = old_character.dbref
    
    # Stack ID (consciousness identifier)
    old_stack_id = getattr(old_character.db, 'stack_id', None)
    if old_stack_id:
        char.db.stack_id = old_stack_id
    else:
        # Create new stack ID if old char didn't have one
        import uuid
        char.db.stack_id = str(uuid.uuid4())
    
    # Reset state
    char.db.archived = False
    char.db.current_sleeve_birth = time.time()
    
    return char


def get_start_location():
    """
    Get the starting location for new characters.
    
    Returns:
        Room: Starting location object
    """
    from evennia import search_object
    
    # Try START_LOCATION from settings
    start_location_id = getattr(settings, 'START_LOCATION', None)
    if start_location_id:
        try:
            start_location = search_object(f"#{start_location_id}")[0]
            return start_location
        except (IndexError, AttributeError):
            pass
    
    # Fallback to Limbo (#2)
    try:
        return search_object("#2")[0]
    except (IndexError, AttributeError):
        # Last resort - just return None and let Evennia handle it
        return None


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def start_character_creation(account, is_respawn=False, old_character=None):
    """
    Start the character creation process.
    
    Args:
        account: Account object
        is_respawn (bool): True if respawning after death, False if first character
        old_character: If respawn, the dead character object
    """
    # Store context in account NDB for menu access
    account.ndb.charcreate_is_respawn = is_respawn
    account.ndb.charcreate_old_character = old_character
    account.ndb.charcreate_data = {}
    
    # Start appropriate menu
    if is_respawn:
        # Respawn menu: show templates + flash clone option
        EvMenu(
            account,
            "commands.charcreate",
            startnode="respawn_welcome",
            cmdset_mergetype="Replace",
            cmd_on_exit=None
        )
    else:
        # First character menu: custom creation
        EvMenu(
            account,
            "commands.charcreate",
            startnode="first_char_welcome",
            cmdset_mergetype="Replace",
            cmd_on_exit=None
        )


# =============================================================================
# RESPAWN MENU NODES
# =============================================================================

def respawn_welcome(caller, raw_string, **kwargs):
    """Respawn menu entry point - show death message and transition."""
    
    text = """
|r╔════════════════════════════════════════════════════════════════╗
║  CONSCIOUSNESS BACKUP PROTOCOL INITIATED                       ║
║  VECTOR INDUSTRIES - MEDICAL RECONSTRUCTION DIVISION           ║
╚════════════════════════════════════════════════════════════════╝|n

|yYour previous sleeve has been terminated.|n
|yMemory upload successful. Stack integrity: |g98.7%|n

|wPreparing new sleeve for consciousness transfer...|n

Generating available templates...
"""
    
    options = (
        {"key": "_default",
         "goto": "respawn_show_options"},
    )
    
    return text, options


def respawn_show_options(caller, raw_string, **kwargs):
    """Show the 3 templates + flash clone option."""
    
    # Generate 3 random templates
    templates = [generate_random_template() for _ in range(3)]
    caller.ndb.charcreate_data['templates'] = templates
    
    text = """
|w╔════════════════════════════════════════════════════════════════╗
║  AVAILABLE SLEEVES                                             ║
╚════════════════════════════════════════════════════════════════╝|n

Select a consciousness vessel:

"""
    
    # Display templates
    for i, template in enumerate(templates, 1):
        text += f"\n|w[{i}]|n |c{template['first_name']} {template['last_name']}|n\n"
        text += f"    |gGrit:|n {template['grit']:3d}  "
        text += f"|yResonance:|n {template['resonance']:3d}  "
        text += f"|bIntellect:|n {template['intellect']:3d}  "
        text += f"|mMotorics:|n {template['motorics']:3d}\n"
    
    # Flash clone option
    old_char = caller.ndb.charcreate_old_character
    if old_char:
        text += f"\n|w[4]|n |rFLASH CLONE|n - |c{old_char.key}|n (preserve current identity)\n"
        text += f"    |gGrit:|n {old_char.grit:3d}  "
        text += f"|yResonance:|n {old_char.resonance:3d}  "
        text += f"|bIntellect:|n {old_char.intellect:3d}  "
        text += f"|mMotorics:|n {old_char.motorics:3d}\n"
        text += f"    |xInherits appearance, stats, and memories from previous incarnation|n\n"
    
    text += "\n|wEnter choice [1-4]:|n "
    
    options = (
        {"key": "1",
         "goto": ("respawn_confirm_template", {"template_idx": 0})},
        {"key": "2",
         "goto": ("respawn_confirm_template", {"template_idx": 1})},
        {"key": "3",
         "goto": ("respawn_confirm_template", {"template_idx": 2})},
        {"key": "4",
         "goto": "respawn_flash_clone"} if old_char else {"key": "_default", "goto": "respawn_show_options"},
        {"key": "_default",
         "goto": "respawn_show_options"},
    )
    
    return text, options


def respawn_confirm_template(caller, raw_string, template_idx=0, **kwargs):
    """Confirm template selection and choose sex."""
    
    templates = caller.ndb.charcreate_data.get('templates', [])
    if template_idx >= len(templates):
        return "respawn_show_options"
    
    template = templates[template_idx]
    caller.ndb.charcreate_data['selected_template'] = template
    
    text = f"""
|w╔════════════════════════════════════════════════════════════════╗
║  SLEEVE CONFIGURATION                                          ║
╚════════════════════════════════════════════════════════════════╝|n

Selected: |c{template['first_name']} {template['last_name']}|n

|gGrit:|n      {template['grit']:3d}
|yResonance:|n {template['resonance']:3d}
|bIntellect:|n {template['intellect']:3d}
|mMotorics:|n {template['motorics']:3d}

Select biological sex for this sleeve:

|w[1]|n Male
|w[2]|n Female
|w[3]|n Androgynous

|w[B]|n Back to template selection

|wEnter choice:|n """
    
    options = (
        {"key": "1",
         "goto": ("respawn_finalize_template", {"sex": "male"})},
        {"key": "2",
         "goto": ("respawn_finalize_template", {"sex": "female"})},
        {"key": "3",
         "goto": ("respawn_finalize_template", {"sex": "androgynous"})},
        {"key": ("b", "back"),
         "goto": "respawn_show_options"},
        {"key": "_default",
         "goto": ("respawn_confirm_template", {"template_idx": template_idx})},
    )
    
    return text, options


def respawn_finalize_template(caller, raw_string, sex="androgynous", **kwargs):
    """Create character from template and finalize respawn."""
    
    template = caller.ndb.charcreate_data.get('selected_template')
    if not template:
        return "respawn_show_options"
    
    # Create character
    try:
        char = create_character_from_template(caller, template, sex)
        
        # Puppet the new character
        caller.puppet_object(caller.sessions.all()[0], char)
        
        # Send welcome message
        char.msg("|g╔════════════════════════════════════════════════════════════════╗")
        char.msg("|g║  CONSCIOUSNESS TRANSFER COMPLETE                               ║")
        char.msg("|g╚════════════════════════════════════════════════════════════════╝|n")
        char.msg("")
        char.msg(f"|wWelcome back, |c{char.key}|w.|n")
        char.msg(f"|xClone Generation:|n |w1|n")
        char.msg("")
        char.msg("|yYou open your eyes in an unfamiliar body.|n")
        char.msg("|yThe memories feel... borrowed. But they're yours now.|n")
        char.msg("")
        
        # Clean up
        _cleanup_charcreate_ndb(caller)
        
        # Exit menu
        return None
        
    except Exception as e:
        # Error - show message and return to selection
        caller.msg(f"|rError creating character: {e}|n")
        from evennia.comms.models import ChannelDB
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"CHARCREATE_ERROR: {e}")
        except:
            pass
        return "respawn_show_options"


def respawn_flash_clone(caller, raw_string, **kwargs):
    """Create flash clone and finalize respawn."""
    
    old_char = caller.ndb.charcreate_old_character
    if not old_char:
        caller.msg("|rError: No previous character found.|n")
        return "respawn_show_options"
    
    # Create flash clone
    try:
        char = create_flash_clone(caller, old_char)
        
        # Puppet the new character
        caller.puppet_object(caller.sessions.all()[0], char)
        
        # Send welcome message
        generation = char.db.clone_generation
        char.msg("|r╔════════════════════════════════════════════════════════════════╗")
        char.msg("|r║  FLASH CLONE PROTOCOL COMPLETE                                 ║")
        char.msg("|r╚════════════════════════════════════════════════════════════════╝|n")
        char.msg("")
        char.msg(f"|wWelcome back, |c{char.key}|w.|n")
        char.msg(f"|xClone Generation:|n |w{generation}|n")
        char.msg(f"|xDeath Count:|n |w{char.db.death_count}|n")
        char.msg("")
        
        # Generation-specific flavor
        if generation == 2:
            char.msg("|xThis is your first death. The sensation of resleeving is disorienting.|n")
            char.msg("|xYour old body's final moments echo in your mind like static on a dead channel.|n")
        elif generation < 5:
            char.msg("|xThe memories of your previous body fade like analog videotape degradation.|n")
            char.msg("|xYou know you've done this before, but each time feels like the first.|n")
        elif generation < 10:
            char.msg("|xYou've died enough times to know: this never gets easier.|n")
            char.msg("|xBut at least you're still you. Mostly.|n")
        else:
            char.msg("|rHow many times have you done this? The memories blur together like overexposed film.|n")
            char.msg("|rAre you still the person who first stepped into this world?|n")
        
        char.msg("")
        char.msg(f"|xPrevious cause of death:|n |r{old_char.db.death_cause or 'Unknown'}|n")
        char.msg("")
        
        # Clean up
        _cleanup_charcreate_ndb(caller)
        
        # Exit menu
        return None
        
    except Exception as e:
        # Error - show message and return to selection
        caller.msg(f"|rError creating flash clone: {e}|n")
        from evennia.comms.models import ChannelDB
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"FLASH_CLONE_ERROR: {e}")
        except:
            pass
        return "respawn_show_options"


# =============================================================================
# FIRST CHARACTER MENU NODES
# =============================================================================

def first_char_welcome(caller, raw_string, **kwargs):
    """First character creation entry point."""
    
    text = """
|b╔════════════════════════════════════════════════════════════════╗
║  WELCOME TO THE GELATINOUS MONSTER                             ║
║  CHARACTER INITIALIZATION PROTOCOL                             ║
╚════════════════════════════════════════════════════════════════╝|n

|wBeginning consciousness upload sequence...|n

|xThe year is 198█. The broadcast never ends.|n
|xYour memories are... incomplete. But you're here now.|n

Press |w<Enter>|n to begin character creation.
"""
    
    options = (
        {"key": "_default",
         "goto": "first_char_name_first"},
    )
    
    return text, options


def first_char_name_first(caller, raw_string, **kwargs):
    """Get first name."""
    
    text = """
|w╔════════════════════════════════════════════════════════════════╗
║  IDENTITY VERIFICATION                                         ║
╚════════════════════════════════════════════════════════════════╝|n

|wWhat is your FIRST name?|n

(2-30 characters, letters only)

|w>|n """
    
    if raw_string:
        # Validate
        name = raw_string.strip()
        is_valid, error = validate_name(name)
        
        # Note: We're only checking format here, not uniqueness
        # (since we need full name for uniqueness check)
        if len(name) < 2 or len(name) > 30:
            caller.msg(f"|rInvalid name: Name must be 2-30 characters.|n")
            return "first_char_name_first"
        
        if not re.match(r"^[a-zA-Z][a-zA-Z\-']*[a-zA-Z]$", name):
            caller.msg(f"|rInvalid name: Only letters, hyphens, and apostrophes allowed.|n")
            return "first_char_name_first"
        
        # Store first name
        caller.ndb.charcreate_data['first_name'] = name
        return "first_char_name_last"
    
    options = (
        {"key": "_default",
         "goto": "first_char_name_first"},
    )
    
    return text, options


def first_char_name_last(caller, raw_string, **kwargs):
    """Get last name."""
    
    first_name = caller.ndb.charcreate_data.get('first_name', '')
    
    text = f"""
|w╔════════════════════════════════════════════════════════════════╗
║  IDENTITY VERIFICATION                                         ║
╚════════════════════════════════════════════════════════════════╝|n

First name: |c{first_name}|n

|wWhat is your LAST name?|n

(2-30 characters, letters only)

|w>|n """
    
    if raw_string:
        # Validate
        name = raw_string.strip()
        
        if len(name) < 2 or len(name) > 30:
            caller.msg(f"|rInvalid name: Name must be 2-30 characters.|n")
            return "first_char_name_last"
        
        if not re.match(r"^[a-zA-Z][a-zA-Z\-']*[a-zA-Z]$", name):
            caller.msg(f"|rInvalid name: Only letters, hyphens, and apostrophes allowed.|n")
            return "first_char_name_last"
        
        # Check full name uniqueness
        full_name = f"{first_name} {name}"
        is_valid, error = validate_name(full_name)
        if not is_valid:
            caller.msg(f"|r{error}|n")
            return "first_char_name_last"
        
        # Store last name
        caller.ndb.charcreate_data['last_name'] = name
        return "first_char_sex"
    
    options = (
        {"key": "_default",
         "goto": "first_char_name_last"},
    )
    
    return text, options


def first_char_sex(caller, raw_string, **kwargs):
    """Select biological sex."""
    
    first_name = caller.ndb.charcreate_data.get('first_name', '')
    last_name = caller.ndb.charcreate_data.get('last_name', '')
    
    text = f"""
|w╔════════════════════════════════════════════════════════════════╗
║  BIOLOGICAL CONFIGURATION                                      ║
╚════════════════════════════════════════════════════════════════╝|n

Name: |c{first_name} {last_name}|n

Select biological sex:

|w[1]|n Male
|w[2]|n Female
|w[3]|n Androgynous

|wEnter choice:|n """
    
    options = (
        {"key": "1",
         "goto": ("first_char_grim", {"sex": "male"})},
        {"key": "2",
         "goto": ("first_char_grim", {"sex": "female"})},
        {"key": "3",
         "goto": ("first_char_grim", {"sex": "androgynous"})},
        {"key": "_default",
         "goto": "first_char_sex"},
    )
    
    return text, options


def first_char_grim(caller, raw_string, sex="androgynous", **kwargs):
    """Distribute GRIM points."""
    
    # Store sex
    if sex:
        caller.ndb.charcreate_data['sex'] = sex
    
    first_name = caller.ndb.charcreate_data.get('first_name', '')
    last_name = caller.ndb.charcreate_data.get('last_name', '')
    sex = caller.ndb.charcreate_data.get('sex', 'androgynous')
    
    # Get current GRIM values (or defaults)
    grit = caller.ndb.charcreate_data.get('grit', 75)
    resonance = caller.ndb.charcreate_data.get('resonance', 75)
    intellect = caller.ndb.charcreate_data.get('intellect', 75)
    motorics = caller.ndb.charcreate_data.get('motorics', 75)
    
    total = grit + resonance + intellect + motorics
    remaining = 300 - total
    
    text = f"""
|w╔════════════════════════════════════════════════════════════════╗
║  G.R.I.M. ATTRIBUTE DISTRIBUTION                               ║
╚════════════════════════════════════════════════════════════════╝|n

Name: |c{first_name} {last_name}|n
Sex: |c{sex.capitalize()}|n

Distribute |w300 points|n across your attributes (min 1, max 150 per stat):

|gGrit:|n      {grit:3d}  (Physical resilience, endurance, toughness)
|yResonance:|n {resonance:3d}  (Social awareness, empathy, influence)
|bIntellect:|n {intellect:3d}  (Mental acuity, reasoning, knowledge)
|mMotorics:|n {motorics:3d}  (Physical coordination, reflexes, dexterity)

|wTotal:|n {total}/300  |{'|gREMAINING:|n ' + str(remaining) if remaining >= 0 else '|rOVER BY:|n ' + str(abs(remaining))}

Commands:
  |wgrit <value>|n     - Set Grit
  |wresonance <value>|n - Set Resonance
  |winterllect <value>|n - Set Intellect
  |wmotorics <value>|n  - Set Motorics
  |wreset|n             - Reset to defaults (75 each)
  |wdone|n              - Finalize character (when total = 300)

|w>|n """
    
    if raw_string:
        args = raw_string.strip().lower().split()
        
        if not args:
            return "first_char_grim"
        
        command = args[0]
        
        # Reset command
        if command in ["reset", "r"]:
            caller.ndb.charcreate_data['grit'] = 75
            caller.ndb.charcreate_data['resonance'] = 75
            caller.ndb.charcreate_data['intellect'] = 75
            caller.ndb.charcreate_data['motorics'] = 75
            return "first_char_grim"
        
        # Done command
        if command in ["done", "d", "finish", "finalize"]:
            # Validate distribution
            is_valid, error = validate_grim_distribution(grit, resonance, intellect, motorics)
            if not is_valid:
                caller.msg(f"|r{error}|n")
                return "first_char_grim"
            return "first_char_confirm"
        
        # Stat assignment commands
        if len(args) < 2:
            caller.msg("|rUsage: <stat> <value>  (e.g., 'grit 100')|n")
            return "first_char_grim"
        
        try:
            value = int(args[1])
        except ValueError:
            caller.msg("|rValue must be a number.|n")
            return "first_char_grim"
        
        if value < 1 or value > 150:
            caller.msg("|rValue must be between 1 and 150.|n")
            return "first_char_grim"
        
        # Set the stat
        if command in ["grit", "g"]:
            caller.ndb.charcreate_data['grit'] = value
        elif command in ["resonance", "r", "res"]:
            caller.ndb.charcreate_data['resonance'] = value
        elif command in ["intellect", "i", "int"]:
            caller.ndb.charcreate_data['intellect'] = value
        elif command in ["motorics", "m", "mot"]:
            caller.ndb.charcreate_data['motorics'] = value
        else:
            caller.msg("|rUnknown stat. Use: grit, resonance, intellect, or motorics|n")
        
        return "first_char_grim"
    
    options = (
        {"key": "_default",
         "goto": "first_char_grim"},
    )
    
    return text, options


def first_char_confirm(caller, raw_string, **kwargs):
    """Final confirmation and character creation."""
    
    first_name = caller.ndb.charcreate_data.get('first_name', '')
    last_name = caller.ndb.charcreate_data.get('last_name', '')
    sex = caller.ndb.charcreate_data.get('sex', 'androgynous')
    grit = caller.ndb.charcreate_data.get('grit', 75)
    resonance = caller.ndb.charcreate_data.get('resonance', 75)
    intellect = caller.ndb.charcreate_data.get('intellect', 75)
    motorics = caller.ndb.charcreate_data.get('motorics', 75)
    
    text = f"""
|w╔════════════════════════════════════════════════════════════════╗
║  FINAL CONFIRMATION                                            ║
╚════════════════════════════════════════════════════════════════╝|n

|wName:|n |c{first_name} {last_name}|n
|wSex:|n |c{sex.capitalize()}|n

|wG.R.I.M. Attributes:|n
  |gGrit:|n      {grit:3d}
  |yResonance:|n {resonance:3d}
  |bIntellect:|n {intellect:3d}
  |mMotorics:|n {motorics:3d}

|wTotal:|n 300/300

|yOnce created, your name cannot be changed.|n
|yStats can be modified through gameplay.|n

Create this character?

|w[Y]|n Yes, finalize character
|w[N]|n No, go back to GRIM distribution

|w>|n """
    
    options = (
        {"key": ("y", "yes"),
         "goto": "first_char_finalize"},
        {"key": ("n", "no"),
         "goto": "first_char_grim"},
        {"key": "_default",
         "goto": "first_char_confirm"},
    )
    
    return text, options


def first_char_finalize(caller, raw_string, **kwargs):
    """Create the character and enter game."""
    
    from typeclasses.characters import Character
    
    # Get data
    first_name = caller.ndb.charcreate_data.get('first_name', '')
    last_name = caller.ndb.charcreate_data.get('last_name', '')
    full_name = f"{first_name} {last_name}"
    sex = caller.ndb.charcreate_data.get('sex', 'androgynous')
    grit = caller.ndb.charcreate_data.get('grit', 75)
    resonance = caller.ndb.charcreate_data.get('resonance', 75)
    intellect = caller.ndb.charcreate_data.get('intellect', 75)
    motorics = caller.ndb.charcreate_data.get('motorics', 75)
    
    # Get spawn location
    start_location = get_start_location()
    
    # Create character
    try:
        char = create_object(
            Character,
            key=full_name,
            location=start_location,
            home=start_location
        )
        
        # Set account
        char.db.account = caller
        caller.db._last_puppet = char
        
        # Set GRIM stats
        char.grit = grit
        char.resonance = resonance
        char.intellect = intellect
        char.motorics = motorics
        
        # Set sex
        char.sex = sex
        
        # Set defaults
        char.db.clone_generation = 1
        char.db.archived = False
        
        # Generate unique Stack ID
        import uuid
        char.db.stack_id = str(uuid.uuid4())
        char.db.original_creation = time.time()
        char.db.current_sleeve_birth = time.time()
        
        # Puppet the character
        caller.puppet_object(caller.sessions.all()[0], char)
        
        # Send welcome message
        char.msg("|g╔════════════════════════════════════════════════════════════════╗")
        char.msg("|g║  CONSCIOUSNESS UPLOAD COMPLETE                                 ║")
        char.msg("|g╚════════════════════════════════════════════════════════════════╝|n")
        char.msg("")
        char.msg(f"|wWelcome to Gelatinous Monster, |c{char.key}|w.|n")
        char.msg("")
        char.msg("|xThe static clears. You open your eyes.|n")
        char.msg("|xThe year is 198█. The broadcast continues.|n")
        char.msg("|xYou are here. You are real. You are... something.|n")
        char.msg("")
        char.msg("|yType |wlook|y to examine your surroundings.|n")
        char.msg("|yType |whelp|y for a list of commands.|n")
        char.msg("")
        
        # Clean up
        _cleanup_charcreate_ndb(caller)
        
        # Exit menu
        return None
        
    except Exception as e:
        # Error - show message and return to confirmation
        caller.msg(f"|rError creating character: {e}|n")
        from evennia.comms.models import ChannelDB
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"CHARCREATE_ERROR: {e}")
        except:
            pass
        return "first_char_confirm"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _cleanup_charcreate_ndb(caller):
    """Clean up character creation NDB data."""
    if hasattr(caller.ndb, 'charcreate_is_respawn'):
        delattr(caller.ndb, 'charcreate_is_respawn')
    if hasattr(caller.ndb, 'charcreate_old_character'):
        delattr(caller.ndb, 'charcreate_old_character')
    if hasattr(caller.ndb, 'charcreate_data'):
        delattr(caller.ndb, 'charcreate_data')
