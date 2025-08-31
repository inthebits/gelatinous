"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""


from evennia import default_cmds
from commands import CmdCharacter
from commands import CmdInventory
from commands import CmdAdmin
from commands import CmdClothing
from commands.CmdSpawnMob import CmdSpawnMob
from commands.CmdAdmin import CmdHeal, CmdPeace, CmdTestDeathCurtain, CmdWeather
from commands.combat.cmdset_combat import CombatCmdSet
from commands.combat.special_actions import CmdAim, CmdGrapple
from commands.CmdThrow import CmdThrow, CmdPull, CmdCatch, CmdRig, CmdDefuse
from commands.CmdGraffiti import CmdGraffiti, CmdPress
from commands.CmdCharacter import CmdLongdesc
from commands.CmdSkintone import CmdSkintone
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        # Add individual character commands
        self.add(CmdCharacter.CmdStats)
        self.add(CmdSpawnMob())
        self.add(CmdAdmin.CmdHeal())
        self.add(CmdAdmin.CmdPeace())
        self.add(CmdAdmin.CmdTestDeathCurtain())
        self.add(CmdWeather())
        
        # Add aim command for ranged combat preparation
        self.add(CmdAim())
        
        # Add grapple command for initiating grappling combat
        self.add(CmdGrapple())
        
        # Add the entire combat command set
        self.add(CombatCmdSet)
        
        # Add inventory commands
        self.add(CmdInventory.CmdWield())
        self.add(CmdInventory.CmdUnwield())
        self.add(CmdInventory.CmdFreeHands())
        self.add(CmdInventory.CmdInventory())
        self.add(CmdInventory.CmdDrop())
        self.add(CmdInventory.CmdGet())
        self.add(CmdInventory.CmdGive())
        
        # Add wrest command (non-combat item snatching)
        self.add(CmdInventory.CmdWrest())
        
        # Add throw command system
        self.add(CmdThrow())
        self.add(CmdPull())
        self.add(CmdCatch())
        self.add(CmdRig())
        self.add(CmdDefuse())
        
        # Add character placement commands
        self.add(CmdCharacter.CmdLookPlace())
        self.add(CmdCharacter.CmdTempPlace())
        
        # Add graffiti system commands
        self.add(CmdGraffiti())
        self.add(CmdPress())
        
        # Add longdesc system command
        self.add(CmdLongdesc())
        
        # Add skintone system command
        self.add(CmdSkintone())
        
        # Add clothing system commands
        self.add(CmdClothing.CmdWear())
        self.add(CmdClothing.CmdRemove())
        self.add(CmdClothing.CmdRollUp())
        self.add(CmdClothing.CmdZip())

class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #

