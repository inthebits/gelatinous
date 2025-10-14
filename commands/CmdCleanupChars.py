"""
Character cleanup and inspection commands for dealing with legacy/test data.

This module provides admin commands to inspect and clean up character states,
particularly useful after testing character creation/death systems.
"""

from evennia import Command
from evennia.utils.search import search_object


class CmdInspectChars(Command):
    """
    Inspect all characters for an account, showing their states.
    
    Usage:
        @inspect_chars <account_name>
        @inspect_chars
    
    Shows detailed information about all characters linked to an account,
    including their archived status, location, and key attributes. If no
    account name is provided, inspects your own account.
    
    Useful for debugging character creation/death issues and identifying
    orphaned or corrupted character data.
    """
    
    key = "@inspect_chars"
    locks = "cmd:perm(Builder)"
    help_category = "Admin"
    
    def func(self):
        from typeclasses.characters import Character
        
        # Determine target account
        if self.args.strip():
            # Search for specified account
            account_name = self.args.strip()
            from evennia.accounts.models import AccountDB
            try:
                target_account = AccountDB.objects.get(username__iexact=account_name)
            except AccountDB.DoesNotExist:
                self.caller.msg(f"Account '{account_name}' not found.")
                return
        else:
            # Use caller's account
            target_account = self.caller.account
        
        # Get all characters for account
        all_chars = Character.objects.filter(db_account=target_account)
        
        if not all_chars:
            self.caller.msg(f"Account '{target_account.key}' has no characters.")
            return
        
        self.caller.msg(f"\n|wCharacter Inspection for Account: {target_account.key}|n")
        self.caller.msg("-" * 70)
        
        for char in all_chars:
            # Gather character info
            char_id = char.id
            char_key = char.key
            location = char.location.key if char.location else "None/Void"
            
            # Check various attributes
            archived = getattr(char.db, 'archived', None)
            archived_reason = getattr(char.db, 'archived_reason', None)
            clone_generation = getattr(char.db, 'clone_generation', None)
            death_count = getattr(char.db, 'death_count', None)
            stack_id = getattr(char.db, 'stack_id', None)
            
            # Display character info
            self.caller.msg(f"\n|cCharacter:|n {char_key} (#{char_id})")
            self.caller.msg(f"  Location: {location}")
            self.caller.msg(f"  Archived: {archived} {f'({archived_reason})' if archived_reason else ''}")
            self.caller.msg(f"  Clone Generation: {clone_generation}")
            self.caller.msg(f"  Death Count: {death_count}")
            self.caller.msg(f"  Stack ID: {stack_id}")
            
            # Show status summary
            if archived is True:
                status = "|rARCHIVED|n"
            elif archived is None:
                status = "|yLEGACY (no archived attribute)|n"
            else:
                status = "|gACTIVE|n"
            self.caller.msg(f"  Status: {status}")
        
        self.caller.msg("\n" + "-" * 70)
        self.caller.msg(f"Total characters: {len(all_chars)}")


class CmdArchiveChar(Command):
    """
    Manually archive a character (mark as inactive).
    
    Usage:
        @archive_char <character_name> [reason]
    
    Marks a character as archived, removing them from active character lists.
    The character is not deleted, but will not appear in character selection
    menus and will be treated as inactive.
    
    Example:
        @archive_char Laszlo "test character"
        @archive_char "Laszlo II" testing
    """
    
    key = "@archive_char"
    locks = "cmd:perm(Builder)"
    help_category = "Admin"
    
    def func(self):
        if not self.args.strip():
            self.caller.msg("Usage: @archive_char <character_name> [reason]")
            return
        
        # Parse character name and optional reason
        parts = self.args.strip().split(None, 1)
        char_name = parts[0]
        reason = parts[1] if len(parts) > 1 else "manual archive"
        
        # Find character
        chars = search_object(char_name, typeclass="typeclasses.characters.Character")
        
        if not chars:
            self.caller.msg(f"Character '{char_name}' not found.")
            return
        
        if len(chars) > 1:
            self.caller.msg(f"Multiple matches found: {', '.join(c.key for c in chars)}")
            self.caller.msg("Please be more specific or use character ID: @archive_char #<id>")
            return
        
        char = chars[0]
        
        # Archive the character
        char.db.archived = True
        char.db.archived_reason = reason
        
        import time
        char.db.archived_date = time.time()
        
        self.caller.msg(f"|gArchived character:|n {char.key} (#{char.id})")
        self.caller.msg(f"Reason: {reason}")


