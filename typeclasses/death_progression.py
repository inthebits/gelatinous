"""
Death Progression Script - Time-Delayed Death System

This script creates a dramatic 6-minute window between death and final death,
allowing for medical intervention and creating suspenseful RP opportunities.

The system works as follows:
1. Character "dies" - death curtain plays, they enter dying state
2. 6-minute timer begins with periodic messages
3. Other characters can attempt revival during this window
4. After 6 minutes, final death occurs (permanent until manual revival)

This creates urgency for medical response while making death less instantaneous.
"""

from evennia import DefaultScript
from evennia.utils import delay
from evennia.comms.models import ChannelDB
import random
import time


class DeathProgressionScript(DefaultScript):
    """
    Script that manages the time-delayed death progression.
    
    Attached to a character who is dying but not yet permanently dead.
    Provides a window for medical intervention and creates dramatic tension.
    """
    
    def at_script_creation(self):
        """Initialize the death progression script."""
        self.key = "death_progression"
        self.desc = "Time-delayed death progression"
        self.persistent = True
        self.autostart = True
        
        # Death progression timing (6 minutes total)
        self.db.total_duration = 360  # 6 minutes in seconds
        self.db.message_intervals = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]  # Every 30 seconds
        self.db.start_time = time.time()
        self.db.messages_sent = []
        self.db.can_be_revived = True
        
        # Store character reference
        if not hasattr(self.db, 'character'):
            self.db.character = None
            
        # Start the progression
        self.interval = 30  # Check every 30 seconds
        
    def at_start(self):
        """Called when script starts."""
        character = self.db.character
        if not character:
            self.stop()
            return
            
        # Log start of death progression
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_PROGRESSION: Started for {character.key} - 6 minute revival window")
        except:
            pass
            
        # Send initial dying message
        self._send_initial_message()
        
    def at_repeat(self):
        """Called every 30 seconds during death progression."""
        character = self.db.character
        if not character:
            self.stop()
            return
            
        current_time = time.time()
        elapsed = current_time - self.db.start_time
        
        # Check if medical conditions have been resolved and character should be revived
        if self._check_medical_revival_conditions(character):
            self._handle_medical_revival()
            return
        
        # Check if we should send a progression message
        for interval in self.db.message_intervals:
            if interval not in self.db.messages_sent and elapsed >= interval:
                self._send_progression_message(interval)
                self.db.messages_sent.append(interval)
                
        # Check if death progression is complete
        if elapsed >= self.db.total_duration:
            self._complete_death_progression()
            
    def _check_medical_revival_conditions(self, character):
        """
        Check if the character's medical state has improved enough to warrant revival.
        This integrates with the existing medical system.
        
        Args:
            character: The character to check
            
        Returns:
            bool: True if character should be revived due to medical improvement
        """
        if not hasattr(character, 'medical_state') or not character.medical_state:
            return False
            
        medical_state = character.medical_state
        
        # Check if the character is no longer dead according to medical system
        if not medical_state.is_dead():
            # Medical treatment has resolved the fatal conditions!
            return True
            
        # Additional checks for improvement trends could go here
        # For example: blood level increasing, organ HP being restored, etc.
        
        return False
        
    def _handle_medical_revival(self):
        """Handle revival due to successful medical intervention."""
        character = self.db.character
        if not character:
            return
            
        # Log medical revival
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            elapsed = time.time() - self.db.start_time
            splattercast.msg(f"MEDICAL_REVIVAL: {character.key} revived by medical treatment after {elapsed:.1f}s")
        except:
            pass
            
        # Medical revival messages
        character.msg(
            "|gThe medical treatment takes effect! You feel life returning to your body.|n\n"
            "|gYou have been pulled back from death's door by skilled medical intervention.|n"
        )
        
        if character.location:
            room_msg = f"|g{character.key} responds to medical treatment and returns from the brink of death!|n"
            character.location.msg_contents(room_msg, exclude=[character])
            
        # Restore character to living state
        if hasattr(character, 'remove_death_state'):
            character.remove_death_state()
            
        # Stop the death progression
        self.stop()
            
    def _send_initial_message(self):
        """Send the initial message when death progression begins."""
        character = self.db.character
        if not character:
            return
            
        # Message to the dying character
        dying_msg = (
            "|R║ You hover at the threshold between life and death. ║|n\n"
            "|r║ Your essence flickers like a candle in the wind... ║|n\n"
            "|R║ There may still be time for intervention. ║|n"
        )
        character.msg(dying_msg)
        
        # Message to observers in the room
        if character.location:
            observer_msg = (
                f"|r{character.key} lies at death's door, their life hanging by a thread.|n\n"
                f"|R{character.key}'s breathing is labored and irregular - they may still be saved.|n"
            )
            character.location.msg_contents(observer_msg, exclude=[character])
            
    def _send_progression_message(self, interval):
        """Send a message at specific intervals during death progression."""
        character = self.db.character
        if not character:
            return
            
        # Calculate remaining time
        elapsed = time.time() - self.db.start_time
        remaining = self.db.total_duration - elapsed
        minutes_remaining = int(remaining / 60)
        
        # Select message based on interval
        messages = self._get_progression_messages()
        message_data = messages.get(interval, messages[330])  # Default to final message
        
        # Send message to dying character
        character.msg(message_data["dying"])
        
        # Send message to observers
        if character.location:
            character.location.msg_contents(message_data["observer"].format(name=character.key), exclude=[character])
            
        # Log progression
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_PROGRESSION: {character.key} at {interval}s - {minutes_remaining}m remaining")
        except:
            pass
            
    def _get_progression_messages(self):
        """Get the progression messages for different time intervals."""
        return {
            30: {  # 30 seconds - 5.5 minutes left
                "dying": "|rTime becomes elastic, like chewing gum stretched between your teeth and the fluorescent lights are humming a song you remember from childhood but can't quite place. The edges of everything are soft now, melting like crayons left in a hot car, and you're floating in this warm red soup that tastes like copper pennies and your mother's disappointment.|n",
                "observer": "|r{name}'s eyes roll back, showing only whites.|n"
            },
            60: {  # 1 minute - 5 minutes left
                "dying": "|RYou're sinking through the floor now, through layers of concrete and earth and forgotten promises, and the voices above sound like they're speaking underwater. Everything tastes like iron and regret. Your body feels like it belongs to someone else, some stranger whose story you heard in a bar once but never really believed.|n",
                "observer": "|R{name}'s breathing becomes shallow and erratic.|n"
            },
            90: {  # 1.5 minutes - 4.5 minutes left
                "dying": "|rThe world is a television with bad reception and someone keeps changing the channels. Static. Your grandmother's kitchen. Static. That time you nearly drowned. Static. The taste of blood and birthday cake and the sound of someone crying who might be you but probably isn't because you're somewhere else now, somewhere darker.|n",
                "observer": "|r{name} makes a low, rattling sound in their throat.|n"
            },
            120: {  # 2 minutes - 4 minutes left
                "dying": "|RYou're watching yourself from the ceiling corner like a security camera recording the most boring crime ever committed. That body down there, that meat puppet with your face, it's leaking life like a punctured water balloon. And you're thinking, this is it? This is the grand finale? This wet, messy, disappointing finale?|n",
                "observer": "|R{name}'s skin takes on a waxy, gray pallor.|n"
            },
            150: {  # 2.5 minutes - 3.5 minutes left
                "dying": "|rMemory becomes a kaleidoscope where every piece is broken glass and every turn cuts deeper. You taste the last cigarette you ever smoked, feel the first hand you ever held, hear the last lie you ever told, and it's all happening simultaneously in this carnival of consciousness where the rides are broken and the music is playing backward.|n",
                "observer": "|r{name}'s fingers twitch spasmodically.|n"
            },
            180: {  # 3 minutes - 3 minutes left
                "dying": "|RThe darkness isn't dark anymore, it's every color that doesn't have a name, every sound that was never made, every word that was never spoken. You're dissolving into the spaces between seconds, becoming the pause between heartbeats, the silence between screams. And it's beautiful and terrible and completely, utterly ordinary.|n",
                "observer": "|R{name}'s body convulses once, violently.|n"
            },
            210: {  # 3.5 minutes - 2.5 minutes left
                "dying": "|rYou're a radio losing signal, static eating away at the song of yourself until there's nothing left but the spaces between the notes. The pain is gone now, replaced by this vast emptiness that feels like Sunday afternoons and unfinished conversations and all the things you meant to say but never did.|n",
                "observer": "|r{name} lies perfectly still except for the barely perceptible rise and fall of their chest.|n"
            },
            240: {  # 4 minutes - 2 minutes left
                "dying": "|RYou're becoming weather now, becoming the wind that carries other people's secrets, the rain that washes away their sins. You're evaporating into stories that will never be told, jokes that will never be finished, dreams that will never be dreamed. And it's okay. It's all okay. Everything is okay in this place between places.|n",
                "observer": "|R{name}'s breathing has become so faint it's almost imperceptible.|n"
            },
            270: {  # 4.5 minutes - 1.5 minutes left
                "dying": "|rThe last thoughts are like photographs burning in a fire, curling at the edges before disappearing into ash. You remember everything and nothing. You are everyone and no one. The boundary between self and not-self becomes as meaningless as the difference between Tuesday and the color blue.|n",
                "observer": "|r{name}'s lips have turned blue.|n"
            },
            300: {  # 5 minutes - 1 minute left
                "dying": "|RYou're the echo of an echo, the shadow of a shadow, the dream that someone else is forgetting. The darkness isn't coming for you anymore because you ARE the darkness, you are the silence, you are the space where something used to be. And in this final moment of dissolution, you understand everything and nothing at all.|n",
                "observer": "|R{name} doesn't appear to be breathing anymore.|n"
            },
            330: {  # 5.5 minutes - 30 seconds left
                "dying": "|r... ...you are... ...you... ...|n",
                "observer": "|r{name} lies motionless, their body completely still.|n"
            }
        }
        
    def _complete_death_progression(self):
        """Complete the death progression - character is now permanently dead."""
        character = self.db.character
        if not character:
            self.stop()
            return
            
        # Mark as permanently dead
        self.db.can_be_revived = False
        
        # Send final death messages
        final_msg = (
            "|R║ The darkness claims you completely... ║|n\n"
            "|r║ Your consciousness fades into the void. ║|n"
        )
        character.msg(final_msg)
        
        if character.location:
            observer_msg = f"|R{character.key} takes their final breath and passes into death.|n"
            character.location.msg_contents(observer_msg, exclude=[character])
            
        # Apply final death state (if not already done)
        if hasattr(character, 'apply_final_death_state'):
            character.apply_final_death_state()
            
        # Log completion
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_PROGRESSION: {character.key} completed - now permanently dead")
        except:
            pass
            
        # Stop the script
        self.stop()


