
from evennia import DefaultScript, create_script
from random import randint

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    # Remove broken/inactive scripts
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            if not script.is_active:
                location.msg_contents("[DEBUG] Found broken combat script. Removing...")
                script.stop()
                script.delete()
            else:
                location.msg_contents("[DEBUG] Reusing existing combat script.")
                return script

    location.msg_contents("[DEBUG] Creating new combat script...")
    combat = create_script("world.combathandler.CombatHandler", key=COMBAT_SCRIPT_KEY, obj=location)
    if combat:
        location.msg_contents("[DEBUG] Combat script successfully created.")
    else:
        location.msg_contents("[ERROR] Combat script creation failed.")
    return combat


class CombatHandler(DefaultScript):
    def at_script_creation(self):
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6
        self.persistent = True
        self.desc = "Handles room combat logic."
        self.db.combatants = []
        self.db.round = 1
        self.db.turn_index = 0

        if self.obj:
            self.obj.msg_contents("[DEBUG] CombatHandler created and attached to location.")

        self.start()

    def add_combatant(self, char):
        combatants = self.db.combatants or []
        if any(c["char"] == char for c in combatants):
            return
        initiative = randint(1, max(1, char.motorics))
        combatants.append({"char": char, "initiative": initiative})
        combatants.sort(key=lambda x: x["initiative"], reverse=True)
        self.db.combatants = combatants

        char.msg(f"|y[DEBUG] You enter combat. Initiative: {initiative}|n")

        if not self.is_active:
            self.start()

    def remove_combatant(self, char):
        self.db.combatants = [c for c in self.db.combatants if c["char"] != char]
        if not self.db.combatants:
            self.obj.msg_contents("[DEBUG] No combatants left. Ending combat.")
            self.stop()

    def at_repeat(self):
        location = self.obj
        if not location:
            return

        location.msg_contents("[DEBUG] at_repeat() tick triggered.")

        combatants = self.db.combatants or []
        if not combatants:
            location.msg_contents("[DEBUG] No combatants found. Stopping.")
            self.stop()
            return

        current_index = self.db.turn_index
        if current_index >= len(combatants):
            self.db.turn_index = 0
            self.db.round += 1
            location.msg_contents(f"[DEBUG] New round begins: Round {self.db.round}")
            return

        entry = combatants[current_index]
        attacker = entry["char"]
        if not attacker or not attacker.location == location:
            self.db.turn_index += 1
            return

        # Pick any valid target
        targets = [c["char"] for c in combatants if c["char"] != attacker and c["char"].location == location]
        if not targets:
            location.msg_contents("[DEBUG] No valid targets. Skipping turn.")
            self.db.turn_index += 1
            return

        target = targets[randint(0, len(targets) - 1)]
        atk_roll = randint(1, max(1, attacker.grit))
        def_roll = randint(1, max(1, target.motorics))

        location.msg_contents(f"{attacker.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")

        if atk_roll > def_roll:
            damage = attacker.grit
            target.hp = max(0, target.hp - damage)
            location.msg_contents(f"{target.key} is hit for {damage} damage. HP: {target.hp}/{target.hp_max}")
            if target.hp <= 0:
                location.msg_contents(f"{target.key} collapses!")
                target.at_death()
                self.remove_combatant(target)
        else:
            location.msg_contents(f"{attacker.key} misses.")

        self.db.turn_index += 1
