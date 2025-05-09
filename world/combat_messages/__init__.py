import importlib
import random

def get_combat_message(weapon_type, phase, attacker=None, target=None, item=None, **kwargs):
    """
    Load the appropriate combat message from a specific weapon_type module.

    Args:
        weapon_type (str): e.g., "melee", "blade"
        phase (str): One of "initiate", "hit", "miss", "kill"
        attacker (Object): The attacker
        target (Object): The target
        item (Object): The weapon/item used
        **kwargs: Any extra variables for formatting (e.g., damage)

    Returns:
        str: A formatted combat message string.
    """
    try:
        module = importlib.import_module(f"world.combat_messages.{weapon_type}")
        messages = getattr(module, "MESSAGES", {})
        templates = messages.get(phase, [])
    except ModuleNotFoundError:
        templates = []

    if not templates:
        return ""

    return random.choice(templates).format(
        attacker=attacker.key if attacker else "Someone",
        target=target.key if target else "someone",
        item=item.key if item else "something",
        **kwargs
    )
