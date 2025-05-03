
from evennia import DefaultScript
from random import randint

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    # Remove broken scripts
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            if not script.is_active:
                location.msg_contents("[DEBUG] Removing broken combat script...")
                script.stop()
                script.delete()
            else:
                return script

    # Correct usage: reference by string path
    location.msg_contents("[DEBUG] Creating new combat script...")
    from evennia import create_script
    combat = create_script("world.combathandler.CombatHandler", key=COMBAT_SCRIPT_KEY, obj=location)
    return combat


class CombatHandler(DefaultScript):
    def at_script_creation(self):
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6
        self.desc = "Handles room combat logic."
        self.persistent = True
        self.db.combatants = []
        self.db.round = 1
        self.db.turn_index = 0
        if self.obj:
            self.obj.msg_contents("[DEBUG] at_script_creation() was called.")

    def add_combatant(self, char):
        combatants = self.db.combatants or []
        if any(c["char"] == char for c in combatants):
            return
        init = randint(1, max(1, char.motorics))
        combatants.append({ "char": char, "initiative": init })
        self.db.combatants = sorted(combatants, key=lambda x: x["initiative"], reverse=True)
        char.msg(f"|yYou enter combat. Initiative: {init}|n")
        if not self.is_active:
            self.start()

    def remove_combatant(self, char):
        self.db.combatants = [c for c in self.db.combatants if c["char"] != char]
        if not self.db.combatants:
            self.stop()

    def at_repeat(self):
        self.obj.msg_contents("[DEBUG] at_repeat() tick fired")
        self.db.combatants = [
            c for c in self.db.combatants
            if c["char"].location == self.obj and c["char"].hp > 0
        ]
        combatants = self.db.combatants
        if not combatants:
            self.stop()
            return
        if self.db.turn_index >= len(combatants):
            self.db.turn_index = 0
        self.obj.msg_contents(f"|c-- Round {self.db.round} --|n")
        try:
            actor_entry = combatants[self.db.turn_index]
            actor = actor_entry["char"]
            self.obj.msg_contents(f"[DEBUG] Turn index {self.db.turn_index} | Actor: {actor.key}")
            targets = [c["char"] for i, c in enumerate(combatants) if i != self.db.turn_index]
            if not targets:
                self.obj.msg_contents(f"|y{actor.key} stands alone.|n")
                self.stop()
                return
            target = targets[randint(0, len(targets) - 1)]
            atk_roll = randint(1, max(1, actor.grit))
            def_roll = randint(1, max(1, target.motorics))
            self.obj.msg_contents(f"{actor.key} attacks {target.key}!")
            actor.msg(f"(Attack Roll: {atk_roll} vs {def_roll})")
            if atk_roll > def_roll:
                dmg = actor.grit
                target.hp -= dmg
                self.obj.msg_contents(f"|rHit! {actor.key} deals {dmg} damage to {target.key}.|n")
                if target.hp <= 0:
                    self.obj.msg_contents(f"|R{target.key} collapses.|n")
                    target.at_death()
                    self.remove_combatant(target)
            else:
                self.obj.msg_contents(f"{actor.key} misses {target.key}.")
        except Exception as e:
            self.obj.msg_contents(f"[ERROR] Turn failed: {e}")
        self.db.turn_index += 1
        self.db.round += 1

    def stop(self):
        self.obj.msg_contents("|rCombat ends.|n")
        super().stop()
