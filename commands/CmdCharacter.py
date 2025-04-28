from evennia import Command

class CmdStats(Command):
    """
    View your character's stats.

    Usage:
      @stats
      score

    Displays your G.R.I.M. attributes and any future derived stats.
    """

    key = "@stats"
    aliases = ["score"]

    def func(self):
        "Implement the command."

        caller = self.caller

        grit = caller.grit
        resonance = caller.resonance
        intellect = caller.intellect
        motorics = caller.motorics
        hp = caller.hp
        hp_max = caller.hp_max
        vitals_display = f"{hp}/{hp_max}".rjust(5)
        


        string = """|g╔════════════════════════════════════════════════╗|n
|g║ PSYCHOPHYSICAL EVALUATION REPORT               ║|n
|g║ Subject ID: [########]                         ║|n
|g║ File Reference: GEL-MST/PR-221A                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║                                                ║|n
|g║         Grit:       {}                          ║|n
|g║         Resonance:  {}                          ║|n
|g║         Intellect:  {}                          ║|n
|g║         Motorics:   {}                          ║|n
|g║                                                ║|n
|g║         Vitals:     {}                     ║|n
|g║                                                ║|n
|g╠════════════════════════════════════════════════╣|n
|g║ Notes:                                         ║|n
|g║                                                ║|n
|g║                                                ║|n
|g╚════════════════════════════════════════════════╝|n""".format(
            grit,
            resonance,
            intellect,
            motorics,
            vitals_display,
        )

        caller.msg(string)
