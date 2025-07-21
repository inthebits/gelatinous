"""
Throw Command Implementation

Comprehensive throwing system supporting:
- Utility object transfer between rooms
- Combat weapon deployment with damage
- Grenade mechanics with proximity and timers
- Flight state management and room announcements
- Universal proximity system integration

Part of the G.R.I.M. Combat System.
"""

import random
from evennia import Command, utils
from evennia.utils import search
from evennia.comms.models import ChannelDB
from world.combat.constants import *
from world.combat.utils import (
    apply_damage
)
from world.combat.handler import get_or_create_combat


class CmdThrow(Command):
    """
    Throw objects at targets or in directions.
    
    Usage:
        throw <object>                    # Throw randomly in current room or aimed direction
        throw <object> at <target>        # Throw at specific target (requires aim for cross-room)
        throw <object> to <direction>     # Throw to adjacent room in specified direction
        throw <object> to here            # Throw randomly in current room
    
    Examples:
        throw knife at bob               # Target Bob in current room or aimed room
        throw grenade to north           # Throw grenade north to adjacent room
        throw keys to here               # Throw keys randomly in current room
        throw rock                       # Throw rock in aimed direction or current room
    
    The throw command serves dual purposes: utility object transfer and combat weapon
    deployment. Objects with the 'is_throwing_weapon' property will trigger combat
    mechanics, while utility objects transfer harmlessly between rooms.
    
    Thrown objects have a 2-second flight time and appear in room descriptions during
    flight. Landing creates proximity relationships for grenade mechanics and chain
    reactions.
    """
    
    key = "throw"
    aliases = ["toss", "hurl"]
    locks = "cmd:all()"
    help_category = "Combat"
    
    def parse(self):
        """Parse throw command with intelligent syntax detection."""
        self.args = self.args.strip()
        
        # Initialize parsing results
        self.object_name = None
        self.target_name = None
        self.direction = None
        self.throw_type = None  # 'at_target', 'to_direction', 'to_here', 'fallback'
        
        if not self.args:
            return
        
        # Parse for "at" keyword - targeted throwing
        if " at " in self.args:
            parts = self.args.split(" at ", 1)
            if len(parts) == 2:
                self.object_name = parts[0].strip()
                target_part = parts[1].strip()
                
                # Handle "throw knife at here" -> convert to "throw knife to here"
                if target_part.lower() == "here":
                    self.throw_type = "to_here"
                else:
                    self.target_name = target_part
                    self.throw_type = "at_target"
                return
        
        # Parse for "to" keyword - directional or here throwing
        if " to " in self.args:
            parts = self.args.split(" to ", 1)
            if len(parts) == 2:
                self.object_name = parts[0].strip()
                target_part = parts[1].strip()
                
                if target_part.lower() == "here":
                    self.throw_type = "to_here"
                else:
                    # Check if it's a direction or character name
                    self.direction = target_part
                    self.throw_type = "to_direction"
                return
        
        # Fallback - single object name
        self.object_name = self.args
        self.throw_type = "fallback"
    
    def func(self):
        """Execute the throw command."""
        if not self.args:
            self.caller.msg("Throw what? Use 'throw <object>' or 'throw <object> at <target>'.")
            return
        
        # Validate and get the object to throw
        obj = self.get_object_to_throw()
        if not obj:
            return
        
        # Determine destination and target based on throw type
        destination, target = self.determine_destination()
        if destination is None:
            return
        
        # Check if this is a weapon throw and handle combat
        is_weapon = self.is_throwing_weapon(obj)
        if is_weapon and target:
            if self.handle_weapon_throw(obj, target, destination):
                return  # Combat handled the throw
        
        # Handle utility throw or weapon miss
        self.handle_utility_throw(obj, destination, target)
    
    def get_object_to_throw(self):
        """Validate and return the object to throw."""
        if not self.object_name:
            self.caller.msg(MSG_THROW_NOTHING_WIELDED)
            return None
        
        # Check if caller has hands (AttributeProperty compatible)
        caller_hands = getattr(self.caller, 'hands', None)
        if caller_hands is None:
            self.caller.msg(MSG_THROW_NOTHING_WIELDED)
            return None
        
        # Check for empty hands dict (no hands at all)
        if not caller_hands:
            self.caller.msg(MSG_THROW_NO_HANDS)
            return None
        
        # Find object in hands
        obj = None
        hand_name = None
        for hand, wielded_obj in caller_hands.items():
            if wielded_obj and self.object_name.lower() in wielded_obj.key.lower():
                obj = wielded_obj
                hand_name = hand
                break
        
        if not obj:
            # Check if object exists but not wielded
            search_obj = self.caller.search(self.object_name, location=self.caller, quiet=True)
            if search_obj:
                self.caller.msg(MSG_THROW_OBJECT_NOT_WIELDED.format(object=self.object_name))
                return None
            else:
                self.caller.msg(MSG_THROW_OBJECT_NOT_FOUND.format(object=self.object_name))
                return None
        
        # Check for special grenade validation
        if self.is_explosive(obj):
            if not self.validate_grenade_throw(obj):
                return None
        
        # Check if caller is grappled
        if hasattr(self.caller, 'ndb') and hasattr(self.caller.ndb, NDB_COMBAT_HANDLER):
            handler = getattr(self.caller.ndb, NDB_COMBAT_HANDLER)
            if handler:
                combat_entry = handler.get_combatant_entry(self.caller)
                if combat_entry and combat_entry.get(DB_GRAPPLED_BY_DBREF):
                    self.caller.msg(MSG_THROW_GRAPPLED)
                    return None
        
        return obj
    
    def validate_grenade_throw(self, obj):
        """Validate grenade-specific throwing requirements."""
        # Allow unpinned grenades to be thrown as inert objects
        # Players should be able to make tactical mistakes or intentional choices
        
        # Only check if grenade timer has expired (explosion in hands)
        if hasattr(obj.ndb, NDB_COUNTDOWN_REMAINING):
            remaining = getattr(obj.ndb, NDB_COUNTDOWN_REMAINING, 0)
            if remaining is not None and remaining <= 0:
                self.caller.msg(MSG_THROW_TIMER_EXPIRED)
                # Apply damage to caller
                blast_damage = getattr(obj.db, DB_BLAST_DAMAGE, 10)
                apply_damage(self.caller, blast_damage)
                obj.delete()
                return False
        
        return True
    
    def determine_destination(self):
        """Determine destination room and target based on throw type."""
        if self.throw_type == "to_here":
            return self.caller.location, self.select_random_target_in_room(self.caller.location)
        
        elif self.throw_type == "at_target":
            # Find target in current room or aimed room
            target = self.find_target()
            if not target:
                return None, None
            return target.location, target
        
        elif self.throw_type == "to_direction":
            # Validate direction and get destination room
            destination = self.get_destination_room(self.direction)
            if not destination:
                return None, None
            target = self.select_random_target_in_room(destination)
            return destination, target
        
        elif self.throw_type == "fallback":
            # Use aim state or current room
            aim_direction = getattr(self.caller.ndb, NDB_AIMING_DIRECTION, None)
            if aim_direction:
                destination = self.get_destination_room(aim_direction)
                if destination:
                    target = self.select_random_target_in_room(destination)
                    return destination, target
            
            # Fallback to current room
            return self.caller.location, self.select_random_target_in_room(self.caller.location)
        
        return None, None
    
    def find_target(self):
        """Find target for 'at' syntax throwing."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not self.target_name:
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: find_target: No target_name provided")
            return None
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: Looking for target '{self.target_name}' in {self.caller.location}(#{self.caller.location.id})")
        
        # First check current room
        target_search = self.caller.search(self.target_name, location=self.caller.location, quiet=True)
        target = target_search[0] if target_search else None
        target_hands = getattr(target, 'hands', None) if target else None
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: search result = {target_search}, target = {target}, has_hands = {target_hands is not None}")
        
        if target and target_hands is not None:  # Is a character with hands attribute
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: find_target: Found valid character target: {target}")
            return target
        
        # Check aimed room for cross-room targeting
        aim_direction = getattr(self.caller.ndb, NDB_AIMING_DIRECTION, None)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: aim_direction = {aim_direction}")
        
        if aim_direction:
            destination = self.get_destination_room(aim_direction)
            if destination:
                target_search = self.caller.search(self.target_name, location=destination, quiet=True)
                target = target_search[0] if target_search else None
                target_hands = getattr(target, 'hands', None) if target else None
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: cross-room search result = {target_search}, target = {target}, has_hands = {target_hands is not None}")
                if target and target_hands is not None:
                    return target
        else:
            # No aim for cross-room targeting
            if not target:
                self.caller.msg(MSG_THROW_NO_AIM_CROSS_ROOM)
                return None
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_FAIL: find_target: No valid target found for '{self.target_name}'")
        self.caller.msg(MSG_THROW_TARGET_NOT_FOUND.format(target=self.target_name))
        return None
    
    def get_destination_room(self, direction):
        """Get destination room for directional throwing."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        if not direction:
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: get_destination_room: No direction provided")
            return None
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: Looking for exit '{direction}' in {self.caller.location}(#{self.caller.location.id})")
        
        # Find exit in current room using standard Evennia patterns
        exit_search = self.caller.search(direction, location=self.caller.location, quiet=True)
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: search result = {exit_search}")
        
        # Handle search result - could be list or single object
        exit_obj = exit_search[0] if exit_search else None
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: exit_obj = {exit_obj}")
        
        # Check if we got a valid exit with destination (standard Evennia way)
        if exit_obj and hasattr(exit_obj, 'destination') and exit_obj.destination:
            # Additional debug: check if destination is the same as current room
            current_room = self.caller.location
            destination_room = exit_obj.destination
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: current_room = {current_room}(#{current_room.id}), destination_room = {destination_room}(#{destination_room.id})")
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: rooms_are_same = {current_room == destination_room}")
            
            if current_room == destination_room:
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: get_destination_room: Exit {exit_obj} destination points back to same room!")
                self.caller.msg(f"The exit '{direction}' seems to loop back to this room. Cannot throw that way.")
                return None
            
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: get_destination_room: Found valid exit {exit_obj} -> {exit_obj.destination}(#{exit_obj.destination.id})")
            return exit_obj.destination
        
        # Debug: log what we found if the exit is invalid
        if exit_obj:
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: Found object type: {type(exit_obj)}, destination: {getattr(exit_obj, 'destination', 'NONE')}")
        
        # If not found or invalid, check if it might be a character name mistaken for direction
        if exit_obj:
            char_hands = getattr(exit_obj, 'hands', None)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: Found object but no destination, has_hands = {char_hands is not None}")
            
            if char_hands is not None:
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: '{direction}' is a character, suggesting 'at' syntax")
                self.caller.msg(MSG_THROW_SUGGEST_AT_SYNTAX.format(
                    object=self.object_name, target=direction))
                return None
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_FAIL: get_destination_room: Invalid direction '{direction}'")
        self.caller.msg(MSG_THROW_INVALID_DIRECTION.format(direction=direction))
        return None
    
    def select_random_target_in_room(self, room):
        """Select random character in room for proximity assignment."""
        if not room:
            return None
        
        characters = [obj for obj in room.contents if getattr(obj, 'hands', None) is not None and obj != self.caller]
        if characters:
            return random.choice(characters)
        return None
    
    def is_throwing_weapon(self, obj):
        """Check if object is a throwing weapon."""
        return getattr(obj.db, DB_IS_THROWING_WEAPON, False)
    
    def is_explosive(self, obj):
        """Check if object is explosive."""
        return getattr(obj.db, DB_IS_EXPLOSIVE, False)
    
    def handle_weapon_throw(self, obj, target, destination):
        """Handle throwing weapon combat mechanics."""
        # Enter combat if not already in combat
        handler = get_or_create_combat(self.caller.location)
        if not handler:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Failed to get combat handler for weapon throw")
            return False
        
        # Add combatants to handler
        handler.add_combatant(self.caller)
        if target:
            handler.add_combatant(target)
        
        # Consume combat turn (skip turn mechanic)
        setattr(self.caller.ndb, NDB_SKIP_ROUND, True)
        
        # Remove object from hand before flight
        self.remove_from_hand(obj)
        
        # Start flight with combat resolution
        self.start_flight(obj, destination, target, is_weapon=True)
        return True
    
    def handle_utility_throw(self, obj, destination, target):
        """Handle utility object throwing."""
        # Remove object from hand
        self.remove_from_hand(obj)
        
        # Start flight
        self.start_flight(obj, destination, target, is_weapon=False)
    
    def remove_from_hand(self, obj):
        """Remove object from caller's hand."""
        caller_hands = getattr(self.caller, 'hands', {})
        for hand_name, wielded_obj in caller_hands.items():
            if wielded_obj == obj:
                caller_hands[hand_name] = None
                break
    
    def start_flight(self, obj, destination, target, is_weapon=False):
        """Start object flight with timer."""
        # Announce throw in origin room
        self.announce_throw_origin(obj, destination, target)
        
        # Add to room's flying objects - ensure we have a proper list
        flying_objects = getattr(self.caller.location.ndb, NDB_FLYING_OBJECTS, None)
        if not flying_objects:
            setattr(self.caller.location.ndb, NDB_FLYING_OBJECTS, [])
        
        flying_objects = getattr(self.caller.location.ndb, NDB_FLYING_OBJECTS)
        if flying_objects is None:
            flying_objects = []
            setattr(self.caller.location.ndb, NDB_FLYING_OBJECTS, flying_objects)
        
        flying_objects.append(obj)
        
        # Store flight data on object
        obj.ndb.flight_destination = destination
        obj.ndb.flight_target = target
        obj.ndb.flight_origin = self.caller.location
        obj.ndb.flight_is_weapon = is_weapon
        obj.ndb.flight_thrower = self.caller
        
        # Start flight timer
        utils.delay(THROW_FLIGHT_TIME, self.complete_flight, obj)
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: {self.caller} started flight for {obj} to {destination}(#{destination.id})")
    
    def announce_throw_origin(self, obj, destination, target):
        """Announce throw in origin room."""
        caller_name = self.caller.key
        object_name = obj.key
        
        # Determine announcement based on throw type
        if self.throw_type == "to_direction":
            direction = self.direction
            message = MSG_THROW_ORIGIN_DIRECTIONAL.format(
                thrower=caller_name, object=object_name, direction=direction)
        
        elif self.throw_type == "at_target" and target and target.location == self.caller.location:
            target_name = target.key
            message = MSG_THROW_ORIGIN_TARGETED_SAME.format(
                thrower=caller_name, object=object_name, target=target_name)
        
        elif self.throw_type == "at_target" and target:
            # Cross-room targeting
            aim_direction = getattr(self.caller.ndb, NDB_AIMING_DIRECTION, "that direction")
            message = MSG_THROW_ORIGIN_TARGETED_CROSS.format(
                thrower=caller_name, object=object_name, direction=aim_direction)
        
        elif self.throw_type == "to_here":
            message = MSG_THROW_ORIGIN_HERE.format(
                thrower=caller_name, object=object_name)
        
        else:  # fallback
            aim_direction = getattr(self.caller.ndb, NDB_AIMING_DIRECTION, "nearby")
            if aim_direction == "nearby":
                message = MSG_THROW_ORIGIN_HERE.format(
                    thrower=caller_name, object=object_name)
            else:
                message = MSG_THROW_ORIGIN_FALLBACK.format(
                    thrower=caller_name, object=object_name, direction=aim_direction)
        
        # Broadcast to room
        self.caller.location.msg_contents(message, exclude=self.caller)
        self.caller.msg(f"You throw {object_name}.")
    
    def complete_flight(self, obj):
        """Complete the flight and handle landing."""
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Starting complete_flight for {obj}")
            
            # Get flight data
            destination = obj.ndb.flight_destination
            target = obj.ndb.flight_target
            origin = obj.ndb.flight_origin
            is_weapon = getattr(obj.ndb, 'flight_is_weapon', False)
            thrower = getattr(obj.ndb, 'flight_thrower', None)
            
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Flight data - destination: {destination}, target: {target}, origin: {origin}")
            
            # Clean up origin room flying objects
            origin_flying_objects = getattr(origin.ndb, NDB_FLYING_OBJECTS, None)
            if origin and origin_flying_objects:
                flying_objects = getattr(origin.ndb, NDB_FLYING_OBJECTS)
                if flying_objects and obj in flying_objects:
                    flying_objects.remove(obj)
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Removed {obj} from origin flying objects")
            
            # Move object to destination
            if destination:
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Moving {obj} to destination {destination}")
                obj.move_to(destination)
                
                # Announce arrival
                if destination != origin:
                    # Determine arrival direction
                    arrival_dir = self.get_arrival_direction(origin, destination)
                    message = MSG_THROW_ARRIVAL.format(object=obj.key, direction=arrival_dir)
                    destination.msg_contents(message)
                
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: About to call handle_landing")
                # Handle landing and proximity
                self.handle_landing(obj, destination, target, is_weapon, thrower)
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Completed handle_landing")
            
            # Clean up flight data
            del obj.ndb.flight_destination
            del obj.ndb.flight_target  
            del obj.ndb.flight_origin
            del obj.ndb.flight_is_weapon
            del obj.ndb.flight_thrower
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Cleaned up flight data for {obj}")
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in complete_flight: {e}")
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error details - destination: {destination}, target: {target}, origin: {origin}")
            # Failsafe: move object to origin if destination fails
            flight_origin = getattr(obj.ndb, 'flight_origin', None)
            if flight_origin:
                obj.move_to(flight_origin)
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Moved {obj} back to origin {flight_origin} due to error")
    
    def get_arrival_direction(self, origin, destination):
        """Determine arrival direction for announcement."""
        # Simple implementation - would need room connection mapping for accuracy
        return "somewhere"
    
    def handle_landing(self, obj, destination, target, is_weapon, thrower):
        """Handle object landing and proximity assignment."""
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: handle_landing called - obj: {obj}, destination: {destination}, target: {target}, is_weapon: {is_weapon}")
            
            # Weapon combat resolution
            if is_weapon and target:
                try:
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Resolving weapon hit")
                    self.resolve_weapon_hit(obj, target, thrower)
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: resolve_weapon_hit completed")
                except Exception as e:
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in resolve_weapon_hit: {e}")
                    # Continue with landing even if weapon hit fails
            
            # Utility object bounce
            elif target and not is_weapon:
                try:
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Utility object bounce")
                    target.location.msg_contents(MSG_THROW_UTILITY_BOUNCE.format(
                        object=obj.key, target=target.key))
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Utility bounce message sent")
                except Exception as e:
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in utility bounce: {e}")
                    # Continue with landing even if bounce message fails
            
            # Assign proximity for universal proximity system
            try:
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Assigning landing proximity")
                self.assign_landing_proximity(obj, target)
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: assign_landing_proximity completed")
            except Exception as e:
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in assign_landing_proximity: {e}")
                # Continue with landing even if proximity assignment fails
            
            # Handle grenade-specific landing
            if self.is_explosive(obj):
                try:
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Handling grenade landing")
                    self.handle_grenade_landing(obj, target)
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: handle_grenade_landing completed")
                except Exception as e:
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in handle_grenade_landing: {e}")
                    # Continue with landing even if grenade landing fails
            
            # General landing announcement
            try:
                if target:
                    message = MSG_THROW_LANDING_PROXIMITY.format(object=obj.key, target=target.key)
                else:
                    message = MSG_THROW_LANDING_ROOM.format(object=obj.key)
                
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Sending landing message: {message}")
                destination.msg_contents(message)
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Landing message sent successfully")
            except Exception as e:
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in landing message: {e}")
                # Continue even if landing message fails
            
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: handle_landing completed successfully")
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Unexpected error in handle_landing: {e}")
            # Don't re-raise - let the object land even if there are issues
    
    def resolve_weapon_hit(self, weapon, target, thrower):
        """Resolve weapon throw hit/miss and damage."""
        try:
            # Simple hit resolution - could be enhanced with accuracy system
            hit_chance = 0.7  # 70% base hit chance
            
            if random.random() <= hit_chance:
                # Hit - apply damage
                base_damage = getattr(weapon.db, 'damage', 1)
                total_damage = random.randint(1, 6) + base_damage
                
                apply_damage(target, total_damage)
                
                target.msg(MSG_THROW_WEAPON_HIT.format(weapon=weapon.key, target=target.key))
                thrower.msg(f"Your {weapon.key} strikes {target.key}!")
                
                # Establish proximity if hit (safe pattern)
                proximity_list = getattr(target.ndb, NDB_PROXIMITY_UNIVERSAL, None)
                if not proximity_list:
                    setattr(target.ndb, NDB_PROXIMITY_UNIVERSAL, [])
                    proximity_list = getattr(target.ndb, NDB_PROXIMITY_UNIVERSAL, [])
                
                # Validate proximity_list is a list
                if not isinstance(proximity_list, list):
                    proximity_list = []
                    setattr(target.ndb, NDB_PROXIMITY_UNIVERSAL, proximity_list)
                
                if thrower and thrower not in proximity_list:
                    proximity_list.append(thrower)
            
            else:
                # Miss
                target.msg(MSG_THROW_WEAPON_MISS.format(weapon=weapon.key, target=target.key))
                thrower.msg(f"Your {weapon.key} misses {target.key}!")
                
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in resolve_weapon_hit: {e}")
            # Don't re-raise - weapon hit failure shouldn't fail entire throw
    
    def assign_landing_proximity(self, obj, target):
        """Assign proximity for universal proximity system."""
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: assign_landing_proximity called - obj: {obj}, target: {target}")
            
            # Ensure object has proximity list (use same pattern as drop command)
            proximity_list = getattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, None)
            if not proximity_list:
                setattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, [])
                proximity_list = getattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            
            # Validate proximity_list is actually a list
            if not isinstance(proximity_list, list):
                proximity_list = []
                setattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, proximity_list)
            
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: obj proximity_list: {proximity_list}")
            
            if target:
                # Add target to object proximity
                if target not in proximity_list:
                    proximity_list.append(target)
                    splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Added target {target} to obj proximity")
                
                # Inherit target's existing proximity relationships
                target_proximity = getattr(target.ndb, NDB_PROXIMITY_UNIVERSAL, None)
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: target_proximity: {target_proximity}")
                if target_proximity and isinstance(target_proximity, list):
                    for character in target_proximity:
                        if character and character not in proximity_list:
                            proximity_list.append(character)
                            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Added {character} from target proximity")
            
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: assign_landing_proximity completed successfully")
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in assign_landing_proximity: {e}")
            raise  # Re-raise to let handle_landing handle it
    
    def handle_grenade_landing(self, grenade, target):
        """Handle grenade-specific landing mechanics."""
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: handle_grenade_landing called - grenade: {grenade}, target: {target}")
            
            # If grenade lands near someone, everyone in their proximity gets added
            target_proximity = getattr(target.ndb, NDB_PROXIMITY_UNIVERSAL, None) if target else None
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: target_proximity: {target_proximity}")
            
            if target_proximity and isinstance(target_proximity, list):
                grenade_proximity = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
                if not isinstance(grenade_proximity, list):
                    grenade_proximity = []
                
                for character in target_proximity:
                    if character and character not in grenade_proximity:
                        grenade_proximity.append(character)
                        splattercast.msg(f"{DEBUG_PREFIX_THROW}_DEBUG: Added {character} to grenade proximity")
                
                setattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, grenade_proximity)
            
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: Grenade {grenade} landed with proximity: {getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])}")
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in handle_grenade_landing: {e}")
            # Don't re-raise here - grenade landing failure shouldn't fail entire throw


