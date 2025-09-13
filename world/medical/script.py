"""
Medical condition script for characters.

This script manages all medical conditions for a single character,
ticking them at regular intervals and cleaning up when no conditions remain.
"""

from evennia import DefaultScript
from evennia.comms.models import ChannelDB
from world.combat.constants import SPLATTERCAST_CHANNEL


class MedicalScript(DefaultScript):
    """
    Per-character script that manages all medical conditions.
    
    This script:
    - Runs every 60 seconds to process medical conditions
    - Automatically starts when first condition is added
    - Automatically stops when no conditions remain
    - Provides centralized medical condition management
    """
    
    def at_script_creation(self):
        """Called when script is first created."""
        self.key = "medical_script"  # Use consistent key for searching
        self.desc = f"Medical condition manager for {self.obj.key}"
        self.interval = 12  # Tick every 12 seconds (was 60 for production)
        self.persistent = True
        self.start_delay = False  # Start immediately
        
    def at_repeat(self):
        """Process all medical conditions for this character."""
        try:
            # Get splattercast for debugging
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            
            # Get character's medical state
            if not hasattr(self.obj, 'medical_state'):
                splattercast.msg(f"MEDICAL_SCRIPT: {self.obj.key} has no medical_state, stopping script")
                self.stop()
                return
                
            medical_state = self.obj.medical_state
            conditions = medical_state.conditions.copy()  # Copy to avoid modification during iteration
            
            if not conditions:
                splattercast.msg(f"MEDICAL_SCRIPT: {self.obj.key} has no conditions, stopping script")
                self.stop()
                return
                
            splattercast.msg(f"MEDICAL_SCRIPT: Processing {len(conditions)} conditions for {self.obj.key}")
            
            # Process each condition
            conditions_to_remove = []
            for condition in conditions:
                try:
                    if hasattr(condition, 'requires_ticker') and condition.requires_ticker:
                        splattercast.msg(f"MEDICAL_SCRIPT: Ticking {condition.condition_type} severity {condition.severity}")
                        condition.tick_effect(self.obj)
                        
                        # Check if condition should be removed (e.g., severity reached 0)
                        if hasattr(condition, 'should_end') and condition.should_end():
                            conditions_to_remove.append(condition)
                            splattercast.msg(f"MEDICAL_SCRIPT: {condition.condition_type} marked for removal")
                            
                except Exception as e:
                    splattercast.msg(f"MEDICAL_SCRIPT_ERROR: Error processing {condition.condition_type}: {e}")
                    conditions_to_remove.append(condition)
            
            # Remove ended conditions
            for condition in conditions_to_remove:
                medical_state.conditions.remove(condition)
                splattercast.msg(f"MEDICAL_SCRIPT: Removed {condition.condition_type}")
            
            # Check if we should stop (no conditions left)
            if not medical_state.conditions:
                splattercast.msg(f"MEDICAL_SCRIPT: All conditions processed, stopping script for {self.obj.key}")
                self.stop()
                
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"MEDICAL_SCRIPT_CRITICAL_ERROR: {self.obj.key}: {e}")
            self.stop()
    
    def at_stop(self):
        """Called when script stops."""
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"MEDICAL_SCRIPT_STOP: Medical script stopped for {self.obj.key}")
        except:
            pass


def start_medical_script(character):
    """
    Start or get the medical script for a character.
    
    Args:
        character: The character to start medical script for
        
    Returns:
        MedicalScript: The active medical script
    """
    try:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"START_MEDICAL_SCRIPT: Checking for existing script on {character.key}")
    except:
        pass
        
    # Check if script already exists
    existing_script = character.scripts.get("medical_script")
    if existing_script:
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"START_MEDICAL_SCRIPT: Found existing script for {character.key}")
        except:
            pass
        return existing_script.first() if existing_script else None
    
    # Create new script
    try:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"START_MEDICAL_SCRIPT: Creating new script for {character.key}")
    except:
        pass
        
    script = character.scripts.add(MedicalScript)
    
    try:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"START_MEDICAL_SCRIPT: Script created: {script}")
    except:
        pass
        
    return script


def stop_medical_script(character):
    """
    Stop the medical script for a character.
    
    Args:
        character: The character to stop medical script for
    """
    existing_script = character.scripts.get("medical_script")
    if existing_script:
        for script in existing_script:
            script.stop()
