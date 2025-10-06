"""
Prototypes

A prototype is a simple way to create individualized instances of a
given typeclass. It is dictionary with specific key names.

For example, you might have a Sword typeclass that implements everything a
Sword would need to do. The only difference between different individual Swords
would be their key, description and some Attributes. The Prototype system
allows to create a range of such Swords with only minor variations. Prototypes
can also inherit and combine together to form entire hierarchies (such as
giving all Sabres and all Broadswords some common properties). Note that bigger
variations, such as custom commands or functionality belong in a hierarchy of
typeclasses instead.

A prototype can either be a dictionary placed into a global variable in a
python module (a 'module-prototype') or stored in the database as a dict on a
special Script (a db-prototype). The former can be created just by adding dicts
to modules Evennia looks at for prototypes, the latter is easiest created
in-game via the `olc` command/menu.

Prototypes are read and used to create new objects with the `spawn` command
or directly via `evennia.spawn` or the full path `evennia.prototypes.spawner.spawn`.

A prototype dictionary have the following keywords:

Possible keywords are:
- `prototype_key` - the name of the prototype. This is required for db-prototypes,
  for module-prototypes, the global variable name of the dict is used instead
- `prototype_parent` - string pointing to parent prototype if any. Prototype inherits
  in a similar way as classes, with children overriding values in their parents.
- `key` - string, the main object identifier.
- `typeclass` - string, if not set, will use `settings.BASE_OBJECT_TYPECLASS`.
- `location` - this should be a valid object or #dbref.
- `home` - valid object or #dbref.
- `destination` - only valid for exits (object or #dbref).
- `permissions` - string or list of permission strings.
- `locks` - a lock-string to use for the spawned object.
- `aliases` - string or list of strings.
- `attrs` - Attributes, expressed as a list of tuples on the form `(attrname, value)`,
  `(attrname, value, category)`, or `(attrname, value, category, locks)`. If using one
   of the shorter forms, defaults are used for the rest.
- `tags` - Tags, as a list of tuples `(tag,)`, `(tag, category)` or `(tag, category, data)`.
-  Any other keywords are interpreted as Attributes with no category or lock.
   These will internally be added to `attrs` (equivalent to `(attrname, value)`.

See the `spawn` command and `evennia.prototypes.spawner.spawn` for more info.

"""

# =============================================================================
# EXPLOSIVE PROTOTYPES FOR THROW COMMAND TESTING
# =============================================================================

# Base explosive prototype with common properties
EXPLOSIVE_BASE = {
    "typeclass": "typeclasses.items.Item",
    "desc": "A military-grade explosive device with a pin-pull mechanism.",
    "is_explosive": True,
    "requires_pin": True,
    "pin_pulled": False,
    "chain_trigger": True,
    "dud_chance": 0.05,  # 5% chance to fail
    "damage_type": "laceration",  # Fragmentation/shrapnel wounds
}

# Standard fragmentation grenade
FRAG_GRENADE = {
    "prototype_parent": "EXPLOSIVE_BASE",
    "key": "frag grenade",
    "aliases": ["grenade", "frag"],
    "desc": "A standard military fragmentation grenade. Pull the pin and throw within 8 seconds or take cover!",
    "fuse_time": 8,
    "blast_damage": 25,
}

# Shorter fuse tactical grenade
TACTICAL_GRENADE = {
    "prototype_parent": "EXPLOSIVE_BASE", 
    "key": "tactical grenade",
    "aliases": ["tac grenade", "tactical"],
    "desc": "A tactical grenade with a shorter 5-second fuse for close-quarters combat.",
    "fuse_time": 5,
    "blast_damage": 20,
    "dud_chance": 0.02,  # More reliable
}

# High-damage demo charge
DEMO_CHARGE = {
    "prototype_parent": "EXPLOSIVE_BASE",
    "key": "demo charge", 
    "aliases": ["charge", "demo", "c4"],
    "desc": "A powerful demolition charge. Devastating blast with a 10-second timer.",
    "fuse_time": 10,
    "blast_damage": 40,
    "dud_chance": 0.01,  # Very reliable
}

# Flashbang (non-lethal)
FLASHBANG = {
    "prototype_parent": "EXPLOSIVE_BASE",
    "key": "flashbang",
    "aliases": ["flash", "stun grenade"],
    "desc": "A non-lethal stun grenade that produces a blinding flash and deafening bang.",
    "fuse_time": 6,
    "blast_damage": 5,  # Minimal damage, mainly stunning
    "dud_chance": 0.10,  # 10% dud chance
    "damage_type": "blunt",  # Concussion/pressure wave damage
}

# Smoke grenade (minimal damage)
SMOKE_GRENADE = {
    "prototype_parent": "EXPLOSIVE_BASE",
    "key": "smoke grenade",
    "aliases": ["smoke"],
    "desc": "A smoke grenade that creates a thick concealing cloud. Minimal explosive force.",
    "fuse_time": 4,
    "blast_damage": 2,  # Very low damage
    "dud_chance": 0.15,  # Higher dud chance
    "damage_type": "burn",  # Chemical irritation from smoke
}

# =============================================================================
# MELEE WEAPON PROTOTYPES (for grenade deflection testing)
# =============================================================================

# Base melee weapon
MELEE_WEAPON_BASE = {
    "prototype_key": "melee_weapon_base",
    "key": "melee weapon",
    "typeclass": "typeclasses.items.Item",
    "desc": "A weapon designed for close combat.",
    "tags": [
        ("weapon", "type"),
        ("melee", "category"),
        ("item", "general")
    ],
    "attrs": [
        ("is_ranged", False),  # Explicitly melee (though this is the default)
    ]
}

# Sword (standard deflection)
SWORD = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "sword",
    "aliases": ["blade"],
    "desc": "A well-balanced sword. Good for both combat and deflecting projectiles.",
    "damage": 10,
    "weapon_type": "long_sword",  # Using existing message type
    "damage_type": "cut",  # Medical system injury type
}

# Baseball bat (enhanced deflection)
BASEBALL_BAT = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "baseball bat",
    "aliases": ["bat"],
    "desc": "A wooden baseball bat. Perfect for batting away incoming objects!",
    "damage": 8,
    "deflection_bonus": 0.30,  # +6 to deflection threshold (0.30 * 20)
    "weapon_type": "baseball_bat",  # Using existing message type
    "damage_type": "blunt",  # Medical system injury type
}

# Staff (good deflection)
STAFF = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "staff",
    "aliases": ["quarterstaff", "bo"],
    "desc": "A long wooden staff. Its reach makes it excellent for deflecting projectiles.",
    "damage": 7,
    "deflection_bonus": 0.10,  # +2 to deflection threshold (0.10 * 20)
    "weapon_type": "staff",  # Using existing message type
    "damage_type": "blunt",  # Medical system injury type
}

