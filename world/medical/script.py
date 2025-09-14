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
                splattercast.msg(f"MEDICAL_SCRIPT: {self.obj.key} has no conditions, stopping and deleting script")
                self.stop()
                self.delete()
                return
                
            splattercast.msg(f"MEDICAL_SCRIPT: Processing {len(conditions)} conditions for {self.obj.key}")
            
            # Process each condition
            conditions_to_remove = []
            total_bleeding_severity = 0
            total_pain_severity = 0
            
            for condition in conditions:
                try:
                    if hasattr(condition, 'requires_ticker') and condition.requires_ticker:
                        splattercast.msg(f"MEDICAL_SCRIPT: Ticking {condition.condition_type} severity {condition.severity}")
                        condition.tick_effect(self.obj)
                        
                        # Track bleeding severity for consolidated messaging
                        if condition.condition_type == "minor_bleeding":
                            total_bleeding_severity += condition.severity
                        
                        # Track pain severity for consolidated messaging
                        if condition.condition_type == "pain":
                            total_pain_severity += condition.severity
                        
                        # Check if condition should be removed (e.g., severity reached 0)
                        if hasattr(condition, 'should_end') and condition.should_end():
                            conditions_to_remove.append(condition)
                            splattercast.msg(f"MEDICAL_SCRIPT: {condition.condition_type} marked for removal")
                            
                except Exception as e:
                    splattercast.msg(f"MEDICAL_SCRIPT_ERROR: Error processing {condition.condition_type}: {e}")
                    conditions_to_remove.append(condition)
            
            # Send consolidated messaging if conditions are active
            if total_bleeding_severity > 0 or total_pain_severity > 0:
                self._send_medical_messages(total_bleeding_severity, total_pain_severity)
            
            if total_bleeding_severity > 0:
                self._create_blood_pool(total_bleeding_severity)
            
            # Remove ended conditions
            for condition in conditions_to_remove:
                medical_state.conditions.remove(condition)
                splattercast.msg(f"MEDICAL_SCRIPT: Removed {condition.condition_type}")
            
            # Check for death/unconsciousness after processing conditions
            if medical_state.is_dead():
                splattercast.msg(f"MEDICAL_SCRIPT_DEATH: {self.obj.key} has died from medical conditions")
                
                # Trigger full death processing (includes death analysis and death curtain)
                self.obj.at_death()
                self.stop()
                self.delete()
                return
            elif medical_state.is_unconscious():
                splattercast.msg(f"MEDICAL_SCRIPT_UNCONSCIOUS: {self.obj.key} has become unconscious")
                # Trigger unconsciousness handling
                from world.combat.utils import handle_character_death
                handle_character_death(self.obj, death=False)
            
            # Check if we should stop (no conditions left)
            if not medical_state.conditions:
                splattercast.msg(f"MEDICAL_SCRIPT: All conditions processed, stopping and deleting script for {self.obj.key}")
                self.stop()
                self.delete()
                
        except Exception as e:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"MEDICAL_SCRIPT_CRITICAL_ERROR: {self.obj.key}: {e}")
            self.stop()
            self.delete()
    
    def at_stop(self):
        """Called when script stops."""
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"MEDICAL_SCRIPT_STOP: Medical script stopped for {self.obj.key}")
        except:
            pass
    
    def _send_medical_messages(self, bleeding_severity, pain_severity):
        """Send consolidated medical messages combining bleeding and pain."""
        import random
        
        # Build message components
        personal_parts = []
        room_parts = []
        
        # Add bleeding components if present
        if bleeding_severity > 0:
            if bleeding_severity <= 3:
                personal_parts.append("|RYou feel warm blood trickling from your wounds.|n")
                room_parts.append(f"Small droplets of blood fall from {self.obj.key}'s wounds.")
            elif bleeding_severity <= 7:
                personal_parts.append("|RBlood flows freely from your wounds, leaving crimson trails.|n")
                room_parts.append(f"Blood steadily drips from {self.obj.key}, forming dark stains.")
            elif bleeding_severity <= 12:
                personal_parts.append("|RYou feel your life ebbing away as blood pours from your wounds.|n")
                room_parts.append(f"Crimson flows freely from {self.obj.key}'s wounds, pooling on the ground.")
            else:  # 13+
                personal_parts.append("|RYour vision dims as life-blood gushes from grievous wounds.|n")
                room_parts.append(f"{self.obj.key} leaves a trail of blood, their wounds gushing freely.")
        
        # Add pain components if present
        if pain_severity > 0:
            if pain_severity <= 5:
                personal_parts.append("|RYou feel a persistent ache from your injuries.|n")
            elif pain_severity <= 12:
                personal_parts.append("|RSharp pain flares from your wounds.|n")
            elif pain_severity <= 20:
                personal_parts.append("|RAgony courses through your battered form.|n")
            else:  # 21+
                personal_parts.append("|RUnbearable agony threatens to drive you unconscious.|n")
        
        # Combine and send messages
        if personal_parts:
            # Join personal messages with space
            personal_msg = " ".join(personal_parts)
            self.obj.msg(personal_msg)
        
        if room_parts:
            # Join room messages and add color
            room_msg = f"|R{' '.join(room_parts)}|n"
            if self.obj.location:
                self.obj.location.msg_contents(room_msg, exclude=self.obj)
    
    def _create_blood_pool(self, severity):
        """Create or update blood pool object in the room (like graffiti system)."""
        if not self.obj.location:
            return
            
        # Check for existing blood pool (single pool per room)
        existing_pool = None
        for obj in self.obj.location.contents:
            if hasattr(obj, 'db') and obj.db.is_blood_pool:
                existing_pool = obj
                break
        
        if existing_pool:
            # Merge into existing pool (like graffiti entries)
            existing_pool.add_bleeding_incident(self.obj.key, severity)
        else:
            # Create new blood pool
            from evennia import create_object
            from typeclasses.objects import BloodPool
            
            blood_pool = create_object(
                BloodPool,
                key="blood stains",
                location=self.obj.location
            )
            blood_pool.add_bleeding_incident(self.obj.key, severity)
    
    def _send_pain_messages(self, total_severity):
        """Send consolidated pain messages to character based on total pain severity."""
        import random
        
        # Personal pain messages based on severity
        if total_severity <= 5:
            pain_msgs = [
                "|yYou feel a persistent ache from your injuries.|n",
                "|yDull pain reminds you of your wounds.|n",
                "|yA nagging discomfort troubles your injured areas.|n"
            ]
        elif total_severity <= 12:
            pain_msgs = [
                "|rSharp pain flares from your wounds.|n",
                "|rIntense aching throbs through your injured body.|n",
                "|rPain pulses steadily from your various injuries.|n"
            ]
        elif total_severity <= 20:
            pain_msgs = [
                "|RAgony courses through your battered form.|n",
                "|RExcruciating pain overwhelms your senses.|n",
                "|RWaves of torment wash over you from multiple wounds.|n"
            ]
        else:  # 21+
            pain_msgs = [
                "|RUnbearable agony threatens to drive you unconscious.|n",
                "|RThe pain is so intense you can barely think straight.|n",
                "|REvery movement sends lightning bolts of pure torment through you.|n"
            ]
        
        # Send personal pain message (no room message for pain - it's internal)
        pain_msg = random.choice(pain_msgs)
        self.obj.msg(pain_msg)


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
    Stop and delete the medical script for a character.
    
    Args:
        character: The character to stop medical script for
    """
    try:
        splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
        splattercast.msg(f"STOP_MEDICAL_SCRIPT: Looking for medical scripts on {character.key}")
    except:
        pass
    
    # Find and delete all medical scripts (active or stopped)
    existing_scripts = character.scripts.get("medical_script")
    if existing_scripts:
        for script in existing_scripts:
            try:
                splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
                splattercast.msg(f"STOP_MEDICAL_SCRIPT: Found script {script}, deleting it")
            except:
                pass
            script.stop()
            script.delete()
    else:
        try:
            splattercast = ChannelDB.objects.get_channel(SPLATTERCAST_CHANNEL)
            splattercast.msg(f"STOP_MEDICAL_SCRIPT: No medical scripts found on {character.key}")
        except:
            pass
