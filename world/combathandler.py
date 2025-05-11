from evennia import DefaultScript, create_script
from random import randint
from evennia.utils.utils import delay
from world.combat_messages import get_combat_message
from evennia.comms.models import ChannelDB

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    """
    Returns the active CombatHandler for this location, or creates one if needed.
    Logs all actions to Splattercast for debugging.
    Ensures only one handler per location.
    """
    splattercast = ChannelDB.objects.get_channel("Splattercast")
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            if script.is_active:
                splattercast.msg(f"Found active CombatHandler on {location.key}.")
                return script
            else:
                splattercast.msg(f"Found inactive CombatHandler on {location.key}, stopping and deleting it.")
                script.stop()
                script.delete()
    new_script = create_script(
        "world.combathandler.CombatHandler",
        key=COMBAT_SCRIPT_KEY,
        obj=location,
        persistent=True,
    )
    splattercast.msg(f"Created new CombatHandler on {location.key}.")
    return new_script

class CombatHandler(DefaultScript):
    """
    Script that manages turn-based combat for all combatants in a location.
    Handles initiative, targeting, combat rounds, and cleanup.
    """

    def at_script_creation(self):
        """
        Initialize combat handler script attributes.
        """
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6
        self.persistent = True
        self.db.combatants = []
        self.db.round = 0
        self.db.ready_to_start = False
        self.db.round_scheduled = False

    def start(self):
        """
        Start the combat handler's repeat timer if not already active.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if self.is_active:
            splattercast.msg(f"CombatHandler is already active. Skipping redundant start.")
            return
        splattercast.msg(f"CombatHandler started.")
        self.is_active = True
        self.start_repeat(self.interval)

    def at_stop(self):
        """
        Clean up when combat ends. Remove all combatants and delete the handler.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        for entry in self.db.combatants:
            char = entry["char"]
            splattercast.msg(f"{char.key} removed from combat.")
            if char.ndb.combat_handler:
                del char.ndb.combat_handler
        splattercast.msg("Combat ends.")
        self.stop_repeat()
        self.is_active = False
        self.delete()

    def add_combatant(self, char, target=None):
        """
        Add a character to combat, assigning initiative and an optional target.
        Logs if joining an already-running combat.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if any(entry["char"] == char for entry in self.db.combatants):
            return
        initiative = randint(1, max(1, char.db.motorics or 1))
        self.db.combatants.append({
            "char": char,
            "initiative": initiative,
            "target": target
        })
        char.ndb.combat_handler = self
        splattercast.msg(f"{char.key} joins combat with initiative {initiative}.")
        splattercast.msg(f"{char.key} added to combat. Total combatants: {len(self.db.combatants)}.")
        if self.db.round == 0:
            splattercast.msg(f"Combat is in setup phase (round 0). Waiting for more combatants.")
        elif self.is_active:
            splattercast.msg(f"{char.key} joined an already-running combat.")
        if len(self.db.combatants) > 1:
            self.db.ready_to_start = True
        if self.db.ready_to_start and not self.is_active:
            splattercast.msg(f"Enough combatants added. Starting combat.")
            self.start()

    def remove_combatant(self, char):
        """
        Remove a character from combat and clean up their handler reference.
        If only one or zero combatants remain, end combat.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        self.db.combatants = [entry for entry in self.db.combatants if entry["char"] != char]
        if char.ndb.combat_handler:
            del char.ndb.combat_handler
        splattercast.msg(f"{char.key} removed from combat.")
        if len(self.db.combatants) <= 1:
            self.stop()

    def get_target(self, char):
        """
        Determine the current valid target for a combatant.
        If their target is invalid, retargets or removes them from combat.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        entry = next((e for e in self.db.combatants if e["char"] == char), None)
        if not entry:
            splattercast.msg(f"No combat entry found for {char.key}.")
            return None
        target = entry.get("target")
        valid_chars = [e["char"] for e in self.db.combatants]
        if not target or target not in valid_chars:
            splattercast.msg(
                f"{char.key} has no valid target or their target is not in combat."
            )
            # Find attackers targeting this char
            attackers = [e["char"] for e in self.db.combatants if e.get("target") == char and e["char"] != char]
            splattercast.msg(
                f"Attackers targeting {char.key}: {[a.key for a in attackers]}"
            )
            if attackers:
                # Retarget to a random attacker
                target = attackers[randint(0, len(attackers) - 1)]
                splattercast.msg(
                    f"{char.key} now targets {target.key} (was being targeted)."
                )
                self.set_target(char, target)
            else:
                # No attackers, remove from combat
                splattercast.msg(
                    f"{char.key} is not being targeted by anyone and will be removed from combat."
                )
                return None
        else:
            splattercast.msg(
                f"{char.key} keeps current target {target.key}."
            )
        return target

    def set_target(self, char, target):
        """
        Set a new target for a combatant.
        """
        for entry in self.db.combatants:
            if entry["char"] == char:
                entry["target"] = target

    def get_initiative_order(self):
        """
        Return combatants sorted by initiative, highest first.
        """
        return sorted(self.db.combatants, key=lambda e: e["initiative"], reverse=True)

    def at_repeat(self):
        """
        Main combat loop, processes each combatant's turn in initiative order.
        Handles attacks, misses, deaths, and round progression.
        Removes combatants with no valid target or who are not being targeted.
        """
        splattercast = ChannelDB.objects.get_channel("Splattercast")
        if not self.is_active:
            return
        # Setup phase: wait for enough combatants to start
        if self.db.round == 0:
            active_combatants = [e for e in self.db.combatants if e["char"].location == self.obj]
            splattercast.msg(f"Round 0: Active combatants: {[e['char'].key for e in active_combatants]}.")
            if len(active_combatants) > 1:
                splattercast.msg(f"Enough combatants present. Starting combat in round 1.")
                self.db.round = 1
            else:
                splattercast.msg(f"Waiting for more combatants to join...")
                return
        splattercast.msg(f"Combat round {self.db.round} begins.")
        active_combatants = [e for e in self.db.combatants if e["char"].location == self.obj]
        splattercast.msg(f"Active combatants: {[e['char'].key for e in active_combatants]}.")
        if len(active_combatants) <= 1:
            splattercast.msg(f"Not enough combatants remain. Ending combat.")
            self.stop()
            return
        for entry in list(self.get_initiative_order()):
            char = entry["char"]
            target = self.get_target(char)
            if not target:
                # Remove combatants with no valid target or who are not being targeted
                splattercast.msg(
                    f"{char.key} has no valid target and is not being targeted. Removing from combat."
                )
                self.remove_combatant(char)
                continue
            # Roll for attack and defense
            atk_roll = randint(1, max(1, char.grit))
            def_roll = randint(1, max(1, target.motorics))
            splattercast.msg(f"{char.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")
            # Determine weapon and type
            hands = char.hands
            weapon = None
            for hand, item in hands.items():
                if item:
                    weapon = item
                    break
            weapon_type = "unarmed"
            if weapon and hasattr(weapon.db, "weapon_type") and weapon.db.weapon_type:
                weapon_type = str(weapon.db.weapon_type).lower()
            if atk_roll > def_roll:
                # Successful hit
                damage = char.grit or 1
                splattercast.msg(f"{char.key} hits {target.key} for {damage} damage.")
                msg = get_combat_message(
                    weapon_type,
                    "hit",
                    attacker=char,
                    target=target,
                    item=weapon,
                    damage=damage
                )
                splattercast.msg(f"get_combat_message (hit) returned: {msg!r}")
                if msg:
                    self.obj.msg_contents(f"|R{msg}|n")
                target.take_damage(damage)
                if target.is_dead():
                    # Handle death and retargeting
                    splattercast.msg(f"{target.key} has been defeated and removed from combat.")
                    msg = get_combat_message(
                        weapon_type,
                        "kill",
                        attacker=char,
                        target=target,
                        item=weapon,
                        damage=damage
                    )
                    splattercast.msg(f"get_combat_message (kill) returned: {msg!r}")
                    if msg:
                        self.obj.msg_contents(f"|R{msg}|n")
                    self.remove_combatant(target)
                    # Retarget anyone who was targeting the now-removed character
                    for entry in self.db.combatants:
                        if entry.get("target") == target:
                            new_target = self.get_target(entry["char"])
                            old_name = target.key if hasattr(target, "key") else str(target)
                            new_name = new_target.key if new_target else "None"
                            splattercast.msg(
                                f"{entry['char'].key} was targeting {old_name} (now removed) and now targets {new_name}."
                            )
                            entry["target"] = new_target
                    continue
            else:
                # Missed attack
                msg = get_combat_message(
                    weapon_type,
                    "miss",
                    attacker=char,
                    target=target,
                    item=weapon
                )
                splattercast.msg(f"get_combat_message (miss) returned: {msg!r}")
                if msg:
                    self.obj.msg_contents(f"|[X{msg}|n")
                else:
                    self.obj.msg_contents(f"{char.key} misses {target.key}.")
        self.db.round += 1
        splattercast.msg(f"Round {self.db.round} scheduled.")