class CmdPull(Command):
    """
    Pull pins on grenades to arm them.
    
    Usage:
        pull pin on <grenade>
    
    Examples:
        pull pin on grenade
        pull pin on flashbang
    
    Pulling the pin on a grenade starts its countdown timer. The grenade must be
    thrown or dropped before the timer expires, or it will explode in your hands.
    """
    
    key = "pull"
    locks = "cmd:all()"
    help_category = "Combat"
    
    def parse(self):
        """Parse pull command syntax."""
        self.args = self.args.strip()
        
        # Expected syntax: "pin on <grenade>"
        if self.args.startswith("pin on "):
            self.grenade_name = self.args[7:].strip()
        else:
            self.grenade_name = None
    
    def func(self):
        """Execute pull command."""
        if not self.args:
            self.caller.msg(MSG_PULL_WHAT)
            return
        
        if not self.grenade_name:
            self.caller.msg(MSG_PULL_INVALID_SYNTAX)
            return
        
        # Check for hands at all
        caller_hands = getattr(self.caller, 'hands', None)
        if caller_hands is None or not caller_hands:
            self.caller.msg(MSG_PULL_NO_HANDS)
            return
        
        # Find grenade in hands
        grenade = None
        for hand, wielded_obj in caller_hands.items():
            if wielded_obj and self.grenade_name.lower() in wielded_obj.key.lower():
                grenade = wielded_obj
                break
        
        if not grenade:
            # Check if exists but not wielded
            search_obj = self.caller.search(self.grenade_name, location=self.caller, quiet=True)
            if search_obj:
                self.caller.msg(MSG_PULL_OBJECT_NOT_WIELDED.format(object=self.grenade_name))
                return
            else:
                self.caller.msg(MSG_PULL_OBJECT_NOT_FOUND.format(object=self.grenade_name))
                return
        
        # Validate explosive
        if not getattr(grenade.db, DB_IS_EXPLOSIVE, False):
            self.caller.msg(MSG_PULL_NOT_EXPLOSIVE.format(object=grenade.key))
            return
        
        # Check if requires pin
        if not getattr(grenade.db, DB_REQUIRES_PIN, True):
            self.caller.msg(MSG_PULL_NO_PIN_REQUIRED.format(object=grenade.key))
            return
        
        # Check if already pulled
        if getattr(grenade.db, DB_PIN_PULLED, False):
            self.caller.msg(MSG_PULL_ALREADY_PULLED.format(object=grenade.key))
            return
        
        # Pull pin and start timer
        self.pull_pin(grenade)
    
    def pull_pin(self, grenade):
        """Pull the pin and start countdown."""
        # Set pin pulled flag
        setattr(grenade.db, DB_PIN_PULLED, True)
        
        # Get fuse time
        fuse_time = getattr(grenade.db, DB_FUSE_TIME, 8)
        
        # Start countdown
        setattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, fuse_time)
        setattr(grenade.ndb, NDB_GRENADE_TIMER, utils.delay(fuse_time, self.explode_grenade, grenade))
        
        # Announce
        self.caller.msg(MSG_PULL_SUCCESS.format(object=grenade.key))
        self.caller.location.msg_contents(
            MSG_PULL_SUCCESS_ROOM.format(puller=self.caller.key, object=grenade.key),
            exclude=self.caller
        )
        
        # Timer warning
        self.caller.msg(MSG_PULL_TIMER_WARNING.format(object=grenade.key, time=fuse_time))
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: {self.caller} pulled pin on {grenade}, timer: {fuse_time}s")
    
    def explode_grenade(self, grenade):
        """Handle grenade explosion."""
        try:
            # Check dud chance
            dud_chance = getattr(grenade.db, DB_DUD_CHANCE, 0.0)
            if random.random() < dud_chance:
                self.handle_dud(grenade)
                return
            
            # Get blast damage
            blast_damage = getattr(grenade.db, DB_BLAST_DAMAGE, 10)
            
            # Check if grenade is in someone's inventory when it explodes
            holder = None
            if grenade.location and hasattr(grenade.location, 'has_account'):
                # Grenade is in a character's inventory - they're holding it!
                holder = grenade.location
            
            # Get proximity list
            proximity_list = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            
            # Handle explosion in someone's hands (much more dangerous!)
            if holder:
                # Explosion in hands - double damage and guaranteed hit
                holder_damage = blast_damage * 2
                apply_damage(holder, holder_damage)
                holder.msg(f"|rThe {grenade.key} EXPLODES IN YOUR HANDS!|n You take {holder_damage} damage!")
                
                # Announce to the room
                if holder.location:
                    holder.location.msg_contents(
                        f"|r{holder.key}'s {grenade.key} explodes in their hands!|n",
                        exclude=holder
                    )
                    
                # Still damage others in proximity, but less (shielded by holder's body)
                for character in proximity_list:
                    if character != holder and hasattr(character, 'msg'):
                        reduced_damage = blast_damage // 2  # Half damage due to body shielding
                        apply_damage(character, reduced_damage)
                        character.msg(MSG_GRENADE_DAMAGE.format(grenade=grenade.key))
                        
            else:
                # Normal room explosion
                if grenade.location:
                    grenade.location.msg_contents(MSG_GRENADE_EXPLODE_ROOM.format(grenade=grenade.key))
                
                # Apply damage to all in proximity
                for character in proximity_list:
                    if hasattr(character, 'msg'):  # Is a character
                        apply_damage(character, blast_damage)
                        character.msg(MSG_GRENADE_DAMAGE.format(grenade=grenade.key))
                        if character.location:
                            character.location.msg_contents(
                                MSG_GRENADE_DAMAGE_ROOM.format(victim=character.key, grenade=grenade.key),
                                exclude=character
                            )
            
            # Handle chain reactions
            self.handle_chain_reactions(grenade)
            
            # Clean up
            grenade.delete()
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in explode_grenade: {e}")
    
    def handle_dud(self, grenade):
        """Handle grenade dud (failure to explode)."""
        if grenade.location:
            grenade.location.msg_contents(MSG_GRENADE_DUD_ROOM.format(grenade=grenade.key))
        
        # Clear timer state but keep grenade
        setattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 0)
        if hasattr(grenade.ndb, NDB_GRENADE_TIMER):
            delattr(grenade.ndb, NDB_GRENADE_TIMER)
    
    def handle_chain_reactions(self, exploding_grenade):
        """Handle chain reactions with other explosives."""
        if not getattr(exploding_grenade.db, DB_CHAIN_TRIGGER, False):
            return
        
        # Find other explosives in proximity
        proximity_list = getattr(exploding_grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        if proximity_list is None:
            proximity_list = []
        
        for obj in proximity_list:
            if (hasattr(obj, 'db') and 
                getattr(obj.db, DB_IS_EXPLOSIVE, False) and 
                obj != exploding_grenade):
                
                # Trigger chain explosion
                if exploding_grenade.location:
                    exploding_grenade.location.msg_contents(
                        MSG_GRENADE_CHAIN_TRIGGER.format(grenade=obj.key))
                
                # Start immediate explosion timer
                utils.delay(0.5, self.explode_grenade, obj)


class CmdCatch(Command):
    """
    Catch thrown objects out of the air.
    
    Usage:
        catch <object>
    
    Examples:
        catch grenade
        catch knife
    
    Attempt to catch objects that are currently flying through the air.
    Requires at least one free hand. Useful for catching and re-throwing
    live grenades or intercepting thrown weapons.
    """
    
    key = "catch"
    locks = "cmd:all()"
    help_category = "Combat"
    
    def func(self):
        """Execute catch command."""
        if not self.args:
            self.caller.msg(MSG_CATCH_WHAT)
            return
        
        object_name = self.args.strip()
        
        # Check for hands at all
        caller_hands = getattr(self.caller, 'hands', None)
        if caller_hands is None or not caller_hands:
            self.caller.msg(MSG_CATCH_NO_HANDS_AT_ALL)
            return
        
        # Check for free hands
        free_hand = None
        for hand_name, wielded_obj in caller_hands.items():
            if wielded_obj is None:
                free_hand = hand_name
                break
        
        if not free_hand:
            self.caller.msg(MSG_CATCH_NO_FREE_HANDS)
            return
        
        # Find flying object in current room
        flying_objects = getattr(self.caller.location.ndb, NDB_FLYING_OBJECTS, [])
        target_obj = None
        
        for obj in flying_objects:
            if object_name.lower() in obj.key.lower():
                target_obj = obj
                break
        
        if not target_obj:
            self.caller.msg(MSG_CATCH_OBJECT_NOT_FOUND.format(object=object_name))
            return
        
        # Attempt catch (simple success/fail)
        catch_chance = 0.6  # 60% base catch chance
        
        if random.random() <= catch_chance:
            # Success - catch object
            self.catch_object(target_obj, free_hand)
        else:
            # Failure - object continues flight
            self.caller.msg(MSG_CATCH_FAILED.format(object=target_obj.key))
            self.caller.location.msg_contents(
                MSG_CATCH_FAILED_ROOM.format(catcher=self.caller.key, object=target_obj.key),
                exclude=self.caller
            )
    
    def catch_object(self, obj, hand_name):
        """Successfully catch the object."""
        # Remove from flying objects
        flying_objects = getattr(self.caller.location.ndb, NDB_FLYING_OBJECTS, [])
        if obj in flying_objects:
            flying_objects.remove(obj)
        
        # Cancel flight timer by moving to caller and wielding
        obj.move_to(self.caller)
        caller_hands = getattr(self.caller, 'hands', {})
        caller_hands[hand_name] = obj
        
        # Announce success
        self.caller.msg(MSG_CATCH_SUCCESS.format(object=obj.key))
        self.caller.location.msg_contents(
            MSG_CATCH_SUCCESS_ROOM.format(catcher=self.caller.key, object=obj.key),
            exclude=self.caller
        )
        
        # Clean up flight data
        if hasattr(obj.ndb, 'flight_destination'):
            del obj.ndb.flight_destination
        if hasattr(obj.ndb, 'flight_target'):
            del obj.ndb.flight_target
        if hasattr(obj.ndb, 'flight_origin'):
            del obj.ndb.flight_origin
        if hasattr(obj.ndb, 'flight_is_weapon'):
            del obj.ndb.flight_is_weapon
        if hasattr(obj.ndb, 'flight_thrower'):
            del obj.ndb.flight_thrower
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: {self.caller} caught {obj} mid-flight")


class CmdRig(Command):
    """
    Rig explosives to exits as traps.
    
    Usage:
        rig <grenade> to <exit>
    
    Examples:
        rig grenade to north
        rig flashbang to door
    
    Set up a grenade as a trap on an exit. The grenade will explode when
    someone tries to pass through that exit. The grenade must NOT have its
    pin pulled - the pin will be pulled automatically when triggered.
    """
    
    key = "rig"
    locks = "cmd:all()"
    help_category = "Combat"
    
    def parse(self):
        """Parse rig command syntax."""
        self.args = self.args.strip()
        
        # Expected syntax: "<grenade> to <exit>"
        if " to " in self.args:
            parts = self.args.split(" to ", 1)
            if len(parts) == 2:
                self.grenade_name = parts[0].strip()
                self.exit_name = parts[1].strip()
                return
        
        self.grenade_name = None
        self.exit_name = None
    
    def func(self):
        """Execute rig command."""
        if not self.args:
            self.caller.msg(MSG_RIG_WHAT)
            return
        
        if not self.grenade_name or not self.exit_name:
            self.caller.msg(MSG_RIG_INVALID_SYNTAX)
            return
        
        # Check for hands at all
        caller_hands = getattr(self.caller, 'hands', None)
        if caller_hands is None or not caller_hands:
            self.caller.msg(MSG_RIG_NO_HANDS)
            return
        
        # Find grenade in hands
        grenade = None
        for hand, wielded_obj in caller_hands.items():
            if wielded_obj and self.grenade_name.lower() in wielded_obj.key.lower():
                grenade = wielded_obj
                break
        
        if not grenade:
            # Check if exists but not wielded
            search_obj = self.caller.search(self.grenade_name, location=self.caller, quiet=True)
            if search_obj:
                self.caller.msg(MSG_RIG_OBJECT_NOT_WIELDED.format(object=self.grenade_name))
                return
            else:
                self.caller.msg(MSG_RIG_OBJECT_NOT_FOUND.format(object=self.grenade_name))
                return
        
        # Validate explosive
        if not getattr(grenade.db, DB_IS_EXPLOSIVE, False):
            self.caller.msg(MSG_RIG_NOT_EXPLOSIVE.format(object=grenade.key))
            return
        
        # Check if pin is NOT pulled (should be unpinned for rigging)
        if getattr(grenade.db, DB_PIN_PULLED, False):
            self.caller.msg(MSG_RIG_ALREADY_PINNED)
            return
        
        # Find exit
        exit_search = self.caller.search(self.exit_name, location=self.caller.location, quiet=True)
        exit_obj = exit_search[0] if exit_search else None
        if not exit_obj or not hasattr(exit_obj, 'destination') or not exit_obj.destination:
            self.caller.msg(MSG_RIG_INVALID_EXIT.format(exit=self.exit_name))
            return
        
        # Check if exit already rigged
        existing_rigged = getattr(exit_obj.db, 'rigged_grenade', None)
        if existing_rigged:
            self.caller.msg(MSG_RIG_EXIT_ALREADY_RIGGED)
            return
        
        # Check if return exit is already rigged too
        return_exit = self.find_return_exit_for_check(exit_obj)
        if return_exit and getattr(return_exit.db, 'rigged_grenade', None):
            self.caller.msg(MSG_RIG_EXIT_ALREADY_RIGGED)
            return
        
        # Rig the grenade
        self.rig_grenade(grenade, exit_obj)
    
    def find_return_exit_for_check(self, exit_obj):
        """Find the return exit for pre-rigging checks."""
        if not exit_obj.destination:
            return None
        
        destination_room = exit_obj.destination
        current_room = self.caller.location
        
        # Look for an exit in the destination room that leads back to current room
        for obj in destination_room.contents:
            if (hasattr(obj, 'destination') and 
                obj.destination == current_room and
                obj != exit_obj):  # Don't check the same exit twice
                return obj
        
        return None
    
    def rig_grenade(self, grenade, exit_obj):
        """Rig the grenade to the exit and its return exit."""
        # Remove from hand
        caller_hands = getattr(self.caller, 'hands', {})
        for hand_name, wielded_obj in caller_hands.items():
            if wielded_obj == grenade:
                caller_hands[hand_name] = None
                break
        
        # Move grenade to exit (conceptually attached)
        grenade.move_to(exit_obj)
        
        # Set up rigging on the main exit
        setattr(exit_obj.db, 'rigged_grenade', grenade)
        setattr(grenade.db, 'rigged_to_exit', exit_obj)
        setattr(grenade.db, 'rigged_by', self.caller)  # Store who rigged it for immunity
        
        # Find and rig the return exit too
        return_exit = self.find_return_exit(exit_obj)
        if return_exit:
            setattr(return_exit.db, 'rigged_grenade', grenade)
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: Also rigged return exit {return_exit} in {return_exit.location}")
        
        # Cancel normal countdown and set up trigger
        if hasattr(grenade.ndb, NDB_GRENADE_TIMER):
            # Cancel existing timer
            delattr(grenade.ndb, NDB_GRENADE_TIMER)
        
        # Announce
        self.caller.msg(MSG_RIG_SUCCESS.format(object=grenade.key, exit=self.exit_name))
        self.caller.location.msg_contents(
            MSG_RIG_SUCCESS_ROOM.format(rigger=self.caller.key, object=grenade.key, exit=self.exit_name),
            exclude=self.caller
        )
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: {self.caller} rigged {grenade} to {exit_obj}")
    
    def find_return_exit(self, exit_obj):
        """Find the return exit that leads back to the current room."""
        if not exit_obj.destination:
            return None
        
        destination_room = exit_obj.destination
        current_room = self.caller.location
        
        # Look for an exit in the destination room that leads back to current room
        for obj in destination_room.contents:
            if (hasattr(obj, 'destination') and 
                obj.destination == current_room and
                obj != exit_obj):  # Don't rig the same exit twice
                return obj
        
        return None


def check_rigged_grenade(character, exit_obj):
    """Check if character triggers a rigged grenade. Character should already be at destination."""
    # Safe check - only proceed if rigged_grenade actually exists and has a value
    rigged_grenade = getattr(exit_obj.db, 'rigged_grenade', None)
    if not rigged_grenade:
        return False
    
    # Check if character is the rigger - they have immunity to their own traps
    rigger = getattr(rigged_grenade.db, 'rigged_by', None)
    if rigger and character == rigger:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_RIGGED: {character.key} safely bypassed their own rigged {rigged_grenade.key}")
        return False
    
    # Trigger explosion messages (character is now at destination)
    character.msg(MSG_RIG_TRIGGERED.format(object=rigged_grenade.key))
    character.location.msg_contents(
        MSG_RIG_TRIGGERED_ROOM.format(object=rigged_grenade.key, victim=character.key),
        exclude=character
    )
    
    # Pull the pin and start countdown timer when triggered
    setattr(rigged_grenade.db, DB_PIN_PULLED, True)
    fuse_time = 1  # Rigged grenades explode almost immediately
    setattr(rigged_grenade.ndb, NDB_COUNTDOWN_REMAINING, fuse_time)
    
    # Move grenade to the character's location quietly (no movement announcements)
    rigged_grenade.move_to(character.location, quiet=True)
    
    # Establish proximity for auto-defuse system (rigged grenades need this!)
    proximity_list = getattr(rigged_grenade.ndb, NDB_PROXIMITY_UNIVERSAL, None)
    if not proximity_list:
        setattr(rigged_grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        proximity_list = getattr(rigged_grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
    
    # Validate proximity_list is actually a list
    if not isinstance(proximity_list, list):
        proximity_list = []
        setattr(rigged_grenade.ndb, NDB_PROXIMITY_UNIVERSAL, proximity_list)
    
    # Add the triggering character to proximity
    if character not in proximity_list:
        proximity_list.append(character)
    
    # Add other characters in the room to proximity (rigged grenades affect everyone in room)
    for obj in character.location.contents:
        if (hasattr(obj, 'has_account') and obj.has_account and 
            obj != character and obj not in proximity_list):
            proximity_list.append(obj)
    
    splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
    splattercast.msg(f"{DEBUG_PREFIX_THROW}_RIGGED: Established proximity for {rigged_grenade.key}: {[char.key for char in proximity_list]}")
    
    # Start countdown timer
    # Create a closure to handle explosion
    def explode_rigged_grenade():
        """Handle rigged grenade explosion after timer."""
        try:
            # Check dud chance
            dud_chance = getattr(rigged_grenade.db, DB_DUD_CHANCE, 0.0)
            if random.random() < dud_chance:
                if rigged_grenade.location:
                    rigged_grenade.location.msg_contents(MSG_GRENADE_DUD_ROOM.format(grenade=rigged_grenade.key))
                return
            
            # Get blast damage
            blast_damage = getattr(rigged_grenade.db, DB_BLAST_DAMAGE, 10)
            
            # Room explosion
            if rigged_grenade.location:
                rigged_grenade.location.msg_contents(MSG_GRENADE_EXPLODE_ROOM.format(grenade=rigged_grenade.key))
            
            # Apply damage to trigger character
            apply_damage(character, blast_damage)
            character.msg(MSG_GRENADE_DAMAGE.format(grenade=rigged_grenade.key))
            if character.location:
                character.location.msg_contents(
                    MSG_GRENADE_DAMAGE_ROOM.format(victim=character.key, grenade=rigged_grenade.key),
                    exclude=character
                )
            
            # Apply damage to others in proximity
            proximity_list = getattr(rigged_grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            if proximity_list is None:
                proximity_list = []
            
            for other_character in proximity_list:
                if other_character != character and hasattr(other_character, 'msg'):
                    apply_damage(other_character, blast_damage)
                    other_character.msg(MSG_GRENADE_DAMAGE.format(grenade=rigged_grenade.key))
                    if other_character.location:
                        other_character.location.msg_contents(
                            MSG_GRENADE_DAMAGE_ROOM.format(victim=other_character.key, grenade=rigged_grenade.key),
                            exclude=other_character
                        )
            
            # Handle chain reactions if enabled
            if getattr(rigged_grenade.db, DB_CHAIN_TRIGGER, False):
                for obj in proximity_list:
                    if (hasattr(obj, 'db') and 
                        getattr(obj.db, DB_IS_EXPLOSIVE, False) and 
                        obj != rigged_grenade):
                        
                        # Trigger chain explosion
                        if rigged_grenade.location:
                            rigged_grenade.location.msg_contents(
                                MSG_GRENADE_CHAIN_TRIGGER.format(grenade=obj.key))
                        
                        # Start immediate explosion timer (reuse this function's pattern)
                        utils.delay(0.5, lambda: check_rigged_grenade(character, obj))
            
            # Delete the rigged grenade
            rigged_grenade.delete()
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in explode_rigged_grenade: {e}")
    
    # Start the timer
    utils.delay(fuse_time, explode_rigged_grenade)
    
    # Clean up rigging from both exits
    delattr(exit_obj.db, 'rigged_grenade')
    
    # Find and clean up return exit too
    original_exit = getattr(rigged_grenade.db, 'rigged_to_exit', None)
    if original_exit and original_exit.destination:
        destination_room = original_exit.destination
        character_room = character.location
        
        # Look for return exit that might also be rigged
        for obj in destination_room.contents:
            if (hasattr(obj, 'destination') and 
                obj.destination == character_room and
                hasattr(obj.db, 'rigged_grenade') and
                getattr(obj.db, 'rigged_grenade') == rigged_grenade):
                delattr(obj.db, 'rigged_grenade')
                splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: Cleaned up return exit rigging on {obj}")
                break
    
    # Announce timer start
    character.location.msg_contents(f"The {rigged_grenade.key} starts counting down! {fuse_time} seconds!")
    
    splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
    splattercast.msg(f"{DEBUG_PREFIX_THROW}_RIGGED: {character.key} triggered rigged {rigged_grenade.key} on {exit_obj.key}, timer: {fuse_time}s")
    
    # Return True to indicate explosion timer started
    return True


def check_auto_defuse(character):
    """Check for auto-defuse opportunities when character enters a room with live grenades."""
    try:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"AUTO_DEFUSE: Checking for auto-defuse opportunities for {character.key} in {character.location}")
        
        # Find live grenades in the room that have the character in proximity
        live_grenades = []
        
        for obj in character.location.contents:
            splattercast.msg(f"AUTO_DEFUSE: Checking object {obj.key} - is_explosive: {getattr(obj.db, DB_IS_EXPLOSIVE, False)}")
            
            # Check if object is an explosive
            if not getattr(obj.db, DB_IS_EXPLOSIVE, False):
                continue
                
            # Check if grenade is live (pin pulled and timer active)
            pin_pulled = getattr(obj.db, DB_PIN_PULLED, False)
            splattercast.msg(f"AUTO_DEFUSE: {obj.key} pin_pulled: {pin_pulled}")
            if not pin_pulled:
                continue
                
            # Check if grenade has time remaining
            remaining_time = getattr(obj.ndb, NDB_COUNTDOWN_REMAINING, 0)
            splattercast.msg(f"AUTO_DEFUSE: {obj.key} remaining_time: {remaining_time}")
            if remaining_time is None or remaining_time <= 0:
                continue
            
            # Check if character is in this grenade's proximity
            obj_proximity = getattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            splattercast.msg(f"AUTO_DEFUSE: {obj.key} proximity: {[char.key if hasattr(char, 'key') else str(char) for char in obj_proximity]}")
            if obj_proximity and character in obj_proximity:
                # Check if character has already attempted to defuse this grenade
                attempted_by = getattr(obj.ndb, 'defuse_attempted_by', [])
                if attempted_by is None:
                    attempted_by = []
                    
                if character not in attempted_by:
                    live_grenades.append(obj)
                    splattercast.msg(f"AUTO_DEFUSE: Found auto-defuse candidate: {obj.key} (time remaining: {remaining_time}s)")
                else:
                    splattercast.msg(f"AUTO_DEFUSE: {obj.key} already attempted by {character.key}")
            else:
                splattercast.msg(f"AUTO_DEFUSE: {character.key} not in {obj.key} proximity or proximity empty")
        
        if not live_grenades:
            splattercast.msg(f"AUTO_DEFUSE: No auto-defuse opportunities found for {character.key}")
            return
        
        # Auto-defuse attempt for each grenade (like D&D trap detection)
        for grenade in live_grenades:
            attempt_auto_defuse(character, grenade)
            
    except Exception as e:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"AUTO_DEFUSE_ERROR: Error in check_auto_defuse for {character.key}: {e}")


def attempt_auto_defuse(character, grenade):
    """Attempt automatic defuse when entering proximity of live grenade."""
    try:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Mark attempt to prevent spam (same as manual defuse)
        attempted_by = getattr(grenade.ndb, 'defuse_attempted_by', [])
        if attempted_by is None:
            attempted_by = []
        attempted_by.append(character)
        setattr(grenade.ndb, 'defuse_attempted_by', attempted_by)
        
        # Get remaining time for pressure calculation
        remaining_time = getattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 0)
        
        # Calculate difficulty (same as manual defuse)
        base_difficulty = 15  # Base difficulty
        time_pressure = max(0, 10 - remaining_time)  # Gets harder as time runs out
        total_difficulty = base_difficulty + time_pressure
        
        # Auto-defuse uses same skill system as manual defuse
        from world.combat.utils import roll_stat
        
        # Simulate combined stat roll (Intellect + Motorics)
        intellect_roll = roll_stat(character, 'intellect')
        motorics_roll = roll_stat(character, 'motorics')
        combined_roll = intellect_roll + motorics_roll
        
        # Determine success
        success = combined_roll >= total_difficulty
        
        # Announce auto-defuse attempt (more subtle than manual)
        character.msg(f"You notice the live {grenade.key} and instinctively attempt to defuse it...")
        character.location.msg_contents(
            f"{character.key} quickly works on defusing the {grenade.key}.",
            exclude=character
        )
        
        # Debug output
        splattercast.msg(f"AUTO_DEFUSE: {character.key} rolled {combined_roll} vs difficulty {total_difficulty} "
                       f"(base {base_difficulty} + pressure {time_pressure}, {remaining_time}s left) - "
                       f"{'SUCCESS' if success else 'FAILURE'}")
        
        if success:
            handle_auto_defuse_success(character, grenade)
        else:
            handle_auto_defuse_failure(character, grenade)
            
    except Exception as e:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"AUTO_DEFUSE_ERROR: Error in attempt_auto_defuse for {character.key} and {grenade.key}: {e}")


