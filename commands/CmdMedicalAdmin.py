"""
Medical Administration Commands

Commands for managing the medical system, including mass updates
and medical state maintenance.
"""

from evennia import Command
from typeclasses.characters import Character


class CmdResetMedicalStates(Command):
    """
    Reset medical states for all characters to use new bone structure.
    
    Usage:
        @resetmedical
        @resetmedical all
        @resetmedical <character>
    
    This command clears existing medical states and rebuilds them
    using the current ORGANS definition. Useful after medical 
    system updates.
    """
    
    key = "@resetmedical"
    aliases = ["@medicalreset", "@resetmed"]
    help_category = "Medical Admin"
    locks = "cmd:perm(Builder)"
    
    def func(self):
        """Execute the medical reset command."""
        caller = self.caller
        args = self.args.strip()
        
        if not args or args.lower() == "all":
            # Reset all characters
            characters = Character.objects.all()
            count = 0
            
            for char in characters:
                if hasattr(char, '_medical_state'):
                    # Clear cached medical state
                    delattr(char, '_medical_state')
                if char.db.medical_state:
                    # Clear stored medical state
                    del char.db.medical_state
                count += 1
                
            caller.msg(f"|gReset medical states for {count} characters.|n")
            caller.msg("|yCharacters will get new bone structure on next medical access.|n")
            
        else:
            # Reset specific character
            target = caller.search(args, global_search=True)
            if not target:
                return
                
            if hasattr(target, '_medical_state'):
                delattr(target, '_medical_state')
            if target.db.medical_state:
                del target.db.medical_state
                
            caller.msg(f"|gReset medical state for {target.get_display_name(caller)}.|n")
            caller.msg("|yThey will get new bone structure on next medical access.|n")


class CmdMedicalMigration(Command):
    """
    Migrate existing medical states to new structure.
    
    Usage:
        @medmigrate
        @medmigrate <character>
    
    This attempts to preserve existing damage/conditions while
    updating to the new bone structure.
    """
    
    key = "@medmigrate"
    aliases = ["@migratemedical"]
    help_category = "Medical Admin"
    locks = "cmd:perm(Builder)"
    
    def func(self):
        """Execute the medical migration command."""
        caller = self.caller
        args = self.args.strip()
        
        if not args:
            # Migrate all characters
            characters = Character.objects.all()
            migrated_count = 0
            
            for char in characters:
                if self._migrate_character(char, caller):
                    migrated_count += 1
                    
            caller.msg(f"|gMigrated {migrated_count} characters to new bone structure.|n")
            
        else:
            # Migrate specific character
            target = caller.search(args, global_search=True)
            if not target:
                return
                
            if self._migrate_character(target, caller):
                caller.msg(f"|gMigrated {target.get_display_name(caller)} to new bone structure.|n")
            else:
                caller.msg(f"|yNo migration needed for {target.get_display_name(caller)}.|n")
    
    def _migrate_character(self, character, caller):
        """
        Migrate a single character's medical state.
        
        Returns:
            bool: True if migration was performed, False if not needed
        """
        try:
            # Check if character has old medical state
            old_medical_data = character.db.medical_state
            if not old_medical_data:
                return False
                
            # Check if already migrated (has new bones)
            if 'organs' in old_medical_data:
                old_organs = old_medical_data['organs']
                if 'left_humerus' in old_organs and 'left_arm_system' not in old_organs:
                    return False  # Already migrated
                    
            # Clear old medical state
            if hasattr(character, '_medical_state'):
                delattr(character, '_medical_state')
            del character.db.medical_state
            
            # Force recreation with new structure
            _ = character.medical_state
            
            return True
            
        except Exception as e:
            caller.msg(f"|rError migrating {character}: {e}|n")
            return False


class CmdMedicalAudit(Command):
    """
    Audit medical states across all characters.
    
    Usage:
        @medaudit
        @medaudit summary
        @medaudit details
    
    Shows statistics about medical state versions and issues.
    """
    
    key = "@medaudit"
    aliases = ["@auditmedical"]
    help_category = "Medical Admin"
    locks = "cmd:perm(Builder)"
    
    def func(self):
        """Execute the medical audit command."""
        caller = self.caller
        args = self.args.strip().lower()
        
        characters = Character.objects.all()
        stats = {
            'total': len(characters),
            'has_medical': 0,
            'old_structure': 0,
            'new_structure': 0,
            'no_medical': 0,
            'errors': 0
        }
        
        details = []
        
        for char in characters:
            try:
                medical_data = char.db.medical_state
                if not medical_data:
                    stats['no_medical'] += 1
                    if args == 'details':
                        details.append(f"{char.key}: No medical state")
                    continue
                    
                stats['has_medical'] += 1
                
                if 'organs' in medical_data:
                    organs = medical_data['organs']
                    if 'left_humerus' in organs and 'left_arm_system' not in organs:
                        stats['new_structure'] += 1
                        if args == 'details':
                            details.append(f"{char.key}: New bone structure ✓")
                    else:
                        stats['old_structure'] += 1
                        if args == 'details':
                            details.append(f"{char.key}: Old system structure (needs migration)")
                else:
                    stats['old_structure'] += 1
                    if args == 'details':
                        details.append(f"{char.key}: Very old structure (needs migration)")
                        
            except Exception as e:
                stats['errors'] += 1
                if args == 'details':
                    details.append(f"{char.key}: ERROR - {e}")
        
        # Show summary
        caller.msg("|cMedical State Audit Results:|n")
        caller.msg(f"Total Characters: {stats['total']}")
        caller.msg(f"Has Medical State: {stats['has_medical']}")
        caller.msg(f"New Bone Structure: |g{stats['new_structure']}|n")
        caller.msg(f"Old Structure (needs migration): |y{stats['old_structure']}|n")
        caller.msg(f"No Medical State: {stats['no_medical']}")
        caller.msg(f"Errors: |r{stats['errors']}|n")
        
        if args == 'details' and details:
            caller.msg("\n|wDetailed Results:|n")
            for detail in details[:20]:  # Limit output
                caller.msg(f"  {detail}")
            if len(details) > 20:
                caller.msg(f"  ... and {len(details) - 20} more")


# Add commands to default command set
from evennia import default_cmds

class MedicalAdminCmdSet(default_cmds.CharacterCmdSet):
    """
    Command set containing medical administration commands.
    """
    
    key = "MedicalAdminCmdSet"
    
    def at_cmdset_creation(self):
        """Populate the cmdset."""
        super().at_cmdset_creation()
        self.add(CmdResetMedicalStates())
        self.add(CmdMedicalMigration())
        self.add(CmdMedicalAudit())
