"""
Medical Commands

Commands for interacting with the medical system, including diagnosis,
status checking, and basic medical actions.
"""

from evennia import Command
from evennia.utils.evtable import EvTable


class CmdMedical(Command):
    """
    Check your medical status or diagnose others.
    
    Usage:
        medical
        medical <character>
        medical me
        diagnose <character>
    
    Shows detailed information about medical conditions, organ health,
    and vital signs. Can be used on yourself or others (if you have
    medical training).
    """
    
    key = "medical"
    aliases = ["diagnose", "medstat", "health"]
    help_category = "Medical"
    
    def func(self):
        """Execute the medical command."""
        caller = self.caller
        args = self.args.strip()
        
        # Determine target
        if not args or args.lower() == "me":
            target = caller
            is_self = True
        else:
            target = caller.search(args)
            if not target:
                return
            is_self = (target == caller)
            
        # Check if target has medical state
        try:
            medical_state = target.medical_state
            if medical_state is None:
                caller.msg(f"{target.get_display_name(caller)} has no medical information available.")
                return
        except AttributeError:
            caller.msg(f"{target.get_display_name(caller)} has no medical information available.")
            return
            
        # Get medical status
        from world.medical.utils import get_medical_status_summary
        status = get_medical_status_summary(target)
        
        # Format output
        if is_self:
            caller.msg(f"|cYour Medical Status:|n\n{status}")
        else:
            caller.msg(f"|c{target.get_display_name(caller)}'s Medical Status:|n\n{status}")


class CmdDamageTest(Command):
    """
    Test command for applying anatomical damage.
    
    Usage:
        damagetest <amount> [location] [injury_type]
    
    Examples:
        damagetest 10
        damagetest 15 chest cut
        damagetest 8 left_arm blunt
    
    This command is for testing the medical system during development.
    """
    
    key = "damagetest"
    help_category = "Medical"
    locks = "cmd:perm(Builder)"
    
    def func(self):
        """Execute the damage test command."""
        caller = self.caller
        
        if not self.args:
            caller.msg("Usage: damagetest <amount> [location] [injury_type]")
            return
            
        args = self.args.strip().split()
        
        try:
            damage_amount = int(args[0])
        except (ValueError, IndexError):
            caller.msg("Please provide a valid damage amount.")
            return
            
        location = args[1] if len(args) > 1 else "chest"
        injury_type = args[2] if len(args) > 2 else "generic"
        
        # Apply damage
        results = caller.take_anatomical_damage(damage_amount, location, injury_type)
        
        # Show results
        caller.msg(f"|rYou take {damage_amount} {injury_type} damage to your {location}!|n")
        
        if results["organs_damaged"]:
            caller.msg("|yOrgans damaged:|n")
            for organ_name, damage in results["organs_damaged"]:
                caller.msg(f"  - {organ_name}: {damage} damage")
                
        if results["organs_destroyed"]:
            caller.msg(f"|rOrgans destroyed: {', '.join(results['organs_destroyed'])}|n")
            
        if results["conditions_added"]:
            caller.msg("|yNew conditions:|n")
            for condition_type, severity in results["conditions_added"]:
                caller.msg(f"  - {condition_type.title()} ({severity})")
                
        # Check for critical status
        if caller.is_dead():
            caller.msg("|R*** YOU ARE DEAD ***|n")
        elif caller.is_unconscious():
            caller.msg("|Y*** YOU ARE UNCONSCIOUS ***|n")


class CmdHealTest(Command):
    """
    Test command for healing medical conditions.
    
    Usage:
        healtest [condition_type]
        healtest all
    
    Examples:
        healtest bleeding
        healtest fracture
        healtest all
    
    This command is for testing medical healing during development.
    """
    
    key = "healtest"
    help_category = "Medical"
    locks = "cmd:perm(Builder)"
    
    def func(self):
        """Execute the heal test command."""
        caller = self.caller
        
        try:
            medical_state = caller.medical_state
            if medical_state is None:
                caller.msg("No medical state to heal.")
                return
        except AttributeError:
            caller.msg("No medical state to heal.")
            return
            
        medical_state = caller.medical_state
        
        if not self.args:
            # Show available conditions to heal
            if medical_state.conditions:
                caller.msg("Available conditions to heal:")
                for i, condition in enumerate(medical_state.conditions):
                    location_str = f" ({condition.location})" if condition.location else ""
                    caller.msg(f"  {i+1}. {condition.type} ({condition.severity}){location_str}")
                caller.msg("Usage: healtest <condition_type> or healtest all")
            else:
                caller.msg("No conditions to heal.")
            return
            
        args = self.args.strip().lower()
        
        if args == "all":
            # Heal all conditions
            condition_count = len(medical_state.conditions)
            medical_state.conditions.clear()
            
            # Restore all organs to full health
            for organ in medical_state.organs.values():
                organ.current_hp = organ.max_hp
                
            # Restore vital signs
            medical_state.blood_level = 100.0
            medical_state.pain_level = 0.0
            medical_state.consciousness = 100.0
            
            # Update HP
            caller.hp = caller.hp_max
            
            caller.save_medical_state()
            caller.msg(f"|gHealed all {condition_count} conditions and restored organs to full health.|n")
            
        else:
            # Heal specific condition type
            conditions_to_remove = [c for c in medical_state.conditions if c.type == args]
            
            if not conditions_to_remove:
                caller.msg(f"No {args} conditions found.")
                return
                
            for condition in conditions_to_remove:
                medical_state.remove_condition(condition)
                
            caller.save_medical_state()
            caller.msg(f"|gHealed {len(conditions_to_remove)} {args} condition(s).|n")


