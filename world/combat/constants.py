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
# LONGDESC SYSTEM CONSTANTS
# ===================================================================

# Default human anatomy (auto-created on character creation)
DEFAULT_LONGDESC_LOCATIONS = {
    "head": None, "face": None, "left_eye": None, "right_eye": None, 
    "left_ear": None, "right_ear": None, "neck": None,
    "chest": None, "back": None, "abdomen": None, "groin": None,
    "left_arm": None, "right_arm": None, "left_hand": None, "right_hand": None,
    "left_thigh": None, "right_thigh": None, "left_shin": None, "right_shin": None,
    "left_foot": None, "right_foot": None
}

# Practical limit for total body locations per character
MAX_LONGDESC_LOCATIONS = 50  # Very high, accommodates extensive modifications

# Individual description character limit
MAX_DESCRIPTION_LENGTH = 1000  # Generous limit, allows detailed descriptions

# Paragraph formatting thresholds
PARAGRAPH_BREAK_THRESHOLD = 400  # Characters before automatic paragraph break
REGION_BREAK_PRIORITY = True     # Prefer breaking between anatomical regions

# Valid location validation set (expandable)
VALID_LONGDESC_LOCATIONS = set(DEFAULT_LONGDESC_LOCATIONS.keys())

# Anatomical display order (head to toe)
ANATOMICAL_DISPLAY_ORDER = [
    # Head region
    "head", "face", "left_eye", "right_eye", "left_ear", "right_ear", "neck",
    # Torso region  
    "chest", "back", "abdomen", "groin",
    # Arm region
    "left_arm", "right_arm", "left_hand", "right_hand",
    # Leg region
    "left_thigh", "right_thigh", "left_shin", "right_shin", "left_foot", "right_foot"
]

# Anatomical regions for paragraph breaking
ANATOMICAL_REGIONS = {
    "head_region": ["head", "face", "left_eye", "right_eye", "left_ear", "right_ear", "neck"],
    "torso_region": ["chest", "back", "abdomen", "groin"],
    "arm_region": ["left_arm", "right_arm", "left_hand", "right_hand"],
    "leg_region": ["left_thigh", "right_thigh", "left_shin", "right_shin", "left_foot", "right_foot"]
}

# ===================================================================
# CLOTHING SYSTEM CONSTANTS  
# ===================================================================

# Clothing uses same body locations as longdesc system for consistency
CLOTHING_LOCATIONS = VALID_LONGDESC_LOCATIONS

# Default clothing layer assignments
DEFAULT_CLOTHING_LAYER = 2

# Layer categories for intuitive layering
CLOTHING_LAYERS = {
    1: "Undergarments",    # underwear, undershirts
    2: "Base clothing",    # shirts, pants, dresses  
    3: "Outer wear",       # jackets, coats, robes
    4: "Accessories",      # belts, jewelry
    5: "Outerwear"         # cloaks, heavy coats
}

# Example coverage definitions for common clothing types
SHIRT_COVERAGE = ["chest", "back", "abdomen"]
PANTS_COVERAGE = ["groin", "left_thigh", "right_thigh"] 
JACKET_COVERAGE = ["chest", "back", "abdomen", "left_arm", "right_arm"]
GLOVES_COVERAGE = ["left_hand", "right_hand"]
BOOTS_COVERAGE = ["left_foot", "right_foot"]
HAT_COVERAGE = ["head"]
FULL_ROBE_COVERAGE = ["chest", "back", "abdomen", "groin", "left_arm", "right_arm", "left_thigh", "right_thigh"]

# Style property names (generic for flexibility)
STYLE_ADJUSTABLE = "adjustable"  # rollup/unroll commands
STYLE_CLOSURE = "closure"        # zip/unzip commands

# Default style states
STYLE_STATE_NORMAL = "normal"
STYLE_STATE_ROLLED = "rolled"
STYLE_STATE_ZIPPED = "zipped"
STYLE_STATE_UNZIPPED = "unzipped"

