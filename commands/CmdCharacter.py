from evennia import Command
from evennia.utils.search import search_object

class CmdStats(Command):
    """
    View your character's stats, or inspect another character if you're a Builder+.

    Usage:
      @stats
      @stats <target>  (Builder or Developer only)

    Displays your G.R.I.M. attributes and any future derived stats.
    """

    key = "@stats"
    aliases = ["score"]
    locks = "cmd:all()"

    def func(self):
        "Implement the command."

        caller = self.caller
        target = caller

        if self.args:
            if (
                self.account.check_permstring("Builder")
                or self.account.check_permstring("Developer")
            ):
                matches = search_object(self.args.strip(), exact=False)
                if matches:
                    target = matches[0]

        grit = target.grit
        resonance = target.resonance
        intellect = target.intellect
        motorics = target.motorics
        hp = target.hp
        hp_max = target.hp_max
        vitals_display = f"{hp}/{hp_max}"

        name_display = f"Subject: {target.key}".ljust(48)
        grit_line = f"         Grit:       {grit}".ljust(48)
        resonance_line = f"         Resonance:  {resonance}".ljust(48)
        intellect_line = f"         Intellect:  {intellect}".ljust(48)
        motorics_line = f"         Motorics:   {motorics}".ljust(48)
        vitals_line = f"         Vitals:     {vitals_display}".ljust(48)

        string = f"""|g╔════════════════════════════════════════════════╗|n
|g║ PSYCHOPHYSICAL EVALUATION REPORT               ║|n
|g║ {name_display} ║|n
|g║ File Reference: GEL-MST/PR-221A                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║ {grit_line} ║|n
|g║ {resonance_line} ║|n
|g║ {intellect_line} ║|n
|g║ {motorics_line} ║|n
|g║                                                ║|n
|g║ {vitals_line} ║|n
|g║                                                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║ Notes:                                         ║|n
|g║                                                ║|n
|g║                                                ║|n
|g╚════════════════════════════════════════════════╝|n"""

        caller.msg(string)
