"""
Medical System Utilities

Utility functions for medical system integration, damage calculation,
and medical state management.
"""

from .constants import ORGANS, HIT_WEIGHTS
from .core import MedicalState


def get_organ_by_body_location(location):
    """
    Get all organs that are contained within a specific body location.
    
    Args:
        location (str): Body location (e.g., "chest", "head", "left_arm")
        
    Returns:
        list: List of organ names in that location
    """
    organs_in_location = []
    for organ_name, organ_data in ORGANS.items():
        if organ_data.get("container") == location:
            organs_in_location.append(organ_name)
    return organs_in_location


def calculate_hit_weights_for_location(location):
    """
    Calculate hit weights for all organs in a body location.
    
    Args:
        location (str): Body location
        
    Returns:
        dict: {organ_name: hit_weight_value} mapping
    """
    organs = get_organ_by_body_location(location)
    hit_weights = {}
    
    for organ_name in organs:
        organ_data = ORGANS.get(organ_name, {})
        weight_category = organ_data.get("hit_weight", "common")
        weight_value = HIT_WEIGHTS.get(weight_category, HIT_WEIGHTS["common"])
        hit_weights[organ_name] = weight_value
        
    return hit_weights


def distribute_damage_to_organs(location, total_damage, injury_type="generic"):
    """
    Distribute damage across organs in a body location based on hit weights.
    
    Args:
        location (str): Body location hit
        total_damage (int): Total damage to distribute
        injury_type (str): Type of injury
        
    Returns:
        dict: {organ_name: damage_amount} mapping
    """
    organs = get_organ_by_body_location(location)
    if not organs:
        return {}
        
    hit_weights = calculate_hit_weights_for_location(location)
    total_weight = sum(hit_weights.values())
    
    if total_weight == 0:
        return {}
        
    damage_distribution = {}
    remaining_damage = total_damage
    
    # Distribute damage proportionally based on hit weights
    for organ_name in organs[:-1]:  # All but last organ
        organ_weight = hit_weights.get(organ_name, 0)
        organ_damage = int((organ_weight / total_weight) * total_damage)
        damage_distribution[organ_name] = organ_damage
        remaining_damage -= organ_damage
        
    # Give remaining damage to last organ to ensure total is preserved
    if organs:
        damage_distribution[organs[-1]] = remaining_damage
        
    return damage_distribution


def apply_anatomical_damage(character, damage_amount, location, injury_type="generic"):
    """
    Apply damage to a specific body location, affecting relevant organs.
    
    This is the main integration point with the combat system.
    
    Args:
        character: Character object with medical state
        damage_amount (int): Amount of damage
        location (str): Body location hit
        injury_type (str): Type of injury
        
    Returns:
        dict: Results of damage application
    """
    # Ensure medical state exists - access property to trigger initialization
    try:
        medical_state = character.medical_state
    except AttributeError:
        # Initialize medical state if character doesn't have the property
        initialize_character_medical_state(character)
        medical_state = character.medical_state
        
    medical_state = character.medical_state
    
    # Distribute damage to organs in the location
    damage_distribution = distribute_damage_to_organs(location, damage_amount, injury_type)
    
    results = {
        "organs_damaged": [],
        "organs_destroyed": [],
        "conditions_added": [],
        "total_damage": damage_amount,
        "location": location
    }
    
    # Apply damage to each organ
    for organ_name, organ_damage in damage_distribution.items():
        if organ_damage > 0:
            was_destroyed = medical_state.take_organ_damage(organ_name, organ_damage, injury_type)
            results["organs_damaged"].append((organ_name, organ_damage))
            
            if was_destroyed:
                results["organs_destroyed"].append(organ_name)
                
    # Add appropriate conditions based on injury type and damage
    conditions = _generate_conditions_for_injury(location, damage_amount, injury_type)
    for condition_type, severity in conditions:
        condition = medical_state.add_condition(condition_type, location, severity)
        results["conditions_added"].append((condition_type, severity))
        
    # Update vital signs after damage
    medical_state.update_vital_signs()
    
    return results


