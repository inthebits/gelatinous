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
    if not hasattr(character, 'medical_state') or character.medical_state is None:
        # Initialize medical state if it doesn't exist
        character.medical_state = MedicalState(character)
        
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
    if not hasattr(character, 'medical_state') or character.medical_state is None:
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
    if not hasattr(character, 'medical_state') or character.medical_state is None:
        character.medical_state = MedicalState(character)
        
        # Store in db for persistence
        character.db.medical_state = character.medical_state.to_dict()


def save_medical_state(character):
    """
    Save character's medical state to database.
    
    Args:
        character: Character with medical state to save
    """
    if hasattr(character, 'medical_state') and character.medical_state is not None:
        character.db.medical_state = character.medical_state.to_dict()


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
        character.medical_state = MedicalState.from_dict(medical_data, character)
        return True
    else:
        # Initialize new medical state if none exists
        initialize_character_medical_state(character)
        return False
