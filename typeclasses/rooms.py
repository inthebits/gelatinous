"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia.objects.objects import DefaultRoom
from world.combat.constants import NDB_FLYING_OBJECTS

from .objects import ObjectParent


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Enhanced to show flying objects during throw mechanics.
        """
        # Get the base description from the parent class
        appearance = super().return_appearance(looker, **kwargs)
        
        # Add flying objects if any exist
        flying_objects = getattr(self.ndb, NDB_FLYING_OBJECTS, [])
        if flying_objects:
            flying_desc = []
            for obj in flying_objects:
                flying_desc.append(f"|y{obj.key} is flying through the air|n")
            
            if flying_desc:
                # Add flying objects section to room description
                appearance += "\n\n" + "\n".join(flying_desc)
        
        return appearance
