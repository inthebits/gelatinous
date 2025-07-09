"""
Combat System Constants

All constants used throughout the combat system, organized by category
for easy maintenance and modification. Extracted from actual codebase
analysis to prevent magic strings and improve maintainability.

Following Python best practices with clear, descriptive names and
logical grouping.
"""

# ===================================================================
# CHARACTER ATTRIBUTES & DEFAULTS
# ===================================================================

# G.R.I.M. system defaults
DEFAULT_GRIT = 1
DEFAULT_RESONANCE = 1
DEFAULT_INTELLECT = 1
DEFAULT_MOTORICS = 1

# G.R.I.M. stat names (for attribute access)
STAT_GRIT = "grit"
STAT_RESONANCE = "resonance" 
STAT_INTELLECT = "intellect"
STAT_MOTORICS = "motorics"

# Health system
DEFAULT_HP = 10
HP_GRIT_MULTIPLIER = 2

# Equipment defaults
DEFAULT_HANDS = {"left": None, "right": None}
DEFAULT_WEAPON_TYPE = "unarmed"
FALLBACK_WEAPON_NAME = "your fists"

# ===================================================================
# CHANNELS & LOGGING
# ===================================================================

# Channel names
SPLATTERCAST_CHANNEL = "Splattercast"

# Debug message prefixes
DEBUG_PREFIX_HANDLER = "HANDLER"
DEBUG_PREFIX_ATTACK = "ATTACK_CMD"
DEBUG_PREFIX_FLEE = "FLEE_CMD"
DEBUG_PREFIX_RETREAT = "RETREAT"
DEBUG_PREFIX_ADVANCE = "ADVANCE"
DEBUG_PREFIX_GRAPPLE = "GRAPPLE"
DEBUG_PREFIX_CHARGE = "CHARGE"
DEBUG_PREFIX_AIM = "AIM"

# Debug action types
DEBUG_VALID = "VALID"
DEBUG_INVALID = "INVALID"
DEBUG_SUCCESS = "SUCCESS"
DEBUG_FAIL = "FAIL"
DEBUG_ERROR = "ERROR"
DEBUG_FAILSAFE = "FAILSAFE"
DEBUG_ABORT = "ABORT"
DEBUG_CLEANUP = "CLEANUP"
DEBUG_TEMPLATE = "DEBUG"  # Generic debug prefix for utility functions

# ===================================================================
# NDB FIELD NAMES (Critical for State Management)
# ===================================================================

# Combat state fields
NDB_COMBAT_HANDLER = "combat_handler"
NDB_PROXIMITY = "in_proximity_with"
NDB_SKIP_ROUND = "skip_combat_round"

# Aiming state fields
NDB_AIMING_AT = "aiming_at"
NDB_AIMED_AT_BY = "aimed_at_by"
NDB_AIMING_DIRECTION = "aiming_direction"

# ===================================================================
# DATABASE FIELD NAMES
# ===================================================================

# Handler database fields
DB_COMBATANTS = "combatants"
DB_COMBAT_RUNNING = "combat_is_running"
DB_MANAGED_ROOMS = "managed_rooms"

# Combatant entry fields
DB_CHAR = "char"
DB_TARGET_DBREF = "target_dbref"
DB_GRAPPLING_DBREF = "grappling_dbref"
DB_GRAPPLED_BY_DBREF = "grappled_by_dbref"
DB_IS_YIELDING = "is_yielding"

# ===================================================================
# PERMISSIONS & ACCESS
# ===================================================================

# Permission strings
PERM_BUILDER = "Builder"
PERM_DEVELOPER = "Developer"
PERM_ALL = "all()"

# Access types
ACCESS_TRAVERSE = "traverse"
ACCESS_VIEW = "view"

# ===================================================================
# COLOR CODES & FORMATTING
# ===================================================================

# Combat colors
COLOR_SUCCESS = "|g"
COLOR_FAILURE = "|r"
COLOR_WARNING = "|y"
COLOR_COMBAT = "|R"
COLOR_NORMAL = "|n"

# Box drawing characters (for @stats and other displays)
BOX_TOP_LEFT = "╔"
BOX_TOP_RIGHT = "╗"
BOX_BOTTOM_LEFT = "╚"
BOX_BOTTOM_RIGHT = "╝"
BOX_HORIZONTAL = "═"
BOX_VERTICAL = "║"
BOX_TEE_DOWN = "╠"
BOX_TEE_UP = "╣"

# ===================================================================
# MOVEMENT & ACTIONS
# ===================================================================

