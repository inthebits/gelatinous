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
            
            is_targeted_by_others = False
            if handler.db.combatants: # Ensure list is not empty before iterating
                is_targeted_by_others = any(
                    entry.get("target") == traversing_object
                    for entry in handler.db.combatants
                    if entry["char"] != traversing_object
                )

            if grappled_victim_obj and is_yielding and not is_targeted_by_others:
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
                #    This also clears their .ndb.combat_handler and handles grapple release within old_handler.db.combatants.
                old_handler.remove_combatant(traversing_object)
                old_handler.remove_combatant(grappled_victim_obj)
                # old_handler.remove_combatant will call old_handler.stop() if it's now empty or has 1 combatant.

                # 2. Get or create a combat handler in the new location.
                new_handler = get_or_create_combat(target_location)

                # 3. Add combatants to the new handler.
                #    add_combatant defaults is_yielding to False and target to None.
                new_handler.add_combatant(traversing_object)
                new_handler.add_combatant(grappled_victim_obj)

                # 4. Re-establish the grapple and yielding state in the new handler's entries.
                new_char_entry = next((e for e in new_handler.db.combatants if e["char"] == traversing_object), None)
                new_victim_entry = next((e for e in new_handler.db.combatants if e["char"] == grappled_victim_obj), None)

                if new_char_entry and new_victim_entry:
                    new_char_entry["grappling"] = grappled_victim_obj
                    new_char_entry["is_yielding"] = True  # Preserve yielding state for the grappler
                    new_char_entry["target"] = None       # Yielding grappler has no offensive target
                    
                    new_victim_entry["grappled_by"] = traversing_object
                    # Victim's target will be determined by get_target logic if they take a turn.
                    splattercast.msg(f"DRAG: Grapple state re-established in new handler {new_handler.key} for {traversing_object.key} (yielding) and {grappled_victim_obj.key}.")
                else:
                    splattercast.msg(f"DRAG ERROR: Could not find entries in new_handler {new_handler.key} to re-establish grapple state.")
                
                # Ensure the new handler is active if it now has combatants
                # add_combatant should handle starting if ready_to_start and not active.
                # As a safeguard, if it has 2+ people and isn't active, try to start.
                if len(new_handler.db.combatants) > 1 and not new_handler.is_active:
                    splattercast.msg(f"DRAG: New handler {new_handler.key} has {len(new_handler.db.combatants)} combatants, ensuring it starts if not already active.")
                    new_handler.start() # This also sets is_active = True

                return  # Movement and combat transfer handled successfully

            else:
                # In combat, but conditions for dragging are not met
                traversing_object.msg("|rYou can't leave while in combat! Try to flee instead.|n")
                splattercast.msg(f"{traversing_object.key} tried to move via exit '{self.key}' while in combat. Drag conditions not met (grappling: {bool(grappled_victim_obj)}, yielding: {is_yielding}, targeted_by_others: {is_targeted_by_others}).")
                return  # Block movement

        # Not in combat, standard traversal
        super().at_traverse(traversing_object, target_location)
