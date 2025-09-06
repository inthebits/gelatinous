from evennia import Command
from evennia.utils.search import search_object
from world.combat.messages import get_combat_message
from evennia.comms.models import ChannelDB
from world.weather import weather_system
from world.weather.weather_messages import WEATHER_INTENSITY

class CmdHeal(Command):
    """
    Instantly heal a target character using the medical system.

    Usage:
        @heal <target> [= <amount>]
        @heal here [= <amount>]
        @heal <room #> [= <amount>]
    
    Without amount: Completely heal target (remove all medical conditions)
    With amount: Heal a specific number of medical conditions (least severe first)
    
    Examples:
        @heal bob - Completely heal bob
        @heal here = 3 - Heal 3 conditions from everyone here
        @heal #123 - Fully heal everyone in room #123
    """

    key = "@heal"
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        if not self.args:
            caller.msg("|rUsage: @heal <target|here|room #> [= <amount>]|n")
            return

        parts = self.args.split("=", 1)
        target_name = parts[0].strip()
        amount = None

        if len(parts) > 1:
            try:
                amount = int(parts[1].strip())
                if amount < 0:
                    caller.msg("|rAmount must be zero or positive.|n")
                    return
            except ValueError:
                caller.msg("|rAmount must be an integer.|n")
                return

        targets = []

        # Handle 'here' keyword
        if target_name.lower() == "here":
            location = caller.location
            if not location:
                caller.msg("|rYou have no location.|n")
                return
            # Heal all characters in location (both PCs and NPCs)
            from typeclasses.characters import Character
            targets = [obj for obj in location.contents if isinstance(obj, Character)]
            if not targets:
                caller.msg("|yNo healable targets found in this location.|n")
                return
            target_desc = f"everyone in {location.key}"
        # Handle room dbref (number)
        elif target_name.startswith("#") and target_name[1:].isdigit():
            room = search_object(target_name)
            if not room:
                caller.msg(f"|rNo room found with dbref {target_name}.|n")
                return
            room = room[0]
            # Heal all characters in room (both PCs and NPCs)
            from typeclasses.characters import Character
            targets = [obj for obj in room.contents if isinstance(obj, Character)]
            if not targets:
                caller.msg(f"|yNo healable targets found in {room.key}.|n")
                return
            target_desc = f"everyone in {room.key}"
        # Handle character dbref (number)
        elif target_name.isdigit():
            char = search_object(f"#{target_name}")
            if not char:
                caller.msg(f"|rNo character found with dbref #{target_name}.|n")
                return
            char = char[0]
            targets = [char]
            target_desc = char.key
        else:
            # Normal name search
            matches = search_object(target_name)
            if not matches:
                caller.msg(f"|rNo character named '{target_name}' found.|n")
                return
            target = matches[0]
            targets = [target]
            target_desc = target.key

        # Heal all targets using medical system
        for target in targets:
            # Check if target has medical system
            if not hasattr(target, 'medical_state') or not target.medical_state:
                caller.msg(f"|r{target.key} has no medical system to heal.|n")
                continue
            
            # Get current condition count
            conditions_before = len(target.medical_state.conditions)
            
            # Full heal - complete medical restoration
            if amount is None:
                medical_state = target.medical_state
                
                # Clear all conditions
                medical_state.conditions.clear()
                
                # Restore all organs to full health
                organs_healed = 0
                for organ in medical_state.organs.values():
                    if organ.current_hp < organ.max_hp:
                        organ.current_hp = organ.max_hp
                        organs_healed += 1
                
                # Restore vital signs
                medical_state.blood_level = 100.0
                medical_state.pain_level = 0.0
                medical_state.consciousness = 100.0
                
                target.save_medical_state()
                caller.msg(f"|g{target.key} fully healed - cleared all {conditions_before} conditions, healed {organs_healed} organs, and restored vital signs.|n")
            else:
                # Partial heal - heal a limited number of conditions
                conditions_to_heal = min(amount, conditions_before)
                for _ in range(conditions_to_heal):
                    if target.medical_state.conditions:
                        # Remove the least severe condition first
                        condition = min(target.medical_state.conditions.values(), 
                                      key=lambda c: c.get('severity', 1))
                        target.medical_state.conditions.pop(next(
                            k for k, v in target.medical_state.conditions.items() 
                            if v == condition), None)
                
                target.save_medical_state()
                conditions_after = len(target.medical_state.conditions)
                healed_count = conditions_before - conditions_after
                caller.msg(f"|g{target.key} healed {healed_count} conditions ({conditions_after} remaining).|n")

        if len(targets) > 1:
            caller.msg(f"|gHealed {len(targets)} targets in {target_desc}.|n")