# ===================================================================
# SKINTONE SYSTEM
# ===================================================================

# Skintone palette mapping descriptive names to xterm256 color codes  
SKINTONE_PALETTE = {
    # Pale spectrum - realistic pale tones
    "porcelain": "|555",   # Pure white (5,5,5)
    "pale": "|543",        # Very pale with slight warmth (5,4,3) 
    "fair": "|531",        # Fair peachy tone (5,3,1)
    
    # Natural skin tone range
    "light": "|521",       # Light peach tone (5,2,1)  
    "golden": "|420",      # Golden tone (4,2,0)
    "tan": "|410",         # Tan (4,1,0)
    "olive": "|320",       # Olive undertone (3,2,0)
    "brown": "|210",       # Brown (2,1,0)
    "rich": "|310",        # Rich brown (3,1,0)
}

# Valid skintone names for validation
VALID_SKINTONES = set(SKINTONE_PALETTE.keys())

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
DEBUG_PREFIX_JUMP = "JUMP"
DEBUG_PREFIX_AIM = "AIM"
DEBUG_PREFIX_THROW = "THROW"

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

# Charge system fields (temporary states)
NDB_CHARGE_BONUS = "charge_attack_bonus_active"
NDB_CHARGE_VULNERABILITY = "charging_vulnerability_active"

# Aiming state fields
NDB_AIMING_AT = "aiming_at"
NDB_AIMED_AT_BY = "aimed_at_by"
NDB_AIMING_DIRECTION = "aiming_direction"

# Throw/grenade system fields
NDB_FLYING_OBJECTS = "flying_objects"
NDB_PROXIMITY_UNIVERSAL = "proximity"  # Universal proximity system for grenades
NDB_GRENADE_TIMER = "grenade_timer"
NDB_COUNTDOWN_REMAINING = "countdown_remaining"

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

# Explosive/throwing weapon properties
DB_IS_THROWING_WEAPON = "is_throwing_weapon"
DB_IS_EXPLOSIVE = "is_explosive"
DB_FUSE_TIME = "fuse_time"
DB_BLAST_DAMAGE = "blast_damage"
DB_CHAIN_TRIGGER = "chain_trigger"
DB_REQUIRES_PIN = "requires_pin"
DB_DUD_CHANCE = "dud_chance"
DB_BLAST_RADIUS = "blast_radius"
DB_PIN_PULLED = "pin_pulled"

# Exit properties
DB_IS_EDGE = "is_edge"
DB_EDGE_TYPE = "edge_type"
DB_HEIGHT_ADVANTAGE = "height_advantage"

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
ACTION_THROW = "throw"
ACTION_CATCH = "catch"
ACTION_PULL = "pull"
ACTION_RIG = "rig"

# ===================================================================
# COMBAT ACTION CONSTANTS
# ===================================================================

# Turn-based combat actions
COMBAT_ACTION_RETREAT = "retreat"
COMBAT_ACTION_ADVANCE = "advance"
COMBAT_ACTION_CHARGE = "charge"
COMBAT_ACTION_DISARM = "disarm"

# Existing combat actions (for reference)
COMBAT_ACTION_GRAPPLE_INITIATE = "grapple_initiate"
COMBAT_ACTION_GRAPPLE_JOIN = "grapple_join"
COMBAT_ACTION_RELEASE_GRAPPLE = "release_grapple"
COMBAT_ACTION_ESCAPE_GRAPPLE = "escape_grapple"

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
MSG_RETREAT_PREPARE = "|yYou prepare to retreat from combat.|n"
MSG_RETREAT_QUEUE_SUCCESS = "|yYou will attempt to retreat on your next turn.|n"

