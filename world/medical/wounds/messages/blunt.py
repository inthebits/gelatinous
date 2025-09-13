"""
Blunt trauma wound descriptions following weapon message pattern.

Multiple description variants for each healing stage.
"""

WOUND_DESCRIPTIONS = {
    "fresh": [
        "|Ra {severity} bruise on the {location} with dark discoloration|n",
        "|Ra {severity} contusion in the {location} swollen and tender|n",
        "|Ra {severity} impact wound on the {location} with split skin|n",
        "|Ra {severity} blunt trauma to the {location} showing purple marks|n",
        "|Ra {severity} crushing injury on the {location} with broken capillaries|n",
        "|Ra {severity} bludgeoning wound in the {location} deeply bruised|n",
        "|Ra {severity} impact bruise on the {location} with spreading hematoma|n"
    ],
    
    "treated": [
        "{skintone}a {severity} treated bruise on the {location} with {ice_pack_color}ice pack marks|n",
        "{skintone}a {severity} bandaged contusion in the {location}|n",
        "{skintone}a {severity} wrapped blunt trauma on the {location} with {compression_wrap_color}compression|n",
        "{skintone}a {severity} treated impact wound in the {location}|n",
        "{skintone}a {severity} compressed crushing injury on the {location}|n",
        "{skintone}a {severity} dressed bludgeoning wound in the {location}|n",
        "{skintone}a {severity} treated impact bruise on the {location} with {compression_wrap_color}support wrap|n"
    ],
    
    "healing": [
        "{skintone}a {severity} healing bruise on the {location} changing to yellow-green|n",
        "{skintone}a {severity} fading contusion in the {location} with reduced swelling|n",
        "{skintone}a {severity} improving blunt trauma on the {location}|n",
        "{skintone}a {severity} mending impact wound in the {location} less tender|n",
        "{skintone}a {severity} healing crushing injury on the {location}|n",
        "{skintone}a {severity} recovering bludgeoning wound in the {location}|n",
        "{skintone}a {severity} healing impact bruise on the {location} with normal color returning|n"
    ],
    
    "scarred": [
        "{skintone}a {severity} faded bruise mark on the {location}|n",
        "{skintone}a {severity} old contusion scar in the {location} barely visible|n",
        "{skintone}a {severity} healed blunt trauma mark on the {location}|n",
        "{skintone}a {severity} impact scar in the {location} with slight discoloration|n",
        "{skintone}a {severity} old crushing injury mark on the {location}|n",
        "{skintone}a {severity} bludgeoning scar in the {location} permanently marking|n",
        "{skintone}a {severity} healed impact wound scar on the {location}|n"
    ]
}
