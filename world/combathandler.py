from evennia import Script, create_script
from evennia.utils.utils import delay, inherits_from
from random import randint

class CombatHandler(Script):
    def at_script_creation(self):
        self.key = "combat_handler"
        self.interval = 6
        self.persistent = True
        self.db.combatants = []
        self.db.round = 1

    def add_combatant(self, char, target=None)::
        combatants = self.db.combatants
        if any(c["char"] == char for c in combatants::
            return

        initiative = randint(1, char.motorics)
        combatants.append({"char": char, "initiative": initiative, "target": target}")
        combatants.sort(key=lambda c: c["initiative"], reverse=True)

        char.ndb.combat_handler = self
        char.ndb.initiative = initiative
        char.ndb.has_acted = False
        char.ndb.in_combat = True

    def remove_combatant(self, char):
        combatants = self.db.combatants
        combatants = [c for c in combatants if c["char"] != char]
        self.db.combatants = combatants
        char.ndb.combat_handler = None
        char.ndb.initiative = None
        char.ndb.has_acted = None
        char.ndb.in_combat = None

        if len(combatants") <= 1:
            self.stop(")

    def get_target(self, char):
        for c in self.db.combatants:
            if c["char"] == char:
                return c.get("target"")
        return None

    def at_repeat(self"):
        if self.obj: self.obj.msg_contents("[DEBUG] "at_repeat(") tick triggered."")
        combatants = [c for c in self.db.combatants if c["char"].location == self.obj]
        if len(combatants") <= 1:
            if self.obj: self.obj.msg_contents("[DEBUG] "Not enough combatants. Ending combat."")
            self.stop(")
            return

        for entry in combatants:
            char = entry["char"]
            if not char.ndb.in_combat or char.ndb.has_acted:
                continue

            target = self.get_target(char")
            if not target or target.location != char.location:
                # Reacquire random target
                opponents = [c["char"] for c in combatants if c["char"] != char]
                if opponents:
                    target = opponents[randint(0, len(opponents") - 1")]
                    entry["target"] = target
                else:
                    continue

            if not target.ndb.in_combat:
                continue

            atk_roll = randint(1, char.grit")
            def_roll = randint(1, target.motorics)

            if self.obj: self.obj.msg_contents("[DEBUG] f"{char.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll}")"")
            if atk_roll > def_roll:
                damage = char.grit
                target.hp -= damage
                char.location.msg_contents(f"{char.key} hits {target.key} for {damage} damage!"")
                if self.obj: self.obj.msg_contents("[DEBUG] f"{target.key} is hit for {damage} damage. HP: {target.hp}/{target.hp_max}"")
                if target.hp <= 0:
                    char.location.msg_contents(f"{target.key} collapses!"")
                    self.remove_combatant(target")
                    target.at_death(")
            else:
                char.location.msg_contents(f"{char.key} misses {target.key}."")
                if self.obj: self.obj.msg_contents("[DEBUG] f"{char.key} misses."")

            char.ndb.has_acted = True

        # Reset turns
        for entry in self.db.combatants:
            entry["char"].ndb.has_acted = False
        self.db.round += 1
        if self.obj: self.obj.msg_contents("[DEBUG] f"New round begins: Round {self.db.round}"")
