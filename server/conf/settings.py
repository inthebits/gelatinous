r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

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
GAME_SLOGAN = "An abomination to behold"
# The url address to your server, like mymudgame.com. This should be the publicly
# visible location. This is used e.g. on the web site to show how you connect to the
# game over telnet. Default is localhost (only on your machine).
SERVER_HOSTNAME = "play.gel.monster"
# Lockdown mode will cut off the game from any external connections
# and only allow connections from localhost. Requires a cold reboot.
LOCKDOWN_MODE = False
# Controls whether new account registration is available.
# Set to False to lock down the registration page and the create account command.
NEW_ACCOUNT_REGISTRATION_ENABLED = False
# Activate telnet service
TELNET_ENABLED = True
# A list of ports the Evennia telnet server listens on Can be one or many.
TELNET_PORTS = [23]
# This is a security setting protecting against host poisoning
# attacks.  It defaults to allowing all. In production, make
# sure to change this to your actual host addresses/IPs.
ALLOWED_HOSTS = ["gel.monster", "gelatinous.org", "gelatinous.monster", "96d01c0600eef9c99db924a15939abf3-578402624.us-west-2.elb.amazonaws.com"]
# This is a security setting protecting against DJANGO CSRF nonsense
CSRF_TRUSTED_ORIGINS = ['https://gel.monster', 'https://gelatinous.monster', 'https://gelatinous.org', 'https://96d01c0600eef9c99db924a15939abf3-578402624.us-west-2.elb.amazonaws.com', 'https://35.165.102.12']
# Start the evennia webclient. This requires the webserver to be running and
# offers the fallback ajax-based webclient backbone for browsers not supporting
# the websocket one.
WEBCLIENT_ENABLED = False

# Default exit typeclass
DEFAULT_EXIT_TYPECLASS = "typeclasses.exits.Exit"

######################################################################
# Account and Character Management
######################################################################

# Set multisession mode to 1: Account-based login with single character
# This enables proper account/character separation for resleeving mechanics
# Mode 1: Login with account (email), then select/create character
MULTISESSION_MODE = 1

# Enable auto-puppeting for seamless login experience
# Characters will be created/managed through resleeving system
AUTO_CREATE_CHARACTER_WITH_ACCOUNT = False  # We'll handle this custom
AUTO_PUPPET_ON_LOGIN = True  # Puppet last available sleeve

# Use our custom email-based login system
CMDSET_UNLOGGEDIN = "commands.unloggedin_email.UnloggedinEmailCmdSet"
CONNECTION_SCREEN_MODULE = "server.conf.connection_screens"

######################################################################
# Channels
######################################################################
CHANNEL_MUDINFO = {
    "key": "G-INFO",
    "aliases": "",
    "desc": "Connection Log",
    "locks": "control:perm(Developer);listen:perm(Admin);send:false()",
}

DEFAULT_CHANNELS = [
    {
        "key": "Splattercast",
        "aliases": "",
        "desc": "Combat Log",
        "locks": "control:perm(Developer);listen:perm(Admin);send:false()",
    },
]

######################################################################
# Django web features
######################################################################

# While DEBUG is False, show a regular server error page on the web
# stuff, email the traceback to the people in the ADMINS tuple
# below. If True, show a detailed traceback for the web
# browser to display. Note however that this will leak memory when
# active, so make sure to turn it off for a production server!
DEBUG = False

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
