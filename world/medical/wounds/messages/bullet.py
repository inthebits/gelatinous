"""
Bullet wound descriptions following weapon message pattern.

Multiple description variants for each healing stage.
"""

WOUND_DESCRIPTIONS = {
    "fresh": [
        "|Ra {severity} bullet hole punched through the {location}|n",
        "|Ra {severity} gunshot wound in the {location} with ragged edges|n",
        "|Ra {severity} bullet wound on the {location}, still oozing blood|n",
        "|Ra {severity} entry wound in the {location} surrounded by powder burns|n",
        "|Ra {severity} ballistic injury to the {location} with torn flesh|n",
        "|Ra {severity} projectile wound in the {location}, bleeding freely|n",
        "|Ra {severity} bullet puncture on the {location} with blackened edges|n"
    ],
    
    "treated": [
        "{skintone}a {severity} bandaged bullet wound on the {location}|n",
        "{skintone}a {severity} gunshot wound in the {location} wrapped in {bandage_color}clean gauze|n",
        "{skintone}a {severity} treated bullet hole in the {location} with {medical_tape_color}surgical dressing|n",
        "{skintone}a {severity} bullet wound on the {location} secured with {bandage_color}medical tape|n",
        "{skintone}a {severity} patched gunshot wound in the {location}|n",
        "{skintone}a {severity} dressed ballistic injury on the {location}|n",
        "{skintone}a {severity} bullet wound in the {location} covered by {bandage_color}field dressing|n"
    ],
    
    "healing": [
        "{skintone}a {severity} healing bullet wound on the {location} with fresh scab|n",
        "{skintone}a {severity} gunshot wound in the {location} showing pink new tissue|n",
        "{skintone}a {severity} mending bullet hole in the {location} with reduced swelling|n",
        "{skintone}a {severity} recovering ballistic injury on the {location}|n",
        "{skintone}a {severity} bullet wound in the {location} with healthy granulation|n",
        "{skintone}a {severity} healing gunshot wound on the {location}, less tender|n",
        "{skintone}a {severity} improving bullet puncture in the {location}|n"
    ],
    
    "scarred": [
        "{skintone}a {severity} bullet wound scar on the {location}|n",
        "{skintone}a {severity} gunshot scar in the {location} with puckered edges|n", 
        "{skintone}a {severity} ballistic scar on the {location}, permanently marking the flesh|n",
        "{skintone}a {severity} bullet hole scar in the {location} with radiating lines|n",
        "{skintone}a {severity} old gunshot wound mark on the {location}|n",
        "{skintone}a {severity} faded bullet scar in the {location}|n",
        "{skintone}a {severity} healed projectile wound scar on the {location}|n"
    ]
}
