r"""
Evennia settings file.

The available options are found in the default settings file found
here:

/home/ubuntu/muddev/evennia/evennia/settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Gelatinous Monster"
# Short one-sentence blurb describing your game. Shown under the title
# on the website and could be used in online listings of your game etc.
GAME_SLOGAN = "A game of Amorphous Oozes"
# Interface addresses to listen to. If 0.0.0.0, listen to all. Use :: for IPv6.
WEBSERVER_INTERFACES = ['127.0.0.1']
# Interface addresses to listen to. If 0.0.0.0, listen to all. Use :: for IPv6.
WEBSOCKET_CLIENT_INTERFACE = '127.0.0.1'
# Actual URL for webclient component to reach the websocket. You only need
# to set this if you know you need it, like using some sort of proxy setup.
# If given it must be on the form "ws[s]://hostname[:port]". If left at None,
# the client will itself figure out this url based on the server's hostname.
# e.g. ws://external.example.com or wss://external.example.com:443
WEBSOCKET_CLIENT_URL ="wss://gel.monster:4002/"
# Activate Telnet+SSL protocol (SecureSocketLibrary) for supporting clients
SSL_ENABLED = False
# While DEBUG is False, show a regular server error page on the web
# stuff, email the traceback to the people in the ADMINS tuple
# below. If True, show a detailed traceback for the web
# browser to display. Note however that this will leak memory when
# active, so make sure to turn it off for a production server!
DEBUG = False
# Cross Site Request Forgery Trusted Origins
CSRF_TRUSTED_ORIGINS = ['https://gelatinous.monster','https://gel.monster','https://gelatinous.org']

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
