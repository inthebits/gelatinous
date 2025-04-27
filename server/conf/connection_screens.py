# -*- coding: utf-8 -*-
"""
Connection screen

This is the text to show the user when they first connect to the game (before
they log in).

To change the login screen in this module, do one of the following:

- Define a function `connection_screen()`, taking no arguments. This will be
  called first and must return the full string to act as the connection screen.
  This can be used to produce more dynamic screens.
- Alternatively, define a string variable in the outermost scope of this module
  with the connection string that should be displayed. If more than one such
  variable is given, Evennia will pick one of them at random.

The commands available to the user when the connection screen is shown
are defined in evennia.default_cmds.UnloggedinCmdSet. The parsing and display
of the screen is done by the unlogged-in "look" command.

"""

# -*- coding: utf-8 -*-
"""
Connection screen

Dynamic connection screen with random signal number.
"""

from django.conf import settings
import random
from evennia import utils

# Random 2-digit signal number
signal_number = f"{random.randint(0, 99):02d}"

# Random glitch message
glitch_messages = [
    "WARNING: Signal instability detected.",
    "ERROR: Calibration pattern failed.",
    "ALERT: Tone sequence corrupted.",
    "NOTICE: Broadcast medium deteriorated."
]
glitch_message = random.choice(glitch_messages)

# Random corrupted year
year_display = random.choice(["198█", "NULL"])

CONNECTION_SCREEN = """

|b█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒█
█▒▒▒▒ |g{} SYSTEM |n ::: SIGNAL {} |b▒▒▒▒▒█
█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒█|n

[ {} ]
[ Color bars desaturated. ]
[ Anomalous resonance detected at 7.8Hz. ] 

YEAR: {} (ENDLESS BROADCAST)
LOCATION: PARTS UNKNOWN
 
>> Streets: Flowing.
>> Airwaves: Distorted.
>> Flesh: Grainy.
>> Memory: OFFLINE.

__ Connect : |wconnect <accountname> <password>|n
__ Create  : |wcreate <accountname> <password>|n

If you have spaces in your username, enclose it in quotes.
Enter |whelp|n for more info. |wlook|n will re-show this screen.

>>> END OF TEST PATTERN. BROADCAST WILL NOT RESUME WITHOUT PROMPT.

|b█████████████████████████████████████████████████████|n

""".format(
    settings.SERVERNAME, signal_number, glitch_message, year_display
)