class CmdMedicalInfo(Command):
    """
    Display detailed information about the medical system.
    
    Usage:
        medinfo
        medinfo organs
        medinfo conditions
        medinfo capacities
    
    Shows information about organ health, body capacities, and medical conditions.
    """
    
    key = "medinfo"
    help_category = "Medical"
    
    def func(self):
        """Execute the medical info command."""
        caller = self.caller
        args = self.args.strip().lower()
        
        try:
            medical_state = caller.medical_state
            if medical_state is None:
                caller.msg("No medical information available.")
                return
        except AttributeError:
            caller.msg("No medical information available.")
            return
            
        medical_state = caller.medical_state
        
        if not args or args == "summary":
            self._show_summary(caller, medical_state)
        elif args == "organs":
            self._show_organs(caller, medical_state)
        elif args == "conditions":
            self._show_conditions(caller, medical_state)
        elif args == "capacities":
            self._show_capacities(caller, medical_state)
        else:
            caller.msg("Available options: summary, organs, conditions, capacities")
            
    def _show_summary(self, caller, medical_state):
        """Show summary view."""
        table = EvTable("Status", "Value", border="cells")
        
        # Basic status
        status = "DEAD" if medical_state.is_dead() else ("UNCONSCIOUS" if medical_state.is_unconscious() else "CONSCIOUS")
        table.add_row("Overall Status", f"|{'r' if status == 'DEAD' else 'y' if status == 'UNCONSCIOUS' else 'g'}{status}|n")
        
        # Vital signs
        table.add_row("Blood Level", f"{medical_state.blood_level:.1f}%")
        table.add_row("Pain Level", f"{medical_state.pain_level:.1f}")
        table.add_row("Consciousness", f"{medical_state.consciousness:.1f}%")
        
        # Counts
        damaged_organs = sum(1 for organ in medical_state.organs.values() if organ.current_hp < organ.max_hp)
        table.add_row("Damaged Organs", str(damaged_organs))
        table.add_row("Active Conditions", str(len(medical_state.conditions)))
        
        caller.msg(f"|cMedical Summary:|n\n{table}")
        
    def _show_organs(self, caller, medical_state):
        """Show detailed organ information."""
        table = EvTable("Organ", "HP", "Status", "Location", border="cells")
        
        for organ_name, organ in medical_state.organs.items():
            hp_str = f"{organ.current_hp}/{organ.max_hp}"
            
            if organ.current_hp == organ.max_hp:
                status = "|gHealthy|n"
            elif organ.current_hp > organ.max_hp * 0.5:
                status = "|yDamaged|n"
            elif organ.current_hp > 0:
                status = "|rSeverely Damaged|n"
            else:
                status = "|RDestroyed|n"
                
            table.add_row(organ_name.replace('_', ' ').title(), hp_str, status, organ.container)
            
        caller.msg(f"|cOrgan Status:|n\n{table}")
        
    def _show_conditions(self, caller, medical_state):
        """Show detailed condition information."""
        if not medical_state.conditions:
            caller.msg("No active medical conditions.")
            return
            
        table = EvTable("Condition", "Location", "Severity", "Treated", border="cells")
        
        for condition in medical_state.conditions:
            location_str = condition.location or "General"
            treated_str = "|gYes|n" if condition.treated else "|rNo|n"
            
            table.add_row(
                condition.type.title(),
                location_str,
                condition.severity.title(),
                treated_str
            )
            
        caller.msg(f"|cActive Conditions:|n\n{table}")
        
    def _show_capacities(self, caller, medical_state):
        """Show body capacity information."""
        from world.medical.constants import BODY_CAPACITIES
        
        table = EvTable("Capacity", "Level", "Status", border="cells")
        
        for capacity_name in BODY_CAPACITIES.keys():
            level = medical_state.calculate_body_capacity(capacity_name)
            level_percent = level * 100
            
            if level >= 0.8:
                status = "|gGood|n"
            elif level >= 0.5:
                status = "|yImpaired|n" 
            elif level > 0:
                status = "|rSeverely Impaired|n"
            else:
                status = "|RNon-functional|n"
                
            table.add_row(
                capacity_name.replace('_', ' ').title(),
                f"{level_percent:.1f}%",
                status
            )
            
        caller.msg(f"|cBody Capacities:|n\n{table}")


# Add commands to default command set
from evennia import default_cmds

class MedicalCmdSet(default_cmds.CharacterCmdSet):
    """
    Command set containing medical system commands.
    """
    
    key = "MedicalCmdSet"
    
    def at_cmdset_creation(self):
        """Populate the cmdset."""
        super().at_cmdset_creation()
        self.add(CmdMedical())
        self.add(CmdDamageTest())
        self.add(CmdHealTest())
        self.add(CmdMedicalInfo())