def _generate_conditions_for_injury(location, damage_amount, injury_type):
    """
    Generate appropriate medical conditions based on injury parameters.
    
    Args:
        location (str): Body location
        damage_amount (int): Amount of damage
        injury_type (str): Type of injury
        
    Returns:
        list: List of (condition_type, severity) tuples
    """
    conditions = []
    
    # Generate bleeding for most injury types
    if injury_type in ["cut", "stab", "bullet", "laceration"]:
        if damage_amount >= 15:
            conditions.append(("bleeding", "severe"))
        elif damage_amount >= 8:
            conditions.append(("bleeding", "moderate"))
        elif damage_amount >= 3:
            conditions.append(("bleeding", "minor"))
            
    # Generate fractures for blunt trauma to limbs
    limb_locations = ["left_arm", "right_arm", "left_thigh", "right_thigh", 
                     "left_shin", "right_shin", "left_hand", "right_hand"]
    if injury_type == "blunt" and location in limb_locations and damage_amount >= 10:
        conditions.append(("fracture", "moderate"))
        
    # Generate burns for fire/heat damage
    if injury_type == "burn":
        if damage_amount >= 20:
            conditions.append(("burn", "severe"))
        elif damage_amount >= 10:
            conditions.append(("burn", "moderate"))
        elif damage_amount >= 5:
            conditions.append(("burn", "minor"))
            
    return conditions


def get_medical_status_summary(character):
    """
    Generate a human-readable summary of character's medical status.
    
    Args:
        character: Character with medical state
        
    Returns:
        str: Medical status description
    """
    try:
        medical_state = character.medical_state
    except AttributeError:
        return "No medical information available."
        
    if medical_state is None:
        return "No medical information available."
        
    medical_state = character.medical_state
    lines = []
    
    # Overall status
    if medical_state.is_dead():
        return "DECEASED"
    elif medical_state.is_unconscious():
        lines.append("UNCONSCIOUS")
    else:
        lines.append("CONSCIOUS")
        
    # Vital signs
    lines.append(f"Blood Level: {medical_state.blood_level:.1f}%")
    lines.append(f"Pain Level: {medical_state.pain_level:.1f}")
    lines.append(f"Consciousness: {medical_state.consciousness:.1f}%")
    
    # Active conditions
    if medical_state.conditions:
        lines.append("Active Conditions:")
        for condition in medical_state.conditions:
            location_str = f" ({condition.location})" if condition.location else ""
            lines.append(f"  - {condition.type.title()} ({condition.severity}){location_str}")
    else:
        lines.append("No active medical conditions")
        
    # Damaged organs
    damaged_organs = [name for name, organ in medical_state.organs.items() 
                     if organ.current_hp < organ.max_hp]
    if damaged_organs:
        lines.append("Damaged Organs:")
        for organ_name in damaged_organs:
            organ = medical_state.organs[organ_name]
            hp_percent = (organ.current_hp / organ.max_hp) * 100
            lines.append(f"  - {organ_name}: {hp_percent:.1f}% functional")
            
    return "\n".join(lines)


def initialize_character_medical_state(character):
    """
    Initialize medical state for a character if it doesn't exist.
    
    Args:
        character: Character object to initialize
    """
    if not hasattr(character, '_medical_state') or character._medical_state is None:
        character._medical_state = MedicalState(character)
        
        # Store in db for persistence
        character.db.medical_state = character._medical_state.to_dict()


def save_medical_state(character):
    """
    Save character's medical state to database.
    
    Args:
        character: Character with medical state to save
    """
    try:
        medical_state = character.medical_state
        if medical_state is not None:
            character.db.medical_state = medical_state.to_dict()
    except AttributeError:
        pass  # Character doesn't have medical state


