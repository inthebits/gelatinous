"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import AttributeProperty
from evennia.comms.models import ChannelDB  # Ensure this is imported

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    In this instance, we are also adding the G.R.I.M. attributes using AttributeProperty.
    """
    
# G.R.I.M. Attributes
    # Grit, Resonance, Intellect, Motorics
    grit = AttributeProperty(1, category='stat', autocreate=True)
    resonance = AttributeProperty(1, category='stat', autocreate=True)
    intellect = AttributeProperty(1, category='stat', autocreate=True)
    motorics = AttributeProperty(1, category='stat', autocreate=True)
    sex = AttributeProperty("ambiguous", category="biology", autocreate=True)

    @property
    def gender(self):
        """
        Maps the existing sex attribute to Evennia's pronoun system.
        Returns a string suitable for use with $pron() functions.
        
        Maps:
        - "male", "man", "masculine" -> "male"
        - "female", "woman", "feminine" -> "female"  
        - "ambiguous", "neutral", "non-binary", "they" -> "neutral"
        - default -> "neutral"
        """
        sex_value = (self.sex or "ambiguous").lower().strip()
        
        # Male mappings
        if sex_value in ("male", "man", "masculine", "m"):
            return "male"
        # Female mappings
        elif sex_value in ("female", "woman", "feminine", "f"):
            return "female"
        # Neutral/ambiguous mappings (default)
        else:
            return "neutral"

# Possession Identifier
    def is_possessed(self):
        """
        Returns True if this character is currently puppeted by a player session.
        """
        return bool(self.sessions.all())

# Health Points
    hp = AttributeProperty(10, category='health', autocreate=True)
    hp_max = AttributeProperty(10, category='health', autocreate=True)

# Character Placement Descriptions
    look_place = AttributeProperty("standing here.", category='description', autocreate=True)
    temp_place = AttributeProperty("", category='description', autocreate=True)
    override_place = AttributeProperty("", category='description', autocreate=True)

    def at_object_creation(self):
        """
        Called once, at creation, to set dynamic stats.
        """
        super().at_object_creation()

        # Set dynamic hp_max based on grit
        grit_value = self.grit or 1
        self.hp_max = 10 + (grit_value * 2)
        self.hp = self.hp_max  # Start at full health

        # Initialize longdesc system with default anatomy
        from world.combat.constants import DEFAULT_LONGDESC_LOCATIONS
        if not self.longdesc:
            self.longdesc = DEFAULT_LONGDESC_LOCATIONS.copy()

# Mortality Management  
    def take_damage(self, amount):
        """
        Reduces current HP by `amount`.
        Triggers death if HP falls to zero or below.
        
        Returns True if the character died from this damage.
        """
        if not isinstance(amount, int) or amount <= 0:
            return False  # Ignore bad inputs

        self.hp = max(self.hp - amount, 0)
        # This is where descriptive indicator of how damaged you are would go.
        # self.msg(f"|rYou take {amount} damage!|n")

        # Return death status but don't trigger death processing yet
        # This allows the caller to handle death at the appropriate time
        return self.is_dead()

    def heal(self, amount):
        """
        Restores HP by `amount`, without exceeding hp_max.
        """
        if not isinstance(amount, int) or amount <= 0:
            return  # Ignore bad inputs

        new_hp = min(self.hp + amount, self.hp_max)
        healed = new_hp - self.hp
        self.hp = new_hp

        self.msg(f"|gYou recover {healed} health.|n")

    def is_dead(self):
        """
        Returns True if HP is 0 or lower.
        """
        return self.hp <= 0

    def get_search_candidates(self, searchdata, **kwargs):
        """
        Override to include aimed-at room contents when aiming.
        
        This is called by the search method to determine what objects
        are available to search through. When aiming at a direction,
        this includes both current room and aimed-room contents.
        
        Args:
            searchdata (str): The search criterion
            **kwargs: Same as passed to search method
            
        Returns:
            list: Objects that can be searched through
        """
        # Get the default candidates first
        candidates = super().get_search_candidates(searchdata, **kwargs)
        
        # Don't interfere with self-lookup or basic character functionality
        # Only enhance when specifically aiming at a direction
        aiming_direction = getattr(self.ndb, 'aiming_direction', None) if hasattr(self, 'ndb') else None
        
        if (candidates is not None and 
            aiming_direction and 
            self.location and
            hasattr(self.location, 'search_for_target')):  # Make sure the room supports this
            try:
                # Use the room's search_for_target method to get unified candidates
                # This leverages the existing vetted aiming logic
                unified_candidates = self.location.search_for_target(
                    self, searchdata, return_candidates_only=True
                )
                if unified_candidates:
                    # Use the unified candidates instead of default ones
                    # This maintains ordinal support and all existing logic
                    candidates = unified_candidates
            except (AttributeError, TypeError):
                # If anything goes wrong, fall back to default candidates
                # This ensures we never break normal searching
                pass
        
        return candidates

    def at_death(self):
        """
        Handles what happens when this character dies.
        Override this for player-specific or mob-specific death logic.
        """
        from .curtain_of_death import show_death_curtain
        
        # Start the death curtain animation
        show_death_curtain(self)
        
        # You can override this to handle possession, corpse creation, etc.
        # PERMANENT-DEATH. DO NOT ENABLE YET. self.delete()

    # MR. HANDS SYSTEM
    # Persistent hand slots: supports dynamic anatomy eventually
    hands = AttributeProperty(
        {"left": None, "right": None},
        category="equipment",
        autocreate=True
    )

    # LONGDESC SYSTEM
    # Detailed body part descriptions: anatomy source of truth
    longdesc = AttributeProperty(
        None,  # Will be set to copy of DEFAULT_LONGDESC_LOCATIONS in at_object_creation
        category="appearance",
        autocreate=True
    )
    
    # CLOTHING SYSTEM
    # Storage for worn clothing items organized by body location
    worn_items = AttributeProperty({}, category="clothing", autocreate=True)
    # Structure: {
    #     "chest": [jacket_obj, shirt_obj],  # Ordered by layer (outer first)
    #     "head": [hat_obj],
    #     "left_hand": [glove_obj],
    #     "right_hand": [glove_obj]
    # }

    def wield_item(self, item, hand="right"):
        hands = self.hands
        if hand not in hands:
            return f"You don't have a {hand} hand."

        if hands[hand]:
            return f"You're already holding something in your {hand}."

        if item.location != self:
            return "You're not carrying that item."
        
        # Check if item is currently worn
        if hasattr(self, 'is_item_worn') and self.is_item_worn(item):
            return "You can't wield something you're wearing. Remove it first."

        hands[hand] = item
        item.location = None
        self.hands = hands  # Save updated hands dict
        return f"You wield {item.get_display_name(self)} in your {hand} hand."
    
    def unwield_item(self, hand="right"):
        hands = self.hands
        item = hands.get(hand, None)

        if not item:
            return f"You're not holding anything in your {hand} hand."

        item.location = self
        hands[hand] = None
        self.hands = hands
        return f"You unwield {item.get_display_name(self)} from your {hand} hand."
    
    def list_held_items(self):
        hands = self.hands
        lines = []
        for hand, item in hands.items():
            if item:
                lines.append(f"{hand.title()} Hand: {item.get_display_name(self)}")
            else:
                lines.append(f"{hand.title()} Hand: (empty)")
        return lines

    def clear_aim_state(self, reason_for_clearing=""):
        """
        Clears any current aiming state (character or direction) for this character.
        Provides feedback to the character and any previously aimed-at target.

        Args:
            reason_for_clearing (str, optional): A short phrase describing why aim is cleared,
                                                 e.g., "as you move", "as you stop aiming".
        Returns:
            bool: True if an aim state was actually cleared, False otherwise.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        stopped_aiming_message_parts = []
        log_message_parts = []
        action_taken = False

        # Clear character-specific aim
        old_aim_target_char = getattr(self.ndb, "aiming_at", None)
        if old_aim_target_char:
            action_taken = True
            del self.ndb.aiming_at
            log_message_parts.append(f"stopped aiming at {old_aim_target_char.key}")
            
            if hasattr(old_aim_target_char, "ndb") and getattr(old_aim_target_char.ndb, "aimed_at_by", None) == self:
                del old_aim_target_char.ndb.aimed_at_by
                old_aim_target_char.msg(f"{self.get_display_name(old_aim_target_char)} is no longer aiming directly at you.")
            
            # Clear override_place and handle mutual showdown cleanup
            self._clear_aim_override_place_on_aim_clear(old_aim_target_char)
            
            stopped_aiming_message_parts.append(f"at {old_aim_target_char.get_display_name(self)}")

        # Clear directional aim
        old_aim_direction = getattr(self.ndb, "aiming_direction", None)
        if old_aim_direction:
            action_taken = True
            del self.ndb.aiming_direction
            log_message_parts.append(f"stopped aiming {old_aim_direction}")
            
            # Clear directional aim override_place
            self.override_place = ""
            
            stopped_aiming_message_parts.append(f"{old_aim_direction}")

        if action_taken:
            # Construct details of what was being aimed at for the player message
            aim_details_for_msg = ""
            if stopped_aiming_message_parts:
                # stopped_aiming_message_parts contains things like "at {target_name}" or "{direction}"
                # Example: " at YourTarget", " east", or " at YourTarget, east"
                aim_details_for_msg = f" {', '.join(stopped_aiming_message_parts)}"

            # Base player message
            player_msg_text = f"You stop aiming{aim_details_for_msg}"

            # Append the reason, but only if it's not the default "as you stop aiming"
            # (which is implicit when the player uses the 'stop aiming' command)
            if reason_for_clearing and reason_for_clearing != "as you stop aiming":
                player_msg_text += f" {reason_for_clearing.strip()}"
            
            player_msg_text += "." # Add a period at the end.
            self.msg(player_msg_text)

            # Construct log message (this part's logic for suffix remains the same)
            log_reason_suffix = ""
            if reason_for_clearing:
                log_reason_suffix = f" ({reason_for_clearing.strip()})" # Log always includes the reason clearly
            splattercast.msg(f"AIM_CLEAR: {self.key} {', '.join(log_message_parts)}{log_reason_suffix}.")
        
        return action_taken

    def _clear_aim_override_place_on_aim_clear(self, target):
        """
        Clear override_place for aiming when clearing aim state, handling mutual showdown cleanup.
        
        Args:
            target: The character that was being aimed at
        """
        # Check if they were in a mutual showdown
        if (hasattr(self, 'override_place') and hasattr(target, 'override_place') and
            self.override_place == "locked in a deadly showdown." and 
            target.override_place == "locked in a deadly showdown."):
            # They were in a showdown - clear aimer's place, check if target should revert to normal aiming
            self.override_place = ""
            
            # If target is still aiming at aimer, revert them to normal aiming
            target_still_aiming = getattr(target.ndb, "aiming_at", None)
            if target_still_aiming == self:
                target.override_place = f"aiming carefully at {self.key}."
            else:
                # Target isn't aiming at anyone, clear their place too
                target.override_place = ""

    # ===================================================================
    # CLOTHING SYSTEM METHODS
    # ===================================================================
    
    def wear_item(self, item):
        """Wear a clothing item, handling layer conflicts and coverage"""
        # Validate item is wearable
        if not item.is_wearable():
            return False, "That item can't be worn."
        
        # Validate item is in inventory
        if item.location != self:
            return False, "You're not carrying that item."
        
        # Auto-unwield if currently held
        hands = getattr(self, 'hands', {})
        for hand, held_item in hands.items():
            if held_item == item:
                hands[hand] = None
                break
        
        # Get item's current coverage (accounting for style states)
        item_coverage = item.get_current_coverage()
        
        # Check for layer conflicts and build worn_items structure
        if not self.worn_items:
            self.worn_items = {}
        
        for location in item_coverage:
            if location not in self.worn_items:
                self.worn_items[location] = []
            
            # Add item to location, maintaining layer order (outer first)
            location_items = self.worn_items[location]
            
            # Find insertion point based on layer
            insert_index = 0
            for i, worn_item in enumerate(location_items):
                if item.layer <= worn_item.layer:
                    insert_index = i + 1
                else:
                    break
            
            location_items.insert(insert_index, item)
        
        return True, f"You put on {item.key}."
    
    def remove_item(self, item):
        """Remove worn clothing item"""
        # Validate item is worn
        if not self.is_item_worn(item):
            return False, "You're not wearing that item."
        
        # Remove from all worn_items locations
        if self.worn_items:
            for location, items in self.worn_items.items():
                if item in items:
                    items.remove(item)
                    # Clean up empty lists
                    if not items:
                        del self.worn_items[location]
        
        return True, f"You remove {item.key}."
    
    def is_item_worn(self, item):
        """Check if a specific item is currently worn"""
        if not self.worn_items:
            return False
        
        for items in self.worn_items.values():
            if item in items:
                return True
        return False
    
    def get_worn_items(self, location=None):
        """Get worn items, optionally filtered by location"""
        if not self.worn_items:
            return []
        
        if location:
            return self.worn_items.get(location, [])
        
        # Return all worn items (deduplicated since items can cover multiple locations)
        seen_items = set()
        all_items = []
        for items in self.worn_items.values():
            for item in items:
                if item not in seen_items:
                    seen_items.add(item)
                    all_items.append(item)
        return all_items
    
    def is_location_covered(self, location):
        """Check if body location is covered by clothing"""
        if not self.worn_items:
            return False
        
        return bool(self.worn_items.get(location, []))
    
    def get_coverage_description(self, location):
        """Get clothing description for covered location"""
        if not self.worn_items or location not in self.worn_items:
            return None
        
        # Get outermost (first) item for this location
        items = self.worn_items[location]
        if not items:
            return None
        
        outermost_item = items[0]
        return outermost_item.get_current_worn_desc()
    
    def _build_clothing_coverage_map(self):
        """Map each body location to outermost covering clothing item."""
        coverage = {}
        if not self.worn_items:
            return coverage
        
        for location, items in self.worn_items.items():
            if items:
                # First item is outermost due to layer ordering
                coverage[location] = items[0]
        
        return coverage

    # ===================================================================
    # LONGDESC APPEARANCE SYSTEM
    # ===================================================================

    def get_longdesc_appearance(self, looker=None, **kwargs):
        """
        Builds and returns the character's longdesc appearance.
        
        Returns:
            str: Formatted appearance with base description + longdescs
        """
        # Get base description
        base_desc = self.db.desc or ""
        
        # Get visible body descriptions (longdesc + clothing integration)
        visible_body_descriptions = self._get_visible_body_descriptions(looker)
        
        if not visible_body_descriptions:
            return base_desc
        
        # Combine with smart paragraph formatting
        formatted_body_descriptions = self._format_longdescs_with_paragraphs(visible_body_descriptions)
        
        # Combine base description with body descriptions
        if base_desc:
            return f"{base_desc}\n\n{formatted_body_descriptions}"
        else:
            return formatted_body_descriptions

    def _get_visible_body_descriptions(self, looker=None):
        """
        Get all visible descriptions, integrating clothing with existing longdesc system.
        
        Args:
            looker: Character looking (for future permission checks)
            
        Returns:
            list: List of (location, description) tuples in anatomical order
        """
        from world.combat.constants import ANATOMICAL_DISPLAY_ORDER
        
        descriptions = []
        coverage_map = self._build_clothing_coverage_map()
        longdescs = self.longdesc or {}
        
        # Track which clothing items we've already added to avoid duplicates
        added_clothing_items = set()
        
        # Process in anatomical order
        for location in ANATOMICAL_DISPLAY_ORDER:
            if location in coverage_map:
                # Location covered by clothing - use outermost item's current worn_desc
                clothing_item = coverage_map[location]
                
                # Only add each clothing item once, regardless of how many locations it covers
                if clothing_item not in added_clothing_items:
                    # Use new method with $pron() processing and color integration
                    desc = clothing_item.get_current_worn_desc_with_perspective(looker, self)
                    if desc:
                        descriptions.append((location, desc))
                        added_clothing_items.add(clothing_item)
            else:
                # Location not covered - use character's longdesc if set
                if location in longdescs and longdescs[location]:
                    descriptions.append((location, longdescs[location]))
        
        # Add any extended anatomy not in default order (clothing or longdesc)
        all_locations = set(longdescs.keys()) | set(coverage_map.keys())
        for location in all_locations:
            if location not in ANATOMICAL_DISPLAY_ORDER:
                if location in coverage_map:
                    # Extended location with clothing
                    clothing_item = coverage_map[location]
                    if clothing_item not in added_clothing_items:
                        # Use new method with $pron() processing and color integration
                        desc = clothing_item.get_current_worn_desc_with_perspective(looker, self)
                        if desc:
                            descriptions.append((location, desc))
                            added_clothing_items.add(clothing_item)
                elif location in longdescs and longdescs[location]:
                    # Extended location with longdesc
                    descriptions.append((location, longdescs[location]))
        
        return descriptions

    def _format_longdescs_with_paragraphs(self, longdesc_list):
        """
        Formats longdesc descriptions with smart paragraph breaks.
        
        Args:
            longdesc_list: List of (location, description) tuples
            
        Returns:
            str: Formatted description with paragraph breaks
        """
        from world.combat.constants import (
            PARAGRAPH_BREAK_THRESHOLD, 
            ANATOMICAL_REGIONS,
            REGION_BREAK_PRIORITY
        )
        
        if not longdesc_list:
            return ""
        
        paragraphs = []
        current_paragraph = []
        current_char_count = 0
        current_region = None
        
        for location, description in longdesc_list:
            # Determine which anatomical region this location belongs to
            location_region = self._get_anatomical_region(location)
            
            # Check if we should break for a new paragraph
            should_break = False
            
            if REGION_BREAK_PRIORITY and current_region and location_region != current_region:
                # Region changed - check if we should break
                if current_char_count >= PARAGRAPH_BREAK_THRESHOLD * 0.7:  # 70% threshold for region breaks
                    should_break = True
            elif current_char_count + len(description) > PARAGRAPH_BREAK_THRESHOLD:
                # Would exceed threshold - break now
                should_break = True
            
            if should_break and current_paragraph:
                # Finish current paragraph and start new one
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []
                current_char_count = 0
            
            # Add description to current paragraph
            current_paragraph.append(description)
            current_char_count += len(description) + 1  # +1 for space
            current_region = location_region
        
        # Add final paragraph
        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
        
        return "\n\n".join(paragraphs)

    def _get_anatomical_region(self, location):
        """
        Determines which anatomical region a location belongs to.
        
        Args:
            location: Body location string
            
        Returns:
            str: Region name or 'extended' for non-standard anatomy
        """
        from world.combat.constants import ANATOMICAL_REGIONS
        
        for region_name, locations in ANATOMICAL_REGIONS.items():
            if location in locations:
                return region_name
        return "extended"

    def has_location(self, location):
        """
        Checks if this character has a specific body location.
        
        Args:
            location: Body location to check
            
        Returns:
            bool: True if character has this location
        """
        longdescs = self.longdesc or {}
        return location in longdescs

    def get_available_locations(self):
        """
        Gets list of all body locations this character has.
        
        Returns:
            list: List of available body location names
        """
        longdescs = self.longdesc or {}
        return list(longdescs.keys())

    def set_longdesc(self, location, description):
        """
        Sets a longdesc for a specific location.
        
        Args:
            location: Body location
            description: Description text (None to clear)
            
        Returns:
            bool: True if successful, False if location invalid
        """
        if not self.has_location(location):
            return False
        
        longdescs = self.longdesc or {}
        longdescs[location] = description
        self.longdesc = longdescs
        return True

    def get_longdesc(self, location):
        """
        Gets longdesc for a specific location.
        
        Args:
            location: Body location
            
        Returns:
            str or None: Description text or None if unset/invalid
        """
        if not self.has_location(location):
            return None
        
        longdescs = self.longdesc or {}
        return longdescs.get(location)

    def return_appearance(self, looker, **kwargs):
        """
        This method is called when someone looks at this character.
        Integrates longdesc system with Evennia's look command.
        
        Args:
            looker: Character doing the looking
            **kwargs: Additional parameters
            
        Returns:
            str: Complete character appearance with longdescs
        """
        # Get Evennia's default character appearance first
        # This handles all the built-in functionality like search resolution, permissions, etc.
        default_appearance = super().return_appearance(looker, **kwargs)
        
        # If we don't have longdesc initialized or available, just return default
        if self.longdesc is None:
            try:
                from world.combat.constants import DEFAULT_LONGDESC_LOCATIONS
                self.longdesc = DEFAULT_LONGDESC_LOCATIONS.copy()
            except ImportError:
                return default_appearance
        
        # Get visible body descriptions (longdesc + clothing integration)
        visible_body_descriptions = self._get_visible_body_descriptions(looker)
        
        if not visible_body_descriptions:
            # No body descriptions to show, return default
            return default_appearance
        
        # Split default appearance to extract header and description parts
        lines = default_appearance.split('\n')
        if not lines:
            return default_appearance
            
        # First line is typically the character name/header
        header = lines[0]
        
        # Everything after the first line is the description
        base_desc = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        # Format body descriptions with smart paragraph breaks
        formatted_body_descriptions = self._format_longdescs_with_paragraphs(visible_body_descriptions)
        
        # Combine: header + base_desc + body descriptions
        if base_desc:
            # Process template variables for perspective-aware descriptions
            processed_base_desc = self._process_description_variables(base_desc, looker)
            return f"{header}\n{processed_base_desc}\n\n{formatted_body_descriptions}"
        else:
            return f"{header}\n{formatted_body_descriptions}"

    def _process_description_variables(self, desc, looker):
        """
        Process template variables in descriptions for perspective-aware text.
        
        This enables template variables like {observer_pronoun_possessive} in 
        character descriptions that get substituted based on who's looking.
        
        Args:
            desc (str): Description text with potential template variables
            looker (Character): Who is looking at this character
            
        Returns:
            str: Description with variables substituted
        """
        if not desc or not looker:
            return desc
            
        # Map of available template variables based on perspective
        is_self = (looker == self)
        
        # Get pronoun information for this character
        gender_mapping = {
            'male': 'male',
            'female': 'female', 
            'neutral': 'plural',
            'nonbinary': 'plural',
            'other': 'plural'
        }
        
        character_gender = gender_mapping.get(self.gender, 'plural')
        
        # Template variable mapping
        variables = {
            # Subject pronouns: he/she/they (when looking at others) or "you" (when looking at self)
            'observer_pronoun_subject': 'you' if is_self else self._get_pronoun('subject', character_gender),
            
            # Object pronouns: him/her/them (when looking at others) or "you" (when looking at self)
            'observer_pronoun_object': 'you' if is_self else self._get_pronoun('object', character_gender),
            
            # Possessive pronouns: his/her/their (when looking at others) or "your" (when looking at self)  
            'observer_pronoun_possessive': 'your' if is_self else self._get_pronoun('possessive', character_gender),
            
            # Possessive absolute: his/hers/theirs (when looking at others) or "yours" (when looking at self)
            'observer_pronoun_possessive_absolute': 'yours' if is_self else self._get_pronoun('possessive_absolute', character_gender),
            
            # Reflexive: himself/herself/themselves (when looking at others) or "yourself" (when looking at self)
            'observer_pronoun_reflexive': 'yourself' if is_self else self._get_pronoun('reflexive', character_gender),
            
            # Character name (use "you" when looking at self, otherwise character name)
            'observer_character_name': 'you' if is_self else self.get_display_name(looker),
            
            # Character name possessive (use "your" when looking at self, otherwise "Alice's")
            'observer_character_name_possessive': 'your' if is_self else f"{self.get_display_name(looker)}'s"
        }
        
        # Substitute all variables in the description
        try:
            return desc.format(**variables)
        except (KeyError, ValueError):
            # If there are template errors, return original description
            return desc
    
    def _get_pronoun(self, pronoun_type, gender):
        """
        Get specific pronoun based on gender and type.
        
        Args:
            pronoun_type (str): Type of pronoun (subject, object, possessive, etc.)
            gender (str): Gender identifier (male, female, plural)
            
        Returns:
            str: Appropriate pronoun
        """
        pronouns = {
            'male': {
                'subject': 'he',
                'object': 'him', 
                'possessive': 'his',
                'possessive_absolute': 'his',
                'reflexive': 'himself'
            },
            'female': {
                'subject': 'she',
                'object': 'her',
                'possessive': 'her', 
                'possessive_absolute': 'hers',
                'reflexive': 'herself'
            },
            'plural': {  # Used for they/them, nonbinary, neutral, other
                'subject': 'they',
                'object': 'them',
                'possessive': 'their',
                'possessive_absolute': 'theirs', 
                'reflexive': 'themselves'
            }
        }
        
        return pronouns.get(gender, pronouns['plural']).get(pronoun_type, 'they')
