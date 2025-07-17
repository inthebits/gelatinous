#!/usr/bin/env python3
"""
Curtain of Death effect for Evennia MUD
Adapted from curtain_of_death.py by a friend

Creates a dynamic "dissolving" animation effect for death sequences.
"""

import random
from typing import List
from evennia.utils.utils import delay


# ---------------------------------------------------------------------------
#  Core death curtain effect
# ---------------------------------------------------------------------------
def generate_death_curtain(message: str, width: int = 80) -> List[str]:
    """
    Generate frames for the death curtain effect.
    
    Args:
        message: The death message to display
        width: Display width (defaults to 80 for MUD compatibility)
    
    Returns:
        List of strings representing animation frames
    """
    # Center the message on a sea of '|' characters
    padded = message.center(width, "|")
    chars = list(padded)
    
    # Build the "plan": a shuffled list of (index, drop-distance) pairs
    plan = [(i, random.randint(1, i + 1)) for i in range(len(chars))]
    random.shuffle(plan)
    
    # First frame: complete message with simple red coloring
    frames = [f"|r{''.join(chars)}|n"]
    
    # Progressive dissolution
    for idx, _ in plan:
        if chars[idx] == " ":
            continue
        chars[idx] = " "  # 'erase' the character
        frame = "".join(chars).center(width, "#")  # replace the sea
        frames.append(f"|r{frame}|n")
    
    # Final frame: restore original message
    frames.append(f"|r{padded}|n")
    
    return frames


def send_death_curtain(character, message: str = None, width: int = 80, 
                      frame_delay: float = 0.2, speed_increase: float = 1.01):
    """
    Send the death curtain effect to a character with proper timing.
    
    Args:
        character: The character object to send the effect to
        message: Death message (defaults to standard message)
        width: Display width
        frame_delay: Initial delay between frames (increased for readability)
        speed_increase: Multiplier for increasing speed
    """
    if message is None:
        message = "A red haze blurs your vision as the world slips away..."
    
    try:
        frames = generate_death_curtain(message, width)
        
        def send_frame(frame_index, current_delay):
            """Send a single frame with proper timing."""
            if frame_index >= len(frames):
                return
                
            character.msg(frames[frame_index])
            
            # Schedule next frame with increasing speed
            next_delay = current_delay * speed_increase
            if frame_index + 1 < len(frames):
                delay(next_delay, send_frame, frame_index + 1, next_delay)
        
        # Start the animation
        send_frame(0, frame_delay)
        
    except Exception as e:
        # Fallback to simple message if curtain effect fails
        character.msg(f"|r{message}|n")
        # Optional: log the error for debugging
        # print(f"Death curtain error: {e}")


def send_death_curtain_instant(character, message: str = None, width: int = 80):
    """
    Send the death curtain effect instantly (all frames at once).
    For players who prefer immediate feedback.
    """
    if message is None:
        message = "A red haze blurs your vision as the world slips away..."
    
    frames = generate_death_curtain(message, width)
    
    # Send all frames immediately
    for frame in frames:
        character.msg(frame)


# ---------------------------------------------------------------------------
#  Convenience functions for different death types
# ---------------------------------------------------------------------------
def death_by_combat(character):
    """Standard combat death curtain."""
    send_death_curtain(
        character,
        "Steel parts flesh as your life ebbs away in crimson rivulets...",
        frame_delay=0.08
    )


def death_by_magic(character):
    """Magical death curtain with different colors."""
    # Could modify colors here for magical deaths
    send_death_curtain(
        character,
        "Arcane energies tear through your essence as reality dissolves...",
        frame_delay=0.06
    )


def death_by_poison(character):
    """Poison death curtain."""
    send_death_curtain(
        character,
        "Toxins course through your veins as darkness claims you...",
        frame_delay=0.12  # Slower for poison
    )


def death_peaceful(character):
    """Peaceful death curtain."""
    send_death_curtain(
        character,
        "A gentle darkness embraces you as you slip into eternal rest...",
        frame_delay=0.15  # Much slower for peaceful death
    )
