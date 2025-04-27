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
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        "Implement the command."

        caller = self.caller

        grit = caller.grit
        resonance = caller.resonance
        intellect = caller.intellect
        motorics = caller.motorics

        string = """
|b==============================================================|n
|g{} SYSTEM SCAN - SUBJECT FILE|n
|b==============================================================|n
  |wGrit     |n : {}
  |wResonance|n : {}
  |wIntellect|n : {}
  |wMotorics |n : {}

|b==============================================================|n
""".format(
            caller.key,
            grit,
            resonance,
            intellect,
            motorics
        )

        caller.msg(string)