# Advance messages
MSG_ADVANCE_NOT_IN_COMBAT = "You need to be in combat to advance on a target."
MSG_ADVANCE_COMBAT_DATA_MISSING = "Your combat data is missing. Please report this."
MSG_ADVANCE_NO_TARGET = "Advance on whom? (You have no current target)."
MSG_ADVANCE_SELF_TARGET = "You cannot advance on yourself."
MSG_ADVANCE_PREPARE = "|yYou prepare to advance on {target}.|n"
MSG_ADVANCE_QUEUE_SUCCESS = "|yYou will attempt to advance on {target} on your next turn.|n"

# Charge messages
MSG_CHARGE_NOT_IN_COMBAT = "You need to be in combat to charge a target."
MSG_CHARGE_COMBAT_DATA_MISSING = "Your combat data is missing. Please report this."
MSG_CHARGE_NO_TARGET = "Charge whom? (You have no current target)."
MSG_CHARGE_SELF_TARGET = "You cannot charge yourself. That would be silly."
MSG_CHARGE_FAILED_PENALTY = "|rYour failed charge leaves you off-balance for a moment.|n"
MSG_CHARGE_PREPARE = "|yYou prepare to charge recklessly at {target}.|n"
MSG_CHARGE_QUEUE_SUCCESS = "|yYou will attempt to charge at {target} on your next turn.|n"

# Disarm messages
MSG_DISARM_NOT_IN_COMBAT = "You are not in combat."
MSG_DISARM_NO_TARGET = "You have no valid target to disarm."
MSG_DISARM_NOT_IN_PROXIMITY = "You must be in melee proximity with {target} to disarm them."
MSG_GRAPPLE_NOT_IN_PROXIMITY = "You must be in melee proximity with {target} to grapple them."
MSG_DISARM_TARGET_EMPTY_HANDS = "{target} has nothing in their hands to disarm."
MSG_DISARM_FAILED = "You try to disarm {target}, but they resist!"
MSG_DISARM_RESISTED = "{attacker} tried to disarm you, but you resisted!"
MSG_DISARM_NOTHING_TO_DISARM = "{target} has nothing to disarm."
MSG_DISARM_SUCCESS_ATTACKER = "You disarm {target}, sending {item} to the ground!"
MSG_DISARM_SUCCESS_VICTIM = "{attacker} disarms you! {item} falls to the ground."
MSG_DISARM_SUCCESS_OBSERVER = "{attacker} disarms {target}, and {item} falls to the ground."
MSG_DISARM_PREPARE = "|yYou prepare to disarm {target}.|n"
MSG_DISARM_QUEUE_SUCCESS = "|yYou will attempt to disarm {target} on your next turn.|n"

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
MSG_STOP_ALREADY_ACCEPTING_GRAPPLE = "You are already accepting the grapple. Use 'escape' to resist violently."
MSG_STOP_ALREADY_YIELDING = "You are already yielding (not actively attacking)."
MSG_RESUME_ATTACKING = "|rYou steel yourself and resume actively attacking (no longer yielding).|n"
MSG_GRAPPLE_AUTO_YIELD = "|yYou are being grappled and automatically yield (restraint mode). Use 'escape' to resist violently.|n"
MSG_GRAPPLE_VIOLENT_SWITCH = "|rYou switch to violent resistance against {grappler}!|n"
MSG_GRAPPLE_ESCAPE_VIOLENT_SWITCH = "|rYou fight desperately for your life against {grappler}'s hold!|n"
MSG_GRAPPLE_AUTO_ESCAPE_VIOLENT = "|rYour successful escape fills you with fighting spirit - you're now actively resisting!|n"
MSG_GRAPPLE_RESTRAINT_HOLD = "|gYou maintain a restraining hold on {victim} (non-violent).|n"
MSG_GRAPPLE_VIOLENT_HOLD = "|rYou tighten your grip on {victim} violently!|n"

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