def start_death_progression(character):
    """
    Start the death progression script for a character.
    
    Args:
        character: The character entering death progression
        
    Returns:
        DeathProgressionScript: The created script
    """
    # Check if character already has a death progression script
    existing_script = character.scripts.get("death_progression")
    if existing_script:
        return existing_script
        
    # Create new death progression script
    script = character.scripts.add(DeathProgressionScript)[0]
    script.db.character = character
    
    return script


def get_death_progression_script(character):
    """
    Get the death progression script for a character if it exists.
    
    Args:
        character: The character to check
        
    Returns:
        DeathProgressionScript or None: The script if found, None otherwise
    """
    return character.scripts.get("death_progression")


def get_death_progression_status(character):
    """
    Get the status of a character's death progression for medical system integration.
    
    Args:
        character: The character to check
        
    Returns:
        dict: Status information including time remaining, condition, etc.
    """
    script = get_death_progression_script(character)
    if not script:
        return {"in_progression": False}
        
    import time
    elapsed = time.time() - script.db.start_time
    remaining = script.db.total_duration - elapsed
    
    return {
        "in_progression": True,
        "time_elapsed": elapsed,
        "time_remaining": remaining,
        "total_duration": script.db.total_duration,
        "can_be_revived": script.db.can_be_revived,
        "time_factor": 1.0 - (elapsed / script.db.total_duration)
    }
            
    def _handle_successful_revival(self, revivor=None):
        """Handle successful revival during death progression."""
        character = self.db.character
        if not character:
            return
            
        # Revival messages
        character.msg("|gYou feel the spark of life return! You have been pulled back from death's door.|n")
        
        if character.location:
            if revivor:
                room_msg = f"|g{revivor.key} successfully revives {character.key}!|n"
            else:
                room_msg = f"|g{character.key} miraculously returns from the brink of death!|n"
            character.location.msg_contents(room_msg, exclude=[character])
            
        # Restore character to living state
        if hasattr(character, 'remove_death_state'):
            character.remove_death_state()
            
        # Log successful revival
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            revivor_name = revivor.key if revivor else "miraculous intervention"
            splattercast.msg(f"DEATH_PROGRESSION: {character.key} successfully revived by {revivor_name}")
        except:
            pass
            
        # Stop the death progression
        self.stop()
        
    def _handle_failed_revival(self, revivor=None):
        """Handle failed revival attempt during death progression."""
        character = self.db.character
        if not character:
            return
            
        # Failure messages
        if revivor:
            revivor.msg(f"|rYour revival attempt on {character.key} has failed.|n")
            
        if character.location:
            if revivor:
                room_msg = f"|r{revivor.key}'s attempt to revive {character.key} fails.|n"
            else:
                room_msg = f"|rThe revival attempt on {character.key} fails.|n"
            character.location.msg_contents(room_msg, exclude=[character])
            
        # Log failed revival
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            revivor_name = revivor.key if revivor else "unknown"
            splattercast.msg(f"DEATH_PROGRESSION: Revival attempt on {character.key} by {revivor_name} failed")
        except:
            pass


def start_death_progression(character):
    """
    Start the death progression script for a character.
    
    Args:
        character: The character entering death progression
        
    Returns:
        DeathProgressionScript: The created script
    """
    # Check if character already has a death progression script
    existing_script = character.scripts.get("death_progression")
    if existing_script:
        return existing_script
        
    # Create new death progression script
    script = character.scripts.add(DeathProgressionScript)[0]
    script.db.character = character
    
    return script


def get_death_progression_script(character):
    """
    Get the death progression script for a character if it exists.
    
    Args:
        character: The character to check
        
    Returns:
        DeathProgressionScript or None: The script if found, None otherwise
    """
    return character.scripts.get("death_progression")


