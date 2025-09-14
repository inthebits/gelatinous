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
    
    # Appearance attributes - stored in db but no auto-creation for optional features
    # skintone is set via @skintone command and stored as db.skintone

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

# Health Points - REMOVED in Phase 3: Pure Medical System
    # Legacy HP system eliminated - health now managed entirely by medical system
    # Death/unconsciousness determined by organ functionality and medical conditions

# Character Placement Descriptions
    look_place = AttributeProperty("standing here.", category='description', autocreate=True)
    temp_place = AttributeProperty("", category='description', autocreate=True)
    override_place = AttributeProperty("", category='description', autocreate=True)

    def at_object_creation(self):
        """
        Called once, at creation, to set dynamic stats.
        """
        super().at_object_creation()

        # Initialize longdesc system with default anatomy
        from world.combat.constants import DEFAULT_LONGDESC_LOCATIONS
        if not self.longdesc:
            self.longdesc = DEFAULT_LONGDESC_LOCATIONS.copy()

        # Initialize medical system - replaces legacy HP system
        self._initialize_medical_state()

    def _initialize_medical_state(self):
        """Initialize the character's medical state."""
        from world.medical.utils import initialize_character_medical_state
        initialize_character_medical_state(self)

    @property
    def medical_state(self):
        """Get the character's medical state, loading from db if needed."""
        if not hasattr(self, '_medical_state') or self._medical_state is None:
            from world.medical.utils import load_medical_state
            load_medical_state(self)
        return self._medical_state
        
    @medical_state.setter
    def medical_state(self, value):
        """Set the character's medical state."""
        self._medical_state = value
        
    def save_medical_state(self):
        """Save medical state to database."""
        from world.medical.utils import save_medical_state
        save_medical_state(self)

