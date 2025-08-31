"""
Character Skintone System

Allows players and staff to set character skintones using xterm256 colors
to provide visual distinction between character longdescs and clothing descriptions.
"""

from evennia import Command
from evennia.utils.search import search_object
from world.combat.constants import SKINTONE_PALETTE, VALID_SKINTONES


class CmdSkintone(Command):
    """
    Set your character's skintone for longdesc display coloring.

    Usage:
      @skintone <tone>
      @skintone list
      @skintone clear
      @skintone <character> <tone>    (staff only)
      @skintone <character> clear     (staff only)

    Sets the color tone used for your character's longdesc descriptions.
    This creates visual distinction between your character's body/skin
    descriptions and clothing descriptions.

    Available tones:
      Goth/Pale: porcelain, ivory, ash, cool, warm
      Natural: fair, light, medium, olive, tan, brown, dark, deep

    Examples:
      @skintone ivory
      @skintone tan
      @skintone list
      @skintone clear
    """
    
    key = "@skintone"
    aliases = ["skintone"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            self._show_current_skintone(caller)
            return
            
        # Handle list command
        if args.lower() == "list":
            self._show_available_tones(caller)
            return
            
        # Handle clear command
        if args.lower() == "clear":
            self._clear_skintone(caller, caller)
            return
            
        # Check if this might be staff targeting another character
        parts = args.split()
        if len(parts) == 2 and caller.locks.check_lockstring(caller, "perm(Builder)"):
            character_name, tone_or_clear = parts
            target = self._find_character(caller, character_name)
            if target:
                if tone_or_clear.lower() == "clear":
                    self._clear_skintone(caller, target)
                else:
                    self._set_skintone(caller, target, tone_or_clear.lower())
                return
            else:
                caller.msg(f"Could not find character '{character_name}'.")
                return
        
        # Single argument - set skintone on self
        tone = args.lower()
        self._set_skintone(caller, caller, tone)

    def _show_current_skintone(self, caller):
        """Show the caller's current skintone setting"""
        skintone = getattr(caller.db, 'skintone', None)
        if skintone:
            color_code = SKINTONE_PALETTE.get(skintone, "")
            if color_code:
                colored_preview = f"|{color_code}Sample longdesc text in {skintone} tone|n"
                caller.msg(f"Your current skintone is: {skintone}")
                caller.msg(f"Preview: {colored_preview}")
            else:
                caller.msg(f"Your current skintone is: {skintone} (invalid)")
        else:
            caller.msg("You have no skintone set. Longdescs will appear uncolored.")
            
    def _show_available_tones(self, caller):
        """Display available skintones with previews"""
        caller.msg("|wAvailable Skintones:|n")
        caller.msg("")
        
        # Goth/Pale section
        caller.msg("|cGoth/Pale Spectrum:|n")
        goth_tones = ["porcelain", "ivory", "ash", "cool", "warm"]
        for tone in goth_tones:
            color_code = SKINTONE_PALETTE[tone]
            preview = f"{color_code}Sample text|n"
            caller.msg(f"  {tone:<10} - {preview}")
        
        caller.msg("")
        
        # Natural section  
        caller.msg("|yNatural Range:|n")
        natural_tones = ["fair", "light", "medium", "olive", "tan", "brown", "dark", "deep"]
        for tone in natural_tones:
            color_code = SKINTONE_PALETTE[tone]
            preview = f"{color_code}Sample text|n"
            caller.msg(f"  {tone:<10} - {preview}")
            
        caller.msg("")
        caller.msg("Use: |w@skintone <tone>|n to set your skintone")
        caller.msg("Use: |w@skintone clear|n to remove coloring")

    def _set_skintone(self, caller, target, tone):
        """Set skintone on target character"""
        if tone not in VALID_SKINTONES:
            caller.msg(f"'{tone}' is not a valid skintone. Use '@skintone list' to see available options.")
            return
            
        target.db.skintone = tone
        color_code = SKINTONE_PALETTE[tone]
        preview = f"|{color_code}Sample longdesc text|n"
        
        if target == caller:
            caller.msg(f"Set your skintone to: {tone}")
            caller.msg(f"Preview: {preview}")
        else:
            caller.msg(f"Set {target.name}'s skintone to: {tone}")
            caller.msg(f"Preview: {preview}")
            target.msg(f"{caller.name} has set your skintone to: {tone}")

    def _clear_skintone(self, caller, target):
        """Clear skintone from target character"""
        if hasattr(target.db, 'skintone'):
            del target.db.skintone
            
        if target == caller:
            caller.msg("Cleared your skintone. Longdescs will appear uncolored.")
        else:
            caller.msg(f"Cleared {target.name}'s skintone.")
            target.msg(f"{caller.name} has cleared your skintone setting.")

    def _find_character(self, caller, character_name):
        """Find a character by name for staff targeting"""
        # Use Evennia's search system to find the character
        results = search_object(character_name, typeclass="typeclasses.characters.Character")
        
        if not results:
            return None
        elif len(results) > 1:
            # Multiple matches - try to find exact match
            exact_matches = [obj for obj in results if obj.name.lower() == character_name.lower()]
            if len(exact_matches) == 1:
                return exact_matches[0]
            else:
                caller.msg(f"Multiple characters match '{character_name}': {', '.join(obj.name for obj in results)}")
                return None
        else:
            return results[0]