# Tennis Racket (excellent deflection!)
TENNIS_RACKET = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "tennis racket",
    "aliases": ["racket", "racquet"],
    "desc": "A professional tennis racket with tight strings and a lightweight frame. Perfect for returning serves... and grenades!",
    "damage": 5,  # Lower damage but amazing deflection
    "deflection_bonus": 0.50,  # +10 to deflection threshold (0.50 * 20) - BEST deflection weapon!
    "weapon_type": "tennis_racket",
    "damage_type": "blunt",  # Medical system injury type
    "hands": 1,
}

# Katana (legendary weapon of the samurai soul)
KATANA = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "katana",
    "aliases": ["sword", "blade", "japanese sword", "nihonto", "samurai sword"],
    "desc": "A legendary nihonto katana forged by a master swordsmith in the ancient traditions of the samurai. The curved, single-edged blade bears the distinctive hamon temper line like frozen lightning captured in tamahagane steel. Its razor-sharp ha (cutting edge) whispers promises of iai-jutsu and the Way of the Sword, while the sacred geometry of its curvature channels the very essence of bushido. The ray-skin wrapped tsuka handle, bound with silk ito in traditional diamond patterns, fits perfectly in the hand as if forged for your soul alone. This is not merely a weapon—it is the steel incarnation of honor, discipline, and the indomitable spirit of the warrior. To wield it is to walk the path of the samurai, where each cut carries the weight of a thousand generations of swordmasters. The blade seems to hum with latent spiritual energy, as if it remembers every duel, every moment of perfect technique, every drop of blood spilled in service to the code. In the right hands, this katana transcends mere metal to become an extension of one's very being—the soul made manifest in folded steel.",
    "damage": 14,
    "deflection_bonus": 0.25,  # +5 to deflection threshold (excellent for parrying)
    "weapon_type": "katana",  # Using existing katana message type
    "damage_type": "cut",  # Medical system injury type
}

# Dagger (poor deflection)
DAGGER = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "dagger",
    "aliases": ["knife"],
    "desc": "A small, sharp dagger. Not ideal for deflecting larger objects.",
    "damage": 6,
    "deflection_bonus": -0.05,  # -1 to deflection threshold (penalty)
    "weapon_type": "knife",  # Using existing message type
    "damage_type": "stab",  # Medical system injury type
}

# Chainsaw (devastating damage, no deflection)
CHAINSAW = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "chainsaw",
    "aliases": ["saw", "power saw"],
    "desc": "A gas-powered chainsaw with razor-sharp teeth. The engine sputters and growls, hungry for violence. Its mechanical brutality leaves no room for finesse.",
    "damage": 25,  # Extremely high damage
    "deflection_bonus": -0.50,  # -10 to deflection threshold (major penalty - chainsaws are terrible for defense)
    "weapon_type": "chainsaw",  # Using our newly converted message type
    "damage_type": "laceration",  # Medical system injury type
}

# =============================================================================
# THROWING WEAPON PROTOTYPES
# =============================================================================

# Base throwing weapon
THROWING_WEAPON_BASE = {
    "prototype_key": "throwing_weapon_base",
    "key": "throwing weapon",
    "typeclass": "typeclasses.items.Item",
    "desc": "A weapon designed for throwing.",
    "tags": [
        ("weapon", "type"),
        ("throwing", "category"),
        ("item", "general")
    ],
    "attrs": [
        ("is_ranged", True),  # Throwing weapons are ranged weapons
        ("is_explosive", False),
        ("is_throwing_weapon", True),  # Dedicated throwing weapon - uses attack command
    ]
}

# Throwing knife
THROWING_KNIFE = {
    "prototype_parent": "THROWING_WEAPON_BASE",
    "key": "throwing knife",
    "aliases": ["knife", "blade"],
    "desc": "A balanced knife designed for throwing. Sharp and deadly.",
    "damage": 8,
    "attrs": [
        ("weapon_type", "throwing_knife"),
        ("damage_type", "stab"),  # Medical system injury type
    ]
}

# Throwing axe
THROWING_AXE = {
    "prototype_parent": "THROWING_WEAPON_BASE", 
    "key": "throwing axe",
    "aliases": ["axe", "hatchet"],
    "desc": "A heavy axe perfect for throwing. Deals significant damage on impact.",
    "damage": 12,
    "attrs": [
        ("weapon_type", "throwing_axe"),
        ("damage_type", "cut"),  # Medical system injury type
    ]
}

# Shuriken
SHURIKEN = {
    "prototype_parent": "THROWING_WEAPON_BASE",
    "key": "shuriken",
    "aliases": ["star", "ninja star"],
    "desc": "A traditional throwing star. Light and precise.",
    "damage": 6,
    "attrs": [
        ("weapon_type", "shuriken"),
        ("damage_type", "laceration"),  # Medical system injury type
    ]
}

# =============================================================================
# RANGED WEAPON PROTOTYPES (firearms and projectile weapons)
# =============================================================================

# Base ranged weapon
RANGED_WEAPON_BASE = {
    "prototype_key": "ranged_weapon_base",
    "key": "ranged weapon",
    "typeclass": "typeclasses.items.Item",
    "desc": "A weapon designed for ranged combat.",
    "tags": [
        ("weapon", "type"),
        ("ranged", "category"),
        ("item", "general")
    ],
    "attrs": [
        ("is_ranged", True),  # Ranged weapons
        ("hands_required", 2),  # Most firearms require two hands
        ("deflection_bonus", 0.0),  # Base deflection capability
    ]
}

# Light pistol (existing message type)
LIGHT_PISTOL = {
    "prototype_parent": "RANGED_WEAPON_BASE",
    "key": "light pistol",
    "aliases": ["pistol", "handgun", "9mm"],
    "desc": "A compact semi-automatic pistol. Lightweight and easy to conceal, perfect for close-quarters combat.",
    "damage": 12,
    "attrs": [
        ("weapon_type", "light_pistol"),
        ("damage_type", "bullet"),  # Medical system injury type
        ("hands_required", 1),  # Pistols can be fired one-handed
    ]
}

# Heavy pistol (existing message type) 
HEAVY_PISTOL = {
    "prototype_parent": "RANGED_WEAPON_BASE",
    "key": "heavy pistol",
    "aliases": ["magnum", ".44", "revolver"],
    "desc": "A powerful heavy-caliber pistol. This hand cannon delivers devastating stopping power with thunderous reports.",
    "damage": 18,
    "attrs": [
        ("weapon_type", "heavy_pistol"),
        ("damage_type", "bullet"),  # Medical system injury type
        ("hands_required", 1),  # Can be fired one-handed but difficult
    ]
}

# Pump-action shotgun (existing message type)
PUMP_SHOTGUN = {
    "prototype_parent": "RANGED_WEAPON_BASE", 
    "key": "pump-action shotgun",
    "aliases": ["shotgun", "pump", "scattergun"],
    "desc": "A reliable pump-action shotgun. The distinctive *chk-chk* of the pump action strikes fear into enemies at close range.",
    "damage": 20,
    "attrs": [
        ("weapon_type", "pump-action_shotgun"),
        ("damage_type", "bullet"),  # Medical system injury type
    ]
}

