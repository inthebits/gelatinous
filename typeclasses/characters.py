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

    def wield_item(self, item, hand="right"):
        hands = self.hands
        if hand not in hands:
            return f"You don't have a {hand} hand."

        if hands[hand]:
            return f"You're already holding something in your {hand}."

        if item.location != self:
            return "You're not carrying that item."

        hands[hand] = item
        item.location = None
        self.hands = hands  # Save updated hands dict
        return f"You wield {item.key} in your {hand} hand."
    
    def unwield_item(self, hand="right"):
        hands = self.hands
        item = hands.get(hand, None)

        if not item:
            return f"You're not holding anything in your {hand} hand."

        item.location = self
        hands[hand] = None
        self.hands = hands
        return f"You unwield {item.key} from your {hand} hand."
    
    def list_held_items(self):
        hands = self.hands
        lines = []
        for hand, item in hands.items():
            if item:
                lines.append(f"{hand.title()} Hand: {item.key}")
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
            
            stopped_aiming_message_parts.append(f"at {old_aim_target_char.get_display_name(self)}")

        # Clear directional aim
        old_aim_direction = getattr(self.ndb, "aiming_direction", None)
        if old_aim_direction:
            action_taken = True
            del self.ndb.aiming_direction
            log_message_parts.append(f"stopped aiming {old_aim_direction}")
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
