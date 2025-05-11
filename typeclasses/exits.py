"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit
from evennia.comms.models import ChannelDB


from .objects import ObjectParent

class Exit(DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they define the `destination` property and override some hooks
    and methods to represent the exits.
    """

    def at_object_creation(self):
        super().at_object_creation()
        # Add abbreviation aliases for cardinal directions TEST
        cardinal_aliases = {
            "north": "n",
            "south": "s",
            "east": "e",
            "west": "w",
            "northeast": "ne",
            "northwest": "nw",
            "southeast": "se",
            "southwest": "sw",
            "up": "u",
            "down": "d",
            "in": "in",
            "out": "out"
        }
        alias = cardinal_aliases.get(self.key.lower())
        if alias and alias not in self.aliases.all():
            self.aliases.add(alias)

    def at_traverse(self, traversing_object, target_location):
        traversing_object.msg("DEBUG: at_traverse called on exit.")
        if getattr(traversing_object.ndb, "combat_handler", None):
            traversing_object.msg("|rYou can't leave while in combat! Try to flee instead.|n")
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"{traversing_object.key} tried to move via exit '{self.key}' while in combat.")
            return  # Block movement by not calling super()
        super().at_traverse(traversing_object, target_location)
