"""
Weather System for Gelatinous

Provides atmospheric weather descriptions that integrate into room appearance.
Weather messages are selected based on current weather state, time of day,
and player sensory capabilities.
"""

from .weather_system import WeatherSystem
from .weather_messages import WEATHER_MESSAGES
from .time_system import TimeSystem

# Global weather system instance
weather_system = WeatherSystem()
time_system = TimeSystem()

__all__ = ['weather_system', 'time_system', 'WeatherSystem', 'TimeSystem', 'WEATHER_MESSAGES']
