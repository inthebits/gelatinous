"""
Generic wound descriptions following weapon message pattern.

Fallback descriptions for unknown injury types.
"""

WOUND_DESCRIPTIONS = {
    "fresh": [
        "|Ra {severity} wound on the {location}|n",
        "|Ra {severity} injury to the {location} showing damage|n",
        "|Ra {severity} trauma on the {location} with visible harm|n",
        "|Ra {severity} wound in the {location} requiring attention|n",
        "|Ra {severity} injury on the {location} showing signs of damage|n",
        "|Ra {severity} traumatic wound in the {location}|n",
        "|Ra {severity} damaged area on the {location}|n"
    ],
    
    "treated": [
        "{skintone}a {severity} treated wound on the {location}|n",
        "{skintone}a {severity} bandaged injury in the {location}|n",
        "{skintone}a {severity} dressed wound on the {location} with {bandage_color}medical care|n",
        "{skintone}a {severity} treated trauma in the {location}|n",
        "{skintone}a {severity} medically attended injury on the {location}|n",
        "{skintone}a {severity} cared-for wound in the {location}|n",
        "{skintone}a {severity} treated damaged area on the {location}|n"
    ],
    
    "healing": [
        "{skintone}a {severity} healing wound on the {location}|n",
        "{skintone}a {severity} mending injury in the {location} showing recovery|n",
        "{skintone}a {severity} improving wound on the {location}|n",
        "{skintone}a {severity} healing trauma in the {location}|n",
        "{skintone}a {severity} recovering injury on the {location}|n",
        "{skintone}a {severity} mending wound in the {location} with progress|n",
        "{skintone}a {severity} healing damaged area on the {location}|n"
    ],
    
    "scarred": [
        "{skintone}a {severity} wound scar on the {location}|n",
        "{skintone}a {severity} injury scar in the {location} permanently marked|n",
        "{skintone}a {severity} trauma scar on the {location}|n",
        "{skintone}a {severity} old wound mark in the {location}|n",
        "{skintone}a {severity} healed injury scar on the {location}|n",
        "{skintone}a {severity} permanent wound mark in the {location}|n",
        "{skintone}a {severity} scar from old trauma on the {location}|n"
    ]
}
