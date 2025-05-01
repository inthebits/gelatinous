"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import AttributeProperty

from .objects import ObjectParent
from .deathscroll import DEATH_SCROLL


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

# Posession
# Possession state
    def is_possessed(self):
        """
        Returns True if a player is currently controlling this body.
        """
        return bool(self.sessions.all())




# Health Points
    hp = AttributeProperty(10, category='health', autocreate=True)
    hp_max = AttributeProperty(10, category='health', autocreate=True)

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
        """
        if not isinstance(amount, int) or amount <= 0:
            return  # Ignore bad inputs

        self.hp = max(self.hp - amount, 0)
        self.msg(f"|rYou take {amount} damage!|n")

        if self.is_dead():
            self.at_death()

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
        location = self.location
        if location:
            location.msg_contents(f"|r{self.key} collapses into inert flesh.|n")
        self.msg("|rYou feel your consciousness unravel...|n")
        # You can override this to handle possession, corpse creation, etc.
        # PERMANENT-DEATH. DO NOT ENABLE YET. self.delete()
        for line in DEATH_SCROLL:
            self.msg(f"|r{line}|n")