class CmdUnarchiveChar(Command):
    """
    Unarchive a character (restore to active status).
    
    Usage:
        @unarchive_char <character_name>
    
    Removes the archived status from a character, making them available
    for play again. This is useful for restoring characters that were
    archived during testing or by mistake.
    
    Example:
        @unarchive_char Laszlo
        @unarchive_char #12345
    """
    
    key = "@unarchive_char"
    locks = "cmd:perm(Builder)"
    help_category = "Admin"
    
    def func(self):
        if not self.args.strip():
            self.caller.msg("Usage: @unarchive_char <character_name>")
            return
        
        char_name = self.args.strip()
        
        # Find character (including archived ones)
        chars = search_object(char_name, typeclass="typeclasses.characters.Character")
        
        if not chars:
            self.caller.msg(f"Character '{char_name}' not found.")
            return
        
        if len(chars) > 1:
            self.caller.msg(f"Multiple matches found: {', '.join(c.key for c in chars)}")
            self.caller.msg("Please be more specific or use character ID: @unarchive_char #<id>")
            return
        
        char = chars[0]
        
        # Check if actually archived
        if not getattr(char.db, 'archived', False):
            self.caller.msg(f"Character {char.key} is not archived.")
            return
        
        # Unarchive the character
        char.db.archived = False
        if hasattr(char.db, 'archived_reason'):
            del char.db.archived_reason
        if hasattr(char.db, 'archived_date'):
            del char.db.archived_date
        
        self.caller.msg(f"|gUnarchived character:|n {char.key} (#{char.id})")
        self.caller.msg("Character is now active and available for play.")


class CmdDeleteChar(Command):
    """
    Permanently delete a character (cannot be undone).
    
    Usage:
        @delete_char <character_name> /confirm
    
    PERMANENTLY deletes a character from the database. This cannot be undone.
    Use @archive_char instead if you want to keep the character but make them
    inactive.
    
    The /confirm switch is required to prevent accidental deletion.
    
    Example:
        @delete_char Laszlo /confirm
        @delete_char #12345 /confirm
    """
    
    key = "@delete_char"
    locks = "cmd:perm(Developer)"
    help_category = "Admin"
    
    def func(self):
        if not self.args.strip():
            self.caller.msg("Usage: @delete_char <character_name> /confirm")
            self.caller.msg("|rWARNING: This permanently deletes the character!|n")
            return
        
        # Check for /confirm switch
        if "/confirm" not in self.raw_string.lower():
            self.caller.msg("|rYou must use /confirm switch to delete a character.|n")
            self.caller.msg("Usage: @delete_char <character_name> /confirm")
            return
        
        # Parse character name (remove /confirm)
        char_name = self.args.strip().replace("/confirm", "").strip()
        
        if not char_name:
            self.caller.msg("Please specify a character name.")
            return
        
        # Find character
        chars = search_object(char_name, typeclass="typeclasses.characters.Character")
        
        if not chars:
            self.caller.msg(f"Character '{char_name}' not found.")
            return
        
        if len(chars) > 1:
            self.caller.msg(f"Multiple matches found: {', '.join(c.key for c in chars)}")
            self.caller.msg("Please be more specific or use character ID: @delete_char #<id> /confirm")
            return
        
        char = chars[0]
        char_key = char.key
        char_id = char.id
        
        # Delete the character
        char.delete()
        
        self.caller.msg(f"|rPermanently deleted character:|n {char_key} (#{char_id})")
