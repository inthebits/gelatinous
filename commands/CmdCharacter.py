from evennia import Command
from evennia.utils.search import search_object
from world.combat.constants import (
    PERM_BUILDER, PERM_DEVELOPER,
    BOX_TOP_LEFT, BOX_TOP_RIGHT, BOX_BOTTOM_LEFT, BOX_BOTTOM_RIGHT,
    BOX_HORIZONTAL, BOX_VERTICAL, BOX_TEE_DOWN, BOX_TEE_UP,
    COLOR_SUCCESS, COLOR_NORMAL
)

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
                self.account.check_permstring(PERM_BUILDER)
                or self.account.check_permstring(PERM_DEVELOPER)
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
        string = f"""{COLOR_SUCCESS}{BOX_TOP_LEFT}{BOX_HORIZONTAL * 48}{BOX_TOP_RIGHT}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} PSYCHOPHYSICAL EVALUATION REPORT               {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} Subject: {target.key[:38]:<38}{BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} File Reference: GEL-MST/PR-221A                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_TEE_DOWN}{BOX_HORIZONTAL * 48}{BOX_TEE_UP}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Grit:       {grit:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Resonance:  {resonance:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Intellect:  {intellect:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Motorics:   {motorics:>3}                        {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}         Vitals:     {vitals_display[:7]:>7}                    {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_TEE_DOWN}{BOX_HORIZONTAL * 48}{BOX_TEE_UP}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL} Notes:                                         {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_VERTICAL}                                                {BOX_VERTICAL}{COLOR_NORMAL}
{COLOR_SUCCESS}{BOX_BOTTOM_LEFT}{BOX_HORIZONTAL * 48}{BOX_BOTTOM_RIGHT}{COLOR_NORMAL}"""

        caller.msg(string)
