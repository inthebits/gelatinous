
from evennia import DefaultScript, create_script
from random import randint

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    script = next((s for s in location.scripts.all() if s.key == COMBAT_SCRIPT_KEY), None)
    if script and script.is_active:
        return script
    if script:
        script.stop()
    new_script = create_script("world.combathandler.CombatHandler", key=COMBAT_SCRIPT_KEY, obj=location)
    location.msg_contents("[DEBUG] CombatHandler created.")
    return new_script

class CombatHandler(DefaultScript):
    def at_script_creation(self):
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6
        self.persistent = True
        self.db.combatants = []
        self.db.round = 1
        delay(0.1, self.start)

    def at_start(self):
        self.obj.msg_contents("[DEBUG] CombatHandler started.")

    def at_stop(self):
        self.obj.msg_contents("[DEBUG] Combat ends.")
        for entry in self.db.combatants:
            char = entry["char"]
            if char.ndb.combat_handler:
                del char.ndb.combat_handler

    def add_combatant(self, char, target=None):
        if any(entry["char"] == char for entry in self.db.combatants):
            return

        initiative = randint(1, max(1, char.db.motorics or 1))
        self.db.combatants.append({
            "char": char,
            "initiative": initiative,
            "target": target
        })
        char.ndb.combat_handler = self
        self.obj.msg_contents(f"[DEBUG] {char.key} joins combat with initiative {initiative}.")

    def remove_combatant(self, char):
        self.db.combatants = [entry for entry in self.db.combatants if entry["char"] != char]
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
            self.obj.msg_contents("[DEBUG] Not enough combatants remain. Ending combat.")
            self.stop()
            return

        for entry in self.get_initiative_order():
            char = entry["char"]
            target = entry.get("target")

            if not target or target not in [e["char"] for e in self.db.combatants]:
                others = [e["char"] for e in self.db.combatants if e["char"] != char]
                if not others:
                    continue
                target = others[randint(0, len(others) - 1)]
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
        self.obj.msg_contents(f"[DEBUG] Combat round {self.db.round} scheduled.")
