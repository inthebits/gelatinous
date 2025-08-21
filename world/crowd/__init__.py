"""
Crowd System for Gelatinous

Provides atmospheric crowd descriptions based on room occupancy,
room type, weather conditions, and base crowd levels.
"""

from .crowd_system import CrowdSystem
from .crowd_messages import get_crowd_messages, CROWD_INTENSITY

# Global crowd system instance
crowd_system = CrowdSystem()

__all__ = [
    'crowd_system',
    'CrowdSystem', 
    'get_crowd_messages',
    'CROWD_INTENSITY'
]
