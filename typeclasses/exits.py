"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit
from evennia.comms.models import ChannelDB
from world.combat.handler import get_or_create_combat 
from world.combat.constants import SPLATTERCAST_CHANNEL, DB_CHAR 


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
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # --- AIMING LOCK CHECK ---
        aimer = getattr(traversing_object.ndb, "aimed_at_by", None)
        if aimer:
            # Check if the aimer is still valid and in the same location
            if not aimer.location or aimer.location != traversing_object.location:
                # Aimer is gone or no longer in the same room, clear the lock
                splattercast.msg(f"AIM LOCK: {traversing_object.key} was aimed at by {aimer.key if aimer else 'Unknown'}, but aimer is no longer present/valid. Clearing lock.")
                del traversing_object.ndb.aimed_at_by
                if hasattr(aimer, "ndb") and getattr(aimer.ndb, "aiming_at", None) == traversing_object:
                    del aimer.ndb.aiming_at
            else:
                traversing_object.msg(f"|r{aimer.key} is aiming at you, locking you in place! You cannot move.|n")
                aimer.msg(f"|yYour target, {traversing_object.key}, tries to move but is locked by your aim!|n")
                splattercast.msg(f"AIM LOCK: {traversing_object.key} attempted to traverse {self.key} but is locked by {aimer.key}'s aim.")
                return # Block traversal
        # --- END AIMING LOCK CHECK ---

        # --- CLEAR TRAVERSER'S OWN AIM STATE UPON MOVING ---
        if hasattr(traversing_object, "clear_aim_state"):
            # This will only send messages if an aim state was actually cleared.
            traversing_object.clear_aim_state(reason_for_clearing="as you move")
        else:
            # Fallback - manually clear aim state if the method isn't on the object
            aim_cleared = False
            
            # Clear target aiming
            old_aim_target = getattr(traversing_object.ndb, "aiming_at", None)
            if old_aim_target:
                del traversing_object.ndb.aiming_at
                if hasattr(old_aim_target, "ndb") and getattr(old_aim_target.ndb, "aimed_at_by", None) == traversing_object:
                    del old_aim_target.ndb.aimed_at_by
                    old_aim_target.msg(f"{traversing_object.key} stops aiming at you as they move.")
                traversing_object.msg(f"You stop aiming at {old_aim_target.key} as you move.")
                aim_cleared = True
            
            # Clear direction aiming  
            old_aim_direction = getattr(traversing_object.ndb, "aiming_direction", None)
            if old_aim_direction:
                del traversing_object.ndb.aiming_direction
                traversing_object.msg(f"You stop aiming {old_aim_direction} as you move.")
                aim_cleared = True
            
            if not aim_cleared:
                splattercast.msg(f"AIM_CLEAR_ON_MOVE_FAIL: {traversing_object.key} lacks clear_aim_state method during traversal of {self.key}.")
        # --- END CLEAR TRAVERSER'S OWN AIM STATE ---

        # --- PROXIMITY CLEANUP ON ROOM CHANGE ---
        # Clear proximity relationships when moving between rooms (except during combat dragging)
        handler = getattr(traversing_object.ndb, "combat_handler", None)
        is_being_dragged = False
        if handler:
            combatants = getattr(handler.db, "combatants", None)
            if combatants:
                try:
                    is_being_dragged = any(e.get(DB_CHAR) == traversing_object and 
                                         handler.get_grappled_by_obj(e) for e in combatants)
                except (TypeError, AttributeError) as ex:
                    # Log the error but don't crash traversal
                    splattercast.msg(f"TRAVERSE_ERROR: Error checking grapple status for {traversing_object.key}: {ex}")
                    is_being_dragged = False
        
        if not is_being_dragged and hasattr(traversing_object.ndb, "in_proximity_with"):
            if isinstance(traversing_object.ndb.in_proximity_with, set) and traversing_object.ndb.in_proximity_with:
                splattercast.msg(f"PROXIMITY_CLEANUP_ON_MOVE: {traversing_object.key} moving from {traversing_object.location.key} to {target_location.key}. Clearing proximity with: {[o.key for o in traversing_object.ndb.in_proximity_with]}")
                
                # Remove traversing_object from others' proximity sets
                for other_char in list(traversing_object.ndb.in_proximity_with):
                    if hasattr(other_char.ndb, "in_proximity_with") and isinstance(other_char.ndb.in_proximity_with, set):
                        other_char.ndb.in_proximity_with.discard(traversing_object)
                        splattercast.msg(f"PROXIMITY_CLEANUP_ON_MOVE: Removed {traversing_object.key} from {other_char.key}'s proximity list.")
                
                # Clear traversing_object's proximity set
                traversing_object.ndb.in_proximity_with.clear()
        # --- END PROXIMITY CLEANUP ---

        handler = getattr(traversing_object.ndb, "combat_handler", None)

        if handler:
            # Character is in combat - check if handler is still valid
            combatants_list = getattr(handler.db, "combatants", None)
            if combatants_list is None:
                # Handler has been cleaned up but character still has reference
                splattercast.msg(f"TRAVERSAL: {traversing_object.key} has stale combat_handler reference. Clearing and allowing move.")
                setattr(traversing_object.ndb, "combat_handler", None)
                super().at_traverse(traversing_object, target_location)
                return
                
            char_entry_in_handler = next((e for e in combatants_list if e["char"] == traversing_object), None)

            if not char_entry_in_handler:
                # This case should ideally not be reached if ndb.combat_handler is properly managed.
                splattercast.msg(f"ERROR: {traversing_object.key} has ndb.combat_handler but no entry in handler {handler.key}. Allowing move as non-combatant.")
                super().at_traverse(traversing_object, target_location)
                return

            # Check drag conditions
            grappled_victim_obj = handler.get_grappling_obj(char_entry_in_handler)
            is_yielding = char_entry_in_handler.get("is_yielding")
            
            is_targeted_by_others_not_victim = False
            if combatants_list:
                for entry in combatants_list:
                    # Check if this entry is targeting the traversing_object
                    if handler.get_target_obj(entry) == traversing_object:
                        # And this entry is not the traversing_object itself
                        if entry["char"] != traversing_object:
                            # AND this entry is not the person being grappled by the traversing_object
                            if entry["char"] != grappled_victim_obj:
                                is_targeted_by_others_not_victim = True
                                break # Found someone else targeting, no need to check further
            
            # Drag conditions: grappling someone, yielding, and not targeted by anyone *else* (other than the victim)
            if grappled_victim_obj and is_yielding and not is_targeted_by_others_not_victim:
                # Conditions for dragging are met
                victim_entry_in_handler = next((e for e in combatants_list if e["char"] == grappled_victim_obj), None)
                if not victim_entry_in_handler:
                    splattercast.msg(f"ERROR: {traversing_object.key} is grappling {grappled_victim_obj.key if grappled_victim_obj else 'Unknown'}, but victim not in handler. Blocking drag.")
                    traversing_object.msg("|rYour grapple target seems to have vanished from combat. You can't drag them.|n")
                    return

                # --- Immediate resistance check ---
                from random import randint
                victim_grit = getattr(grappled_victim_obj, "grit", 1)
                grappler_grit = getattr(traversing_object, "grit", 1)
                resist_roll = randint(1, max(1, victim_grit))
                drag_roll = randint(1, max(1, grappler_grit))
                splattercast.msg(f"DRAG RESIST: {grappled_victim_obj.key} rolls {resist_roll} vs {drag_roll} ({traversing_object.key})")

                if resist_roll > drag_roll:
                    traversing_object.msg(f"|r{grappled_victim_obj.key} resists your attempt to drag them!|n")
                    grappled_victim_obj.msg(f"|gYou resist {traversing_object.key}'s attempt to drag you!|n")
                    splattercast.msg(f"{grappled_victim_obj.key} successfully resisted being dragged by {traversing_object.key}.")

                    # --- Break the grapple on successful resistance ---
                    # Find both entries in the handler
                    grappler_entry = next((e for e in combatants_list if e["char"] == traversing_object), None)
                    victim_entry = next((e for e in combatants_list if e["char"] == grappled_victim_obj), None)
                    if grappler_entry:
                        grappler_entry["grappling_dbref"] = None
                    if victim_entry:
                        victim_entry["grappled_by_dbref"] = None
                    msg = f"{grappled_victim_obj.key} breaks free from {traversing_object.key}'s grapple!"
                    traversing_object.location.msg_contents(f"|g{msg}|n")
                    splattercast.msg(f"GRAPPLE BROKEN: {msg}")

                    return

                # Proceed with drag if resistance fails
                traversing_object.msg(f"|g{grappled_victim_obj.key} struggles but fails to resist.|n")
                grappled_victim_obj.msg(f"|rYou struggle but fail to resist {traversing_object.key}'s attempt to drag you.|n")
                splattercast.msg(f"{grappled_victim_obj.key} failed to resist being dragged by {traversing_object.key}.")

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
                # 1. Before removing, determine if victim is yielding
                victim_entry_in_handler = next((e for e in combatants_list if e["char"] == grappled_victim_obj), None)
                victim_is_yielding = victim_entry_in_handler.get("is_yielding", False) if victim_entry_in_handler else False

                # 2. Remove combatants from the old handler.
                old_handler.remove_combatant(traversing_object)
                old_handler.remove_combatant(grappled_victim_obj)

                # 3. Get or create a combat handler in the new location.
                new_handler = get_or_create_combat(target_location)

                # 4. Add combatants to the new handler with their transferred state.
                new_handler.add_combatant(
                    traversing_object, 
                    target=None, # Grappler is always yielding when dragging
                    initial_grappling=grappled_victim_obj, 
                    initial_grappled_by=None, 
                    initial_is_yielding=True
                )
                new_handler.add_combatant(
                    grappled_victim_obj, 
                    target=None,  # Victim never has an offensive target immediately after being dragged
                    initial_grappling=None, 
                    initial_grappled_by=traversing_object, 
                    initial_is_yielding=victim_is_yielding # Preserve their yielding state from before the drag
                )
                
                splattercast.msg(f"DRAG: Combatants re-added to new handler {new_handler.key} with transferred grapple state.")

                # No longer need to manually find and update entries here, as add_combatant handles it.
                
                new_handler_combatants = getattr(new_handler.db, "combatants", None)
                if new_handler_combatants and len(new_handler_combatants) > 1 and not new_handler.is_active:
                    splattercast.msg(f"DRAG: New handler {new_handler.key} has {len(new_handler_combatants)} combatants, ensuring it starts if not already active.")
                    new_handler.start()

                return  # Movement and combat transfer handled successfully

            else:
                # In combat, but conditions for dragging are not met
                traversing_object.msg("|rYou can't leave while in combat! Try to flee instead.|n")
                splattercast.msg(f"{traversing_object.key} tried to move via exit '{self.key}' while in combat. Drag conditions not met (grappling: {bool(grappled_victim_obj)}, yielding: {is_yielding}, targeted_by_others_not_victim: {is_targeted_by_others_not_victim}).")
                return  # Block movement

        # Not in combat, standard traversal
        super().at_traverse(traversing_object, target_location)