# Movement parameters
MOVE_QUIET = True
MOVE_HOOKS = False

# Dice rolling
MIN_DICE_VALUE = 1
DEFAULT_DICE_SIDES = 1

# ===================================================================
# WEAPON & COMBAT TYPES
# ===================================================================

# Weapon categories
WEAPON_TYPE_UNARMED = "unarmed"
WEAPON_TYPE_RANGED = "ranged"
WEAPON_TYPE_MELEE = "melee"

# Combat actions
ACTION_ATTACK = "attack"
ACTION_FLEE = "flee"
ACTION_RETREAT = "retreat"
ACTION_ADVANCE = "advance"
ACTION_CHARGE = "charge"
ACTION_GRAPPLE = "grapple"
ACTION_DISARM = "disarm"
ACTION_AIM = "aim"
ACTION_STOP = "stop"

# ===================================================================
# MESSAGE TEMPLATES
# ===================================================================

# Common message patterns
MSG_ATTACK_WHO = "Attack who?"
MSG_SELF_TARGET = "You can't attack yourself."
MSG_NO_COMBAT_DATA = "Your combat data is missing. Please report this."
MSG_NOT_IN_COMBAT = "You are not in combat."
MSG_NOTHING_TO_FLEE = "You have nothing to flee from."

# Flee messages
MSG_NO_EXITS = "There are no exits here to flee through."
MSG_FLEE_NO_EXITS = "|rThere are no exits here to flee through.|n"
MSG_FLEE_PINNED_BY_AIM = "|rYou are being aimed at by {aimer}, and there are no exits here! You are pinned down.|n"
MSG_FLEE_TRAPPED_IN_COMBAT = "|rYou are in combat, and there are no exits here! You are trapped.|n"
MSG_FLEE_ALL_EXITS_COVERED = "|rYou cannot flee! All escape routes are covered by ranged attackers targeting you from adjacent areas.|n Consider using 'charge' or 'advance' to engage them, or 'retreat' if you need to create distance from local threats first."
MSG_FLEE_BREAK_FREE_AIM = "|gYou deftly break free from {aimer}'s aim!|n"
MSG_FLEE_FAILED_BREAK_AIM = "|RYou try to break free from {aimer}'s aim, but they keep you pinned!|n"
MSG_FLEE_COMBAT_FAILED = "|rYou try to flee from combat, but fail!|n"
MSG_FLEE_NO_TARGET_ERROR = "|rError: Your combat entry is missing. Please report to an admin.|n"
MSG_FLEE_DISENGAGE_NO_ATTACKERS = "No one is actively attacking you in combat; you disengage."
MSG_FLEE_DISENGAGE_SUCCESS_GENERIC = "Your attackers seem unable to stop you; you disengage."
MSG_FLEE_PARTIAL_SUCCESS = "|yYou manage to break away from your immediate attackers, but all escape routes are covered or inaccessible! You remain in the area, still in combat.|n"
MSG_FLEE_AIM_BROKEN_NO_MOVE = "You broke free from their aim but found no clear path to move or all paths were unsafe."

# Retreat messages
MSG_RETREAT_NOT_IN_COMBAT = "You are not in combat and thus not in melee proximity with anyone."
MSG_RETREAT_COMBAT_DATA_MISSING = "Your combat data is missing. Please report this."
MSG_RETREAT_PROXIMITY_UNCLEAR = "Your proximity status is unclear. This shouldn't happen. (Error: NDB missing/invalid)"
MSG_RETREAT_NO_PROXIMITY = "You are not in direct melee proximity with anyone to retreat from."
MSG_RETREAT_SUCCESS = "|gYou manage to break away from the immediate melee!|n"
MSG_RETREAT_FAILED = "|rYou try to break away, but you're held fast in the melee!|n"

# Advance messages
MSG_ADVANCE_NOT_IN_COMBAT = "You need to be in combat to advance on a target."
MSG_ADVANCE_COMBAT_DATA_MISSING = "Your combat data is missing. Please report this."
MSG_ADVANCE_NO_TARGET = "Advance on whom? (You have no current target)."
MSG_ADVANCE_SELF_TARGET = "You cannot advance on yourself."

# Charge messages
MSG_CHARGE_NOT_IN_COMBAT = "You need to be in combat to charge a target."
MSG_CHARGE_COMBAT_DATA_MISSING = "Your combat data is missing. Please report this."
MSG_CHARGE_NO_TARGET = "Charge whom? (You have no current target)."
MSG_CHARGE_SELF_TARGET = "You cannot charge yourself. That would be silly."
MSG_CHARGE_FAILED_PENALTY = "|rYour failed charge leaves you off-balance for a moment.|n"

