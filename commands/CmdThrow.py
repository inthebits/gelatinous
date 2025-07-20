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
        
        # Check if object exists in hands (wielded)
        if not hasattr(self.caller, 'hands'):
            self.caller.msg(MSG_THROW_NOTHING_WIELDED)
            return None
        
        # Find object in hands
        obj = None
        hand_name = None
        for hand, wielded_obj in self.caller.hands.items():
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
        # Check if grenade requires pin and if pin is pulled
        requires_pin = getattr(obj.db, DB_REQUIRES_PIN, True)
        if requires_pin:
            pin_pulled = getattr(obj.db, DB_PIN_PULLED, False)
            if not pin_pulled:
                self.caller.msg(MSG_THROW_UNPINNED_GRENADE)
                return False
        
        # Check if grenade timer has expired
        if hasattr(obj.ndb, NDB_COUNTDOWN_REMAINING):
            remaining = getattr(obj.ndb, NDB_COUNTDOWN_REMAINING, 0)
            if remaining <= 0:
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
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: Looking for target '{self.target_name}' in {self.caller.location}")
        
        # First check current room
        target = self.caller.search(self.target_name, location=self.caller.location, quiet=True)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: search result = {target}, has_hands = {hasattr(target, 'hands') if target else 'N/A'}")
        
        if target and hasattr(target, 'hands'):  # Is a character
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: find_target: Found valid character target: {target}")
            return target
        
        # Check aimed room for cross-room targeting
        aim_direction = getattr(self.caller.ndb, NDB_AIMING_DIRECTION, None)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: aim_direction = {aim_direction}")
        
        if aim_direction:
            destination = self.get_destination_room(aim_direction)
            if destination:
                target = self.caller.search(self.target_name, location=destination, quiet=True)
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: find_target: cross-room search result = {target}")
                if target and hasattr(target, 'hands'):
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
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: Looking for exit '{direction}' in {self.caller.location}")
        
        # Find exit in current room
        exit_obj = self.caller.search(direction, location=self.caller.location, quiet=True)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: search result = {exit_obj}, has_destination = {hasattr(exit_obj, 'destination') if exit_obj else 'N/A'}")
        
        if not exit_obj or not hasattr(exit_obj, 'destination'):
            # Check if it might be a character name mistaken for direction
            char_search = self.caller.search(direction, location=self.caller.location, quiet=True)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: char_search result = {char_search}, has_hands = {hasattr(char_search, 'hands') if char_search else 'N/A'}")
            
            if char_search and hasattr(char_search, 'hands'):
                splattercast.msg(f"{DEBUG_PREFIX_THROW}_TEMPLATE: get_destination_room: '{direction}' is a character, suggesting 'at' syntax")
                self.caller.msg(MSG_THROW_SUGGEST_AT_SYNTAX.format(
                    object=self.object_name, target=direction))
                return None
            
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_FAIL: get_destination_room: Invalid direction '{direction}'")
            self.caller.msg(MSG_THROW_INVALID_DIRECTION.format(direction=direction))
            return None
        
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: get_destination_room: Found valid exit {exit_obj} -> {exit_obj.destination}")
        return exit_obj.destination
    
    def select_random_target_in_room(self, room):
        """Select random character in room for proximity assignment."""
        if not room:
            return None
        
        characters = [obj for obj in room.contents if hasattr(obj, 'hands') and obj != self.caller]
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
        for hand_name, wielded_obj in self.caller.hands.items():
            if wielded_obj == obj:
                self.caller.hands[hand_name] = None
                break
    
    def start_flight(self, obj, destination, target, is_weapon=False):
        """Start object flight with timer."""
        # Announce throw in origin room
        self.announce_throw_origin(obj, destination, target)
        
        # Add to room's flying objects
        if not hasattr(self.caller.location.ndb, NDB_FLYING_OBJECTS):
            setattr(self.caller.location.ndb, NDB_FLYING_OBJECTS, [])
        
        flying_objects = getattr(self.caller.location.ndb, NDB_FLYING_OBJECTS)
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
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: {self.caller} started flight for {obj} to {destination}")
    
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
            # Get flight data
            destination = obj.ndb.flight_destination
            target = obj.ndb.flight_target
            origin = obj.ndb.flight_origin
            is_weapon = getattr(obj.ndb, 'flight_is_weapon', False)
            thrower = getattr(obj.ndb, 'flight_thrower', None)
            
            # Clean up origin room flying objects
            if origin and hasattr(origin.ndb, NDB_FLYING_OBJECTS):
                flying_objects = getattr(origin.ndb, NDB_FLYING_OBJECTS)
                if obj in flying_objects:
                    flying_objects.remove(obj)
            
            # Move object to destination
            if destination:
                obj.move_to(destination)
                
                # Announce arrival
                if destination != origin:
                    # Determine arrival direction
                    arrival_dir = self.get_arrival_direction(origin, destination)
                    message = MSG_THROW_ARRIVAL.format(object=obj.key, direction=arrival_dir)
                    destination.msg_contents(message)
                
                # Handle landing and proximity
                self.handle_landing(obj, destination, target, is_weapon, thrower)
            
            # Clean up flight data
            del obj.ndb.flight_destination
            del obj.ndb.flight_target  
            del obj.ndb.flight_origin
            del obj.ndb.flight_is_weapon
            del obj.ndb.flight_thrower
            
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"{DEBUG_PREFIX_THROW}_ERROR: Error in complete_flight: {e}")
            # Failsafe: move object to origin if destination fails
            if hasattr(obj.ndb, 'flight_origin') and obj.ndb.flight_origin:
                obj.move_to(obj.ndb.flight_origin)
    
    def get_arrival_direction(self, origin, destination):
        """Determine arrival direction for announcement."""
        # Simple implementation - would need room connection mapping for accuracy
        return "somewhere"
    
    def handle_landing(self, obj, destination, target, is_weapon, thrower):
        """Handle object landing and proximity assignment."""
        # Weapon combat resolution
        if is_weapon and target:
            self.resolve_weapon_hit(obj, target, thrower)
        
        # Utility object bounce
        elif target and not is_weapon:
            target.location.msg_contents(MSG_THROW_UTILITY_BOUNCE.format(
                object=obj.key, target=target.key))
        
        # Assign proximity for universal proximity system
        self.assign_landing_proximity(obj, target)
        
        # Handle grenade-specific landing
        if self.is_explosive(obj):
            self.handle_grenade_landing(obj, target)
        
        # General landing announcement
        if target:
            message = MSG_THROW_LANDING_PROXIMITY.format(object=obj.key, target=target.key)
        else:
            message = MSG_THROW_LANDING_ROOM.format(object=obj.key)
        
        destination.msg_contents(message)
    
    def resolve_weapon_hit(self, weapon, target, thrower):
        """Resolve weapon throw hit/miss and damage."""
        # Simple hit resolution - could be enhanced with accuracy system
        hit_chance = 0.7  # 70% base hit chance
        
        if random.random() <= hit_chance:
            # Hit - apply damage
            base_damage = getattr(weapon.db, 'damage', 1)
            total_damage = random.randint(1, 6) + base_damage
            
            apply_damage(target, total_damage)
            
            target.msg(MSG_THROW_WEAPON_HIT.format(weapon=weapon.key, target=target.key))
            thrower.msg(f"Your {weapon.key} strikes {target.key}!")
            
            # Establish proximity if hit
            if not hasattr(target.ndb, NDB_PROXIMITY_UNIVERSAL):
                setattr(target.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            proximity_list = getattr(target.ndb, NDB_PROXIMITY_UNIVERSAL)
            if thrower not in proximity_list:
                proximity_list.append(thrower)
        
        else:
            # Miss
            target.msg(MSG_THROW_WEAPON_MISS.format(weapon=weapon.key, target=target.key))
            thrower.msg(f"Your {weapon.key} misses {target.key}!")
    
    def assign_landing_proximity(self, obj, target):
        """Assign proximity for universal proximity system."""
        if not hasattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL):
            setattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL, [])
        
        proximity_list = getattr(obj.ndb, NDB_PROXIMITY_UNIVERSAL)
        
        if target:
            # Add target to object proximity
            if target not in proximity_list:
                proximity_list.append(target)
            
            # Inherit target's existing proximity relationships
            if hasattr(target.ndb, NDB_PROXIMITY_UNIVERSAL):
                target_proximity = getattr(target.ndb, NDB_PROXIMITY_UNIVERSAL)
                for character in target_proximity:
                    if character not in proximity_list:
                        proximity_list.append(character)
    
    def handle_grenade_landing(self, grenade, target):
        """Handle grenade-specific landing mechanics."""
        # If grenade lands near someone, everyone in their proximity gets added
        if target and hasattr(target.ndb, NDB_PROXIMITY_UNIVERSAL):
            target_proximity = getattr(target.ndb, NDB_PROXIMITY_UNIVERSAL)
            grenade_proximity = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            
            for character in target_proximity:
                if character not in grenade_proximity:
                    grenade_proximity.append(character)
            
            setattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, grenade_proximity)
        
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"{DEBUG_PREFIX_THROW}_SUCCESS: Grenade {grenade} landed with proximity: {getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])}")


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
        
        # Find grenade in hands
        grenade = None
        for hand, wielded_obj in getattr(self.caller, 'hands', {}).items():
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
            
            # Get proximity list
            proximity_list = getattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [])
            
            # Announce explosion
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
        
        # Check for free hands
        free_hand = None
        for hand_name, wielded_obj in getattr(self.caller, 'hands', {}).items():
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
        self.caller.hands[hand_name] = obj
        
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
    someone tries to pass through that exit. The grenade must have its
    pin pulled before rigging.
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
        
        # Find grenade in hands
        grenade = None
        for hand, wielded_obj in getattr(self.caller, 'hands', {}).items():
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
        
        # Check if pin is pulled
        if not getattr(grenade.db, DB_PIN_PULLED, False):
            self.caller.msg(MSG_RIG_NOT_PINNED)
            return
        
        # Find exit
        exit_obj = self.caller.search(self.exit_name, location=self.caller.location, quiet=True)
        if not exit_obj or not hasattr(exit_obj, 'destination'):
            self.caller.msg(MSG_RIG_INVALID_EXIT.format(exit=self.exit_name))
            return
        
        # Check if exit already rigged
        if hasattr(exit_obj.db, 'rigged_grenade'):
            self.caller.msg(MSG_RIG_EXIT_ALREADY_RIGGED)
            return
        
        # Rig the grenade
        self.rig_grenade(grenade, exit_obj)
    
    def rig_grenade(self, grenade, exit_obj):
        """Rig the grenade to the exit."""
        # Remove from hand
        for hand_name, wielded_obj in self.caller.hands.items():
            if wielded_obj == grenade:
                self.caller.hands[hand_name] = None
                break
        
        # Move grenade to exit (conceptually attached)
        grenade.move_to(exit_obj)
        
        # Set up rigging
        setattr(exit_obj.db, 'rigged_grenade', grenade)
        setattr(grenade.db, 'rigged_to_exit', exit_obj)
        
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


# Helper function to check for rigged grenades (called from movement)
def check_rigged_grenade(character, exit_obj):
    """Check if character triggers a rigged grenade."""
    if not hasattr(exit_obj.db, 'rigged_grenade'):
        return False
    
    grenade = getattr(exit_obj.db, 'rigged_grenade')
    if not grenade:
        return False
    
    # Trigger explosion
    character.msg(MSG_RIG_TRIGGERED.format(object=grenade.key))
    character.location.msg_contents(
        MSG_RIG_TRIGGERED_ROOM.format(object=grenade.key, victim=character.key),
        exclude=character
    )
    
    # Set proximity to triggerer and explode
    setattr(grenade.ndb, NDB_PROXIMITY_UNIVERSAL, [character])
    
    # Explode immediately
    pull_cmd = CmdPull()
    pull_cmd.explode_grenade(grenade)
    
    # Clean up rigging
    delattr(exit_obj.db, 'rigged_grenade')
    
    return True
