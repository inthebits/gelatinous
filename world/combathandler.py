from evennia import DefaultScript
from random import randint

class CombatHandler(DefaultScript):
    def at_script_creation(self):
        self.key = "combat_handler"
        self.interval = 6  # seconds per round
        self.persistent = True
        self.db.combatants = []
        self.db.initiative_order = []
        self.db.round = 0

    @property
    def combatants(self):
        return self.db.combatants

    @property
    def initiative_order(self):
        return self.db.initiative_order

    @property
    def round(self):
        return self.db.round

    @round.setter
    def round(self, value):
        self.db.round = value

    def add_combatant(self, entity):
        if entity not in self.combatants:
            self.combatants.append(entity)
            entity.ndb.combat_handler = self
            initiative_roll = randint(1, entity.motorics)
            self.initiative_order.append((initiative_roll, entity))
            self.initiative_order.sort(reverse=True, key=lambda x: x[0])
            self.db.initiative_order = [e for _, e in self.initiative_order]
            entity.ndb.has_acted = False
            entity.location.msg_contents(
                f"|y[DEBUG] Adding {entity.key} to combat...|n"
            )

    def remove_combatant(self, entity):
        if entity in self.combatants:
            self.combatants.remove(entity)
        if entity in self.initiative_order:
            self.initiative_order.remove(entity)
        entity.ndb.combat_handler = None
        entity.ndb.has_acted = False
        entity.location.msg_contents(f"|y[DEBUG] Removing {entity.key} from combat.|n")
        if len(self.combatants) < 2:
            self.stop()

    def at_start(self):
        self.db.round = 0
        self.location.msg_contents("|y[DEBUG] Combat script successfully created.|n")

    def at_stop(self):
        for entity in self.combatants:
            entity.ndb.combat_handler = None
            entity.ndb.has_acted = False
        self.db.combatants = []
        self.db.initiative_order = []
        self.db.round = 0
        self.location.msg_contents("|y[DEBUG] Combat has ended.|n")

    def at_repeat(self):
        self.round += 1
        self.location.msg_contents(f"|y[DEBUG] New round begins: Round {self.round}|n")
        self.execute_round()

    def execute_round(self):
        for entity in self.initiative_order:
            if entity not in self.combatants:
                continue
            if not entity.ndb.has_acted:
                self.process_attack(entity)
                entity.ndb.has_acted = True
        for entity in self.combatants:
            entity.ndb.has_acted = False

    def process_attack(self, attacker):
        if not hasattr(attacker, "location"):
            return
        targets = [t for t in self.combatants if t != attacker and t.location == attacker.location]
        if not targets:
            attacker.location.msg_contents("|y[DEBUG] No valid targets. Skipping turn.|n")
            return

        target = targets[0]
        atk_roll = randint(1, attacker.grit)
        def_roll = randint(1, target.motorics)

        if atk_roll > def_roll:
            damage = attacker.grit
            target.hp = max(0, target.hp - damage)
            attacker.location.msg_contents(
                f"{attacker.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})\n"
                f"{target.key} is hit for {damage} damage. HP: {target.hp}/{target.hp_max}."
            )
            if target.hp <= 0:
                target.location.msg_contents(
                    f"|r{target.key} collapses!|n"
                )
                if hasattr(target, "at_death"):
                    target.at_death()
                self.remove_combatant(target)
        else:
            attacker.location.msg_contents(
                f"{attacker.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})\n"
                f"{attacker.key} misses."
            )