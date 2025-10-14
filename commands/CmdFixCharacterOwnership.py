"""
Admin command to fix character ownership for get_all_puppets()
"""

from evennia import Command
from evennia.utils.search import search_object


class CmdFixCharacterOwnership(Command):
    """
    Fix character ownership so get_all_puppets() works.
    
    Usage:
        @fixchar <character name>
        @fixchar all
    
    This fixes characters created before the ownership fix by:
    - Setting char.db_account properly
    - Adding char to account.db._playable_characters list
    
    Use 'all' to fix all your characters.
    """
    
    key = "@fixchar"
    locks = "cmd:all()"
    help_category = "Admin"
    
    def func(self):
        caller = self.caller
        
        if not self.args:
            caller.msg("Usage: @fixchar <character name> or @fixchar all")
            return
        
        if self.args.strip().lower() == "all":
            # Fix all characters puppetable by this account
            from typeclasses.characters import Character
            all_chars = Character.objects.all()
            
            fixed_count = 0
            for char in all_chars:
                # Check if this account can puppet this character
                if char.access(caller, "puppet"):
                    # Fix ownership
                    char.db_account = caller
                    
                    if not caller.db._playable_characters:
                        caller.db._playable_characters = []
                    if char not in caller.db._playable_characters:
                        caller.db._playable_characters.append(char)
                        fixed_count += 1
                        caller.msg(f"|gFixed:|n {char.key}")
            
            caller.msg(f"|gFixed {fixed_count} character(s).|n")
            
            # Show verification
            all_puppets = caller.get_all_puppets()
            caller.msg(f"|yget_all_puppets() now returns {len(all_puppets)} character(s):|n")
            for char in all_puppets:
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
            if not char.access(caller, "puppet"):
                caller.msg(f"|rYou don't have permission to puppet {char.key}.|n")
                return
            
            # Fix ownership
            char.db_account = caller
            
            if not caller.db._playable_characters:
                caller.db._playable_characters = []
            
            if char in caller.db._playable_characters:
                caller.msg(f"|y{char.key} was already in _playable_characters.|n")
            else:
                caller.db._playable_characters.append(char)
                caller.msg(f"|gAdded {char.key} to _playable_characters.|n")
            
            # Verify
            all_puppets = caller.get_all_puppets()
            caller.msg(f"|gget_all_puppets() now returns {len(all_puppets)} character(s).|n")