# Mortality Management  
    def take_damage(self, amount, location="chest", injury_type="generic", target_organ=None):
        """
        Apply damage to a specific body location with injury type.
        
        This is the primary damage method using the pure medical system.
        Replaces the old dual HP/medical approach.
        
        Args:
            amount (int): Damage amount
            location (str): Body location (head, chest, left_arm, etc.)
            injury_type (str): Type of injury (cut, blunt, bullet, etc.)
            target_organ (str): If specified, target this specific organ
            
        Returns:
            bool: True if character died from this damage, False otherwise
        """
        if not isinstance(amount, int) or amount <= 0:
            return False

        # Apply anatomical damage through medical system
        from world.medical.utils import apply_anatomical_damage
        damage_results = apply_anatomical_damage(self, amount, location, injury_type, target_organ)
        
        # Save medical state after damage
        self.save_medical_state()
        
        # Debug broadcast damage application
        try:
            from world.combat.utils import debug_broadcast
            debug_broadcast(f"Applied {amount} {injury_type} damage to {self.key}'s {location}", 
                           "DAMAGE", "SUCCESS")
        except ImportError:
            pass  # debug_broadcast not available
        
        # Handle death/unconsciousness state changes
        died = self.is_dead()
        unconscious = self.is_unconscious()
        
        if died:
            self._handle_death()
        elif unconscious:
            self._handle_unconsciousness()
        
        # Return death status for combat system compatibility
        return died
    
    # Legacy method take_anatomical_damage removed - functionality merged into take_damage()
    
    def is_dead(self):
        """
        Returns True if character should be considered dead.
        
        Uses pure medical system - death from vital organ failure or blood loss.
        """
        try:
            medical_state = self.medical_state
            if medical_state:
                return medical_state.is_dead()
        except AttributeError:
            pass  # Medical system not available - character is alive
        
        return False
        
    def is_unconscious(self):
        """
        Returns True if character is unconscious.
        
        Uses medical system to determine unconsciousness from injuries,
        blood loss, or pain.
        """
        try:
            medical_state = self.medical_state
            if medical_state:
                return medical_state.is_unconscious()
        except AttributeError:
            pass  # Medical system not available
        return False

    def _handle_death(self):
        """
        Handle character death from medical injuries.
        
        Note: Death messaging is handled by the combat system to avoid duplicates.
        This method only handles the death state transition.
        """
        # No death messages here - combat system handles death announcements
        # to avoid duplicate "Character has died" messages
        
        # Optional: Debug broadcast for tracking
        try:
            from world.combat.utils import debug_broadcast
            debug_broadcast(f"{self.key} died from medical injuries", "MEDICAL", "DEATH")
        except ImportError:
            pass  # debug_broadcast not available
    
    def _handle_unconsciousness(self):
        """
        Handle character becoming unconscious from medical injuries.
        
        Provides unconsciousness messaging to character and room.
        Triggers removal from combat if currently fighting.
        """
        self.msg("|rYou collapse, unconscious from your injuries!|n")
        if self.location:
            self.location.msg_contents(
                f"|r{self.key} collapses, unconscious!|n",
                exclude=self
            )
        
        # Check if character is in combat and remove them
        combat_handler = getattr(self.ndb, "combat_handler", None)
        if combat_handler:
            try:
                combat_handler.remove_combatant(self)
                # Optional: Debug broadcast for tracking
                try:
                    from world.combat.utils import debug_broadcast
                    debug_broadcast(f"{self.key} removed from combat due to unconsciousness", "MEDICAL", "UNCONSCIOUS")
                except ImportError:
                    pass  # debug_broadcast not available
            except Exception as e:
                # Optional: Debug broadcast for tracking errors
                try:
                    from world.combat.utils import debug_broadcast
                    debug_broadcast(f"Error removing {self.key} from combat on unconsciousness: {e}", "MEDICAL", "ERROR")
                except ImportError:
                    pass  # debug_broadcast not available
        
        # Optional: Debug broadcast for tracking
        try:
            from world.combat.utils import debug_broadcast
            debug_broadcast(f"{self.key} became unconscious from medical injuries", "MEDICAL", "UNCONSCIOUS")
        except ImportError:
            pass  # debug_broadcast not available

    def debug_death_analysis(self):
        """
        Debug method to show detailed cause of death analysis.
        Returns comprehensive information about why character died or current vital status.
        """
        try:
            medical_state = self.medical_state
            if not medical_state:
                return "No medical state available"
            
            from world.medical.constants import BLOOD_LOSS_DEATH_THRESHOLD
            
            # Check vital organ capacities
            blood_pumping = medical_state.calculate_body_capacity("blood_pumping")
            breathing = medical_state.calculate_body_capacity("breathing") 
            digestion = medical_state.calculate_body_capacity("digestion")
            consciousness = medical_state.calculate_body_capacity("consciousness")
            
            # Check blood level
            blood_level = medical_state.blood_level
            blood_loss_fatal = blood_level <= (100.0 - BLOOD_LOSS_DEATH_THRESHOLD)
            
            # Build analysis
            analysis = [
                f"=== DEATH ANALYSIS FOR {self.key} ===",
                f"Blood Pumping Capacity: {blood_pumping:.1%} {'FATAL' if blood_pumping <= 0 else 'OK'}",
                f"Breathing Capacity: {breathing:.1%} {'FATAL' if breathing <= 0 else 'OK'}",
                f"Digestion Capacity: {digestion:.1%} {'FATAL' if digestion <= 0 else 'OK'}",
                f"Consciousness: {consciousness:.1%} {'UNCONSCIOUS' if consciousness < 0.3 else 'CONSCIOUS'}",
                f"Blood Level: {blood_level:.1f}% {'FATAL BLOOD LOSS' if blood_loss_fatal else 'OK'}",
                f"Pain Level: {medical_state.pain_level:.1f}",
                f"Overall Status: {'DEAD' if self.is_dead() else 'ALIVE'}"
            ]
            
            # If dead, identify primary cause
            if self.is_dead():
                causes = []
                if blood_pumping <= 0:
                    causes.append("HEART FAILURE")
                if breathing <= 0:
                    causes.append("RESPIRATORY FAILURE") 
                if digestion <= 0:
                    causes.append("LIVER FAILURE")
                if blood_loss_fatal:
                    causes.append("BLOOD LOSS")
                
                analysis.append(f"Primary Cause(s): {', '.join(causes)}")
            
            return "\n".join(analysis)
            
        except Exception as e:
            return f"Error in death analysis: {e}"
        
    def get_medical_status(self):
        """
        Get a detailed medical status report.
        
        Returns:
            str: Human-readable medical status
        """
        from world.medical.utils import get_medical_status_summary
        return get_medical_status_summary(self)
        
    def add_medical_condition(self, condition_type, location=None, severity="minor", **kwargs):
        """
        Add a medical condition to this character.
        
        Args:
            condition_type (str): Type of condition (bleeding, fracture, etc.)
            location (str, optional): Body location affected
            severity (str): Severity level
            **kwargs: Additional condition properties
            
        Returns:
            MedicalCondition: The added condition
        """
        condition = self.medical_state.add_condition(condition_type, location, severity, **kwargs)
        self.save_medical_state()
        return condition

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
        from evennia.comms.models import ChannelDB
        from world.combat.constants import SPLATTERCAST_CHANNEL
        
        # Prevent double death processing
        if hasattr(self, 'ndb') and getattr(self.ndb, 'death_processed', False):
            try:
                splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
                splattercast.msg(f"AT_DEATH_SKIP: {self.key} already processed death, skipping")
            except:
                pass
            return
            
        # Mark death as processed
        if not hasattr(self, 'ndb'):
            self.ndb = {}
        self.ndb.death_processed = True
        
        # Always show death analysis when character dies
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            death_analysis = self.debug_death_analysis()
            splattercast.msg(death_analysis)
        except Exception as e:
            # Fallback if splattercast channel not available
            pass
        
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
                # Location not covered - use character's longdesc if set with template variable processing
                if location in longdescs and longdescs[location]:
                    # Longdesc should have skintone applied
                    processed_desc = self._process_description_variables(longdescs[location], looker, force_third_person=True, apply_skintone=True)
                    
                    # Add wounds to this location if any exist
                    try:
                        from world.medical.wounds import append_wounds_to_longdesc
                        processed_desc = append_wounds_to_longdesc(processed_desc, self, location, looker)
                    except ImportError:
                        # Wound system not available, continue without wounds
                        pass
                    
                    descriptions.append((location, processed_desc))
                else:
                    # No longdesc for this location, but check for standalone wounds
                    try:
                        from world.medical.wounds import get_character_wounds
                        wounds = get_character_wounds(self)
                        location_wounds = [w for w in wounds if w['location'] == location]
                        
                        if location_wounds:
                            # Create standalone wound description for this location
                            from world.medical.wounds import get_wound_description
                            wound = location_wounds[0]  # Use first/most significant wound
                            wound_desc = get_wound_description(
                                injury_type=wound['injury_type'],
                                location=wound['location'],
                                severity=wound['severity'],
                                stage=wound['stage'],
                                organ=wound.get('organ'),
                                character=self
                            )
                            descriptions.append((location, wound_desc))
                    except ImportError:
                        # Wound system not available, continue without wounds
                        pass
        
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
                    # Extended location with longdesc - apply template variable processing and skintone
                    processed_desc = self._process_description_variables(longdescs[location], looker, force_third_person=True, apply_skintone=True)
                    
                    # Add wounds to this extended location if any exist
                    try:
                        from world.medical.wounds import append_wounds_to_longdesc
                        processed_desc = append_wounds_to_longdesc(processed_desc, self, location, looker)
                    except ImportError:
                        # Wound system not available, continue without wounds
                        pass
                    
                    descriptions.append((location, processed_desc))
                else:
                    # No longdesc for extended location, but check for standalone wounds
                    try:
                        from world.medical.wounds import get_character_wounds
                        wounds = get_character_wounds(self)
                        location_wounds = [w for w in wounds if w['location'] == location]
                        
                        if location_wounds:
                            # Create standalone wound description for this extended location
                            from world.medical.wounds import get_wound_description
                            wound = location_wounds[0]  # Use first/most significant wound
                            wound_desc = get_wound_description(
                                injury_type=wound['injury_type'],
                                location=wound['location'],
                                severity=wound['severity'],
                                stage=wound['stage'],
                                organ=wound.get('organ'),
                                character=self
                            )
                            descriptions.append((location, wound_desc))
                    except ImportError:
                        # Wound system not available, continue without wounds
                        pass
        
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
        Returns a clean character appearance with name, description, longdesc+clothing, and wielded items.
        
        Args:
            looker: Character doing the looking
            **kwargs: Additional parameters
            
        Returns:
            str: Complete character appearance in clean format
        """
        # Debug: Make sure this method is being called
        
        # Build appearance components
        parts = []
        
        # 1. Character name (header) + main description (no blank line between)
        name_and_desc = [self.get_display_name(looker)]
        if self.db.desc:
            # Initial description should NOT have skintone applied
            processed_desc = self._process_description_variables(self.db.desc, looker, force_third_person=True, apply_skintone=False)
            name_and_desc.append(processed_desc)
        
        parts.append('\n'.join(name_and_desc))
        
        # 2. Longdesc + clothing integration (uses automatic paragraph parsing)
        if self.longdesc is None:
            try:
                from world.combat.constants import DEFAULT_LONGDESC_LOCATIONS
                self.longdesc = DEFAULT_LONGDESC_LOCATIONS.copy()
            except ImportError:
                pass
        
        visible_body_descriptions = self._get_visible_body_descriptions(looker)
        if visible_body_descriptions:
            formatted_body_descriptions = self._format_longdescs_with_paragraphs(visible_body_descriptions)
            parts.append(formatted_body_descriptions)
        
        # 3. Wielded items section (using hands system)
        hands = self.attributes.get('hands', category='equipment') or {'left': None, 'right': None}
        wielded_items = [item for item in hands.values() if item is not None]
        
        if wielded_items:
            wielded_names = [obj.get_display_name(looker) for obj in wielded_items]
            if len(wielded_names) == 1:
                wielded_text = f"{self.get_display_name(looker)} is holding a {wielded_names[0]}."
            elif len(wielded_names) == 2:
                wielded_text = f"{self.get_display_name(looker)} is holding a {wielded_names[0]} and a {wielded_names[1]}."
            else:
                # Multiple items: "a item1, a item2, and a item3"
                wielded_with_articles = [f"a {name}" for name in wielded_names]
                wielded_text = f"{self.get_display_name(looker)} is holding {', '.join(wielded_with_articles[:-1])}, and {wielded_with_articles[-1]}."
            parts.append(wielded_text)
        else:
            # Show explicitly when hands are empty
            parts.append(f"{self.get_display_name(looker)} is holding nothing.")
        
        # 4. Staff-only comprehensive inventory (with explicit admin messaging)
        if looker.check_permstring("Builder"):
            all_contents = [obj for obj in self.contents if obj.location == self]
            if all_contents:
                content_names = [f"{obj.get_display_name(looker)} [{obj.dbref}]" for obj in all_contents]
                parts.append(f"|wWith your administrative visibility, you see:|n {', '.join(content_names)}")
        
        # Join all parts with appropriate spacing (blank lines between major sections)
        return '\n\n'.join(parts)

    def _process_description_variables(self, desc, looker, force_third_person=False, apply_skintone=False):
        """
        Process template variables in descriptions for perspective-aware text.
        
        Uses simple template variables like {their}, {they}, {name} similar to {color}.
        
        Args:
            desc (str): Description text with potential template variables
            looker (Character): Who is looking at this character
            force_third_person (bool): If True, always use 3rd person pronouns
            apply_skintone (bool): If True, apply skintone coloring (for longdescs only)
            
        Returns:
            str: Description with variables substituted
        """
        if not desc or not looker:
            return desc
            
        # Map of available template variables based on perspective
        is_self = (looker == self) and not force_third_person
        
        # Get pronoun information for this character
        gender_mapping = {
            'male': 'male',
            'female': 'female', 
            'neutral': 'plural',
            'nonbinary': 'plural',
            'other': 'plural'
        }
        
        character_gender = gender_mapping.get(self.gender, 'plural')
        
        # Simple template variable mapping (like {color})
        variables = {
            # Most common - possessive pronouns (lowercase)
            'their': 'your' if is_self else self._get_pronoun('possessive', character_gender),
            
            # Subject and object pronouns (lowercase)
            'they': 'you' if is_self else self._get_pronoun('subject', character_gender),
            'them': 'you' if is_self else self._get_pronoun('object', character_gender),
            
            # Possessive absolute and reflexive (less common, lowercase)
            'theirs': 'yours' if is_self else self._get_pronoun('possessive_absolute', character_gender),
            'themselves': 'yourself' if is_self else self._get_pronoun('reflexive', character_gender),
            'themself': 'yourself' if is_self else self._get_pronoun('reflexive', character_gender),  # Alternative form
            
            # Capitalized versions for sentence starts
            'Their': 'Your' if is_self else self._get_pronoun('possessive', character_gender).capitalize(),
            'They': 'You' if is_self else self._get_pronoun('subject', character_gender).capitalize(),
            'Them': 'You' if is_self else self._get_pronoun('object', character_gender).capitalize(),
            'Theirs': 'Yours' if is_self else self._get_pronoun('possessive_absolute', character_gender).capitalize(),
            'Themselves': 'Yourself' if is_self else self._get_pronoun('reflexive', character_gender).capitalize(),
            'Themself': 'Yourself' if is_self else self._get_pronoun('reflexive', character_gender).capitalize(),  # Alternative form
            
            # Character names
            'name': 'you' if is_self else self.get_display_name(looker),
            "name's": 'your' if is_self else f"{self.get_display_name(looker)}'s",
            
            # Legacy support for existing verbose names (can be removed later)
            'observer_pronoun_possessive': 'your' if is_self else self._get_pronoun('possessive', character_gender),
            'observer_pronoun_subject': 'you' if is_self else self._get_pronoun('subject', character_gender),
            'observer_pronoun_object': 'you' if is_self else self._get_pronoun('object', character_gender),
            'observer_pronoun_possessive_absolute': 'yours' if is_self else self._get_pronoun('possessive_absolute', character_gender),
            'observer_pronoun_reflexive': 'yourself' if is_self else self._get_pronoun('reflexive', character_gender),
            'observer_character_name': 'you' if is_self else self.get_display_name(looker),
            'observer_character_name_possessive': 'your' if is_self else f"{self.get_display_name(looker)}'s"
        }
        
        # Substitute all variables in the description
        try:
            processed_desc = desc.format(**variables)
        except (KeyError, ValueError) as e:
            # If there are template errors, use original description and log the issue
            processed_desc = desc
            # Debug: Log the error (remove this later)
            print(f"Template processing error in _process_description_variables: {e}")
            print(f"Description: {desc[:100]}...")  # First 100 chars
            print(f"Variables available: {list(variables.keys())}")
            
        # Apply skintone coloring only if requested (for longdescs only)
        if apply_skintone:
            skintone = getattr(self.db, 'skintone', None)
            if skintone:
                from world.combat.constants import SKINTONE_PALETTE
                color_code = SKINTONE_PALETTE.get(skintone)
                if color_code:
                    # Wrap the entire processed description in the skintone color
                    # Reset color at end to prevent bleeding
                    processed_desc = f"{color_code}{processed_desc}|n"
                
        return processed_desc
    
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
