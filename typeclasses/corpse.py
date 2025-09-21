# =============================================================================
# CORPSE OBJECT - Just-In-Time Decay System
# =============================================================================

from .items import Item
import time

class Corpse(Item):
    """
    A corpse object that preserves forensic data and uses just-in-time decay.
    Decay is calculated on-demand when the corpse is looked at or referenced,
    rather than using continuous scripts.
    """
    
    def at_object_creation(self):
        """Initialize corpse with decay tracking."""
        super().at_object_creation()
        
        # Core corpse properties
        self.db.is_corpse = True
        self.db.creation_time = time.time()
        
        # Preserve original descriptions for decay calculations
        self.db.base_description = getattr(self.db, 'desc', '')
        self.db.base_longdesc = {}
        
        # Forensic data (set by death progression script)
        self.db.original_character_name = "someone"
        self.db.original_character_dbref = None  # Character object dbref
        self.db.original_account_dbref = None    # Account object dbref
        self.db.death_time = time.time()
        self.db.death_cause = "unknown"
        self.db.medical_conditions = []
        self.db.physical_description = ""
        self.db.longdesc_data = {}
        
        # Decay settings
        self.db.decay_stages = {
            "fresh": 3600,      # < 1 hour
            "early": 86400,     # < 1 day
            "moderate": 259200, # < 3 days  
            "advanced": 604800, # < 1 week
            "skeletal": float('inf')  # > 1 week
        }
    
    def get_decay_stage(self):
        """Calculate current decay stage based on time elapsed."""
        elapsed = time.time() - self.db.creation_time
        
        for stage, threshold in self.db.decay_stages.items():
            if elapsed < threshold:
                return stage
        return "skeletal"
    
    def get_decay_factor(self):
        """Get decay factor (0.0 = fresh, 1.0 = fully decayed)."""
        elapsed = time.time() - self.db.creation_time
        max_decay_time = self.db.decay_stages["advanced"]  # 1 week
        return min(1.0, elapsed / max_decay_time)
    
    def get_display_name(self, looker, **kwargs):
        """Update display name based on current decay stage."""
        stage = self.get_decay_stage()
        
        decay_names = {
            "fresh": "fresh corpse",
            "early": "pale corpse", 
            "moderate": "decomposing remains",
            "advanced": "putrid remains",
            "skeletal": "skeletal remains"
        }
        
        return decay_names.get(stage, 'corpse')
    
    def return_appearance(self, looker, **kwargs):
        """Update appearance based on current decay stage when looked at."""
        # Check for complete decay first
        if self._handle_complete_decay():
            return None  # Corpse was destroyed
            
        # Update decay-based descriptions just-in-time
        self._update_decay_descriptions()
        
        # Return normal appearance with updated descriptions
        return super().return_appearance(looker, **kwargs)
    
    def _update_decay_descriptions(self):
        """Update descriptions based on current decay stage."""
        stage = self.get_decay_stage()
        decay_factor = self.get_decay_factor()
        
        # Base physical description
        base_desc = self.db.physical_description or "A lifeless body."
        
        # Stage-specific description modifications
        decay_descriptions = {
            "fresh": f"A recently deceased human body. {base_desc} "
                    f"The body appears fresh, with no signs of decomposition yet visible.",
            
            "early": f"A pale human corpse. {base_desc} "
                    f"The skin has begun to pale and cool, with early signs of lividity visible.",
            
            "moderate": f"Decomposing human remains. "
                       f"Bloating and discoloration have begun, with a distinct odor of decay. "
                       f"The original features are still recognizable but deteriorating.",
            
            "advanced": f"Putrid human remains. "
                       f"Advanced decomposition has set in with severe bloating, fluid leakage, "
                       f"and strong putrid odors. Identification is becoming difficult.",
            
            "skeletal": f"Skeletal human remains. "
                       f"Only bones, dried tissue, and clothing remain. The decomposition process "
                       f"is nearly complete."
        }
        
        # Update main description
        self.db.desc = decay_descriptions.get(stage, base_desc)
        
        # Update longdesc if it exists
        if hasattr(self, 'longdesc') and self.longdesc:
            self._update_longdesc_for_decay(stage, decay_factor)
    
    def _update_longdesc_for_decay(self, stage, decay_factor):
        """Update longdesc details based on decay stage."""
        # This would modify specific longdesc body parts based on decay
        # For now, we'll just add a general decay note
        if hasattr(self, 'longdesc') and self.longdesc:
            # Add decay information to longdesc
            decay_notes = {
                "fresh": "appears fresh and recently deceased",
                "early": "shows early signs of decomposition with pale skin",
                "moderate": "displays moderate decomposition with bloating and discoloration", 
                "advanced": "exhibits advanced putrefaction with severe decay",
                "skeletal": "has decomposed to mostly skeletal remains"
            }
            
            decay_note = decay_notes.get(stage, "shows signs of decay")
            
            # You could modify specific body parts here based on your longdesc system
            # For example: modify skin color, add bloating to torso, etc.
    
    def get_forensic_data(self):
        """Return forensic data for investigation purposes."""
        stage = self.get_decay_stage()
        
        forensic_info = {
            "original_name": self.db.original_character_name,
            "original_character_dbref": self.db.original_character_dbref,
            "original_account_dbref": self.db.original_account_dbref,
            "death_time": self.db.death_time,
            "death_cause": self.db.death_cause,
            "medical_conditions": self.db.medical_conditions,
            "decay_stage": stage,
            "time_since_death": self.get_time_since_death(),
            "identifiable": stage in ["fresh", "early", "moderate"]
        }
        
        return forensic_info
    
    def get_time_since_death(self):
        """Get human-readable time since death."""
        elapsed = time.time() - self.db.death_time
        
        if elapsed < 3600:
            minutes = int(elapsed / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif elapsed < 86400:
            hours = int(elapsed / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = int(elapsed / 86400)
            return f"{days} day{'s' if days != 1 else ''}"
    
    def get_original_character(self):
        """Get the original character object if it still exists."""
        if self.db.original_character_dbref:
            from evennia.utils.search import search_object
            chars = search_object(f"#{self.db.original_character_dbref}")
            return chars[0] if chars else None
        return None
    
    def get_original_account(self):
        """Get the original account object if it still exists.""" 
        if self.db.original_account_dbref:
            from evennia.utils.search import search_object
            accounts = search_object(f"#{self.db.original_account_dbref}")
            return accounts[0] if accounts else None
        return None
    
    def is_character_still_active(self):
        """Check if the original character is still active in the game."""
        char = self.get_original_character()
        if not char:
            return False
        # Character exists but might be in limbo or archived
        return char.location and char.location.key != "Limbo"
    
    def get_admin_info(self):
        """Get administrative information about this corpse (staff only)."""
        char = self.get_original_character()
        account = self.get_original_account()
        
        admin_info = {
            "corpse_dbref": self.dbref,
            "original_character_name": self.db.original_character_name,
            "original_character_dbref": self.db.original_character_dbref,
            "original_account_dbref": self.db.original_account_dbref,
            "character_still_exists": char is not None,
            "character_still_active": self.is_character_still_active(),
            "account_still_exists": account is not None,
            "creation_time": self.db.creation_time,
            "death_time": self.db.death_time,
            "decay_stage": self.get_decay_stage()
        }
        
        return admin_info
    
    def check_complete_decay(self):
        """Check if corpse should be completely decayed and cleaned up."""
        elapsed = time.time() - self.db.creation_time
        
        # 2 weeks for complete decay and cleanup
        complete_decay_time = 1209600  # 2 weeks in seconds
        
        return elapsed > complete_decay_time
    
    def _handle_complete_decay(self):
        """Handle complete decay - drop items and remove corpse."""
        if not self.check_complete_decay():
            return False
            
        # Drop all items to the room
        if self.location:
            for item in self.contents:
                item.move_to(self.location, quiet=True)
                
        # Log the decay completion
        try:
            from evennia.comms.models import ChannelDB
            splattercast = ChannelDB.objects.get_channel("Splattercast")
            splattercast.msg(f"CORPSE_DECAY: {self.key} completely decayed and removed from {self.location}")
        except:
            pass
            
        # Remove the corpse
        self.delete()
        return True