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

        # Fixed format to exactly 48 visible characters per row
        string = """|g╔════════════════════════════════════════════════╗|n
|g║ PSYCHOPHYSICAL EVALUATION REPORT               ║|n
|g║ Subject: {:<38}║|n
|g║ File Reference: GEL-MST/PR-221A                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║                                                ║|n
|g║         Grit:       {:>3}                       ║|n
|g║         Resonance:  {:>3}                       ║|n
|g║         Intellect:  {:>3}                       ║|n
|g║         Motorics:   {:>3}                       ║|n
|g║                                                ║|n
|g║         Vitals:     {:>7}                    ║|n
|g║                                                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║ Notes:                                         ║|n
|g║                                                ║|n
|g║                                                ║|n
|g╚════════════════════════════════════════════════╝|n""".format(
            target.key[:38],
            grit,
            resonance,
            intellect,
            motorics,
            vitals_display[:7],
        )

        caller.msg(string)
