"""
Connection screen file for Evennia.
This version randomizes signal number, glitch message, and year.
"""

import random

def get_connection_screen():
    """
    Dynamically generates a connection screen with slight randomization
    for atmosphere (signal degradation, glitches).
    """
    # Random 2-digit signal number
    signal_number = f"{random.randint(0, 99):02d}"

    # Random glitch message
    glitch_messages = [
        "[ WARNING: Signal instability detected. ]",
        "[ ERROR: Calibration pattern failed. ]",
        "[ ALERT: Tone sequence corrupted. ]",
        "[ NOTICE: Broadcast medium deteriorated. ]"
    ]
    glitch_message = random.choice(glitch_messages)

    # Random corrupted year
    year_display = random.choice(["198█", "NULL"])

    # Return the full screen
    return fr"""
█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒█
█▒▒▒ GELATINOUS MONSTER SYSTEM :: SIGNAL {signal_number} ▒▒▒▒█
█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒█

{glitch_message}
[ Color bars desaturated. ]
[ Anomalous resonance detected at 7.8Hz. ]

YEAR: {year_display} (ENDLESS BROADCAST)
LOCATION: PARTS UNKNOWN

>> Streets: Flowing.
>> Airwaves: Distorted.
>> Flesh: Grainy.
>> Memory: OFFLINE.

__ Connect : connect <accountname> <password>
__ Create  : create <accountname> <password>

>>> END OF TEST PATTERN. BROADCAST WILL NOT RESUME.

█████████████████████████████████████████████████████
"""

