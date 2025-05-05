from evennia import DefaultScript
from evennia.utils.utils import delay
from random import randint
from world.combat_messages import get_combat_message

COMBAT_TICK_RATE = 2  # seconds per round

class CombatHandler(DefaultScript):
    def at_script_creation(self):
        self.key = "combat_handler"
        self.desc = "Handles round-based combat."
        self.interval = COMBAT_TICK_RATE
        self.persistent = True
        self.db.combatants = []
        self.db.initiative = []
        self.db.round = 0
        self.start()

    def add_combatant(self, char):
        if char not in self.db.combatants:
            self.db.combatants.append(char)
            self.db.initiative.append((char, self.roll_initiative(char)))
            self.db.initiative.sort(key=lambda x: x[1], reverse=True)

    def remove_combatant(self, char):
        self.db.combatants = [c for c in self.db.combatants if c != char]
        self.db.initiative = [entry for entry in self.db.initiative if entry[0] != char]
        if len(self.db.combatants) <= 1:
            self.stop()

    def is_in_combat(self, char):
        return char in self.db.combatants

    def roll_initiative(self, char):
        return randint(1, max(1, char.db.motorics or 1))

    def at_repeat(self):
        combatants = list(self.db.combatants)  # Copy so we can modify mid-loop
        if len(combatants) <= 1:
            self.obj.msg_contents("[DEBUG] Not enough combatants remaining. Ending combat.")
            self.stop()
            return

        self.db.round += 1
        self.obj.msg_contents(f"[DEBUG] --- Round {self.db.round} begins ---")

        for char, _ in self.db.initiative:
            if char not in self.db.combatants:
                continue

            target = self.get_target(char)
            if not target or target not in self.db.combatants:
                continue

            # Determine weapon and weapon_type
            weapon = None
            hands = getattr(char.db, "hands", {})
            for hand, item in hands.items():
                if item:
                    weapon = item
                    break
            weapon_type = weapon.db.weapon_type if weapon and hasattr(weapon.db, "weapon_type") else "unarmed"

            # Roll to hit
            atk_roll = randint(1, max(1, char.db.grit or 1))
            def_roll = randint(1, max(1, target.db.motorics or 1))
            self.obj.msg_contents(f"[DEBUG] {char.key} rolls {atk_roll} vs {target.key} who rolls {def_roll}")

            if atk_roll >= def_roll:
                damage = char.db.grit or 1
                target.db.hp = max(0, (target.db.hp or 0) - damage)

                if target.db.hp <= 0:
                    msg = get_combat_message(weapon_type, "kill", attacker=char, target=target, damage=damage)
                    target.at_death()
                else:
                    msg = get_combat_message(weapon_type, "hit", attacker=char, target=target, damage=damage)
                self.obj.msg_contents(msg)
            else:
                msg = get_combat_message(weapon_type, "miss", attacker=char, target=target)
                self.obj.msg_contents(msg)

    def get_target(self, char):
        # Default logic: target the first other combatant
        for other in self.db.combatants:
            if other != char:
                return other
        return None
