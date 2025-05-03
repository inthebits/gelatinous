from evennia import DefaultScript, create_script
from random import randint
from evennia.utils.utils import delay


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


    def at_start(self):
        self.obj.msg_contents("[DEBUG] CombatHandler started.")

    def start(self):
        """
        Start the combat handler, but delay the first execution of at_repeat
        to ensure all combatants are added.
        """
        self.obj.msg_contents("[DEBUG] CombatHandler started.")
        delay(self.interval, self.at_repeat)  # Schedule the next execution

    def at_stop(self):
        self.obj.msg_contents("[DEBUG] Combat ends.")
        for entry in self.db.combatants:
            char = entry["char"]
            if char.ndb.combat_handler:
                del char.ndb.combat_handler

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
        self.obj.msg_contents(f"[DEBUG] {char.key} joins combat with initiative {initiative}.")
        self.obj.msg_contents(f"[DEBUG] {char.key} added to combat. Total combatants: {len(self.db.combatants)}.")

        # Mark as ready to start if there are at least two combatants
        if len(self.db.combatants) > 1:
            self.db.ready_to_start = True

        # Start the combat handler if ready and not already active
        if self.db.ready_to_start and not self.is_active:
            self.obj.msg_contents("[DEBUG] Enough combatants added. Starting combat.")
            self.start()

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
        self.obj.msg_contents(f"[DEBUG] Active combatants: {[e['char'].key for e in active_combatants]}.")

        # Ensure there are enough combatants to proceed
        if len(active_combatants) <= 1:
            self.obj.msg_contents("[DEBUG] Not enough combatants remain. Ending combat.")
            self.stop()
            return

        # Proceed with combat round logic
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

            atk_roll = randint(1, max(1, char.grit))
            def_roll = randint(1, max(1, target.motorics))

            self.obj.msg_contents(f"[DEBUG] {char.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")

            if atk_roll > def_roll:
                damage = char.grit or 1
                self.obj.msg_contents(f"[DEBUG] {char.key} hits {target.key} for {damage} damage.")
                target.take_damage(damage)
                if target.is_dead():
                    self.obj.msg_contents(f"[DEBUG] {target.key} has been defeated and removed from combat.")
                    self.remove_combatant(target)
            else:
                self.obj.msg_contents(f"{char.key} misses {target.key}.")

        self.db.round += 1
        self.obj.msg_contents(f"[DEBUG] Combat round {self.db.round} scheduled.")

        # Reschedule the next round
        self.start()