def handle_auto_defuse_success(character, grenade):
    """Handle successful auto-defuse attempt."""
    try:
        # Cancel countdown timer
        timer = getattr(grenade.ndb, NDB_GRENADE_TIMER, None)
        if timer:
            timer.cancel()
            delattr(grenade.ndb, NDB_GRENADE_TIMER)
        
        # Clear countdown state
        setattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 0)
        setattr(grenade.db, DB_PIN_PULLED, False)  # Grenade is now safe
        
        # Success messages (more dramatic than manual defuse)
        character.msg(f"SUCCESS! You instinctively defuse the {grenade.key} just in time!")
        character.location.msg_contents(
            f"{character.key} quickly defuses the {grenade.key}!",
            exclude=character
        )
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"AUTO_DEFUSE_SUCCESS: {character.key} auto-defused {grenade.key}")
        
    except Exception as e:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"AUTO_DEFUSE_ERROR: Error in handle_auto_defuse_success: {e}")


def handle_auto_defuse_failure(character, grenade):
    """Handle failed auto-defuse attempt (less severe than manual defuse failure)."""
    try:
        # Auto-defuse failures have lower chance of early detonation (10% vs 30%)
        early_detonation_chance = 0.1
        
        if random.random() < early_detonation_chance:
            # Early detonation triggered
            character.msg(f"Your hasty defuse attempt accidentally triggers the {grenade.key}!")
            character.location.msg_contents(
                f"{character.key}'s defuse attempt accidentally triggers the {grenade.key}!",
                exclude=character
            )
            
            # Trigger immediate explosion (same as manual defuse)
            timer = getattr(grenade.ndb, NDB_GRENADE_TIMER, None)
            if timer:
                timer.cancel()
            
            # Set very short timer for dramatic effect
            setattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 1)
            utils.delay(1, trigger_auto_defuse_explosion, grenade)
            
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"AUTO_DEFUSE_FAILURE: {character.key} triggered early detonation of {grenade.key}")
        
        else:
            # Failed but no early detonation (more subtle failure message)
            character.msg(f"You notice the {grenade.key} but can't defuse it in time.")
            character.location.msg_contents(
                f"{character.key} notices the {grenade.key} but can't defuse it.",
                exclude=character
            )
            
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"AUTO_DEFUSE_FAILURE: {character.key} failed to auto-defuse {grenade.key} (no early detonation)")
            
    except Exception as e:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"AUTO_DEFUSE_ERROR: Error in handle_auto_defuse_failure: {e}")