def load_medical_state(character):
    """
    Load character's medical state from database.
    
    Args:
        character: Character to load medical state for
        
    Returns:
        bool: True if state was loaded, False if none existed
    """
    medical_data = character.db.medical_state
    if medical_data:
        character._medical_state = MedicalState.from_dict(medical_data, character)
        return True
    else:
        # Initialize new medical state if none exists
        initialize_character_medical_state(character)
        return False


# =============================================================================
# MEDICAL ITEM UTILITIES
# =============================================================================

def is_medical_item(item):
    """Check if an item is a medical item."""
    return item.tags.has("medical_item", category="item_type")


def get_medical_type(item):
    """Get the medical type of an item."""
    return item.attributes.get("medical_type", "")


def can_be_used(item):
    """Check if this medical item can still be used."""
    if not is_medical_item(item):
        return False
    
    uses_left = item.attributes.get("uses_left", 1)
    return uses_left > 0


def use_item(item):
    """Use the item, reducing uses left."""
    if not is_medical_item(item):
        return False
        
    uses_left = item.attributes.get("uses_left", 1)
    if uses_left > 0:
        item.attributes.add("uses_left", uses_left - 1)
        return True
    return False


def get_stat_requirement(item):
    """Get the stat requirement for using this item."""
    return item.attributes.get("stat_requirement", 0)


def get_effectiveness(item, condition_type):
    """Get item effectiveness for a specific condition."""
    effectiveness = item.attributes.get("effectiveness", {})
    return effectiveness.get(condition_type, 5)  # Default 5/10


def calculate_treatment_success(item, user, target, condition_type):
    """
    Calculate treatment success based on user's medical skill and item effectiveness.
    
    Args:
        item: Medical item being used
        user: Character using the item
        target: Character being treated
        condition_type: Type of condition being treated
        
    Returns:
        dict: Contains roll, medical_skill, total, difficulty, success_level
    """
    import random
    
    # Get user's medical skill (based on Intellect)
    user_intellect = getattr(user, 'intellect', 1)
    medical_skill = user_intellect * 2  # Convert intellect to medical skill
    
    # Get item effectiveness for this condition
    effectiveness = get_effectiveness(item, condition_type)
    
    # Calculate difficulty (higher effectiveness = easier treatment)
    base_difficulty = 15
    difficulty = base_difficulty - effectiveness
    
    # Roll dice (3d6)
    roll = sum(random.randint(1, 6) for _ in range(3))
    total = roll + medical_skill
    
    # Determine success level
    if total >= difficulty + 5:
        success_level = "success"
    elif total >= difficulty:
        success_level = "partial_success"
    else:
        success_level = "failure"
        
    return {
        "roll": roll,
        "medical_skill": medical_skill,
        "total": total,
        "difficulty": difficulty,
        "success_level": success_level
    }