# Disarm messages
MSG_DISARM_NOT_IN_COMBAT = "You are not in combat."
MSG_DISARM_NO_TARGET = "You have no valid target to disarm."
MSG_DISARM_TARGET_EMPTY_HANDS = "{target} has nothing in their hands to disarm."
MSG_DISARM_FAILED = "You try to disarm {target}, but they resist!"
MSG_DISARM_RESISTED = "{attacker} tried to disarm you, but you resisted!"
MSG_DISARM_NOTHING_TO_DISARM = "{target} has nothing to disarm."
MSG_DISARM_SUCCESS_ATTACKER = "You disarm {target}, sending {item} to the ground!"
MSG_DISARM_SUCCESS_VICTIM = "{attacker} disarms you! {item} falls to the ground."
MSG_DISARM_SUCCESS_OBSERVER = "{attacker} disarms {target}, and {item} falls to the ground."

# Grapple messages
MSG_GRAPPLE_WHO = "Grapple whom?"
MSG_GRAPPLE_NO_TARGET = "No valid target found to grapple."
MSG_CANNOT_GRAPPLE_SELF = "You can't grapple yourself."
MSG_CANNOT_GRAPPLE_TARGET = "That can't be grappled."
MSG_GRAPPLE_HANDLER_ERROR = "Error: Could not find or create combat handler."  # Should be rare
MSG_GRAPPLE_COMBAT_ADD_ERROR = "There was an issue adding you to combat. Please try again."
MSG_ALREADY_GRAPPLING = "You are already grappling {target}. You must release them first."
MSG_CANNOT_GRAPPLE_WHILE_GRAPPLED = "You cannot initiate a grapple while {grappler} is grappling you. Try to escape first."
MSG_TARGET_ALREADY_GRAPPLED = "{target} is already being grappled by {grappler}."
MSG_GRAPPLE_PREPARE = "You prepare to grapple {target}..."

# Escape grapple messages
MSG_ESCAPE_NOT_IN_COMBAT = "You are not in combat."
MSG_ESCAPE_NOT_REGISTERED = "You are not properly registered in the current combat."
MSG_ESCAPE_NOT_GRAPPLED = "You are not currently being grappled by anyone."

# Release grapple messages
MSG_RELEASE_NOT_IN_COMBAT = "You are not in combat."
MSG_RELEASE_NOT_GRAPPLING = "You are not currently grappling anyone."

# Stop command messages
MSG_STOP_WHAT = "Stop what? You can 'stop aiming' or 'stop attacking'."
MSG_STOP_NOT_AIMING = "You are not currently aiming at anything."
MSG_STOP_AIM_ERROR = "|rError: Cannot process 'stop aiming'. Character is missing 'clear_aim_state' method.|n"
MSG_STOP_NOT_IN_COMBAT = "You are not in combat to stop attacking."
MSG_STOP_NOT_REGISTERED = "You are not properly registered in the current combat."
MSG_STOP_YIELDING = "|gYou lower your guard and will not actively attack (you are now yielding).|n"
MSG_STOP_ALREADY_ACCEPTING_GRAPPLE = "You are already accepting the grapple. Use 'escape', 'resist', or 'attack [grappler]' to resume struggling."
MSG_STOP_ALREADY_YIELDING = "You are already yielding (not actively attacking)."

# Aim command messages
MSG_AIM_NOT_AIMING = "You are not aiming at anything or in any direction. To aim, use 'aim <target/direction>'."
MSG_AIM_STOP_ERROR = "|rError: Cannot process stop aim command. Character is missing 'clear_aim_state' method.|n"
MSG_AIM_WHO_WHAT = "Aim at whom or in what direction?"
MSG_AIM_SELF_TARGET = "You can't aim at yourself."

# Grapple messages
MSG_CANNOT_WHILE_GRAPPLED = "You cannot {action} while {grappler} is grappling you."
MSG_CANNOT_WHILE_GRAPPLED_RETREAT = "You cannot retreat while {grappler} is grappling you! Try 'escape'."

# Movement messages
MSG_FLEE_SUCCESS = "You succeed in {reason}! You flee {exit} and arrive in {destination}."
MSG_RETREAT_SUCCESS = "|gYou manage to break away from the immediate melee!|n"

# ===================================================================
# SCRIPT & HANDLER CONSTANTS
# ===================================================================

# From existing combathandler.py
COMBAT_SCRIPT_KEY = "combat_handler_script"  # Will need to verify this from actual file