# Break-action shotgun (existing message type)
BREAK_SHOTGUN = {
    "prototype_parent": "RANGED_WEAPON_BASE",
    "key": "break-action shotgun", 
    "aliases": ["double-barrel", "sawed-off", "coach gun"],
    "desc": "A classic break-action double-barrel shotgun. Simple, reliable, and devastatingly effective at close range.",
    "damage": 25,
    "attrs": [
        ("weapon_type", "break-action_shotgun"),
        ("damage_type", "bullet"),  # Medical system injury type
    ]
}

# Bolt-action rifle (existing message type)
BOLT_RIFLE = {
    "prototype_parent": "RANGED_WEAPON_BASE",
    "key": "bolt-action rifle",
    "aliases": ["rifle", "sniper", "bolt-action"],
    "desc": "A precision bolt-action rifle. Excellent accuracy and range make this ideal for long-distance engagements.",
    "damage": 22,
    "attrs": [
        ("weapon_type", "bolt-action_rifle"),
        ("damage_type", "bullet"),  # Medical system injury type
    ]
}

# Anti-material rifle (existing message type)  
ANTI_MATERIAL_RIFLE = {
    "prototype_parent": "RANGED_WEAPON_BASE",
    "key": "anti-material rifle",
    "aliases": ["AMR", "sniper rifle", ".50 cal"],
    "desc": "A massive anti-material rifle chambered in .50 BMG. This beast can punch through armor, vehicles, and walls with devastating effect.",
    "damage": 35,
    "attrs": [
        ("weapon_type", "anti-material_rifle"),
        ("damage_type", "bullet"),  # Medical system injury type
        ("hands_required", 2),  # Requires bipod/support
    ]
}

# Assault rifle (if you have assault rifle messages)
ASSAULT_RIFLE = {
    "prototype_parent": "RANGED_WEAPON_BASE",
    "key": "assault rifle", 
    "aliases": ["rifle", "AR", "automatic"],
    "desc": "A modern selective-fire assault rifle. Versatile and deadly, with both semi-auto and full-auto capabilities.",
    "damage": 15,
    "attrs": [
        ("weapon_type", "assault_rifle"),  # May need to create message file
        ("damage_type", "bullet"),  # Medical system injury type
    ]
}

# SMG/Submachine gun
SMG = {
    "prototype_parent": "RANGED_WEAPON_BASE",
    "key": "submachine gun",
    "aliases": ["SMG", "machine pistol", "auto"],
    "desc": "A compact submachine gun. High rate of fire and manageable recoil make it perfect for close-quarters combat.",
    "damage": 10,
    "attrs": [
        ("weapon_type", "smg"),  # May need to create message file
        ("damage_type", "bullet"),  # Medical system injury type
        ("hands_required", 1),  # Can be fired one-handed
    ]
}

# =============================================================================
# UTILITY OBJECT PROTOTYPES (for non-combat throwing)
# =============================================================================

# Keys for testing utility throws
KEYRING = {
    "key": "keyring",
    "aliases": ["keys", "ring"],
    "desc": "A ring of various keys. Useful for testing throwing mechanics.",
    "typeclass": "typeclasses.objects.Object",
}

# Rock for testing
ROCK = {
    "key": "rock",
    "aliases": ["stone"],
    "desc": "A smooth throwing rock. Perfect for testing directional throws.",
    "typeclass": "typeclasses.objects.Object",
}

# Bottle for testing
BOTTLE = {
    "key": "bottle",
    "aliases": ["glass bottle"],
    "desc": "An empty glass bottle. Makes a satisfying crash when thrown.",
    "typeclass": "typeclasses.objects.Object",
}

# =============================================================================
# GRAFFITI SYSTEM PROTOTYPES
# =============================================================================

# Base spray paint can
SPRAYPAINT_CAN = {
    "prototype_key": "spraypaint_can",
    "key": "can of",
    "aliases": ["can", "paint", "spray", "spraycan", "spraypaint"],
    "typeclass": "typeclasses.items.SprayCanItem", 
    "desc": "A can of spraypaint with a red nozzle. It feels heavy with paint.",
    "attrs": [
        ("aerosol_level", 256),
        ("max_aerosol", 256),
        ("current_color", "red"),
        ("aerosol_contents", "spraypaint"),
        ("damage", 2),
        ("weapon_type", "spraycan"),
        ("damage_type", "burn"),  # Medical system injury type - chemical burn
        ("hands_required", 1)
    ],
    "tags": [
        ("graffiti", "type"),
        ("spray_can", "category"),
        ("item", "general")
    ]
}

# Solvent can for cleaning graffiti
SOLVENT_CAN = {
    "prototype_key": "solvent_can",
    "key": "can of",
    "aliases": ["solvent", "cleaner", "cleaning_can", "can"],
    "typeclass": "typeclasses.items.SolventCanItem",
    "desc": "A can of solvent for cleaning graffiti. It feels heavy with solvent.", 
    "attrs": [
        ("aerosol_level", 256),
        ("max_aerosol", 256),
        ("aerosol_contents", "solvent"),
        ("damage", 2),
        ("weapon_type", "spraycan"), 
        ("damage_type", "burn"),  # Medical system injury type - chemical burn
        ("hands_required", 1)
    ],
    "tags": [
        ("graffiti", "type"),
        ("solvent_can", "category"),
        ("item", "general")
    ]
}

# =============================================================================
# CLOTHING SYSTEM PROTOTYPES
# =============================================================================
"""
Clothing System Implementation Notes:

Phase 1 & 2 COMPLETE: Core infrastructure with dynamic styling and appearance integration
- Attribute-based clothing detection (coverage, layer, worn_desc)
- Multi-property styling system (adjustable + closure combinations)
- Coverage-based visibility masking of longdesc locations
- Inventory integration showing style states

FUTURE EXPANSION POSSIBILITIES:
- Phase 3: Advanced layer conflict resolution, staff targeting commands
- Material Physics: Durability, weather resistance, cleaning requirements
- Fashion Systems: NPC reactions based on clothing combinations/appropriateness
- Condition Tracking: Wear states, stains, damage affecting appearance/stats
- Social Mechanics: Dress codes, cultural clothing significance
- Seasonal Systems: Temperature comfort, weather protection
- Economic Integration: Clothing value, fashion trends affecting prices
- Magical Clothing: Enchantments, transformation items, stat bonuses

Current prototypes are proof-of-concept focusing on core mechanics.
"""

