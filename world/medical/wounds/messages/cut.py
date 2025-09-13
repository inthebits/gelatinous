"""
Cutting wound descriptions following weapon message pattern.

Multiple description variants for each healing stage.
"""

WOUND_DESCRIPTIONS = {
    "fresh": [
        "|Ra {severity} cut across the {location} with clean edges|n",
        "|Ra {severity} slash wound on the {location}, bleeding steadily|n",
        "|Ra {severity} laceration in the {location} with gaping sides|n",
        "|Ra {severity} knife wound on the {location} with sharp borders|n",
        "|Ra {severity} slice through the {location}, deep and precise|n",
        "|Ra {severity} cutting wound in the {location} exposing deeper tissue|n",
        "|Ra {severity} blade mark on the {location} with trickling blood|n"
    ],
    
    "treated": [
        "{skintone}a {severity} sutured cut on the {location} with {suture_color}neat stitches|n",
        "{skintone}a {severity} bandaged slash wound in the {location}|n",
        "{skintone}a {severity} dressed laceration on the {location} with {suture_color}surgical thread|n",
        "{skintone}a {severity} treated knife wound in the {location} held closed|n",
        "{skintone}a {severity} closed cutting wound on the {location} with {medical_staple_color}medical staples|n",
        "{skintone}a {severity} stitched slice in the {location} under {bandage_color}clean dressing|n",
        "{skintone}a {severity} repaired blade wound on the {location}|n"
    ],
    
    "healing": [
        "{skintone}a {severity} healing cut on the {location} with forming scab|n",
        "{skintone}a {severity} mending slash wound in the {location} showing new skin|n",
        "{skintone}a {severity} closing laceration on the {location} with reduced gaping|n",
        "{skintone}a {severity} recovering knife wound in the {location}|n",
        "{skintone}a {severity} healing slice through the {location} with pink edges|n",
        "{skintone}a {severity} improving cutting wound on the {location}|n",
        "{skintone}a {severity} knitting blade wound in the {location}|n"
    ],
    
    "scarred": [
        "{skintone}a {severity} cutting scar across the {location}|n",
        "{skintone}a {severity} slash scar on the {location} with thin white line|n",
        "{skintone}a {severity} laceration scar in the {location} barely visible|n",
        "{skintone}a {severity} knife wound scar on the {location} permanently etched|n",
        "{skintone}a {severity} blade scar through the {location} with smooth texture|n",
        "{skintone}a {severity} old cutting wound mark on the {location}|n",
        "{skintone}a {severity} faded slash scar in the {location}|n"
    ]
}
