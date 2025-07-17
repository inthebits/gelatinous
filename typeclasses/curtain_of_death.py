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
    # Use Evennia's color system - all red variations for pure blood effect
    colors = ["|r", "|R"]  # Just red variations for blood effect
    
    colored = []
    for char in text:
        if char != " ":  # Don't colorize spaces
            colored.append(f"{random.choice(colors)}{char}")
        else:
            colored.append(char)
    
    colored.append("|n")  # Always reset color at the end
    return "".join(colored)


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
    
    # Center the message on a sea of '▓' characters (avoiding | for Evennia colors)
    padded = text.center(width, "▓")
    chars = list(padded)
    
    # Create drip starting positions - focus on creating fewer but more dramatic drips
    num_drips = min(12, width // 6)  # Limit to ~12 drips max, spaced out
    drip_positions = []
    for i in range(num_drips):
        pos = int((i + 1) * width / (num_drips + 1))  # Evenly space drips
        drip_length = random.randint(3, 8)  # Each drip affects 3-8 characters
        drip_positions.append((pos, drip_length))
    
    frames = [_colorize_evennia("".join(chars))]  # First frame (untouched)
    
    # Create dripping effect - each drip progresses downward
    for drip_step in range(8):  # Each drip takes 8 steps to complete
        current_chars = chars[:]  # Copy current state
        
        for drip_pos, drip_len in drip_positions:
            # Create a drip pattern that grows longer each step
            drip_progress = min(drip_step + 1, drip_len)
            
            # Remove characters in a drip pattern from the center outward
            for offset in range(drip_progress):
                left_pos = drip_pos - offset
                right_pos = drip_pos + offset
                
                if 0 <= left_pos < len(current_chars) and current_chars[left_pos] != " ":
                    current_chars[left_pos] = " "
                if 0 <= right_pos < len(current_chars) and current_chars[right_pos] != " ":
                    current_chars[right_pos] = " "
        
        # Create frame with remaining characters
        frame = "".join(current_chars)
        frames.append(_colorize_evennia(frame))
    
    # Final frame: mostly empty with just a few remaining drops
    final_chars = [" "] * width
    for drip_pos, _ in drip_positions[::3]:  # Keep every 3rd drip position
        if random.random() < 0.4:  # 40% chance to keep a remnant
            final_chars[drip_pos] = "▓"
    frames.append(_colorize_evennia("".join(final_chars)))
    
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
        
        # Default death message if none provided
        if message is None:
            message = "A red haze blurs your vision as the world slips away..."
        
        self.message = message
        self.frames = curtain_of_death(message, session=self.session)
        self.current_frame = 0
        self.frame_delay = 0.05  # Start slower than before (was 0.015)
        self.delay_multiplier = 1.02  # More significant slowdown (was 1.005)
        
    def start_animation(self):
        """Start the death curtain animation."""
        self.current_frame = 0
        self._show_next_frame()
        
    def _show_next_frame(self):
        """Show the next frame of the animation."""
        if self.current_frame < len(self.frames):
            # Send current frame to the dying character
            if self.character:
                self.character.msg(self.frames[self.current_frame])
            
            # Optionally send to room observers (less frequently)
            if self.location and self.current_frame % 15 == 0:
                observer_msg = f"|r{self.character.key} is dying...|n"
                self.location.msg_contents(observer_msg, exclude=[self.character])
            
            self.current_frame += 1
            
            # Schedule next frame with increasing delay (like original)
            delay(self.frame_delay, self._show_next_frame)
            self.frame_delay *= self.delay_multiplier
        else:
            # Animation complete, trigger death
            self._on_animation_complete()
            
    def _on_animation_complete(self):
        """Called when the animation completes."""
        # Final death message using detected width
        final_msg = (
            "\n|r" + "=" * self.width + "|n\n"
            "|r" + "DEATH".center(self.width) + "|n\n"
            "|r" + "=" * self.width + "|n"
        )
        
        if self.character:
            self.character.msg(final_msg)
            
        # Notify observers
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
