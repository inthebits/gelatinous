"""
Curtain of Death - Death Animation System for Evennia

This module provides a "dripping blood" death animation that creates
a curtain effect by progressively removing characters from a message.
Based on the elegant design that centers text in a "sea" of characters
and creates a dripping effect by removing characters in sequence.
Compatible with Evennia's messaging and delay systems.
"""

import random
from evennia.utils import delay


def _get_terminal_width(session=None):
    """
    Get terminal width from session, defaulting to 78 for MUD compatibility.
    Subtracts 5 characters for safety margin to prevent wrapping.
    
    Args:
        session: Evennia session object to get width from
        
    Returns:
        int: Terminal width in characters (with safety margin)
    """
    if session:
        # Use Evennia's built-in screen width detection
        try:
            detected_width = session.protocol_flags.get("SCREENWIDTH", [78])[0]
            # Subtract 5 for safety margin to prevent wrapping
            return max(68, detected_width - 5)  # Minimum 68 to ensure readability
        except (IndexError, KeyError, TypeError):
            # Fallback if protocol flags aren't available or malformed
            pass
    return 78


def _colorize_evennia(text):
    """Apply Evennia color codes to text for a blood-red effect."""
    # Use Evennia's color system - random red variations for blood effect
    colors = ["|r", "|R"]  # Red variations for blood effect
    
    colored = []
    for char in text:
        if char != " ":  # Don't colorize spaces
            colored.append(f"{random.choice(colors)}{char}")
        else:
            colored.append(char)
    
    colored.append("|n")  # Always reset color at the end
    return "".join(colored)


def _strip_color_codes(text):
    """
    Remove Evennia color codes to get the visible text length.
    
    Args:
        text (str): Text with color codes
        
    Returns:
        str: Text without color codes
    """
    import re
    # Remove all |x and |xx codes (where x is any character)
    return re.sub(r'\|.', '', text)


def curtain_of_death(text, width=None, session=None):
    """
    Create a "dripping blood" death curtain animation.
    
    Args:
        text (str): The message to animate
        width (int, optional): Width of the display area
        session: Evennia session object for width detection
        
    Returns:
        List[str]: Animation frames
    """
    if width is None:
        width = _get_terminal_width(session)
    
    # Calculate visible text length (without color codes)
    visible_text = _strip_color_codes(text)
    
    # For the first frame, use the text as-is (with its color codes)
    # Center it with colored blocks
    padding_needed = width - len(visible_text)
    left_padding = padding_needed // 2
    right_padding = padding_needed - left_padding
    
    # Create colored padding blocks
    left_blocks = _colorize_evennia("▓" * left_padding)
    right_blocks = _colorize_evennia("▓" * right_padding)
    
    first_frame = left_blocks + text + right_blocks
    
    # For subsequent frames, work with a plain version for character removal
    plain_padded = visible_text.center(width, "▓")
    chars = list(plain_padded)
    
    # Build the "plan": a shuffled list of (index, drop-distance) pairs
    plan = [(i, random.randint(1, i + 1)) for i in range(len(chars))]
    random.shuffle(plan)
    
    frames = [first_frame]  # First frame with proper colors
    
    # Create dripping effect by removing characters in planned sequence
    # Only process every 3rd character to reduce vertical scroll
    for idx, _ in plan[::3]:  # Skip every 3rd character to reduce frame count
        if chars[idx] == " ":  # Skip spaces
            continue
        chars[idx] = " "  # 'Erase' the character
        frame = "".join(chars).center(width, "█")  # Replace the sea with different char
        frames.append(_colorize_evennia(frame))
    
    # Add several more frames of continued dripping
    for i in range(5):  # Add 5 more frames of dripping
        frame = " " * width  # Empty line
        frames.append(_colorize_evennia(frame))
    
    # Add the DEATH message in the middle of continued dripping
    death_frame = "|r" + "DEATH".center(width) + "|n"
    frames.append(death_frame)
    
    # Add one more frame after DEATH
    final_frame = " " * width
    frames.append(_colorize_evennia(final_frame))
    
    return frames


class DeathCurtain:
    """
    Creates a "dripping blood" death animation by progressively removing
    characters from a death message to create a curtain effect.
    """
    
    def __init__(self, character, message=None):
        """
        Initialize the death curtain animation.
        
        Args:
            character: The character object to send the animation to
            message (str, optional): Custom death message
        """
        self.character = character
        self.location = character.location
        
        # Get session for width detection
        self.session = None
        if character and hasattr(character, 'sessions') and character.sessions.get():
            self.session = character.sessions.get()[0]
        
        # Get terminal width for this character's session
        self.width = _get_terminal_width(self.session)
        
        # Create informed death message based on cause
        if message is None:
            # Always use the beautiful mixed red message for the curtain
            message = "|rA |Rred |rhaze |Rblurs |ryour |Rvision |ras |Rthe |rworld |Rslips |raway|R...|n"
        
        self.message = message
        self.frames = curtain_of_death(message, session=self.session)
        self.current_frame = 0
        self.frame_delay = 0.05  # Start slower than before (was 0.015)
        self.delay_multiplier = 1.02  # More significant slowdown (was 1.005)
        
    def start_animation(self):
        """Start the death curtain animation."""
        # Send initial death messages before the curtain starts
        if self.location:
            # Get death cause for both messages
            death_cause = None
            if hasattr(self.character, 'get_death_cause'):
                death_cause = self.character.get_death_cause()
            
            # Send victim's initial death message
            if self.character:
                if death_cause:
                    victim_msg = f"|rYour body succumbs to {death_cause}. The end draws near...|n"
                else:
                    victim_msg = f"|rYour body fails you. The end draws near...|n"
                self.character.msg(victim_msg)
            
            # Send observer message
            if death_cause:
                observer_msg = f"|r{self.character.key} is dying from {death_cause}...|n"
            else:
                observer_msg = f"|r{self.character.key} is dying...|n"
                
            self.location.msg_contents(observer_msg, exclude=[self.character])
        
        self.current_frame = 0
        self._show_next_frame()
        
    def _show_next_frame(self):
        """Show the next frame of the animation."""
        if self.current_frame < len(self.frames):
            # Send current frame to the dying character
            if self.character:
                self.character.msg(self.frames[self.current_frame])
            
            self.current_frame += 1
            
            # Schedule next frame with increasing delay (like original)
            delay(self.frame_delay, self._show_next_frame)
            self.frame_delay *= self.delay_multiplier
        else:
            # Animation complete, trigger death
            self._on_animation_complete()
            
    def _on_animation_complete(self):
        """Called when the animation completes."""
        # Animation already includes the DEATH message, so just notify observers
        if self.location:
            death_msg = f"|r{self.character.key} has died.|n"
            self.location.msg_contents(death_msg, exclude=[self.character])


def show_death_curtain(character, message=None):
    """
    Convenience function to show the death curtain animation.
    
    Args:
        character: The character object to show the animation to
        message (str, optional): Custom death message
    """
    curtain = DeathCurtain(character, message)
    curtain.start_animation()