class CmdPeace(Command):
    """
    Instantly end all combat in your current room or a specified room.

    Usage:
        @peace
        @peace <room #>

    This will stop all combat handlers in your current location or in the specified room.
    """

    key = "@peace"
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"

    def func(self):
        caller = self.caller
        splattercast = ChannelDB.objects.get_channel("Splattercast")

        # Default to caller's location
        location = caller.location

        # If a room dbref is provided, use that instead
        if self.args:
            room_arg = self.args.strip()
            if room_arg.startswith("#") and room_arg[1:].isdigit():
                room = search_object(room_arg)
                if not room:
                    caller.msg(f"|rNo room found with dbref {room_arg}.|n")
                    splattercast.msg(f"@peace failed: No room found with dbref {room_arg}.")
                    return
                location = room[0]
            else:
                caller.msg("|rUsage: @peace [<room #>]|n")
                splattercast.msg("@peace failed: Invalid room argument.")
                return

        if not location:
            caller.msg("|rYou have no location.|n")
            splattercast.msg("@peace failed: Caller has no location.")
            return

        # Find all combat handlers on this location
        handlers = [script for script in location.scripts.all() if script.key == "combat_handler"]
        if not handlers:
            caller.msg(f"|yNo combat to end in {location.key}.|n")
            splattercast.msg(f"@peace: No combat to end in {location.key}.")
            return

        for handler in handlers:
            handler.stop()
        caller.msg(f"|gAll combat in {location.key} has been ended.|n")
        splattercast.msg(f"@peace: All combat in {location.key} has been ended by {caller.key}.")


class CmdTestDeathCurtain(Command):
    """
    Test the death curtain animation with various messages.
    
    Usage:
        @testdeathcurtain [message]
        
    Examples:
        @testdeathcurtain
        @testdeathcurtain You feel your strength ebbing away...
        @testdeathcurtain The darkness consumes you
    """
    
    key = "@testdeathcurtain"
    aliases = ["@testcurtain", "@curtaintest"]
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"
    
    def func(self):
        """Execute the command."""
        from typeclasses.curtain_of_death import show_death_curtain
        
        caller = self.caller
        
        # Use custom message if provided, otherwise use default
        if self.args.strip():
            message = self.args.strip()
            caller.msg(f"|yStarting death curtain animation with message: '{message}'|n")
        else:
            message = None
            caller.msg("|yStarting death curtain animation with default message...|n")
            
        show_death_curtain(caller, message)


class CmdWeather(Command):
    """
    Show or set current weather conditions.
    
    Usage:
        @weather                    - Show current weather
        @weather <weather_type>     - Set weather type
        @weather list               - List available weather types
    
    Examples:
        @weather
        @weather clear
        @weather rainy_thunderstorm
        @weather list
    """
    
    key = "@weather"
    aliases = ["weather"]
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"
    
    def func(self):
        """Execute the weather command."""
        if not self.args:
            # Show current weather details
            from world.weather.time_system import get_current_time_period
            import time
            
            current_weather = weather_system.get_current_weather()
            intensity = weather_system.get_weather_intensity()
            time_period = get_current_time_period()
            real_time = time.strftime("%H:%M:%S")
            weather_key = f"{current_weather}_{time_period}"
            
            self.caller.msg("|WWeather System Status:|n")
            self.caller.msg(f"Current weather: |Y{current_weather}|n (intensity: {intensity})")
            self.caller.msg(f"Time period: |Y{time_period}|n")
            self.caller.msg(f"Real time: {real_time}")
            self.caller.msg(f"Weather key: |c{weather_key}|n")
            
            # Check if this weather/time combination has messages
            from world.weather.weather_messages import WEATHER_MESSAGES
            region_messages = WEATHER_MESSAGES.get('default', {})
            if weather_key in region_messages:
                self.caller.msg(f"Message pool: |gActive|n ({weather_key})")
            elif current_weather in region_messages:
                self.caller.msg(f"Message pool: |yFallback|n ({current_weather})")
            else:
                self.caller.msg(f"Message pool: |rNone found|n")
            return
            
        args = self.args.strip().lower()
        
        if args == "list":
            # List available weather types
            self.caller.msg("|WAvailable Weather Types:|n")
            for weather_type, intensity in WEATHER_INTENSITY.items():
                self.caller.msg(f"  |Y{weather_type}|n ({intensity})")
            return
            
        # Set weather
        if args in WEATHER_INTENSITY:
            weather_system.set_weather(args)
            intensity = WEATHER_INTENSITY[args]
            self.caller.msg(f"Weather set to: |Y{args}|n (intensity: {intensity})")
        else:
            self.caller.msg(f"Unknown weather type: {args}. Use '@weather list' to see options.")
