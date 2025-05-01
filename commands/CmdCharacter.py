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
                matches = search_object(self.args.strip())
                if matches:
                    target = matches[0]

        grit = target.grit
        resonance = target.resonance
        intellect = target.intellect
        motorics = target.motorics
        hp = target.hp
        hp_max = target.hp_max
        vitals_display = f"{hp}/{hp_max}".rjust(5)

        string = """|g╔════════════════════════════════════════════════╗|n
|g║ PSYCHOPHYSICAL EVALUATION REPORT               ║|n
|g║ Subject: {:<38}║|n
|g║ File Reference: GEL-MST/PR-221A                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║                                                ║|n
|g║         Grit:       {:<28}║|n
|g║         Resonance:  {:<28}║|n
|g║         Intellect:  {:<28}║|n
|g║         Motorics:   {:<28}║|n
|g║                                                ║|n
|g║         Vitals:     {:<28}║|n
|g║                                                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║ Notes:                                         ║|n
|g║                                                ║|n
|g║                                                ║|n
|g╚════════════════════════════════════════════════╝|n""".format(
            target.key,
            grit,
            resonance,
            intellect,
            motorics,
            vitals_display,
        )

        caller.msg(string)
