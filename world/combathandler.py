
from evennia import DefaultScript
from evennia.utils.utils import delay
from random import randint

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    script = next((s for s in location.scripts.all() if s.key == COMBAT_SCRIPT_KEY), None)
    if script and script.is_active:
        return script
    if script:
        script.stop()
    return location.scripts.add(CombatHandler)

class CombatHandler(DefaultScript):
    def at_script_creation(self):
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6
        self.persistent = True
        self.desc = "Handles room combat logic."
        self.db.combatants = []
        self.db.round = 1
        self.db.turn_index = 0
        self.db.active = False  # not active until combat starts

        if self.obj:
            self.obj.msg_contents("[DEBUG] CombatHandler initialized.")

    def start(self):
        if not self.db.active:
            self.db.active = True
            self.db.round = 1
            self.db.turn_index = 0
            super().start()
            self.obj.msg_contents("[DEBUG] CombatHandler started.")

    def at_stop(self):
        self.obj.msg_contents("[DEBUG] CombatHandler stopped.")
        for entry in self.db.combatants:
            entry["char"].ndb.combat_handler = None

    def add_combatant(self, char, target=None):
        if any(entry["char"] == char for entry in self.db.combatants):
            return

        initiative = randint(1, max(1, char.db.motorics or 1))
        self.db.combatants.append({"char": char, "initiative": initiative, "target": target})
        char.ndb.combat_handler = self
        self.obj.msg_contents(f"[DEBUG] {char.key} joins combat with initiative {initiative}.")

        if len(self.db.combatants) >= 2 and not self.db.active:
            self.start()

    def remove_combatant(self, char):
        self.db.combatants = [e for e in self.db.combatants if e["char"] != char]
        if char.ndb.combat_handler:
            del char.ndb.combat_handler
        self.obj.msg_contents(f"[DEBUG] {char.key} removed from combat.")
        if len(self.db.combatants) <= 1:
            self.stop()

    def get_target(self, char):
        for entry in self.db.combatants:
            if entry["char"] == char:
                return entry.get("target")
        return None

    def set_target(self, char, target):
        for entry in self.db.combatants:
            if entry["char"] == char:
                entry["target"] = target

    def get_initiative_order(self):
        return sorted(self.db.combatants, key=lambda e: e["initiative"], reverse=True)

    def at_repeat(self):
        self.obj.msg_contents(f"[DEBUG] Combat round {self.db.round} begins.")

        active_combatants = [e for e in self.db.combatants if e["char"].location == self.obj]
        if len(active_combatants) <= 1:
            self.obj.msg_contents("[DEBUG] Not enough combatants. Ending combat.")
            self.stop()
            return

        for entry in self.get_initiative_order():
            char = entry["char"]
            target = entry.get("target")

            if not target or target not in [e["char"] for e in self.db.combatants]:
                others = [e["char"] for e in self.db.combatants if e["char"] != char]
                if others:
                    target = others[0]
                    self.set_target(char, target)

            if not target:
                continue

            atk_roll = randint(1, max(1, char.db.grit or 1))
            def_roll = randint(1, max(1, target.db.motorics or 1))

            self.obj.msg_contents(f"[DEBUG] {char.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")

            if atk_roll > def_roll:
                damage = char.db.grit or 1
                target.db.hp = max(0, target.db.hp - damage)
                self.obj.msg_contents(f"{char.key} hits {target.key} for {damage} damage! HP: {target.db.hp}/{target.db.hp_max}")
                if target.db.hp <= 0:
                    self.obj.msg_contents(f"{target.key} has been defeated!")
                    self.remove_combatant(target)
                    if hasattr(target, "at_death"):
                        target.at_death()
            else:
                self.obj.msg_contents(f"{char.key} misses {target.key}.")

        self.db.round += 1
