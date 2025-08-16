"""
Weather Commands

Administrative commands for testing and managing the weather system.
"""

from evennia import Command
from world.weather import weather_system
from world.weather.weather_messages import WEATHER_INTENSITY


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
    locks = "cmd:perm(Developer)"
    
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
            self.caller.msg(f"Unknown weather type: {args}. Use 'weather list' to see options.")
