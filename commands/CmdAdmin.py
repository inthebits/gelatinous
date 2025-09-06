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
        @heal <target> [= <condition_type>]
        @heal <target> [= <condition_type> <amount>]
        @heal here [= <amount>]
        @heal <room #> [= <amount>]
    
    Without amount: Completely heal target (remove all medical conditions)
    With amount: Heal a specific number of medical conditions (least severe first)
    With condition_type: Heal only specific types of conditions
    
    Examples:
        @heal bob - Completely heal bob
        @heal bob = bleeding - Heal all bleeding conditions
        @heal bob = fracture 2 - Heal 2 fracture conditions
        @heal here = 3 - Heal 3 conditions from everyone here
        @heal bob = list - Show available condition types to heal
    """

    key = "@heal"
    locks = "cmd:perm(Builders) or perm(Developers)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        if not self.args:
            caller.msg("|rUsage: @heal <target|here|room #> [= <amount|condition_type|list>]|n")
            return

        parts = self.args.split("=", 1)
        target_name = parts[0].strip()
        amount = None
        condition_type = None

        if len(parts) > 1:
            heal_args = parts[1].strip().split()
            
            if len(heal_args) == 1:
                arg = heal_args[0]
                if arg == "list":
                    # Special case for listing conditions
                    condition_type = "list"
                elif arg.isdigit():
                    amount = int(arg)
                    if amount < 0:
                        caller.msg("|rAmount must be zero or positive.|n")
                        return
                else:
                    # It's a condition type
                    condition_type = arg.lower()
            elif len(heal_args) == 2:
                # condition_type + amount
                condition_type = heal_args[0].lower()
                try:
                    amount = int(heal_args[1])
                    if amount < 0:
                        caller.msg("|rAmount must be zero or positive.|n")
                        return
                except ValueError:
                    caller.msg("|rAmount must be an integer.|n")
                    return
            else:
                caller.msg("|rToo many arguments. Usage: @heal <target> [= <amount|condition_type|condition_type amount>]|n")
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
            
            medical_state = target.medical_state
            conditions_before = len(medical_state.conditions)
            
            # Handle "list" command to show available conditions
            if condition_type == "list":
                if medical_state.conditions:
                    caller.msg(f"|cAvailable conditions for {target.key}:|n")
                    condition_types = {}
                    for condition_key, condition_data in medical_state.conditions.items():
                        cond_type = condition_data.get('type', 'unknown')
                        if cond_type not in condition_types:
                            condition_types[cond_type] = 0
                        condition_types[cond_type] += 1
                    
                    for cond_type, count in condition_types.items():
                        caller.msg(f"  {cond_type}: {count} condition(s)")
                    caller.msg(f"Usage: @heal {target.key} = <condition_type> [amount]")
                else:
                    caller.msg(f"|g{target.key} has no medical conditions.|n")
                continue
            
            # Full heal without condition type - complete medical restoration
            if amount is None and condition_type is None:
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
                
            # Condition-type specific healing
            elif condition_type:
                # Find conditions of the specified type
                matching_conditions = []
                for condition_key, condition_data in medical_state.conditions.items():
                    if condition_data.get('type', '').lower() == condition_type:
                        matching_conditions.append(condition_key)
                
                if not matching_conditions:
                    caller.msg(f"|y{target.key} has no {condition_type} conditions.|n")
                    continue
                
                # Heal specific number or all of this type
                conditions_to_heal = amount if amount is not None else len(matching_conditions)
                conditions_to_heal = min(conditions_to_heal, len(matching_conditions))
                
                # Remove the conditions
                for i in range(conditions_to_heal):
                    if matching_conditions:
                        condition_key = matching_conditions.pop(0)
                        medical_state.conditions.pop(condition_key, None)
                
                target.save_medical_state()
                caller.msg(f"|g{target.key} healed {conditions_to_heal} {condition_type} condition(s).|n")
                
            # Partial heal - heal N conditions (any type)
            else:
                conditions_to_heal = min(amount, conditions_before)
                conditions_removed = 0
                
                # Remove conditions (least severe first)
                while conditions_removed < conditions_to_heal and medical_state.conditions:
                    # Find least severe condition
                    least_severe_key = None
                    least_severity = float('inf')
                    
                    for condition_key, condition_data in medical_state.conditions.items():
                        severity = condition_data.get('severity', 1)
                        if severity < least_severity:
                            least_severity = severity
                            least_severe_key = condition_key
                    
                    if least_severe_key:
                        medical_state.conditions.pop(least_severe_key)
                        conditions_removed += 1
                    else:
                        break
                
                target.save_medical_state()
                conditions_after = len(medical_state.conditions)
                caller.msg(f"|g{target.key} healed {conditions_removed} conditions ({conditions_after} remaining).|n")

        if len(targets) > 1 and condition_type != "list":
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
