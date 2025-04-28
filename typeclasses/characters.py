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