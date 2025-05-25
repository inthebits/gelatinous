import importlib
import random

def get_combat_message(weapon_type, phase, attacker=None, target=None, item=None, **kwargs):
    """
    Load the appropriate combat message from a specific weapon_type module.
    Returns a dictionary with "attacker_msg", "victim_msg", and "observer_msg".

    Args:
        weapon_type (str): e.g., "unarmed", "blade"
        phase (str): One of "initiate", "hit", "miss", "kill", etc.
        attacker (Object): The attacker
        target (Object): The target
        item (Object): The weapon/item used (can be None for unarmed)
        **kwargs: Any extra variables for formatting (e.g., damage)

    Returns:
        dict: A dictionary containing formatted "attacker_msg", "victim_msg",
              and "observer_msg" strings.
    """
    attacker_s = attacker.key if attacker else "Someone"
    target_s = target.key if target else "someone"
    item_s = item.key if item else "fists" # Default item name if None

    # Determine verb forms for fallback messages based on phase
    verb_root = phase.lower()
    attacker_verb = verb_root # For "You verb..."
    third_person_verb = f"{verb_root}s" # Default for "Someone verbs..."

    if verb_root.endswith("s") or verb_root.endswith("sh") or \
       verb_root.endswith("ch") or verb_root.endswith("x") or \
       verb_root.endswith("z"):
        third_person_verb = f"{verb_root}es"
    elif verb_root.endswith("y") and len(verb_root) > 1 and verb_root[-2].lower() not in "aeiou":
        third_person_verb = f"{verb_root[:-1]}ies"
    
    # Specific overrides for common verbs if needed
    if verb_root == "hit":
        attacker_verb = "hit"
        third_person_verb = "hits"
    elif verb_root == "miss": # "miss" -> "misses"
        attacker_verb = "miss" # "You miss"
        third_person_verb = "misses" # "Someone misses"
    # Add more overrides if other phases require special verb forms

    # Fallback message templates (using placeholders)
    fallback_template_set = {
        "attacker_msg": f"You {attacker_verb} {{target_name}} with {{item_name}}.",
        "victim_msg": f"{{attacker_name}} {third_person_verb} you with {{item_name}}.",
        "observer_msg": f"{{attacker_name}} {third_person_verb} {{target_name}} with {{item_name}}."
    }
    # Simpler fallbacks if item is not always relevant or desired in fallback
    # fallback_template_set = {
    #     "attacker_msg": f"You {attacker_verb} {{target_name}}.",
    #     "victim_msg": f"{{attacker_name}} {third_person_verb} you.",
    #     "observer_msg": f"{{attacker_name}} {third_person_verb} {{target_name}}."
    # }


    chosen_template_set = None
    try:
        module_path = f"world.combat_messages.{weapon_type}"
        module = importlib.import_module(module_path)
        messages_for_weapon = getattr(module, "MESSAGES", {})
        templates_for_phase = messages_for_weapon.get(phase, [])
        
        if templates_for_phase and isinstance(templates_for_phase, list):
            valid_templates = [t for t in templates_for_phase if isinstance(t, dict)]
            if valid_templates:
                chosen_template_set = random.choice(valid_templates)
    except ModuleNotFoundError:
        pass # chosen_template_set remains None, will use fallback
    except Exception as e:
        pass # chosen_template_set remains None, will use fallback

    # If no specific template was loaded (or error), use the fallback set
    if not chosen_template_set:
        chosen_template_set = fallback_template_set

    # Prepare combined kwargs for formatting.
    # These are the names templates should use, e.g., {attacker_name}, {target_name}, {item_name}, {damage}
    format_kwargs = {
        "attacker_name": attacker_s,
        "target_name": target_s,
        "item_name": item_s,
        "attacker": attacker_s,  # Alias for convenience if templates use {attacker}
        "target": target_s,      # Alias for convenience if templates use {target}
        "item": item_s,          # Alias for convenience if templates use {item}
        "phase": phase,          # Pass phase itself if templates need it
        **kwargs                 # e.g., damage, any other custom placeholders
    }

    final_messages = {}
    # Define which phases should be colored red for "successful hits"
    # This assumes 'hit' for grapple initiation should also be red, as per "like the initiate message"
    successful_hit_phases = [
        "hit",  # Covers standard weapon hits and grapple initiation success
        "grapple_damage_hit",
        "kill",
        "grapple_damage_kill"
        # Add any other phases that represent a "successful hit" you want red
    ]

    for msg_key in ["attacker_msg", "victim_msg", "observer_msg"]:
        # Get template string from chosen set, or from fallback_template_set if key is missing in chosen
        template_str = chosen_template_set.get(msg_key, fallback_template_set.get(msg_key, "Error: Message template key missing."))
        try:
            formatted_msg = template_str.format(**format_kwargs)
            
            # Apply red color if the phase is a "successful hit"
            # Assumes the template_str itself does not contain color codes for these phases.
            if phase in successful_hit_phases:
                # Basic check to avoid double-coloring if a template accidentally had it.
                # A more robust solution might involve stripping existing color codes first,
                # or simply enforcing that message files provide plain text for these phases.
                if not (formatted_msg.startswith("|") and formatted_msg.endswith("|n")): # very basic check
                    final_messages[msg_key] = f"|r{formatted_msg}|n"
                else:
                    final_messages[msg_key] = formatted_msg # Already colored, pass through
            else:
                final_messages[msg_key] = formatted_msg

        except KeyError as e_key:
            final_messages[msg_key] = f"(Error: Missing placeholder {e_key} in template for '{msg_key}')"
        except Exception as e_fmt:
            final_messages[msg_key] = f"(Error: Formatting issue for '{msg_key}': {e_fmt})"

    return final_messages
