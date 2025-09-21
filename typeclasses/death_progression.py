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
import re


def _get_terminal_width(session=None):
    """Get terminal width from session, defaulting to 78 for MUD compatibility."""
    if session:
        try:
            detected_width = session.protocol_flags.get("SCREENWIDTH", [78])[0]
            return max(68, detected_width - 5)  # Minimum 68 to ensure readability
        except (IndexError, KeyError, TypeError):
            pass
    return 78


def _strip_color_codes(text):
    """Remove Evennia color codes from text to get actual visible length."""
    # Remove all |x codes (where x is any character) - same pattern as death curtain
    return re.sub(r'\|.', '', text)


def _center_text(text, width=None, session=None):
    """Center text using same approach as curtain_of_death.py for consistency."""
    if width is None:
        width = _get_terminal_width(session)
    
    # Split into lines and center each line - same as curtain
    lines = text.split('\n')
    centered_lines = []
    
    for line in lines:
        if not line.strip():  # Empty line
            centered_lines.append("")
            continue
            
        # Calculate visible text length (without color codes) - same as curtain
        visible_text = _strip_color_codes(line)
        
        # Use Python's built-in center method for proper centering - same as curtain  
        centered_visible = visible_text.center(width)
        
        # Calculate the actual padding that center() applied
        padding_needed = width - len(visible_text)
        left_padding = padding_needed // 2
        
        # Apply the same left padding to the original colored text
        centered_line = " " * left_padding + line
        centered_lines.append(centered_line)
    
    return '\n'.join(centered_lines)


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
        
        # Character reference will be set after creation
        if not hasattr(self.db, 'character'):
            self.db.character = None
            
        # Start the progression
        self.interval = 30  # Check every 30 seconds
        
        # Debug logging - character may not be set yet at creation time
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            char_name = self.db.character.key if self.db.character else "not_set_yet"
            splattercast.msg(f"DEATH_PROGRESSION: Script at_script_creation for {char_name}")
        except:
            pass
        
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
        
        # Debug logging
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_PROGRESSION: at_repeat for {character.key}, elapsed: {elapsed:.1f}s")
        except:
            pass
        
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
            "|gYou have been pulled back from death's door by skilled medical intervention.|n",
            from_obj=self
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
            
        # Message to the dying character - use exact same approach as curtain DEATH message
        # Get session for proper width detection, just like curtain of death does
        session = None
        if hasattr(character, 'sessions') and character.sessions.all():
            session = character.sessions.all()[0]
        
        # Get width using the same function as curtain of death
        width = _get_terminal_width(session)
        
        # Use exact same pattern as curtain: "|r" + text.center(width) + "|n"
        dying_line1 = "|R" + "You hover at the threshold between life and death.".center(width) + "|n"
        dying_line2 = "|r" + "Your essence flickers like a candle in the wind...".center(width) + "|n"
        dying_line3 = "|R" + "There may still be time for intervention.".center(width) + "|n"
        
        # Send each line separately with line breaks
        centered_dying_msg = dying_line1 + "\n" + dying_line2 + "\n" + dying_line3 + "\n"
        character.msg(centered_dying_msg, from_obj=self)
        
        # Message to observers in the room
        if character.location:
            observer_msg = (
                f"|n{character.key} lies at death's door, their life hanging by a thread.|n\n"
                f"|n{character.key}'s breathing is labored and irregular - they may still be saved.|n"
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
        
        # Send message to dying character with death progression script as from_obj
        character.msg(message_data["dying"], from_obj=self)
        
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
                "dying": "|nTime becomes elastic, like chewing gum stretched between your teeth, and the fluorescent lights are humming a song you remember from childhood but can't quite place. The edges of everything are soft now, melting like crayons left in a hot car, and you're floating in this warm red soup that tastes like copper pennies and your mother's disappointment. The clock on the wall is ticking backwards and each second is a small death, a tiny funeral for the person you were just a moment ago. You can taste colors now, hear the weight of silence, feel the texture of your own heartbeat as it stumbles through its final choreography. Someone is playing a violin made of broken dreams in the distance, and the melody sounds suspiciously like that hold music from the unemployment office. Your teeth feel loose in your skull, like Chiclets rattling in a box that someone keeps shaking just to hear the sound.|n\n",
                "observer": "|n{name}'s eyes roll back, showing only whites.|n"
            },
            60: {  # 1 minute - 5 minutes left
                "dying": "|nYou're sinking through the floor now, through layers of concrete and earth and forgotten promises, and the voices above sound like they're speaking underwater. Everything tastes like iron and regret. Your body feels like it belongs to someone else, some stranger whose story you heard in a bar once but never really believed. The pain has become philosophical, an abstract concept that your meat vessel is interpreting through nerve endings that no longer quite remember their job. You're watching your life insurance policy come to life, literally, walking around the room in a three-piece suit made of your own skin, calculating actuarial tables with your dying breath. The wallpaper is breathing now, in and out, like the lungs of some massive beast that swallowed your apartment whole. Your fingernails taste like the metal part of pencil erasers, and somewhere a cash register is tallying up the cost of your accumulated mistakes.|n\n",
                "observer": "|n{name}'s breathing becomes shallow and erratic.|n"
            },
            90: {  # 1.5 minutes - 4.5 minutes left
                "dying": "|nThe world is a television with bad reception and someone keeps changing the channels. Static. Your grandmother's kitchen. Static. That time you nearly drowned. Static. The taste of blood and birthday cake and the sound of someone crying who might be you but probably isn't, because you're somewhere else now, somewhere darker. Your consciousness is a drunk driver careening through memories it doesn't own anymore, sideswiping moments that belonged to other people, other versions of yourself that died small deaths every day until this final, grand production. The static tastes like Saturday mornings and broken promises. The remote control is made of your own ribs, and every channel change cracks another bone in your chest. Your eyeballs feel like they're dissolving into television snow, white noise with a hint of desperation and the aftertaste of commercial jingles.|n\n",
                "observer": "|n{name} makes a low, rattling sound in their throat.|n"
            },
            120: {  # 2 minutes - 4 minutes left
                "dying": "|nYou're watching yourself from the ceiling corner like a security camera recording the most boring crime ever committed. That body down there, that meat puppet with your face, is leaking life like a punctured water balloon. And you're thinking, this is it? This is the grand finale? This wet, messy, disappointing finale? Your ghost is already filling out paperwork in triplicate, applying for unemployment benefits in the afterlife, wondering if death comes with dental coverage. The irony tastes like pennies and pharmaceutical advertisements. The ceiling tiles are counting down in languages you've never heard, and your soul is doing inventory on a warehouse full of unused potential. Your shadow is packing its bags, ready to find employment with someone who might actually cast an interesting silhouette.|n\n",
                "observer": "|n{name}'s skin takes on a waxy, gray pallor.|n"
            },
            150: {  # 2.5 minutes - 3.5 minutes left
                "dying": "|nMemory becomes a kaleidoscope where every piece is broken glass and every turn cuts deeper. You taste the last cigarette you ever smoked, feel the first hand you ever held, hear the last lie you ever told, and it's all happening simultaneously in this carnival of consciousness where the rides are broken and the music is playing backward. Your neurons are firing their final clearance sale—everything must go, rock-bottom prices on experiences you can't even remember having. The carousel horses are bleeding carousel blood and the cotton candy tastes like regret. The funhouse mirrors are showing you every version of yourself you never became, and they're all pointing and laughing at the version you did. Your thoughts are circus peanuts dissolving on your tongue, artificially flavored and ultimately disappointing.|n\n",
                "observer": "|n{name}'s fingers twitch spasmodically.|n"
            },
            180: {  # 3 minutes - 3 minutes left
                "dying": "|nThe darkness isn't dark anymore; it's every color that doesn't have a name, every sound that was never made, every word that was never spoken. You're dissolving into the spaces between seconds, becoming the pause between heartbeats, the silence between screams. And it's beautiful and terrible and completely, utterly ordinary. Your soul is a closing-time bar where the lights have come on and everyone can see exactly how pathetic they really are, but the bartender is Death and she's not calling last call — she's calling first call for the next shift. The jukebox is playing your theme song, but it's off-key and the record keeps skipping on the part where you were supposed to matter. Your consciousness is a newspaper blowing down an empty street at 3 AM, full of yesterday's problems and tomorrow's disappointments.|n\n",
                "observer": "|n{name}'s body convulses once, violently.|n"
            },
            210: {  # 3.5 minutes - 2.5 minutes left
                "dying": "|nYou're a radio losing signal, static eating away at the song of yourself until there's nothing left but the spaces between the notes. The pain is gone now, replaced by this vast emptiness that feels like Sunday afternoons and unfinished conversations and all the things you meant to say but never did. Your thoughts are evaporating like water on hot asphalt, leaving behind these weird mineral deposits of memory that taste like childhood and smell like hospitals. The static between radio stations sounds like your mother's voice reading you the phone book. Your bones are tuning forks that no longer vibrate at the right frequency, and your blood has become elevator music for a building that's being demolished. The antenna of your soul is bent and rusty, receiving only test patterns from a broadcasting system that went off the air decades ago.|n\n",
                "observer": "|n{name} lies perfectly still except for the barely perceptible rise and fall of their chest.|n"
            },
            240: {  # 4 minutes - 2 minutes left
                "dying": "|nYou're becoming weather now, becoming the wind that carries other people's secrets, the rain that washes away their sins. You're evaporating into stories that will never be told, jokes that will never be finished, dreams that will never be dreamed. And it's okay. It's all okay. Everything is okay in this place between places. Your consciousness is a going-out-of-business sale where everything is marked down 90%, but nobody wants to buy your used thoughts, your secondhand emotions, your clearance-rack dreams. The clouds are made of your exhaled words, and it's starting to rain all the conversations you never had. Your temperature is dropping to match the ambient disappointment of the universe, and your pulse is keeping time with a metronome that's winding down like a broken music box.|n\n",
                "observer": "|n{name}'s breathing has become so faint it's almost imperceptible.|n"
            },
            270: {  # 4.5 minutes - 1.5 minutes left
                "dying": "|nThe last thoughts are like photographs burning in a fire, curling at the edges before disappearing into ash. You remember everything and nothing. You are everyone and no one. The boundary between self and not-self becomes as meaningless as the difference between Tuesday and the color blue. Your identity is melting like ice cream in hell—sweet and messy and ultimately disappointing, leaving behind sticky residue that attracts flies and regret. The photographs in your memory are developing in reverse, turning back into silver and chemicals and possibility. Your name tastes like alphabet soup that's gone cold, and your fingerprints are evaporating off your fingers like steam from a cup of coffee nobody wants to drink. The mirror in your mind has cracked down the middle, and both halves are reflecting someone you've never met.|n\n",
                "observer": "|n{name}'s lips have turned blue.|n"
            },
            300: {  # 5 minutes - 1 minute left
                "dying": "|nYou're the echo of an echo, the shadow of a shadow, the dream that someone else is forgetting. The darkness isn't coming for you anymore because you ARE the darkness, you are the silence, you are the space where something used to be. And in this final moment of dissolution, you understand everything and nothing at all. Your last coherent thought is wondering if this is how mayonnaise feels when it expires—this slow dissolution into component parts that never really belonged together anyway. The universe is yawning, and you're the sound it makes between sleeping and waking, the pause before the snooze button gets hit for the final time. Your existence is a receipt from a store that went out of business, crumpled in the pocket of a coat you never liked but wore anyway because it was practical.|n\n",
                "observer": "|n{name} doesn't appear to be breathing anymore.|n"
            },
            330: {  # 5.5 minutes - 30 seconds left
                "dying": "|n...so tired... ...so very... ...tired... ...the light is... ...warm... ...like being... ...held... ...you can hear... ...laughter... ...from somewhere... ...safe... ...you're not... ...scared anymore... ...just... ...tired... ...tell them... ...tell them... ...you tried... ...but... ...so tired... ...|n\n",
                "observer": "|n{name} lies motionless, their body completely still.|n"
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
        
        # Send final death messages - use exact same approach as curtain DEATH message
        # Get session for proper width detection, just like curtain of death does
        session = None
        if hasattr(character, 'sessions') and character.sessions.all():
            session = character.sessions.all()[0]
        
        # Get width using the same function as curtain of death
        width = _get_terminal_width(session)
        
        # Use exact same pattern as curtain: "|r" + text.center(width) + "|n"
        final_line1 = "|R" + "The darkness claims you completely...".center(width) + "|n"
        final_line2 = "|r" + "Your consciousness fades into the void.".center(width) + "|n"
        
        # Send each line with line breaks
        centered_final_msg = final_line1 + "\n" + final_line2 + "\n"
        character.msg(centered_final_msg, from_obj=self)
        
        if character.location:
            observer_msg = f"|r{character.key} takes their final breath and passes into death.|n"
            character.location.msg_contents(observer_msg, exclude=[character])
            
        # Apply final death state (if not already done)
        if hasattr(character, 'apply_final_death_state'):
            character.apply_final_death_state()
            
        # Complete death progression - corpse creation and character transition
        self._handle_corpse_creation_and_transition(character)
            
        # Log completion
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_PROGRESSION: {character.key} completed - corpse created, character transitioned")
        except:
            pass
            
        # Stop the script
        self.stop()

    def _handle_corpse_creation_and_transition(self, character):
        """
        Complete the death progression by creating corpse and transitioning character.
        This separates the dead character object from the corpse object for investigation.
        """
        try:
            # 1. Create corpse object with forensic data
            corpse = self._create_corpse_from_character(character)
            
            # 2. Get account before unpuppeting
            account = character.account
            
            # 3. Transition character out of play
            self._transition_character_to_death(character)
            
            # 4. TODO: Initiate character creation for account (commented out until character creation ready)
            # if account:
            #     self._initiate_new_character_creation(account)
                
            # 5. Log the transition
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"DEATH_COMPLETION: {character.key} -> Corpse created, character transitioned")
            except:
                pass
                
        except Exception as e:
            # Fallback - log error but don't crash the death progression
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"DEATH_COMPLETION_ERROR: {character.key} - {e}")
            except:
                pass

    def _create_corpse_from_character(self, character):
        """Create a corpse object that preserves forensic data from the character."""
        from evennia import create_object
        import time
        
        # Create corpse object
        corpse = create_object(
            typeclass="typeclasses.items.Item",  # Use base Item class for now
            key="a fresh corpse",  # Anonymous corpse name
            location=character.location
        )
        
        # Set corpse properties manually
        corpse.db.is_corpse = True
        corpse.db.creation_time = time.time()
        
        # Transfer forensic data for investigation
        corpse.db.original_character_name = character.key
        corpse.db.original_character_dbref = character.dbref
        corpse.db.original_account_dbref = character.account.dbref if character.account else None
        corpse.db.death_time = time.time()
        corpse.db.physical_description = getattr(character.db, 'desc', 'A person.')
        
        # Transfer medical/death data if available
        if hasattr(character, 'medical_state') and character.medical_state:
            corpse.db.death_cause = character.get_death_cause()
            corpse.db.medical_conditions = character.medical_state.get_condition_summary()
            corpse.db.blood_type = getattr(character.db, 'blood_type', 'unknown')
        
        # Transfer character description data
        if hasattr(character, 'longdesc') and character.longdesc:
            corpse.db.longdesc_data = dict(character.longdesc)  # Copy the dictionary data
        
        # Transfer inventory to corpse
        for item in character.contents:
            if item != corpse:  # Don't move the corpse itself
                item.move_to(corpse, quiet=True)
        
        # Set corpse description
        corpse.db.desc = f"The lifeless body of {character.key}. {corpse.db.physical_description}"
        
        return corpse

    def _transition_character_to_death(self, character):
        """Move character out of play and unpuppet from account."""
        from evennia import search_object
        
        # Get account reference before unpuppeting
        account = character.account
        
        # Move character to limbo/OOC room (Evennia's default limbo is #2)
        try:
            limbo_room = search_object("#2")[0]  # Limbo room
            old_location = character.location
            character.move_to(limbo_room, quiet=True)
            
            # Debug logging for successful teleportation
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"DEATH_TELEPORT_SUCCESS: {character.key} moved from {old_location} to {limbo_room}")
            except:
                pass
                
        except Exception as e:
            # Log the specific error instead of silently failing
            try:
                splattercast = ChannelDB.objects.get_channel("Splattercast")
                splattercast.msg(f"DEATH_TELEPORT_ERROR: {character.key} - {e}")
            except:
                pass
        
        # TODO: Unpuppet character from account (commented out until character creation ready)
        # if account:
        #     account.unpuppet_object(character)
        # 
        # # Clear character state
        # character.db.account = None
        
        # TODO: Consider setting character to inactive or archiving them
        # character.db.archived = True
        # character.db.death_archived_time = time.time()

    def _initiate_new_character_creation(self, account):
        """Start the character creation process for the account."""
        # Give the account feedback about what happened
        account.msg("|r" + "=" * 60 + "|n")
        account.msg("|rYour character has died and cannot be revived.|n")
        account.msg("|rA corpse has been left behind for investigation.|n")
        account.msg("|r" + "=" * 60 + "|n")
        account.msg("")
        account.msg("|gYou must create a new character to continue playing.|n")
        account.msg("")
        
        # TODO: Implement character creation system
        # For now, provide instructions
        account.msg("|yCharacter creation system is under development.|n")
        account.msg("|yPlease contact staff for assistance creating a new character.|n")
        account.msg("|yUse the |cguest|y command to connect as a guest in the meantime.|n")
        account.msg("")
        
        # TODO: Future implementation might:
        # - Set account state to "needs_character_creation"
        # - Redirect to character creation interface
        # - Provide character creation commands
        # - Handle character naming, stats, description setup


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
        try:
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"DEATH_PROGRESSION: Existing script found for {character.key}")
        except:
            pass
        return existing_script
        
    # Create new death progression script
    try:
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"DEATH_PROGRESSION: Creating new script for {character.key}")
    except:
        pass
        
    script = character.scripts.add(DeathProgressionScript)
    # Set character immediately after creation
    script.db.character = character
    
    # Explicitly start the timer to ensure it begins
    script.start()
    
    try:
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        splattercast.msg(f"DEATH_PROGRESSION: Script created and started: {script} for {character.key}")
    except:
        pass
    
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