# Epic coder socks with dynamic styling capabilities
CODER_SOCKS = {
    "prototype_key": "CODER_SOCKS",
    "key": "rainbow coding socks",
    "aliases": ["socks", "coding socks", "rainbow socks"],
    "typeclass": "typeclasses.items.Item",
    "desc": "These magnificent thigh-high socks feature a gradient rainbow pattern with tiny pixelated hearts and coffee cups. The fabric shimmers with an almost magical quality, and they seem to pulse gently with RGB lighting effects. Every serious coder knows these provide +10 to programming ability.",
    "attrs": [
        # Basic clothing attributes
        ("coverage", ["left_foot", "right_foot", "left_shin", "right_shin", "left_thigh", "right_thigh"]),
        ("worn_desc", "Electric {color}rainbow|n coding socks stretching up {their} thighs, {their} prismatic patterns pulsing with soft bioluminescent threads that seem to respond to neural activity"),
        ("layer", 1),  # Undergarment layer
        ("color", "bright_magenta"),
        ("material", "synthetic"),
        ("weight", 0.2),  # Very light
        
        # Style configuration for incredible transformation power
        ("style_configs", {
            "adjustable": {
                "normal": {
                    "coverage_mod": [],
                    "desc_mod": ""  # Use base worn_desc
                },
                "rolled": {
                    "coverage_mod": ["-left_thigh", "-right_thigh"],  # Rolled down to knee-high
                    "desc_mod": "Electric {color}rainbow|n coding socks bunched down around {their} knees, {their} compressed RGB fibers creating intense aurora-like cascades that paint the calves in shifting spectral light"
                }
            },
            "closure": {
                "zipped": {
                    "coverage_mod": [],
                    "desc_mod": "Electric {color}rainbow|n coding socks stretching up {their} thighs, {their} LED matrices blazing at maximum intensity like fiber-optic constellations mapping the topology of pure computational ecstasy"
                },
                "unzipped": {
                    "coverage_mod": [],
                    "desc_mod": "Electric {color}rainbow|n coding socks stretching up {their} thighs, {their} bioluminescent patterns dimmed to a gentle ambient pulse that whispers of late-night debugging sessions and caffeine dreams"
                }
            }
        }),
        
        # Initial style state - full power mode!
        ("style_properties", {
            "adjustable": "normal",  # Full thigh-high
            "closure": "zipped"      # LEDs on full blast
        })
        
        # Future: combat stats for style-based intimidation, coder stat bonuses
        # Future tags: material properties, rarity systems, specialty gear recognition
    ],
    # Future: tags for NPC coder recognition, RGB lighting systems, legendary item mechanics  
    # "tags": [("clothing", "type"), ("socks", "category"), ("coder_gear", "specialty")]
}

# Stylish developer hoodie with hood functionality
DEV_HOODIE = {
    "prototype_key": "DEV_HOODIE", 
    "key": "black developer hoodie",
    "aliases": ["hoodie", "dev hoodie", "black hoodie"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A jet-black hoodie with 'rm -rf /' printed in small, ominous green text on the chest. The fabric is impossibly soft, and the hood seems designed to cast perfect dramatic shadows. Tiny LED threads are woven throughout, creating a subtle matrix-like pattern when activated.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["chest", "back", "abdomen", "left_arm", "right_arm"]),
        ("worn_desc", "A menacing {color}black|n developer hoodie draped loose and open, the cryptic green 'rm -rf /' text glowing with malevolent promise while embedded LED threads create subtle data-stream patterns across {their} fabric"),
        ("layer", 2),  # Base clothing
        ("color", "black"),
        ("material", "cotton"),
        ("weight", 1.8),  # Moderate weight
        
        # Advanced styling - hood and LED modes
        ("style_configs", {
            "adjustable": {
                "normal": {
                    "coverage_mod": [],
                    "desc_mod": ""
                },
                "rolled": {
                    "coverage_mod": ["+head"],  # Hood up adds head coverage
                    "desc_mod": "A menacing {color}black|n developer hoodie with the hood pulled up like digital shadow incarnate, casting {their} face into mysterious darkness while green command-line text pulses ominously across {their} chest like a hacker's heartbeat"
                }
            },
            "closure": {
                "zipped": {
                    "coverage_mod": [],
                    "desc_mod": "A menacing {color}black|n developer hoodie zipped tight against the digital cold, LED matrix patterns cascading across the fabric like endless streams of compiled consciousness while 'rm -rf /' glows with quiet menace"
                },
                "unzipped": {
                    "coverage_mod": ["-chest"],  # Unzipped shows what's underneath
                    "desc_mod": "A menacing {color}black|n developer hoodie hanging open in calculated carelessness, revealing whatever lies beneath while {their} forbidden command-line incantation pulses with green malevolence against the darkness"
                }
            }
        }),
        
        ("style_properties", {
            "adjustable": "normal",    # Hood down initially  
            "closure": "unzipped"      # Casual mode
        })
        
        # Future: intimidation mechanics, focus bonuses, developer culture systems
        # Future tags: LED features, professional gear, meeting avoidance mechanics
    ],
    # Future: tags for developer NPC interactions, LED systems, professional contexts
    # "tags": [("clothing", "type"), ("hoodie", "category"), ("developer_gear", "specialty")]
}

