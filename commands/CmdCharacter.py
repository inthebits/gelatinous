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

        def line(text=""):
            return f"|g║ {text.ljust(50)} ║|n"

        string = "\n".join([
            "|g╔════════════════════════════════════════════════╗|n",
            "|g║ PSYCHOPHYSICAL EVALUATION REPORT               ║|n",
            line(f"Subject: {target.key}"),
            "|g║ File Reference: GEL-MST/PR-221A                ║|n",
            "|g╠════════════════════════════════════════════════╣|n",
            line(),
            line(f"Grit:       {grit}"),
            line(f"Resonance:  {resonance}"),
            line(f"Intellect:  {intellect}"),
            line(f"Motorics:   {motorics}"),
            line(),
            line(f"Vitals:     {vitals_display}"),
            line(),
            "|g╠════════════════════════════════════════════════╣|n",
            line("Notes:"),
            line(),
            line(),
            "|g╚════════════════════════════════════════════════╝|n"
        ])

        caller.msg(string)
