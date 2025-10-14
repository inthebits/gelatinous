"""
One-time admin command to repair legacy character ownership.

This fixes characters created with the old broken manual method by properly
establishing Evennia's internal ownership relationships using the account's
internal _add_character method.

This command will be obsolete once all legacy characters are fixed.
"""

from evennia import Command
from evennia.utils.search import search_object


class CmdFixCharacterOwnership(Command):
    """
    ONE-TIME FIX for legacy character ownership.
    
    Usage:
        @fixchar <character name>
        @fixchar all
    
    This repairs characters created before we switched to account.create_character()
    by using Evennia's internal character tracking methods.
    
    Legacy characters were created with manual setup and don't appear in
    get_all_puppets(). This command fixes that.
    
    Use 'all' to fix all characters you can puppet.
    """
    
    key = "@fixchar"
    locks = "cmd:all()"
    help_category = "Admin"
    
    def func(self):
        caller = self.caller
        
        # Get the account - caller might be a Character, we need the Account
        if hasattr(caller, 'account'):
            account = caller.account
        else:
            account = caller
        
        if not self.args:
            caller.msg("Usage: @fixchar <character name> or @fixchar all")
            return
        
        if self.args.strip().lower() == "all":
            # Fix all characters puppetable by this account
            from typeclasses.characters import Character
            all_chars = Character.objects.all()
            
            fixed_count = 0
            for char in all_chars:
                # Check if this account can puppet this character AND it's not already in playable list
                if char.access(account, "puppet") and char not in account.characters:
                    # Use Evennia's CharactersHandler to add character
                    try:
                        account.characters.add(char)
                        fixed_count += 1
                        caller.msg(f"|gFixed:|n {char.key} (#{char.id})")
                    except Exception as e:
                        caller.msg(f"|rError fixing {char.key}:|n {e}")
            
            if fixed_count == 0:
                caller.msg("|yNo characters needed fixing.|n")
            else:
                caller.msg(f"|gFixed {fixed_count} character(s).|n")
            
            # Show verification
            all_playable = account.characters.all()
            caller.msg(f"|yaccount.characters now returns {len(all_playable)} character(s):|n")
            for char in all_playable:
                caller.msg(f"  - {char.key} (#{char.id})")
            
        else:
            # Fix specific character
            char_name = self.args.strip()
            results = search_object(char_name, typeclass="typeclasses.characters.Character")
            
            if not results:
                caller.msg(f"|rNo character found with name '{char_name}'.|n")
                return
            
            if len(results) > 1:
                caller.msg(f"|rMultiple matches:|n")
                for char in results:
                    caller.msg(f"  - {char.key} (#{char.id})")
                caller.msg("|yPlease be more specific.|n")
                return
            
            char = results[0]
            
            # Check puppet access
            if not char.access(account, "puppet"):
                caller.msg(f"|rYou don't have permission to puppet {char.key}.|n")
                return
            
            # Check if already tracked
            if char in account.characters:
                caller.msg(f"|y{char.key} is already in account.characters list.|n")
                return
            
            # Use Evennia's CharactersHandler to properly add the character
            try:
                account.characters.add(char)
                caller.msg(f"|gFixed {char.key} - added to playable characters.|n")
            except Exception as e:
                caller.msg(f"|rError fixing {char.key}:|n {e}")
                return
            
            # Verify
            all_playable = account.characters.all()
            caller.msg(f"|yaccount.characters now returns {len(all_playable)} character(s):|n")
            for char in all_playable:
                caller.msg(f"  - {char.key} (#{char.id})")