# Classic blue jeans with functional styling
BLUE_JEANS = {
    "prototype_key": "BLUE_JEANS",
    "key": "blue jeans",
    "aliases": ["jeans", "pants", "denim"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A classic pair of medium-wash blue jeans with a comfortable fit. The denim is soft from years of wear, with subtle fading at the knees and pockets. Five-pocket styling with sturdy copper rivets at stress points.",
    
    "attrs": [
        ("category", "clothing"),
        ("worn_desc", "Battle-tested {color}denim|n jeans that cling to {their} form with urban authority, {their} faded indigo surface scarred by countless encounters with concrete and circumstance"),
        ("coverage", ["groin", "left_thigh", "right_thigh", "left_shin", "right_shin"]),
        ("layer", 2),
        ("color", "blue"),
        ("material", "denim"),
        ("weight", 1.5),  # Moderate weight
        
        ("style_configs", {
            "adjustable": {
                "normal": {
                    "coverage_mod": [],
                    "desc_mod": ""  # Use base worn_desc
                },
                "rolled": {
                    "coverage_mod": ["-left_shin", "-right_shin"],
                    "desc_mod": "Battle-tested {color}denim|n jeans with cuffs deliberately rolled up to mid-calf in street-smart defiance, exposing {their} scarred ankles and the promise of swift movement when the situation demands it"
                }
            },
            "closure": {
                "zipped": {
                    "coverage_mod": [],
                    "desc_mod": ""  # Use base worn_desc
                },
                "unzipped": {
                    "coverage_mod": ["-groin"],
                    "desc_mod": "Battle-tested {color}denim|n jeans hanging loose with dangerous nonchalance, {their} undone fly creating a calculated statement of rebellion against the oppressive tyranny of proper dress codes"
                }
            }
        }),
        
        ("style_properties", {
            "adjustable": "normal",
            "closure": "zipped"
        })
        
        # Future: durability/wear system, comfort affects stats, style bonuses
        # Future tags: material properties, fashion categories, condition tracking
    ],
    # Future: tags for material physics, fashion systems, NPC reactions
    # "tags": [("clothing", "type"), ("pants", "category"), ("denim", "material")]
}

# Simple cotton t-shirt 
COTTON_TSHIRT = {
    "prototype_key": "COTTON_TSHIRT",
    "key": "white cotton t-shirt",
    "aliases": ["shirt", "t-shirt", "tshirt", "tee"],
    "typeclass": "typeclasses.items.Item", 
    "desc": "A simple white cotton t-shirt with a classic crew neck. The fabric is soft and breathable, perfect for everyday wear. The shoulders and hem show the clean lines of quality construction.",
    
    "attrs": [
        ("category", "clothing"),
        ("worn_desc", "A deceptively simple {color}white|n cotton t-shirt that seems to absorb and reflect the ambient light of {their} urban environment, its clean lines and perfect fit suggesting either careful maintenance or recent acquisition"),
        ("coverage", ["chest", "back", "abdomen"]),
        ("layer", 2),
        ("color", "white"),
        ("material", "cotton"),
        ("weight", 0.4),  # Light weight
        
        ("style_configs", {
            "adjustable": {
                "normal": {
                    "coverage_mod": [],
                    "desc_mod": ""  # Use base worn_desc
                },
                "rolled": {
                    "coverage_mod": ["-abdomen"],
                    "desc_mod": "A deceptively simple {color}white|n cotton t-shirt deliberately rolled up at the hem to expose {their} midriff, the casual gesture somehow managing to convey both vulnerability and confident defiance of conventional modesty"
                }
            }
        }),
        
        ("style_properties", {
            "adjustable": "normal"
        })
        
        # Future: fabric physics, stain resistance, NPC fashion reactions  
        # Future tags: material breathability, wash cycles, social contexts
    ],
    # Future: tags for clothing care systems, fashion mechanics, NPC interactions
    # "tags": [("clothing", "type"), ("shirt", "category"), ("cotton", "material")]
}

# Tactical leather combat boots with lacing
COMBAT_BOOTS = {
    "prototype_key": "COMBAT_BOOTS",
    "key": "black leather combat boots",
    "aliases": ["boots", "combat boots", "leather boots"],
    "typeclass": "typeclasses.items.Item",
    "desc": "Heavy-duty black leather combat boots with steel-reinforced toes and deep tread soles. The leather is scuffed from use but well-maintained, with military-style speed lacing running up to mid-calf. Perfect for urban warfare or intimidating accountants.",
    
    "attrs": [
        ("category", "clothing"),
        ("worn_desc", "Imposing {color}black leather|n combat boots laced with military precision, {their} steel-reinforced toes and deep-tread soles speaking of {their} owner's serious intent while weathered leather tells stories of urban warfare and late-night foot chases"),
        ("coverage", ["left_foot", "right_foot", "left_shin", "right_shin"]),
        ("layer", 2),
        ("color", "black"),
        ("material", "leather"),
        
        ("style_configs", {
            "closure": {
                "zipped": {
                    "coverage_mod": [],
                    "desc_mod": ""  # Use base worn_desc (laced tight)
                },
                "unzipped": {
                    "coverage_mod": ["-left_shin", "-right_shin"],
                    "desc_mod": "Imposing {color}black leather|n combat boots with speed-laces hanging in deliberate disarray, {their} unlaced tongues flopping open to reveal glimpses of tactical readiness beneath the facade of casual indifference"
                }
            }
        }),
        
        ("style_properties", {
            "closure": "zipped"  # Laced tight by default
        })
        
        # Future: armor rating, movement speed modifiers, intimidation bonuses
        # Future tags: leather durability, tactical gear, weather resistance
    ],
    # Future: tags for combat systems, material physics, professional contexts  
    # "tags": [("clothing", "type"), ("boots", "category"), ("leather", "material")]
}


# =============================================================================
# ARMOR PROTOTYPES (CLOTHING WITH ARMOR ATTRIBUTES)
# =============================================================================

# =============================================================================
# TACTICAL UNIFORM BASE LAYERS (Light Protection)
# =============================================================================

# Tactical Jumpsuit - Base layer with minimal protection
TACTICAL_JUMPSUIT = {
    "key": "tactical jumpsuit",
    "aliases": ["jumpsuit", "coveralls", "tactical suit"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A form-fitting tactical jumpsuit made from reinforced synthetic weave. Provides minimal protection while maintaining maximum mobility and comfort.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["chest", "back", "abdomen", "groin", "left_arm", "right_arm", "left_thigh", "right_thigh"]),
        ("worn_desc", "A sleek {color}black|n tactical jumpsuit that hugs their form like a second skin, its reinforced synthetic weave providing minimal protection while prioritizing mobility and tactical flexibility"),
        ("layer", 1),  # Base layer
        ("color", "black"),
        ("material", "synthetic"),
        ("weight", 1.8),  # Lightweight
        
        # Minimal armor
        ("armor_rating", 1),
        ("armor_type", "synthetic"),
        ("armor_durability", 20),
        ("max_armor_durability", 20),
        ("base_armor_rating", 1),
    ],
}

# Tactical Pants - Alternative to jumpsuit
TACTICAL_PANTS = {
    "key": "tactical pants",
    "aliases": ["pants", "tactical trousers", "combat pants"],
    "typeclass": "typeclasses.items.Item",
    "desc": "Heavy-duty tactical pants with reinforced knees and multiple cargo pockets. Made from ripstop fabric with minimal ballistic protection.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["groin", "left_thigh", "right_thigh", "left_shin", "right_shin"]),
        ("worn_desc", "Durable {color}black|n tactical pants with reinforced knees and cargo pockets, their ripstop fabric providing minimal protection while maintaining tactical functionality"),
        ("layer", 1),  # Base layer
        ("color", "black"),
        ("material", "synthetic"),
        ("weight", 1.2),
        
        # Minimal armor
        ("armor_rating", 1),
        ("armor_type", "synthetic"),
        ("armor_durability", 20),
        ("max_armor_durability", 20),
        ("base_armor_rating", 1),
    ],
}

# Tactical Shirt - Upper body base layer
TACTICAL_SHIRT = {
    "key": "tactical shirt",
    "aliases": ["shirt", "tactical tee", "combat shirt"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A tactical shirt with moisture-wicking fabric and reinforced shoulders. Designed to be worn under armor systems.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["chest", "back", "abdomen", "left_arm", "right_arm"]),
        ("worn_desc", "A practical {color}black|n tactical shirt with moisture-wicking fabric, its reinforced shoulders and minimal protection designed to serve as a foundation for armor systems"),
        ("layer", 1),  # Base layer
        ("color", "black"),
        ("material", "synthetic"),
        ("weight", 0.8),
        
        # Minimal armor
        ("armor_rating", 1),
        ("armor_type", "synthetic"),
        ("armor_durability", 20),
        ("max_armor_durability", 20),
        ("base_armor_rating", 1),
    ],
}

# =============================================================================
# MODULAR PLATE CARRIER SYSTEM
# =============================================================================