# Wrest command messages
MSG_WREST_SUCCESS_CALLER = "You quickly snatch the {object} from {target}'s hand!"
MSG_WREST_SUCCESS_TARGET = "{caller} quickly snatches the {object} from your hand!"
MSG_WREST_SUCCESS_ROOM = "{caller} quickly snatches a {object} from {target}'s hand!"
MSG_WREST_FAILED_CALLER = "You try to grab the {object} from {target}'s hand, but they hold on tight!"
MSG_WREST_FAILED_TARGET = "{caller} tries to grab the {object} from your hand, but you maintain your grip!"
MSG_WREST_FAILED_ROOM = "{caller} tries to grab a {object} from {target}'s hand, but they resist!"
MSG_WREST_IN_COMBAT = "You cannot wrest items while in combat. Use 'disarm' instead."
MSG_WREST_NO_FREE_HANDS = "You need at least one free hand to grab something."
MSG_WREST_TARGET_NOT_FOUND = "You cannot find '{target}' here."
MSG_WREST_OBJECT_NOT_IN_HANDS = "'{target}' is not holding '{object}' in their hands."
MSG_WREST_OBJECT_NOT_FOUND = "You cannot find '{object}' to wrest."
MSG_WREST_SAME_ROOM_REQUIRED = "You must be in the same room as '{target}' to wrest from them."

# Throw command messages
MSG_THROW_NOTHING_WIELDED = "You must be holding something to throw it."
MSG_THROW_NO_HANDS = "You have no hands to throw with."
MSG_THROW_OBJECT_NOT_FOUND = "You don't have '{object}' to throw."
MSG_THROW_OBJECT_NOT_WIELDED = "You must be wielding '{object}' to throw it."
MSG_THROW_TARGET_NOT_FOUND = "You cannot find '{target}' to throw at."
MSG_THROW_NO_AIM_CROSS_ROOM = "You must aim in a direction first to throw at targets in other rooms."
MSG_THROW_INVALID_DIRECTION = "There is no exit '{direction}' to throw through."
MSG_THROW_SUGGEST_AT_SYNTAX = "Did you mean 'throw {object} at {target}' instead?"
MSG_THROW_SUGGEST_TO_SYNTAX = "Did you mean 'throw {object} to {direction}' instead?"
MSG_THROW_UNPINNED_GRENADE = "You must pull the pin first before throwing the grenade."
MSG_THROW_TIMER_EXPIRED = "The grenade explodes in your hands!"
MSG_THROW_GRAPPLED = "You cannot throw while grappled."

# Flight announcement messages
MSG_THROW_ORIGIN_DIRECTIONAL = "{thrower} throws {object} {direction}"
MSG_THROW_ORIGIN_TARGETED_SAME = "{thrower} throws {object} at {target}"
MSG_THROW_ORIGIN_TARGETED_CROSS = "{thrower} throws {object} {direction} at someone"
MSG_THROW_ORIGIN_HERE = "{thrower} tosses {object} nearby"
MSG_THROW_ORIGIN_FALLBACK = "{thrower} throws {object} {direction}"
MSG_THROW_ARRIVAL = "{object} flies in from {direction}"
MSG_THROW_LANDING_PROXIMITY = "{object} lands near {target}"
MSG_THROW_LANDING_ROOM = "{object} lands on the ground"
MSG_THROW_WEAPON_HIT = "Your {weapon} strikes {target}!"
MSG_THROW_WEAPON_MISS = "Your {weapon} misses {target} and clatters to the ground."
MSG_THROW_UTILITY_BOUNCE = "The {object} bounces harmlessly off {target}."

# Pull command messages
MSG_PULL_WHAT = "Pull what? Use 'pull pin on <grenade>'."
MSG_PULL_INVALID_SYNTAX = "Use 'pull pin on <grenade>' to arm an explosive."
MSG_PULL_NO_HANDS = "You have no hands to pull pins with."
MSG_PULL_OBJECT_NOT_FOUND = "You don't have '{object}' to pull the pin on."
MSG_PULL_OBJECT_NOT_WIELDED = "You must be wielding '{object}' to pull its pin."
MSG_PULL_NOT_EXPLOSIVE = "'{object}' is not an explosive device."
MSG_PULL_NO_PIN_REQUIRED = "'{object}' does not require pin pulling to activate."
MSG_PULL_ALREADY_PULLED = "The pin on '{object}' has already been pulled."
MSG_PULL_SUCCESS = "You pull the pin on {object}. It starts counting down!"
MSG_PULL_SUCCESS_ROOM = "{puller} pulls the pin on {object}!"
MSG_PULL_TIMER_WARNING = "The {object} will explode in {time} seconds!"

