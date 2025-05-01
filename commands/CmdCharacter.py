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
        vitals_display = f"{target.hp}/{target.hp_max}"

        # Helper to format internal lines to exactly 48 visible characters
        def fixed_line(label, value):
            line = f"        {label:<12}{str(value)}"
            return line + (" " * (48 - len(line)))

        # Box output
        string = f"""|g╔════════════════════════════════════════════════╗|n
|g║ PSYCHOPHYSICAL EVALUATION REPORT               ║|n
|g║ Subject: {target.key[:38].ljust(38)}║|n
|g║ File Reference: GEL-MST/PR-221A                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║ {fixed_line('', '')} ║|n
|g║ {fixed_line('Grit:', grit)} ║|n
|g║ {fixed_line('Resonance:', resonance)} ║|n
|g║ {fixed_line('Intellect:', intellect)} ║|n
|g║ {fixed_line('Motorics:', motorics)} ║|n
|g║ {fixed_line('', '')} ║|n
|g║ {fixed_line('Vitals:', vitals_display)} ║|n
|g║ {fixed_line('', '')} ║|n
|g╠════════════════════════════════════════════════╣|n
|g║ Notes:                                         ║|n
|g║                                                ║|n
|g║                                                ║|n
|g╚════════════════════════════════════════════════╝|n"""

        caller.msg(string)