# Basic Plate Carrier - Modular platform
PLATE_CARRIER = {
    "key": "plate carrier",
    "aliases": ["carrier", "vest", "tactical vest"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A modular plate carrier system with front and back plate pockets, side plate slots, and tactical webbing. Designed to accept ballistic plates for customizable protection levels.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["chest", "back", "abdomen"]),
        ("worn_desc", "A professional {color}tan|n plate carrier with tactical webbing and modular plate pockets, its adjustable straps and MOLLE system creating a foundation for serious ballistic protection"),
        ("layer", 3),  # Outer armor layer
        ("color", "tan"),
        ("material", "nylon"),
        ("weight", 2.5),  # Just the carrier itself
        
        # Base protection (carrier only)
        ("armor_rating", 2),        # Minimal protection without plates
        ("armor_type", "synthetic"), # Basic synthetic protection
        ("armor_durability", 40),
        ("max_armor_durability", 40),
        ("base_armor_rating", 2),
        
        # Plate carrier system
        ("is_plate_carrier", True),
        ("plate_slots", ["front", "back", "left_side", "right_side"]),
        ("installed_plates", {}),   # Empty initially
        ("plate_slot_coverage", {
            "front": ["chest"],
            "back": ["back"],
            "left_side": ["torso"],
            "right_side": ["torso"]
        }),
        
        # Style system for tactical adjustments
        ("style_configs", {
            "adjustable": {
                "normal": {"coverage_mod": [], "desc_mod": ""},
                "rolled": {"coverage_mod": ["-abdomen"], "desc_mod": "A professional {color}tan|n plate carrier with the lower section rolled up for improved mobility, its tactical webbing still providing modular attachment points"}
            }
        }),
        ("style_properties", {"adjustable": "normal"}),
    ],
}

# =============================================================================
# ARMOR PLATES (For Plate Carriers)
# =============================================================================

# Medium Ballistic Plate - Standard protection
BALLISTIC_PLATE_MEDIUM = {
    "key": "medium ballistic plate",
    "aliases": ["plate", "ballistic plate", "armor plate"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A Level IIIA ballistic plate made from advanced ceramic composite. Designed to stop rifle rounds while remaining relatively lightweight.",
    "attrs": [
        # Not worn directly - installed in carriers
        ("coverage", []),
        ("layer", 0),  # Not a clothing layer
        ("weight", 3.2),  # Significant weight
        ("material", "ceramic"),
        
        # Plate properties
        ("is_armor_plate", True),
        ("plate_size", "medium"),
        ("armor_rating", 7),        # High protection when installed
        ("armor_type", "ceramic"),
        ("armor_durability", 140),
        ("max_armor_durability", 140),
        ("base_armor_rating", 7),
    ],
}

# Large Steel Plate - Heavy protection
STEEL_PLATE_LARGE = {
    "key": "large steel plate",
    "aliases": ["steel plate", "heavy plate"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A heavy steel ballistic plate with excellent all-around protection. Significantly heavier than ceramic alternatives but nearly indestructible.",
    "attrs": [
        ("coverage", []),
        ("layer", 0),
        ("weight", 8.5),  # Very heavy
        ("material", "steel"),
        
        ("is_armor_plate", True),
        ("plate_size", "large"),
        ("armor_rating", 9),        # Maximum protection
        ("armor_type", "steel"),
        ("armor_durability", 180),
        ("max_armor_durability", 180),
        ("base_armor_rating", 9),
    ],
}

# Small Side Plate - Flank protection
SIDE_PLATE_SMALL = {
    "key": "small side plate",
    "aliases": ["side plate", "small plate"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A compact ballistic plate designed for side protection. Lighter than main plates but still provides significant protection against lateral threats.",
    "attrs": [
        ("coverage", []),
        ("layer", 0),
        ("weight", 1.8),  # Lighter for mobility
        ("material", "ceramic"),
        
        ("is_armor_plate", True),
        ("plate_size", "small"),
        ("armor_rating", 5),        # Moderate protection
        ("armor_type", "ceramic"),
        ("armor_durability", 100),
        ("max_armor_durability", 100),
        ("base_armor_rating", 5),
    ],
}

# =============================================================================
# LEGACY ARMOR (Updated with Weight)
# =============================================================================

# Tactical Kevlar Vest - Excellent bullet protection
KEVLAR_VEST = {
    "prototype_parent": "MELEE_WEAPON_BASE",  # Base item properties
    "key": "kevlar vest",
    "aliases": ["vest", "body armor", "bulletproof vest"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A lightweight tactical kevlar vest with trauma plates. Designed to stop bullets while maintaining mobility.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["chest", "back", "abdomen"]),
        ("worn_desc", "A professional {color}black|n kevlar vest with trauma plates, its tactical webbing and ballistic panels speaking of serious protection against projectile threats"),
        ("layer", 3),  # Outer armor layer
        ("color", "black"),
        ("material", "kevlar"),
        ("weight", 4.5),  # Moderate weight
        
        # Armor attributes
        ("armor_rating", 8),        # High armor rating
        ("armor_type", "kevlar"),   # Excellent vs bullets, poor vs stabs
        ("armor_durability", 160),  # Rating * 20
        ("max_armor_durability", 160),
        ("base_armor_rating", 8),
        
        # Combat stats
        ("deflection_bonus", -0.05),  # Slight penalty to deflection (bulky)
    ],
}

# Steel Plate Armor - Medieval style, excellent all-around protection
STEEL_PLATE = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "steel plate armor",
    "aliases": ["plate", "armor", "steel armor", "plate mail"],
    "typeclass": "typeclasses.items.Item", 
    "desc": "Heavy steel plate armor forged in overlapping segments. Provides excellent protection but restricts movement significantly.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["chest", "back", "abdomen", "left_arm", "right_arm"]),
        ("worn_desc", "Imposing {color}steel|n plate armor that encases their torso and arms in overlapping metal segments, each piece precisely fitted and articulated for maximum protection while maintaining combat mobility"),
        ("layer", 3),
        ("color", "bright_white"),  # Polished steel
        ("material", "steel"),
        ("weight", 25.0),  # Very heavy
        
        # Armor attributes
        ("armor_rating", 10),       # Maximum armor rating
        ("armor_type", "steel"),    # Excellent vs everything except fire/chemicals
        ("armor_durability", 200),  # Rating * 20
        ("max_armor_durability", 200),
        ("base_armor_rating", 10),
        
        # Combat penalties
        ("deflection_bonus", -0.15),  # Significant deflection penalty (very bulky)
    ],
}

# Leather Jacket - Light armor, good vs cuts
ARMORED_LEATHER_JACKET = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "armored leather jacket",
    "aliases": ["jacket", "leather armor", "biker jacket"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A heavy leather jacket reinforced with steel studs and padding. Provides moderate protection while maintaining style.",
    "attrs": [
        # Clothing attributes  
        ("coverage", ["chest", "back", "abdomen", "left_arm", "right_arm"]),
        ("worn_desc", "A reinforced {color}black leather|n jacket studded with steel reinforcements, its thick hide and metal accents providing street-smart protection without sacrificing the rebellious aesthetic of urban warfare"),
        ("layer", 2),
        ("color", "black"),
        ("material", "leather"),
        ("weight", 3.2),  # Moderate weight
        
        # Style system for leather jacket
        ("style_configs", {
            "closure": {
                "zipped": {
                    "coverage_mod": [],
                    "desc_mod": "A reinforced {color}black leather|n jacket zipped tight and studded with steel reinforcements, its thick hide creating a defensive shell around their torso"
                },
                "unzipped": {
                    "coverage_mod": ["-chest", "-abdomen"],
                    "desc_mod": "A reinforced {color}black leather|n jacket hanging open to reveal whatever lies beneath, steel studs and thick hide still providing partial protection to their back and arms"
                }
            }
        }),
        ("style_properties", {"closure": "zipped"}),
        
        # Armor attributes
        ("armor_rating", 5),        # Moderate armor rating
        ("armor_type", "leather"),  # Good vs cuts, poor vs bullets
        ("armor_durability", 100),  # Rating * 20
        ("max_armor_durability", 100),
        ("base_armor_rating", 5),
        
        # Combat stats
        ("deflection_bonus", 0.05),  # Slight deflection bonus (flexible)
    ],
}

