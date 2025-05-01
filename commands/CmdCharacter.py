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
        vitals_display = f"{hp}/{hp_max}".rjust(5)

        def boxed_line(label="", value=""):
            # creates a padded stat line with perfect alignment
            label_fmt = f"{label:<16}"  # left-align label
            value_fmt = f"{str(value):>2}"  # right-align value
            return f"|g║   {label_fmt}{value_fmt}{' ' * (48 - (len(label_fmt) + 2))}║|n"

        def plain_line(text=""):
            return f"|g║ {text.ljust(48)} ║|n"

        string = "\n".join([
            "|g╔════════════════════════════════════════════════╗|n",
            "|g║ PSYCHOPHYSICAL EVALUATION REPORT               ║|n",
            plain_line(f"Subject: {target.key[:42]}"),
            "|g║ File Reference: GEL-MST/PR-221A                ║|n",
            "|g╠════════════════════════════════════════════════╣|n",
            plain_line(),
            boxed_line("Grit:", grit),
            boxed_line("Resonance:", resonance),
            boxed_line("Intellect:", intellect),
            boxed_line("Motorics:", motorics),
            plain_line(),
            boxed_line("Vitals:", vitals_display),
            plain_line(),
            "|g╠════════════════════════════════════════════════╣|n",
            plain_line("Notes:"),
            plain_line(),
            plain_line(),
            "|g╚════════════════════════════════════════════════╝|n"
        ])

        caller.msg(string)