# Catch command messages
MSG_CATCH_WHAT = "Catch what? There's nothing flying to catch."
MSG_CATCH_OBJECT_NOT_FOUND = "You don't see '{object}' flying through the air to catch."
MSG_CATCH_NO_FREE_HANDS = "You need at least one free hand to catch something."
MSG_CATCH_NO_HANDS_AT_ALL = "You have no hands to catch with."
MSG_CATCH_SUCCESS = "You catch {object} out of the air!"
MSG_CATCH_SUCCESS_ROOM = "{catcher} catches {object} out of the air!"
MSG_CATCH_FAILED = "You try to catch {object} but miss!"
MSG_CATCH_FAILED_ROOM = "{catcher} tries to catch {object} but misses!"
MSG_CATCH_TOO_LATE = "You're too late - {object} has already landed."

# Rig command messages
MSG_RIG_WHAT = "Rig what? Use 'rig <grenade> to <exit>'."
MSG_RIG_INVALID_SYNTAX = "Use 'rig <grenade> to <exit>' to trap an exit."
MSG_RIG_NO_HANDS = "You have no hands to rig traps with."
MSG_RIG_OBJECT_NOT_FOUND = "You don't have '{object}' to rig."
MSG_RIG_OBJECT_NOT_WIELDED = "You must be wielding '{object}' to rig it."
MSG_RIG_NOT_EXPLOSIVE = "'{object}' cannot be rigged as a trap."
MSG_RIG_ALREADY_PINNED = "You cannot rig a grenade that already has its pin pulled."
MSG_RIG_INVALID_EXIT = "There is no exit '{exit}' to rig a trap to."
MSG_RIG_EXIT_ALREADY_RIGGED = "There is already a grenade rigged to that exit."
MSG_RIG_SUCCESS = "You rig {object} to the {exit} exit as a trap!"
MSG_RIG_SUCCESS_ROOM = "{rigger} rigs {object} to the {exit} exit!"
MSG_RIG_TRIGGERED = "The rigged {object} explodes as you try to leave!"
MSG_RIG_TRIGGERED_ROOM = "The rigged {object} explodes as {victim} tries to leave!"

# Grenade explosion messages
MSG_GRENADE_EXPLODE_ROOM = "The {grenade} explodes with a deafening blast!"
MSG_GRENADE_DAMAGE = "You are caught in the blast from {grenade}!"
MSG_GRENADE_DAMAGE_ROOM = "{victim} is caught in the blast from {grenade}!"
MSG_GRENADE_DUD = "The {grenade} makes a small 'pop' sound but fails to explode."
MSG_GRENADE_DUD_ROOM = "The {grenade} makes a small 'pop' sound but fails to explode."
MSG_GRENADE_CHAIN_TRIGGER = "The explosion triggers another nearby {grenade}!"

# Flight timing constants
THROW_FLIGHT_TIME = 2  # seconds

# ===================================================================
# COMBAT TIMING CONSTANTS
# ===================================================================

# Round timing
COMBAT_ROUND_INTERVAL = 6  # seconds - base combat round duration
STAGGER_DELAY_INTERVAL = 1.5  # seconds - delay between staggered attacks
MAX_STAGGER_DELAY = 4.5  # seconds - maximum delay to ensure completion before next round

# ===================================================================
# SCRIPT & HANDLER CONSTANTS
# ===================================================================

# From existing combathandler.py
COMBAT_SCRIPT_KEY = "combat_handler_script"  # Will need to verify this from actual file
