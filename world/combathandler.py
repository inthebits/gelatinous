from evennia import create_script, DefaultScript
from random import randint

COMBAT_SCRIPT_KEY = "combat_handler"

def get_or_create_combat(location):
    """
    Get or create a CombatHandler script for the given location.
    """
    combat = None
    for script in location.scripts.all():
        if script.key == COMBAT_SCRIPT_KEY:
            combat = script
            break

    if not combat:
        combat = create_script(CombatHandler, key=COMBAT_SCRIPT_KEY, obj=location)
    return combat


class CombatHandler(DefaultScript):
    """
    A room-bound script that tracks combatants and turn order,
    auto-attacks on each tick based on initiative.
    """

    def at_script_creation(self):
        self.key = COMBAT_SCRIPT_KEY
        self.interval = 6  # seconds per round
        self.desc = "Handles room combat logic."
        self.persistent = True
        self.db.combatants = []  # list of {"char": obj, "initiative": int}
        self.db.round = 1
        self.db.turn_index = 0

    def add_combatant(self, char):
        """
        Add a character to combat and roll initiative.
        """
        combatants = self.db.combatants or []

        if any(c["char"] == char for c in combatants):
            return  # Already in combat

        init = randint(1, max(1, char.motorics))
        combatants.append({"char": char, "initiative": init})
        char.msg(f"|yYou enter combat. Initiative: {init}|n")

        # Sort by initiative
        self.db.combatants = sorted(combatants, key=lambda x: x["initiative"], reverse=True)

        if not self.is_active:
            self.start()

    def remove_combatant(self, char):
        """
        Remove a character from combat.
        """
        self.db.combatants = [c for c in self.db.combatants if c["char"] != char]

        if not self.db.combatants:
            self.stop()

    def at_repeat(self):
        """
        Called every combat round.
        Handles one combatant's turn per round.
        """
        combatants = self.db.combatants or []

        # Clean up invalid combatants
        combatants = [c for c in combatants if c["char"].location == self.obj and c["char"].hp > 0]
        self.db.combatants = combatants

        if not combatants:
            self.stop()
            return

        self.location.msg_contents(f"|c-- Round {self.db.round} --|n")

        turn_index = self.db.turn_index % len(combatants)
        actor_entry = combatants[turn_index]
        actor = actor_entry["char"]

        # Find valid targets (anyone else still standing)
        targets = [c["char"] for i, c in enumerate(combatants) if i != turn_index]
        if not targets:
            self.location.msg_contents(f"|y{actor.key} stands alone.|n")
            self.stop()
            return

        target = targets[randint(0, len(targets) - 1)]

        atk_roll = randint(1, max(1, actor.grit))
        def_roll = randint(1, max(1, target.motorics))

        self.location.msg_contents(f"{actor.key} attacks {target.key}!")
        actor.msg(f"(Attack Roll: {atk_roll} vs {def_roll})")

        if atk_roll > def_roll:
            damage = actor.grit
            target.hp -= damage
            self.location.msg_contents(f"|rHit! {actor.key} deals {damage} damage to {target.key}.|n")

            if target.hp <= 0:
                self.location.msg_contents(f"|R{target.key} collapses to the ground.|n")
                target.at_death()
                self.remove_combatant(target)
        else:
            self.location.msg_contents(f"{actor.key} misses {target.key}.")

        self.db.turn_index += 1
        self.db.round += 1

    def stop(self):
        self.location.msg_contents("|rCombat ends.|n")
        super().stop()
