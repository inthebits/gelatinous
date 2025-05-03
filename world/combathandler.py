from evennia import Script
from evennia.utils.utils import delay
import random

class CombatHandler(Script):
	def at_script_creation(self):
		self.key = "combat_handler"
		self.interval = 6
		self.persistent = True
		self.db.combatants = []
		self.db.round = 1

	def add_combatant(self, char, target=None, initiative=None):
		if any(c["char"] == char for c in self.db.combatants):
			return

		if initiative is None:
			initiative = random.randint(1, max(1, char.db.motorics or 1))

		if not target:
			others = [c["char"] for c in self.db.combatants if c["char"] != char]
			target = random.choice(others) if others else None

		self.db.combatants.append({
			"char": char,
			"initiative": initiative,
			"target": target
		})
		char.db.combat_handler = self

	def remove_combatant(self, char):
		self.db.combatants = [c for c in self.db.combatants if c["char"] != char]
		if char.db.combat_handler:
			del char.db.combat_handler
		if not self.db.combatants or len(self.db.combatants) <= 1:
			self.stop()

	def get_target(self, char):
		for combatant in self.db.combatants:
			if combatant["char"] == char:
				return combatant.get("target")
		return None

	def set_target(self, char, new_target):
		for combatant in self.db.combatants:
			if combatant["char"] == char:
				combatant["target"] = new_target
				break

	def get_initiative_order(self):
		return sorted(self.db.combatants, key=lambda c: c["initiative"], reverse=True)

	def at_repeat(self):
		self.obj.msg_contents("[DEBUG] at_repeat() tick triggered.")
		if len(self.db.combatants) <= 1:
			self.obj.msg_contents("[DEBUG] Not enough combatants. Ending combat.")
			self.stop()
			return

		self.db.round += 1
		order = self.get_initiative_order()

		for combatant in order:
			char = combatant["char"]
			target = combatant["target"]

			if not target or target not in [c["char"] for c in self.db.combatants]:
				others = [c["char"] for c in self.db.combatants if c["char"] != char]
				if not others:
					continue
				target = random.choice(others)
				self.set_target(char, target)

			if getattr(char.db, "skip_turn", False):
				char.db.skip_turn = False
				self.obj.msg_contents(f"[DEBUG] {char.key} skips their turn.")
				continue

			atk_roll = random.randint(1, max(1, char.db.grit or 1))
			def_roll = random.randint(1, max(1, target.db.motorics or 1))

			self.obj.msg_contents(f"{char.key} attacks {target.key} (atk:{atk_roll} vs def:{def_roll})")

			if atk_roll > def_roll:
				damage = char.db.grit or 1
				target.db.hp -= damage
				self.obj.msg_contents(f"{target.key} is hit for {damage} damage. HP: {target.db.hp}/{target.db.hp_max}")
				if target.db.hp <= 0:
					self.obj.msg_contents(f"{target.key} has been defeated!")
					self.remove_combatant(target)
					continue
			else:
				self.obj.msg_contents(f"{char.key} misses.")

		self.obj.msg_contents(f"[DEBUG] New round begins: Round {self.db.round}")

	def at_stop(self):
		self.obj.msg_contents("[DEBUG] Combat ends.")
		for combatant in self.db.combatants:
			if combatant["char"].db.combat_handler:
				del combatant["char"].db.combat_handler

def get_or_create_combat(location):
	combat = next((s for s in location.scripts.all() if s.key == "combat_handler"), None)
	if combat and (not combat.is_active or not combat.is_running):
		combat.stop()
		combat = None
	if not combat:
		combat = location.scripts.add(CombatHandler)
		location.msg_contents("[DEBUG] CombatHandler created and attached to location.")
	return combat