def apply_medical_effects(item, user, target, **kwargs):
    """
    Apply the medical item's effects to the target.
    
    This handles the core medical treatment logic.
    """
    medical_type = get_medical_type(item)
    
    if not hasattr(target, 'medical_state'):
        return "Target has no medical state to treat."
    
    medical_state = target.medical_state
    
    # Basic effect application based on medical type
    if medical_type == "blood_restoration":
        # Restore blood volume
        old_volume = medical_state.blood_volume
        medical_state.blood_volume = min(100.0, old_volume + 25.0)
        
        # Reduce bleeding
        bleeding_conditions = [c for c in medical_state.conditions 
                             if c.type == "bleeding"]
        for condition in bleeding_conditions[:2]:  # Reduce up to 2 bleeding conditions
            condition.severity = max(0, condition.severity - 3)
            if condition.severity <= 0:
                medical_state.conditions.remove(condition)
        
        return f"Blood transfusion successful! Blood volume increased from {old_volume:.1f} to {medical_state.blood_volume:.1f}."
        
    elif medical_type == "pain_relief":
        # Reduce pain conditions
        pain_conditions = [c for c in medical_state.conditions 
                         if c.type == "pain"]
        for condition in pain_conditions[:3]:  # Reduce multiple pain sources
            condition.severity = max(0, condition.severity - 2)
            if condition.severity <= 0:
                medical_state.conditions.remove(condition)
        
        return "Painkiller administered. Pain significantly reduced."
        
    elif medical_type == "wound_care":
        # Bandaging effects
        bleeding_conditions = [c for c in medical_state.conditions 
                             if c.type == "bleeding"]
        for condition in bleeding_conditions[:1]:  # Stop one source of bleeding
            condition.severity = max(0, condition.severity - 2)
            if condition.severity <= 0:
                medical_state.conditions.remove(condition)
        
        return "Wounds properly bandaged. Bleeding controlled."
        
    elif medical_type == "fracture_treatment":
        # Splint effects
        fracture_conditions = [c for c in medical_state.conditions 
                             if c.type == "fracture"]
        for condition in fracture_conditions[:1]:  # Stabilize one fracture
            condition.severity = max(0, condition.severity - 4)
            if condition.severity <= 0:
                medical_state.conditions.remove(condition)
        
        return "Fracture stabilized with splint. Mobility partially restored."
        
    elif medical_type == "surgical_treatment":
        # Surgical intervention
        organ_conditions = [c for c in medical_state.conditions 
                          if c.type == "organ_damage"]
        for condition in organ_conditions[:1]:  # Repair one organ
            condition.severity = max(0, condition.severity - 5)
            if condition.severity <= 0:
                medical_state.conditions.remove(condition)
        
        return "Surgical procedure completed. Internal injuries treated."
    
    elif medical_type == "healing_acceleration":
        # Stimpak effects - general healing boost
        all_conditions = medical_state.conditions[:]
        healed_count = 0
        for condition in all_conditions[:3]:  # Heal up to 3 conditions
            condition.severity = max(0, condition.severity - 1)
            if condition.severity <= 0:
                medical_state.conditions.remove(condition)
                healed_count += 1
        
        return f"Stimpak administered. Rapid healing activated - {healed_count} conditions improved."
    
    elif medical_type == "antiseptic":
        # Infection prevention and wound cleaning
        infection_conditions = [c for c in medical_state.conditions 
                              if c.type == "infection"]
        for condition in infection_conditions[:2]:  # Clear multiple infections
            condition.severity = max(0, condition.severity - 3)
            if condition.severity <= 0:
                medical_state.conditions.remove(condition)
        
        return "Antiseptic applied. Infections cleared and wounds sterilized."
    
    return f"Applied {medical_type.replace('_', ' ')} treatment."


def get_medical_item_info(item, viewer):
    """
    Get formatted information about a medical item.
    
    Returns a string with detailed medical item information.
    """
    if not is_medical_item(item):
        return f"{item.get_display_name(viewer)} is not a medical item."
    
    info = [
        f"|w{item.get_display_name(viewer).upper()}|n",
        "=" * 50
    ]
    
    # Basic info
    medical_type = get_medical_type(item)
    info.append(f"Type: {medical_type.replace('_', ' ').title()}")
    info.append(f"Description: {item.db.desc or 'No description.'}")
    
    # Usage info
    uses_left = item.attributes.get("uses_left", "∞")
    max_uses = item.attributes.get("max_uses", "∞")
    info.append(f"Uses remaining: {uses_left}/{max_uses}")
    
    # Requirements
    stat_req = get_stat_requirement(item)
    if stat_req > 0:
        info.append(f"Intellect requirement: {stat_req}")
    else:
        info.append("No skill requirements")
        
    # Effectiveness
    effectiveness = item.attributes.get("effectiveness", {})
    if effectiveness:
        info.append("Effectiveness ratings:")
        for condition, rating in effectiveness.items():
            info.append(f"  {condition.replace('_', ' ').title()}: {rating}/10")
            
    # Special properties
    if not can_be_used(item):
        info.append("|rThis item is empty or used up.|n")
        
    application_time = item.attributes.get("application_time", 1)
    if application_time > 1:
        info.append(f"Application time: {application_time} rounds")
        
    return "\n".join(info)
