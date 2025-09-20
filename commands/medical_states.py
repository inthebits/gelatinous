"""
Medical State Command Sets

This module provides complete command set replacements for different medical states.
Instead of merging or modifying existing commands, we completely replace the default
command set with medical-state-appropriate versions using Evennia's cmdset.add_default()
and cmdset.remove_default() methods.
"""

from evennia import CmdSet, default_cmds


class UnconsciousCmdSet(CmdSet):
    """
    Command set for unconscious characters.
    Only allows minimal OOC commands - no perception, movement, or actions.
    """
    key = "unconscious_cmdset"
    priority = 0  # Same as normal CharacterCmdSet since this replaces it entirely
    no_exits = True  # Prevent exit traversal when unconscious
    
    def at_cmdset_creation(self):
        """
        Add only commands that unconscious characters should be able to use.
        Unconscious = no perception, no movement, no actions.
        """
        # Essential OOC commands only
        self.add(default_cmds.CmdHelp())      # Always allow help
        self.add(default_cmds.CmdWho())       # OOC player information
        self.add(default_cmds.CmdTime())      # OOC time information
        
        # System commands
        self.add(default_cmds.CmdQuit())      # Can always quit
        
        # Staff commands (will be filtered by permissions anyway)
        self.add(default_cmds.CmdPy())        # Staff debugging
        self.add(default_cmds.CmdReload())    # Staff server management
        
        # NO look, NO movement, NO actions when unconscious


class DeathCmdSet(CmdSet):
    """
    Command set for dead characters.
    Only allows minimal OOC commands - no perception, no movement, no actions.
    """
    key = "death_cmdset"
    priority = 0  # Same as normal CharacterCmdSet since this replaces it entirely
    no_exits = True  # Prevent exit traversal when dead
    
    def at_cmdset_creation(self):
        """
        Add only commands that dead characters should be able to use.
        Dead = no perception, no movement, no actions, minimal OOC only.
        """
        # Very minimal set - OOC information only
        self.add(default_cmds.CmdHelp())      # Always allow help
        self.add(default_cmds.CmdWho())       # OOC player information
        self.add(default_cmds.CmdQuit())      # Can always quit
        
        # Staff commands (will be filtered by permissions anyway)
        self.add(default_cmds.CmdPy())        # Staff debugging
        self.add(default_cmds.CmdReload())    # Staff server management
        
        # NO look, NO time, NO movement, NO actions when dead