def trigger_auto_defuse_explosion(grenade):
    """Trigger early explosion from failed auto-defuse attempt (reuses manual defuse logic)."""
    # Reuse the explosion logic from manual defuse
    from world.combat.utils import apply_damage
    
    try:
        # Check dud chance
        dud_chance = getattr(grenade.db, DB_DUD_CHANCE, 0.0)
        if random.random() < dud_chance:
            if grenade.location:
                grenade.location.msg_contents(MSG_GRENADE_DUD_ROOM.format(grenade=grenade.key))
            return
        
        # Get blast damage
        blast_damage = getattr(grenade.db, DB_BLAST_DAMAGE, 10)
        
        # Room explosion
        if grenade.location:
            grenade.location.msg_contents(MSG_GRENADE_EXPLODE_ROOM.format(grenade=grenade.key))
        
        # Apply damage to all in proximity
        proximity_list = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        if proximity_list is None:
            proximity_list = []
        
        for character in proximity_list:
            if hasattr(character, 'msg'):  # Is a character
                apply_damage(character, blast_damage)
                character.msg(MSG_GRENADE_DAMAGE.format(grenade=grenade.key))
                if character.location:
                    character.location.msg_contents(
                        MSG_GRENADE_DAMAGE_ROOM.format(victim=character.key, grenade=grenade.key),
                        exclude=character
                    )
        
        # Handle chain reactions if enabled
        if getattr(grenade.db, DB_CHAIN_TRIGGER, False):
            for obj in proximity_list:
                if (hasattr(obj, 'db') and 
                    getattr(obj.db, DB_IS_EXPLOSIVE, False) and 
                    obj != grenade):
                    
                    # Trigger chain explosion
                    if grenade.location:
                        grenade.location.msg_contents(
                            MSG_GRENADE_CHAIN_TRIGGER.format(grenade=obj.key))
                    
                    # Start immediate explosion timer
                    utils.delay(0.5, trigger_auto_defuse_explosion, obj)
        
        # Clean up
        grenade.delete()
        
    except Exception as e:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"AUTO_DEFUSE_ERROR: Error in trigger_auto_defuse_explosion: {e}")


class CmdDefuse(Command):
    """
    Defuse live grenades and explosives.
    
    Usage:
        defuse <grenade>
    
    Examples:
        defuse grenade
        defuse flashbang
    
    Attempt to defuse a live grenade using technical skill and dexterity.
    Requires the grenade to be in proximity (within reach). Uses Intellect + 
    Motorics skill check with time pressure - the less time remaining, the 
    harder the defuse attempt becomes.
    
    WARNING: Failed defuse attempts may trigger early detonation!
    Each grenade can only be defused once per character to prevent spam.
    """
    
    key = "defuse"
    locks = "cmd:all()"
    help_category = "Combat"
    
    def func(self):
        """Execute defuse command."""
        if not self.args:
            self.caller.msg("Defuse what?")
            return
        
        grenade_name = self.args.strip()
        
        # Find grenade in proximity
        grenade = self.find_grenade_in_proximity(grenade_name)
        if not grenade:
            return
        
        # Validate grenade state
        if not self.validate_grenade_for_defuse(grenade):
            return
        
        # Check one-attempt-per-grenade limit
        if self.already_attempted_defuse(grenade):
            self.caller.msg(f"You have already attempted to defuse the {grenade.key}.")
            return
        
        # Execute defuse attempt
        self.attempt_defuse(grenade)
    
    def find_grenade_in_proximity(self, grenade_name):
        """Find grenade in proximity or establish proximity for nearby grenades."""
        # First check existing proximity relationships
        proximity_candidates = []
        
        # Check both room contents AND character inventory for proximity candidates
        all_candidates = list(self.caller.location.contents) + list(self.caller.contents)
        
        for obj in all_candidates:
            if (grenade_name.lower() in obj.key.lower() and 
                getattr(obj.db, DB_IS_EXPLOSIVE, False)):
                
                # Check if caller is already in this object's proximity
                obj_proximity = getattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, [])
                if obj_proximity and self.caller in obj_proximity:
                    proximity_candidates.append(obj)
        
        # If found in existing proximity, return it
        if proximity_candidates:
            if len(proximity_candidates) > 1:
                self.caller.msg(f"Multiple {grenade_name}s are within reach. Be more specific.")
                return None
            return proximity_candidates[0]
        
        # If not in proximity, check for physical presence and establish mutual proximity
        physical_candidates = []
        
        # Check both room contents AND character inventory for physical candidates
        for obj in all_candidates:
            if (grenade_name.lower() in obj.key.lower() and 
                getattr(obj.db, DB_IS_EXPLOSIVE, False)):
                
                # Check if grenade is live (either pin pulled OR rigged to exit)
                pin_pulled = getattr(obj.db, DB_PIN_PULLED, False)
                is_rigged = getattr(obj.db, 'rigged_to_exit', None) is not None
                
                if pin_pulled or is_rigged:
                    physical_candidates.append(obj)
        
        if not physical_candidates:
            self.caller.msg(f"You don't see any armed '{grenade_name}' within reach to defuse.")
            return None
        
        if len(physical_candidates) > 1:
            self.caller.msg(f"Multiple {grenade_name}s are nearby. Be more specific.")
            return None
        
        # Establish mutual proximity and return the grenade
        grenade = physical_candidates[0]
        
        # Different message for held vs room grenades
        if grenade.location == self.caller:
            self.caller.msg(f"You examine the {grenade.key} in your hands, preparing to defuse it...")
        else:
            self.caller.msg(f"You move closer to the {grenade.key}, entering its blast radius...")
            self.establish_mutual_proximity(grenade)
        
        return grenade
    
    def establish_mutual_proximity(self, grenade):
        """Establish mutual proximity between character and grenade."""
        # Add character to grenade's proximity (enters blast radius)
        grenade_proximity = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        if not isinstance(grenade_proximity, list):
            grenade_proximity = []
        
        if self.caller not in grenade_proximity:
            grenade_proximity.append(self.caller)
            
            # Also establish proximity with other characters already in the grenade's proximity
            for other_char in list(grenade_proximity):  # Use list() to avoid modification during iteration
                if (hasattr(other_char, 'ndb') and other_char != self.caller):
                    other_proximity = getattr(other_char.ndb, NDB_PROXIMITY_UNIVERSAL, [])
                    if not isinstance(other_proximity, list):
                        other_proximity = []
                        setattr(other_char.ndb, NDB_PROXIMITY_UNIVERSAL, other_proximity)
                    
                    if self.caller not in other_proximity:
                        other_proximity.append(self.caller)
        
        setattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, grenade_proximity)
        
        # Add grenade to character's proximity
        char_proximity = getattr(self.caller.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        if not isinstance(char_proximity, list):
            char_proximity = []
            setattr(self.caller.ndb, NDB_PROXIMITY_UNIVERSAL, char_proximity)
        
        if grenade not in char_proximity:
            char_proximity.append(grenade)
            
            # Also add other characters in the grenade's proximity to this character's proximity
            for other_char in grenade_proximity:
                if (hasattr(other_char, 'ndb') and other_char != self.caller and 
                    other_char not in char_proximity):
                    char_proximity.append(other_char)
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        if splattercast:
            splattercast.msg(f"DEFUSE_PROXIMITY: {self.caller.key} established mutual proximity with {grenade.key} "
                           f"(grenade proximity: {[c.key if hasattr(c, 'key') else str(c) for c in grenade_proximity]})")
    
    def validate_grenade_for_defuse(self, grenade):
        """Validate that grenade can be defused."""
        # Must be explosive
        if not getattr(grenade.db, DB_IS_EXPLOSIVE, False):
            self.caller.msg(f"The {grenade.key} is not an explosive device.")
            return False
        
        # Must be live (pin pulled OR rigged)
        pin_pulled = getattr(grenade.db, DB_PIN_PULLED, False)
        is_rigged = getattr(grenade.db, 'rigged_to_exit', None) is not None
        
        if not (pin_pulled or is_rigged):
            self.caller.msg(f"The {grenade.key} is not armed - no need to defuse it.")
            return False
        
        # For rigged grenades, no timer check needed (they're not counting down)
        if is_rigged:
            return True
        
        # For pin-pulled grenades, check timer
        remaining_time = getattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 0)
        if remaining_time is None or remaining_time <= 0:
            self.caller.msg(f"The {grenade.key} has already exploded or is about to explode!")
            return False
        
        return True
    
    def already_attempted_defuse(self, grenade):
        """Check if caller has already attempted to defuse this grenade."""
        attempted_by = getattr(grenade.ndb, 'defuse_attempted_by', [])
        if attempted_by is None:
            attempted_by = []
            setattr(grenade.ndb, 'defuse_attempted_by', attempted_by)
        
        return self.caller in attempted_by
    
    def attempt_defuse(self, grenade):
        """Execute the defuse attempt with skill checks."""
        # Mark attempt to prevent spam
        attempted_by = getattr(grenade.ndb, 'defuse_attempted_by', [])
        if attempted_by is None:
            attempted_by = []
        attempted_by.append(self.caller)
        setattr(grenade.ndb, 'defuse_attempted_by', attempted_by)
        
        # Check if this is a rigged grenade (different difficulty calculation)
        is_rigged = getattr(grenade.db, 'rigged_to_exit', None) is not None
        
        if is_rigged:
            # Rigged grenades: base difficulty only (no time pressure)
            base_difficulty = 18  # Slightly harder base (trap disarmament)
            time_pressure = 0
            total_difficulty = base_difficulty
            remaining_time = "N/A"
        else:
            # Live grenades: time pressure difficulty
            remaining_time = getattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 0)
            base_difficulty = 15  # Base difficulty
            time_pressure = max(0, 10 - remaining_time)  # Gets harder as time runs out
            total_difficulty = base_difficulty + time_pressure
        
        # Get character stats (fallback to 1 if not found)
        intellect = getattr(self.caller, 'intellect', 1)
        motorics = getattr(self.caller, 'motorics', 1)
        
        # Roll Intellect + Motorics (using existing roll pattern)
        from world.combat.utils import roll_stat
        
        # Simulate combined stat roll (would need proper implementation)
        intellect_roll = roll_stat(self.caller, 'intellect')
        motorics_roll = roll_stat(self.caller, 'motorics')
        combined_roll = intellect_roll + motorics_roll
        
        # Determine success
        success = combined_roll >= total_difficulty
        
        # Announce attempt (different message for rigged vs live)
        if is_rigged:
            self.caller.msg(f"You carefully examine the rigged {grenade.key} and attempt to disarm the trap...")
            self.caller.location.msg_contents(
                f"{self.caller.key} carefully works on disarming the rigged {grenade.key}.",
                exclude=self.caller
            )
        else:
            self.caller.msg(f"You carefully examine the live {grenade.key} and attempt to defuse it...")
            self.caller.location.msg_contents(
                f"{self.caller.key} carefully works on defusing the {grenade.key}.",
                exclude=self.caller
            )
        
        # Debug output
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        if splattercast:
            grenade_type = "rigged" if is_rigged else "live"
            splattercast.msg(f"DEFUSE: {self.caller.key} rolled {combined_roll} vs difficulty {total_difficulty} "
                           f"(base {base_difficulty} + pressure {time_pressure}, {remaining_time}s left, {grenade_type}) - "
                           f"{'SUCCESS' if success else 'FAILURE'}")
        
        if success:
            self.handle_defuse_success(grenade)
        else:
            self.handle_defuse_failure(grenade)
    
    def handle_defuse_success(self, grenade):
        """Handle successful defuse attempt."""
        # Cancel countdown timer if active
        timer = getattr(grenade.ndb, NDB_GRENADE_TIMER, None)
        if timer:
            timer.cancel()
            delattr(grenade.ndb, NDB_GRENADE_TIMER)
        
        # Clear countdown state
        setattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 0)
        setattr(grenade.db, DB_PIN_PULLED, False)  # Grenade is now safe
        
        # Clean up rigging if this was a rigged grenade
        self.cleanup_rigging(grenade)
        
        # Clear proximity relationships (grenade is now safe)
        self.clear_grenade_proximity(grenade)
        
        # Success messages
        self.caller.msg(f"SUCCESS! You successfully defuse the {grenade.key}. It is now safe.")
        self.caller.location.msg_contents(
            f"{self.caller.key} successfully defuses the {grenade.key}!",
            exclude=self.caller
        )
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        if splattercast:
            splattercast.msg(f"DEFUSE_SUCCESS: {self.caller.key} defused {grenade.key}")
    
    def clear_grenade_proximity(self, grenade):
        """Clear all proximity relationships for a defused grenade."""
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        
        # Get grenade's proximity list
        grenade_proximity = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        if not isinstance(grenade_proximity, list):
            return
        
        # Remove grenade from all characters' proximity lists
        for character in list(grenade_proximity):
            if hasattr(character, 'ndb'):
                char_proximity = getattr(character.ndb, NDB_PROXIMITY_UNIVERSAL, [])
                if isinstance(char_proximity, list) and grenade in char_proximity:
                    char_proximity.remove(grenade)
                    if splattercast:
                        splattercast.msg(f"DEFUSE_PROXIMITY_CLEAR: Removed {grenade.key} from {character.key}'s proximity")
        
        # Clear grenade's proximity list
        setattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        
        if splattercast:
            splattercast.msg(f"DEFUSE_PROXIMITY_CLEAR: Cleared all proximity for defused {grenade.key}")
    
    def cleanup_rigging(self, grenade):
        """Clean up rigging references when grenade is defused."""
        rigged_to_exit = getattr(grenade.db, 'rigged_to_exit', None)
        if rigged_to_exit:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            
            # Clean up main exit
            if hasattr(rigged_to_exit.db, 'rigged_grenade'):
                delattr(rigged_to_exit.db, 'rigged_grenade')
                if splattercast:
                    splattercast.msg(f"DEFUSE_CLEANUP: Removed rigging from {rigged_to_exit}")
            
            # Find and clean up return exit
            if rigged_to_exit.destination:
                destination_room = rigged_to_exit.destination
                grenade_room = grenade.location if hasattr(grenade, 'location') else self.caller.location
                
                for obj in destination_room.contents:
                    if (hasattr(obj, 'destination') and 
                        obj.destination == grenade_room and
                        hasattr(obj.db, 'rigged_grenade') and
                        getattr(obj.db, 'rigged_grenade') == grenade):
                        delattr(obj.db, 'rigged_grenade')
                        if splattercast:
                            splattercast.msg(f"DEFUSE_CLEANUP: Removed rigging from return exit {obj}")
                        break
            
            # Clean up grenade's rigging reference
            delattr(grenade.db, 'rigged_to_exit')
            if hasattr(grenade.db, 'rigged_by'):
                delattr(grenade.db, 'rigged_by')
            
            # Announce trap disarmament
            self.caller.msg("You also disarm the trap rigging mechanism.")
            self.caller.location.msg_contents(
                f"{self.caller.key} disarms the trap rigging on the {grenade.key}.",
                exclude=self.caller
            )
            
            if splattercast:
                splattercast.msg(f"DEFUSE_CLEANUP: Fully cleaned up rigging for {grenade.key}")
    
    def handle_defuse_failure(self, grenade):
        """Handle failed defuse attempt with potential early detonation."""
        # 30% chance of early detonation on failure
        early_detonation_chance = 0.3
        
        if random.random() < early_detonation_chance:
            # Early detonation triggered
            self.caller.msg(f"FAILURE! Your clumsy attempt triggers the {grenade.key} early!")
            self.caller.location.msg_contents(
                f"{self.caller.key}'s failed defuse attempt triggers the {grenade.key}!",
                exclude=self.caller
            )
            
            # Trigger immediate explosion (reuse existing explosion logic)
            timer = getattr(grenade.ndb, NDB_GRENADE_TIMER, None)
            if timer:
                timer.cancel()
            
            # Set very short timer for dramatic effect
            setattr(grenade.ndb, NDB_COUNTDOWN_REMAINING, 1)
            utils.delay(1, self.trigger_early_explosion, grenade)
            
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            if splattercast:
                splattercast.msg(f"DEFUSE_FAILURE: {self.caller.key} triggered early detonation of {grenade.key}")
        
        else:
            # Failed but no early detonation
            self.caller.msg(f"FAILURE! You fail to defuse the {grenade.key}, but it continues ticking...")
            self.caller.location.msg_contents(
                f"{self.caller.key} fails to defuse the {grenade.key}.",
                exclude=self.caller
            )
            
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            if splattercast:
                splattercast.msg(f"DEFUSE_FAILURE: {self.caller.key} failed to defuse {grenade.key} (no early detonation)")
    
    def trigger_early_explosion(self, grenade):
        """Trigger early explosion from failed defuse attempt."""
        # Reuse the explosion logic from CmdPull
        from world.combat.utils import apply_damage
        
        try:
            # Check dud chance
            dud_chance = getattr(grenade.db, DB_DUD_CHANCE, 0.0)
            if random.random() < dud_chance:
                if grenade.location:
                    grenade.location.msg_contents(MSG_GRENADE_DUD_ROOM.format(grenade=grenade.key))
                return
            
            # Get blast damage
            blast_damage = getattr(grenade.db, DB_BLAST_DAMAGE, 10)
            
            # Room explosion
            if grenade.location:
                grenade.location.msg_contents(MSG_GRENADE_EXPLODE_ROOM.format(grenade=grenade.key))
            
            # Apply damage to all in proximity
            proximity_list = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            if proximity_list is None:
                proximity_list = []
            
            for character in proximity_list:
                if hasattr(character, 'msg'):  # Is a character
                    apply_damage(character, blast_damage)
                    character.msg(MSG_GRENADE_DAMAGE.format(grenade=grenade.key))
                    if character.location:
                        character.location.msg_contents(
                            MSG_GRENADE_DAMAGE_ROOM.format(victim=character.key, grenade=grenade.key),
                            exclude=character
                        )
            
            # Handle chain reactions if enabled
            if getattr(grenade.db, DB_CHAIN_TRIGGER, False):
                for obj in proximity_list:
                    if (hasattr(obj, 'db') and 
                        getattr(obj.db, DB_IS_EXPLOSIVE, False) and 
                        obj != grenade):
                        
                        # Trigger chain explosion
                        if grenade.location:
                            grenade.location.msg_contents(
                                MSG_GRENADE_CHAIN_TRIGGER.format(grenade=obj.key))
                        
                        # Start immediate explosion timer
                        utils.delay(0.5, self.trigger_early_explosion, obj)
            
            # Clean up
            grenade.delete()
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in trigger_early_explosion: {e}")