# Combat Helmet - Head protection
COMBAT_HELMET = {
    "prototype_parent": "MELEE_WEAPON_BASE",
    "key": "combat helmet",
    "aliases": ["helmet", "tactical helmet"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A military-grade combat helmet with ballistic protection and integrated communication systems.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["head"]),
        ("worn_desc", "A menacing {color}matte black|n tactical helmet with ballistic protection, its angular design and integrated electronics creating an intimidating visage of military precision"),
        ("layer", 2),
        ("color", "black"),
        ("material", "kevlar"),
        ("weight", 1.8),  # Light weight
        
        # Armor attributes
        ("armor_rating", 7),        # High head protection
        ("armor_type", "kevlar"),   # Good vs bullets
        ("armor_durability", 140),  # Rating * 20
        ("max_armor_durability", 140),
        ("base_armor_rating", 7),
    ],
}

# Ceramic Trauma Plates - Insert armor for vests
CERAMIC_PLATES = {
    "prototype_parent": "MELEE_WEAPON_BASE", 
    "key": "ceramic trauma plates",
    "aliases": ["plates", "trauma plates", "ceramic insert"],
    "typeclass": "typeclasses.items.Item",
    "desc": "Advanced ceramic trauma plates designed to be inserted into tactical vests. Extremely effective against high-velocity rounds but brittle.",
    "attrs": [
        # Clothing attributes
        ("coverage", ["chest", "back"]),  # Only covers vital organs
        ("worn_desc", "Barely visible {color}white|n ceramic trauma plates integrated seamlessly into their protective gear, their advanced ballistic composition creating an nearly impenetrable barrier against projectile threats"),
        ("layer", 4),  # Layer over other armor
        ("color", "white"),
        ("material", "ceramic"),
        ("weight", 4.0),  # Heavy ceramic
        
        # Armor attributes - single-use super protection
        ("armor_rating", 10),       # Maximum protection
        ("armor_type", "ceramic"),  # Excellent vs bullets, degrades quickly
        ("armor_durability", 50),   # Low durability - shatters after absorbing damage
        ("max_armor_durability", 50),
        ("base_armor_rating", 10),
    ],
}

# =============================================================================  
# REPAIR TOOL PROTOTYPES (FOR ARMOR MAINTENANCE)
# =============================================================================

# Sewing Kit - Best for leather armor
SEWING_KIT = {
    "key": "sewing kit",
    "aliases": ["kit", "needles", "thread"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A comprehensive sewing kit with heavy-duty needles, reinforced thread, and leather patches. Perfect for repairing fabric and leather armor.",
    "attrs": [
        ("repair_tool_type", "sewing_kit"),
        ("tool_durability", 25),
        ("max_tool_durability", 25),
    ],
}

# Metalworking Tools - Best for steel armor  
METALWORK_TOOLS = {
    "key": "metalworking tools",
    "aliases": ["tools", "hammer", "anvil", "metalwork"],
    "typeclass": "typeclasses.items.Item", 
    "desc": "A set of metalworking tools including a small anvil, hammer, tongs, and files. Essential for repairing steel and metal armor components.",
    "attrs": [
        ("repair_tool_type", "metalwork_tools"),
        ("tool_durability", 30),
        ("max_tool_durability", 30),
    ],
}

# Ballistic Repair Kit - Best for kevlar
BALLISTIC_REPAIR_KIT = {
    "key": "ballistic repair kit",
    "aliases": ["ballistic kit", "kevlar kit", "fiber kit"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A specialized kit for repairing ballistic armor, containing aramid fibers, ballistic gel, and precision tools for working with advanced protective materials.",
    "attrs": [
        ("repair_tool_type", "ballistic_repair_kit"),
        ("tool_durability", 15),  # Specialized but fragile
        ("max_tool_durability", 15),
    ],
}

# Ceramic Repair Compound - Best for ceramic plates
CERAMIC_REPAIR_COMPOUND = {
    "key": "ceramic repair compound",
    "aliases": ["compound", "ceramic paste", "armor compound"],
    "typeclass": "typeclasses.items.Item",
    "desc": "An advanced ceramic repair compound that can restore cracked trauma plates. Requires precise application and technical expertise to use effectively.",
    "attrs": [
        ("repair_tool_type", "ceramic_repair_compound"),
        ("tool_durability", 8),   # Very specialized, limited uses
        ("max_tool_durability", 8),
    ],
}

# Generic Tool Kit - Moderate for all armor types
GENERIC_TOOL_KIT = {
    "key": "tool kit",
    "aliases": ["tools", "repair kit", "general tools"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A general-purpose tool kit with basic implements for field repairs. Not specialized for any particular material, but versatile enough for emergency fixes.",
    "attrs": [
        ("repair_tool_type", "generic_tools"),
        ("tool_durability", 20),
        ("max_tool_durability", 20),
    ],
}

# Workshop Bench - For full repairs (location-based)
ARMOR_WORKBENCH = {
    "key": "armor workbench", 
    "aliases": ["workbench", "bench", "workshop"],
    "typeclass": "typeclasses.items.Item",
    "desc": "A professional armor repair workbench equipped with specialized tools, proper lighting, and workspace for comprehensive armor restoration. Enables full repair capabilities.",
    "attrs": [
        ("repair_tool_type", "workshop_bench"),
        ("tool_durability", 1000),  # Extremely durable, permanent installation
        ("max_tool_durability", 1000),
        ("workshop_tool", True),    # Special flag for full repairs
    ],
}

# =============================================================================
# MEDICAL ITEM PROTOTYPES
# =============================================================================

# IV Blood Bag - Emergency blood transfusion
BLOOD_BAG = {
    "key": "blood bag",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["iv", "blood", "transfusion"],
    "desc": "A sterile IV blood bag with attached tubing for emergency transfusion. Contains 500ml of universal donor blood.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "blood_restoration"),
        ("uses_left", 1),
        ("max_uses", 1),
        ("stat_requirement", 1),
        ("application_time", 1),
        ("effectiveness", {
            "bleeding": 9,        # Excellent for severe bleeding
            "blood_loss": 10,     # Perfect for blood restoration
            "shock": 7,          # Good for shock treatment
            "organ_damage": 3,   # Limited help for organs
        })
    ],
}

# Injectable Painkiller - Multi-dose pain management
PAINKILLER = {
    "key": "painkiller",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["syringe", "morphine", "pain meds"],
    "desc": "A medical syringe containing powerful analgesic medication. Multiple doses available.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "pain_relief"),
        ("uses_left", 3),
        ("max_uses", 3),
        ("stat_requirement", 0),
        ("application_time", 1),
        ("effectiveness", {
            "pain": 9,           # Excellent pain relief
            "shock": 6,          # Moderate shock treatment
            "bleeding": 2,       # Minimal bleeding help
            "fracture": 4,       # Some fracture pain relief
        })
    ],
}

# Gauze Bandages - Multi-use wound dressing
GAUZE_BANDAGES = {
    "key": "gauze bandages",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["gauze", "bandages", "dressing"],
    "desc": "Sterile gauze bandages for wound dressing and bleeding control. Multiple applications available.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "wound_care"),
        ("uses_left", 5),
        ("max_uses", 5),
        ("stat_requirement", 0),
        ("application_time", 1),
        ("effectiveness", {
            "bleeding": 7,       # Very good bleeding control
            "infection": 8,      # Excellent infection prevention  
            "wound_healing": 6,  # Good wound protection
            "pain": 3,           # Minimal pain relief
        })
    ],
}

