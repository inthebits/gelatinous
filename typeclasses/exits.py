"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit
from evennia.comms.models import ChannelDB

from .objects import ObjectParent


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they define the `destination` property and override some hooks
    and methods to represent the exits.
    """

    def at_before_traverse(self, traversing_object):
        """
        Prevent movement if the traversing object is in combat.
        """
        if getattr(traversing_object.ndb, "combat_handler", None):
            traversing_object.msg("|rYou can't leave while in combat! Try to flee instead.|n")
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"{traversing_object.key} tried to move via exit '{self.key}' while in combat.")
            return False  # Block movement
        return True  # Allow movement
