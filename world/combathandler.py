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
    """
    splattercast = ChannelDB.objects.get_channel("Splattercast")
    # Look for an existing handler on this location
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            if script.is_active:
                splattercast.msg(f"Found active CombatHandler on {location.key}.")
                return script
            else:
                splattercast.msg(f"Found inactive CombatHandler on {location.key}, stopping and deleting it.")
                script.stop()
                script.delete()  # <-- Add this line
    # If not found, create a new one
    new_script = create_script(
        "world.combathandler.CombatHandler",
        key=COMBAT_SCRIPT_KEY,
        obj=location,
        persistent=True,
    )
    splattercast.msg(f"Created new CombatHandler on {location.key}.")
    return new_script

class CombatHandler(DefaultScript):
    def at_script_creation(self):
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6
        self.persistent = True
        self.db.combatants = []
        self.db.round = 0  # Start at round 0
        self.db.ready_to_start = False  # Ensure this is initialized
        self.db.round_scheduled = False  # Track if a round is already scheduled

    def start(self):
        """
        Start the combat handler, ensuring that at_repeat is called at regular intervals.
        """
        if self.is_active:
            ChannelDB.objects.get_channel("Splattercast").msg(f"CombatHandler is already active. Skipping redundant start.")
            return

        ChannelDB.objects.get_channel("Splattercast").msg(f"CombatHandler started.")
        self.is_active = True  # Mark the handler as active
        self.start_repeat(self.interval)  # Schedule at_repeat to run at regular intervals

    def at_stop(self):
        # Announce and clean up any remaining combatant
        for entry in self.db.combatants:
            char = entry["char"]
            ChannelDB.objects.get_channel("Splattercast").msg(f"{char.key} removed from combat.")
                ChannelDB.objects.get_channel("Splattercast").msg(f"Combat ends.")
            if char.ndb.combat_handler:
                del char.ndb.combat_handler
        self.stop_repeat()
        self.is_active = False
        self.delete()

    def add_combatant(self, char, target=None):
        # Check if the character is already in combat
        if any(entry["char"] == char for entry in self.db.combatants):
            return

        # Roll initiative and add the combatant
        initiative = randint(1, max(1, char.db.motorics or 1))
        self.db.combatants.append({
            "char": char,
            "initiative": initiative,
            "target": target
        })
        char.ndb.combat_handler = self
        ChannelDB.objects.get_channel("Splattercast").msg(f"{char.key} joins combat with initiative {initiative}.")
        ChannelDB.objects.get_channel("Splattercast").msg(f"{char.key} added to combat. Total combatants: {len(self.db.combatants)}.")
        if self.db.round == 0:
            ChannelDB.objects.get_channel("Splattercast").msg(f"Combat is in setup phase (round 0). Waiting for more combatants.")

        # Mark as ready to start if there are at least two combatants
        if len(self.db.combatants) > 1:
            self.db.ready_to_start = True

        # Start the combat handler if ready and not already active
        if self.db.ready_to_start and not self.is_active:
            ChannelDB.objects.get_channel("Splattercast").msg(f"Enough combatants added. Starting combat.")
            self.start()

    def remove_combatant(self, char):
        self.db.combatants = [entry for entry in self.db.combatants if entry["char"] != char]
        if char.ndb.combat_handler:
            del char.ndb.combat_handler
        ChannelDB.objects.get_channel("Splattercast").msg(f"{char.key} removed from combat.")
        if len(self.db.combatants) <= 1:
            self.stop()

    def get_target(self, char):
        entry = next((e for e in self.db.combatants if e["char"] == char), None)
        if not entry:
            ChannelDB.objects.get_channel("Splattercast").msg(f"No combat entry found for {char.key}.")
            return None
        target = entry.get("target")
        valid_chars = [e["char"] for e in self.db.combatants]

        if not target or target not in valid_chars:
            ChannelDB.objects.get_channel("Splattercast").msg(
                f"{char.key} has no valid target or their target is not in combat."
            )
            attackers = [e["char"] for e in self.db.combatants if e.get("target") == char and e["char"] != char]
            ChannelDB.objects.get_channel("Splattercast").msg(
                f"Attackers targeting {char.key}: {[a.key for a in attackers]}"
            )
            if attackers:
                target = attackers[randint(0, len(attackers) - 1)]
                ChannelDB.objects.get_channel("Splattercast").msg(
                    f"{char.key} now targets {target.key} (was being targeted)."
                )
                self.set_target(char, target)
            else:
                ChannelDB.objects.get_channel("Splattercast").msg(
                    f"{char.key} is not being targeted by anyone and will be removed from combat."
                )
                return None
        else:
            ChannelDB.objects.get_channel("Splattercast").msg(
                f"{char.key} keeps current target {target.key}."
            )

        return target

    def set_target(self, char, target):
        for entry in self.db.combatants:
            if entry["char"] == char:
                entry["target"] = target

    def get_initiative_order(self):
        return sorted(self.db.combatants, key=lambda e: e["initiative"], reverse=True)

    def at_repeat(self):
        if not self.is_active:
            return  # Exit early if the handler is inactive

        if self.db.round == 0:
            # Setup phase: Ensure there are enough combatants to start combat
            active_combatants = [e for e in self.db.combatants if e["char"].location == self.obj]
            ChannelDB.objects.get_channel("Splattercast").msg(f"Round 0: Active combatants: {[e['char'].key for e in active_combatants]}.")

            if len(active_combatants) > 1:
                ChannelDB.objects.get_channel("Splattercast").msg(f"Enough combatants present. Starting combat in round 1.")
                self.db.round = 1  # Transition to round 1
            else:
                ChannelDB.objects.get_channel("Splattercast").msg(f"Waiting for more combatants to join...")
                return  # Exit early to prevent combat logic from running

        # Proceed with combat rounds
        ChannelDB.objects.get_channel("Splattercast").msg(f"Combat round {self.db.round} begins.")
        active_combatants = [e for e in self.db.combatants if e["char"].location == self.obj]
        ChannelDB.objects.get_channel("Splattercast").msg(f"Active combatants: {[e['char'].key for e in active_combatants]}.")

        # Ensure there are enough combatants to proceed
        if len(active_combatants) <= 1:
            ChannelDB.objects.get_channel("Splattercast").msg(f"Not enough combatants remain. Ending combat.")
            self.stop()
            return

        # Proceed with combat round logic
        for entry in self.get_initiative_order():
            char = entry["char"]
            target = self.get_target(char)

            if not target:
                ChannelDB.objects.get_channel("Splattercast").msg(
                    f"{char.key} has no valid target and is not being targeted. Removing from combat."
                )
                self.remove_combatant(char)
                continue

            atk_roll = randint(1, max(1, char.grit))
            def_roll = randint(1, max(1, target.motorics))

            ChannelDB.objects.get_channel("Splattercast").msg(f"{char.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")

            # --- Find weapon and weapon_type for both hit and miss ---
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
                damage = char.grit or 1
                ChannelDB.objects.get_channel("Splattercast").msg(f"{char.key} hits {target.key} for {damage} damage.")

                # --- Player-facing hit message ---
                msg = get_combat_message(
                    weapon_type,
                    "hit",
                    attacker=char,
                    target=target,
                    item=weapon,
                    damage=damage
                )
                ChannelDB.objects.get_channel("Splattercast").msg(f"get_combat_message (hit) returned: {msg!r}")
                if msg:
                    self.obj.msg_contents(f"|R{msg}|n")

                target.take_damage(damage)
                if target.is_dead():
                    ChannelDB.objects.get_channel("Splattercast").msg(f"{target.key} has been defeated and removed from combat.")

                    # --- Player-facing kill message ---
                    msg = get_combat_message(
                        weapon_type,
                        "kill",
                        attacker=char,
                        target=target,
                        item=weapon,
                        damage=damage
                    )
                    ChannelDB.objects.get_channel("Splattercast").msg(f"get_combat_message (kill) returned: {msg!r}")
                    if msg:
                        self.obj.msg_contents(f"|R{msg}|n")

                    self.remove_combatant(target)

                    # Re-acquire targets for anyone who was targeting the now-removed character
                    for entry in self.db.combatants:
                        if entry.get("target") == target:
                            new_target = self.get_target(entry["char"])
                            old_name = target.key if hasattr(target, "key") else str(target)
                            new_name = new_target.key if new_target else "None"
                            ChannelDB.objects.get_channel("Splattercast").msg(
                                f"{entry['char'].key} was targeting {old_name} (now removed) and now targets {new_name}."
                            )
                            entry["target"] = new_target

                    continue
            else:
                # --- Player-facing miss message ---
                msg = get_combat_message(
                    weapon_type,
                    "miss",
                    attacker=char,
                    target=target,
                    item=weapon
                )
                ChannelDB.objects.get_channel("Splattercast").msg(f"get_combat_message (miss) returned: {msg!r}")
                if msg:
                    self.obj.msg_contents(f"|[X{msg}|n")
                else:
                    self.obj.msg_contents(f"{char.key} misses {target.key}.")

        self.db.round += 1
        ChannelDB.objects.get_channel("Splattercast").msg(f"Round {self.db.round} scheduled.")