# Medical Splint - Single-use bone stabilization
SPLINT = {
    "key": "medical splint",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["splint", "brace"],
    "desc": "A universal medical splint that adapts to immobilize fractured appendages. Works on arms, legs, tentacles, wings, and other limbs.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "fracture_treatment"),
        ("uses_left", 1),
        ("max_uses", 1),
        ("stat_requirement", 2),
        ("application_time", 2),
        ("effectiveness", {
            "fracture": 8,       # Excellent fracture stabilization
            "pain": 4,           # Some pain relief
            "mobility": 6,       # Restores some movement
            "bleeding": 2,       # Minimal bleeding help
        })
    ],
}

# Surgical Kit - Advanced multi-use medical tools
SURGICAL_KIT = {
    "key": "surgical kit",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["surgery", "medical kit", "scalpel"],
    "desc": "A comprehensive surgical kit containing scalpels, sutures, clamps, and other advanced medical tools. Requires significant medical training.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "surgical_treatment"),
        ("uses_left", 10),
        ("max_uses", 10),
        ("stat_requirement", 3),
        ("application_time", 3),
        ("effectiveness", {
            "organ_damage": 10,  # Perfect for internal injuries
            "internal_bleeding": 9, # Excellent for internal bleeding
            "complex_wounds": 8, # Very good for complex injuries
            "infection": 7,      # Good sterile procedures
            "pain": 5,           # Moderate pain management
        })
    ],
}

# Emergency Stimpak - Rapid healing injection
STIMPAK = {
    "key": "stimpak",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["stim", "healing injection"],
    "desc": "An emergency medical stimulant that accelerates natural healing processes. Single-use auto-injector.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "healing_acceleration"),
        ("uses_left", 1),
        ("max_uses", 1),
        ("stat_requirement", 1),
        ("application_time", 1),
        ("effectiveness", {
            "wound_healing": 8,  # Excellent healing boost
            "bleeding": 6,       # Good bleeding control
            "pain": 7,           # Very good pain relief
            "organ_damage": 4,   # Limited organ help
            "fatigue": 9,        # Excellent energy restoration
        })
    ],
}

# Antiseptic Spray - Infection prevention
ANTISEPTIC = {
    "key": "antiseptic spray",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["antiseptic", "disinfectant", "spray"],
    "desc": "Medical-grade antiseptic spray for wound cleaning and infection prevention. Multiple applications per bottle.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "antiseptic"),
        ("uses_left", 8),
        ("max_uses", 8),
        ("stat_requirement", 0),
        ("application_time", 1),
        ("effectiveness", {
            "infection": 9,      # Excellent infection prevention
            "wound_healing": 5,  # Moderate healing assistance
            "bleeding": 3,       # Minimal bleeding help
            "pain": 2,           # Slight pain relief
        })
    ],
}

# ===================================================================
# PHASE 2.5: INHALATION & SMOKING MEDICAL ITEMS
# ===================================================================

OXYGEN_TANK = {
    "key": "oxygen tank",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["oxygen", "o2", "tank"],
    "desc": "Portable oxygen tank with breathing mask. Essential for respiratory emergencies and consciousness recovery.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "oxygen"),
        ("uses_left", 10),
        ("max_uses", 10),
        ("stat_requirement", 0),
        ("application_time", 1),
        ("effectiveness", {
            "consciousness": 9,      # Excellent consciousness boost
            "breathing_difficulty": 8, # Great respiratory help
            "suffocation": 10,       # Perfect suffocation treatment
        })
    ],
}

STIMPAK_INHALER = {
    "key": "stimpak inhaler",
    "typeclass": "typeclasses.items.Item", 
    "aliases": ["inhaler", "stimpak vapor", "medical inhaler"],
    "desc": "Pressurized inhaler containing vaporized stimpak for rapid respiratory absorption. Single use only.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "vapor"),
        ("uses_left", 1),
        ("max_uses", 1),
        ("stat_requirement", 1),
        ("application_time", 2),
        ("effectiveness", {
            "pain": 7,           # Good pain relief
            "blood_loss": 6,     # Moderate blood restoration
            "breathing_difficulty": 5, # Some respiratory help
        })
    ],
}

ANESTHETIC_GAS = {
    "key": "anesthetic gas",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["anesthetic", "knockout gas", "medical gas"],
    "desc": "Medical anesthetic gas canister. Reduces pain but may cause drowsiness. Use with caution.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "anesthetic"),
        ("uses_left", 5),
        ("max_uses", 5),
        ("stat_requirement", 2),
        ("application_time", 2),
        ("effectiveness", {
            "pain": 9,           # Excellent pain relief
            "consciousness": -2,  # Reduces consciousness (side effect)
        })
    ],
}

MEDICINAL_HERB = {
    "key": "medicinal herb",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["herb", "healing herb", "dried herb"],
    "desc": "Dried medicinal herb that can be smoked for natural pain relief and calming effects. Organic treatment option.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "herb"),
        ("uses_left", 3),
        ("max_uses", 3),
        ("stat_requirement", 0),
        ("application_time", 3),
        ("effectiveness", {
            "pain": 6,           # Good natural pain relief
            "stress": 7,         # Excellent stress relief
            "anxiety": 6,        # Good anxiety reduction
        })
    ],
}

PAIN_RELIEF_CIGARETTE = {
    "key": "pain relief cigarette",
    "typeclass": "typeclasses.items.Item",
    "aliases": ["med cigarette", "medical cigarette", "pain cigarette"],
    "desc": "Specially formulated cigarette infused with mild pain-relieving compounds. For medicinal use only.",
    "tags": [("medical_item", "item_type")],
    "attrs": [
        ("medical_type", "cigarette"),
        ("uses_left", 1),
        ("max_uses", 1),
        ("stat_requirement", 0),
        ("application_time", 4),
        ("effectiveness", {
            "pain": 4,           # Mild pain relief
            "stress": 3,         # Minor stress relief
        })
    ],
}
