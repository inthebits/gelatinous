#!/usr/bin/env python3
"""
Comparison between old deathscroll and new curtain_of_death
"""

from typeclasses.deathscroll import DEATH_SCROLL
from typeclasses.curtain_of_death import generate_death_curtain

print("=== OLD DEATHSCROLL (Static) ===")
print("Number of frames:", len(DEATH_SCROLL))
print("Sample frame:")
print(DEATH_SCROLL[0])
print("\nAll frames are identical static ASCII art.")

print("\n=== NEW CURTAIN OF DEATH (Dynamic) ===")
message = "A red haze blurs your vision as the world slips away..."
frames = generate_death_curtain(message, width=60)
print("Number of frames:", len(frames))
print("Sample frames:")
print("First frame:")
print(frames[0])
print("\nMiddle frame:")
print(frames[len(frames)//2])
print("\nLast frame:")
print(frames[-1])
print("\nEach frame is dynamically generated and shows progressive dissolution!")

print("\n=== COMPARISON SUMMARY ===")
print("Old system: Static ASCII art, same every time")
print("New system: Dynamic dissolution effect, unique every time")
print("Old system: Simple display, no animation")
print("New system: Animated with timing, customizable messages")
print("Old system: Fixed content")
print("New system: Contextual death types (combat, magic, poison, peaceful)")
