"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit
from evennia.comms.models import ChannelDB
from world.combathandler import get_or_create_combat 


from .objects import ObjectParent

class Exit(DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they define the `destination` property and override some hooks
    and methods to represent the exits.
    """

    def at_object_creation(self):
        super().at_object_creation()
        # Add abbreviation aliases for cardinal directions
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
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        handler = getattr(traversing_object.ndb, "combat_handler", None)

        if handler:
            # Character is in combat
            char_entry_in_handler = next((e for e in handler.db.combatants if e["char"] == traversing_object), None)

            if not char_entry_in_handler:
                # This case should ideally not be reached if ndb.combat_handler is properly managed.
                splattercast.msg(f"ERROR: {traversing_object.key} has ndb.combat_handler but no entry in handler {handler.key}. Allowing move as non-combatant.")
                super().at_traverse(traversing_object, target_location)
                return

            # Check drag conditions
            grappled_victim_obj = char_entry_in_handler.get("grappling")
            is_yielding = char_entry_in_handler.get("is_yielding")
            
            is_targeted_by_others_not_victim = False
            if handler.db.combatants:
                for entry in handler.db.combatants:
                    # Check if this entry is targeting the traversing_object
                    if entry.get("target") == traversing_object:
                        # And this entry is not the traversing_object itself
                        if entry["char"] != traversing_object:
                            # AND this entry is not the person being grappled by the traversing_object
                            if entry["char"] != grappled_victim_obj:
                                is_targeted_by_others_not_victim = True
                                break # Found someone else targeting, no need to check further
            
            # Drag conditions: grappling someone, yielding, and not targeted by anyone *else* (other than the victim)
            if grappled_victim_obj and is_yielding and not is_targeted_by_others_not_victim:
                # Conditions for dragging are met
                victim_entry_in_handler = next((e for e in handler.db.combatants if e["char"] == grappled_victim_obj), None)
                if not victim_entry_in_handler:
                    splattercast.msg(f"ERROR: {traversing_object.key} is grappling {grappled_victim_obj.key if grappled_victim_obj else 'Unknown'}, but victim not in handler. Blocking drag.")
                    traversing_object.msg("|rYour grapple target seems to have vanished from combat. You can't drag them.|n")
                    return

                old_handler = handler
                old_location = traversing_object.location

                # Announce dragging
                msg_drag_self = f"|gYou drag {grappled_victim_obj.key} with you through the {self.key} exit...|n"
                msg_drag_victim = f"|r{traversing_object.key} drags you through the {self.key} exit!|n"
                msg_drag_room = f"{traversing_object.key} drags {grappled_victim_obj.key} away through the {self.key} exit."
                
                traversing_object.msg(msg_drag_self)
                grappled_victim_obj.msg(msg_drag_victim)
                old_location.msg_contents(msg_drag_room, exclude=[traversing_object, grappled_victim_obj])
                splattercast.msg(f"DRAG: {traversing_object.key} is dragging {grappled_victim_obj.key} from {old_location.key} to {target_location.key} via {self.key}.")

                # Perform moves: grappler first, then victim quietly
                super().at_traverse(traversing_object, target_location) 
                grappled_victim_obj.move_to(target_location, quiet=True, move_hooks=False)

                # Announce arrival in new location
                msg_arrive_room = f"{traversing_object.key} arrives, dragging {grappled_victim_obj.key}."
                target_location.msg_contents(msg_arrive_room, exclude=[traversing_object, grappled_victim_obj])

                # --- Transfer combat state to the new location ---
                # 1. Remove combatants from the old handler.
                old_handler.remove_combatant(traversing_object)
                old_handler.remove_combatant(grappled_victim_obj)

                # 2. Get or create a combat handler in the new location.
                new_handler = get_or_create_combat(target_location)

                # 3. Add combatants to the new handler with their transferred state.
                new_handler.add_combatant(
                    traversing_object, 
                    target=None, # Drek's offensive target is cleared as he's yielding
                    initial_grappling=grappled_victim_obj, 
                    initial_grappled_by=None, 
                    initial_is_yielding=True
                )
                new_handler.add_combatant(
                    grappled_victim_obj, 
                    target=traversing_object, # Victim might default to targeting grappler
                    initial_grappling=None, 
                    initial_grappled_by=traversing_object, 
                    initial_is_yielding=False # Victim is not yielding by default
                )
                
                splattercast.msg(f"DRAG: Combatants re-added to new handler {new_handler.key} with transferred grapple state.")

                # No longer need to manually find and update entries here, as add_combatant handles it.
                
                if len(new_handler.db.combatants) > 1 and not new_handler.is_active:
                    splattercast.msg(f"DRAG: New handler {new_handler.key} has {len(new_handler.db.combatants)} combatants, ensuring it starts if not already active.")
                    new_handler.start()

                return  # Movement and combat transfer handled successfully

            else:
                # In combat, but conditions for dragging are not met
                traversing_object.msg("|rYou can't leave while in combat! Try to flee instead.|n")
                splattercast.msg(f"{traversing_object.key} tried to move via exit '{self.key}' while in combat. Drag conditions not met (grappling: {bool(grappled_victim_obj)}, yielding: {is_yielding}, targeted_by_others_not_victim: {is_targeted_by_others_not_victim}).")
                return  # Block movement

        # Not in combat, standard traversal
        super().at_traverse(traversing_object, target_location)
