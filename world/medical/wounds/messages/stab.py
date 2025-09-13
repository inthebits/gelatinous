"""
Stabbing wound descriptions following weapon message pattern.

Multiple description variants for each healing stage.
"""

WOUND_DESCRIPTIONS = {
    "fresh": [
        "|Ra {severity} stab wound in the {location} with narrow opening|n",
        "|Ra {severity} puncture wound on the {location}, deep and bleeding|n",
        "|Ra {severity} thrust wound in the {location} with dark entrance|n",
        "|Ra {severity} piercing injury to the {location} penetrating deeply|n", 
        "|Ra {severity} stab hole in the {location} with jagged edges|n",
        "|Ra {severity} penetrating wound on the {location} seeping blood|n",
        "|Ra {severity} thrust puncture in the {location} with torn entry|n"
    ],
    
    "treated": [
        "{skintone}a {severity} packed stab wound in the {location}|n",
        "{skintone}a {severity} bandaged puncture wound on the {location}|n",
        "{skintone}a {severity} treated stab hole in the {location} with {bandage_color}pressure dressing|n",
        "{skintone}a {severity} packed thrust wound in the {location}|n",
        "{skintone}a {severity} dressed piercing injury on the {location}|n",
        "{skintone}a {severity} secured stab wound in the {location} with {bandage_color}gauze packing|n",
        "{skintone}a {severity} treated puncture in the {location} under {bandage_color}medical wrap|n"
    ],
    
    "healing": [
        "{skintone}a {severity} healing stab wound in the {location} with closing entry|n",
        "{skintone}a {severity} mending puncture wound on the {location}|n",
        "{skintone}a {severity} recovering stab hole in the {location} showing improvement|n",
        "{skintone}a {severity} healing thrust wound in the {location} with new tissue|n",
        "{skintone}a {severity} closing piercing injury on the {location}|n",
        "{skintone}a {severity} improving stab wound in the {location} less tender|n",
        "{skintone}a {severity} healing puncture on the {location} with reduced depth|n"
    ],
    
    "scarred": [
        "{skintone}a {severity} stab wound scar in the {location}|n",
        "{skintone}a {severity} puncture scar on the {location} with small depression|n",
        "{skintone}a {severity} thrust wound scar in the {location} barely visible|n",
        "{skintone}a {severity} old piercing injury mark on the {location}|n",
        "{skintone}a {severity} stab scar in the {location} with puckered center|n",
        "{skintone}a {severity} healed puncture wound mark on the {location}|n",
        "{skintone}a {severity} faded stab scar in the {location}|n"
    ]
}
