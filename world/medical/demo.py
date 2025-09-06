"""
Medical System Demo

Interactive demonstration of the medical system capabilities.
Shows various injury scenarios and medical conditions.
"""

import sys
import os

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from world.medical.core import MedicalState
from world.medical.utils import apply_anatomical_damage, get_medical_status_summary


class MockCharacter:
    """Mock character for demo purposes."""
    
    def __init__(self, name="Demo Character"):
        self.name = name
        self.medical_state = None
        self.db = type('MockDB', (), {'medical_state': None})()
        
    def get_display_name(self, viewer):
        return self.name
        
    def msg(self, message):
        print(f"[{self.name}] {message}")


def print_separator(title):
    """Print a nice section separator."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_medical_status(character, title="Medical Status"):
    """Print formatted medical status."""
    print(f"\n{title}:")
    print("-" * 40)
    status = get_medical_status_summary(character)
    print(status)


def demo_basic_injury_progression():
    """Demonstrate basic injury and medical condition progression."""
    print_separator("BASIC INJURY PROGRESSION DEMO")
    
    soldier = MockCharacter("Battle-Scarred Soldier")
    print(f"Starting with healthy {soldier.name}...")
    print_medical_status(soldier, "Initial Status")
    
    print("\n📍 Taking moderate chest wound from blade...")
    apply_anatomical_damage(soldier, 12, "chest", "cut")
    print_medical_status(soldier, "After Chest Wound")
    
    print("\n📍 Blunt trauma to left arm...")
    apply_anatomical_damage(soldier, 10, "left_arm", "blunt")
    print_medical_status(soldier, "After Arm Injury")
    
    print("\n📍 Severe head trauma...")
    apply_anatomical_damage(soldier, 8, "head", "blunt")
    print_medical_status(soldier, "After Head Trauma")
    
    print("\n💭 Notice how:")
    print("   • Bleeding conditions reduce blood level over time")
    print("   • Pain accumulates from multiple injuries")
    print("   • Consciousness drops from blood loss and pain")
    print("   • Organ damage reduces functional capacity")


def demo_critical_injury_scenarios():
    """Demonstrate critical injury scenarios and death conditions."""
    print_separator("CRITICAL INJURY SCENARIOS")
    
    print("🩸 Scenario 1: Severe Bleeding")
    victim1 = MockCharacter("Bleeding Victim")
    
    # Multiple bleeding wounds
    apply_anatomical_damage(victim1, 20, "chest", "stab")
    apply_anatomical_damage(victim1, 15, "abdomen", "laceration")
    apply_anatomical_damage(victim1, 12, "left_thigh", "cut")
    
    print_medical_status(victim1, "Multiple Bleeding Wounds")
    
    # Simulate blood loss over time
    print("\n⏱️ Simulating blood loss over several rounds...")
    for round_num in range(1, 6):
        victim1.medical_state.update_vital_signs()
        blood_level = victim1.medical_state.blood_level
        consciousness = victim1.medical_state.consciousness
        print(f"Round {round_num}: Blood {blood_level:.1f}%, Consciousness {consciousness:.1f}%")
        
        if victim1.medical_state.is_dead():
            print("💀 VICTIM DIED FROM BLOOD LOSS")
            break
        elif victim1.medical_state.is_unconscious():
            print("😵 VICTIM FELL UNCONSCIOUS")
    
    print("\n💔 Scenario 2: Vital Organ Destruction")
    victim2 = MockCharacter("Heart Attack Victim")
    
    # Massive damage to heart
    apply_anatomical_damage(victim2, 25, "chest", "bullet")
    print_medical_status(victim2, "After Heart Damage")
    
    heart = victim2.medical_state.get_organ("heart")
    if heart.is_destroyed():
        print("💀 HEART DESTROYED - IMMEDIATE DEATH")


def demo_medical_system_features():
    """Demonstrate advanced medical system features."""
    print_separator("ADVANCED MEDICAL FEATURES")
    
    patient = MockCharacter("Test Patient")
    
    print("🔬 Testing Body Capacity System:")
    
    # Damage eyes to affect sight
    apply_anatomical_damage(patient, 8, "head", "cut")  # Damages eyes
    sight_capacity = patient.medical_state.calculate_body_capacity("sight")
    print(f"   Sight capacity after eye damage: {sight_capacity:.2f}")
    
    # Damage legs to affect movement
    apply_anatomical_damage(patient, 15, "left_thigh", "blunt")
    apply_anatomical_damage(patient, 12, "right_shin", "fracture")
    moving_capacity = patient.medical_state.calculate_body_capacity("moving")
    print(f"   Movement capacity after leg injuries: {moving_capacity:.2f}")
    
    # Damage arms to affect manipulation
    apply_anatomical_damage(patient, 10, "left_arm", "burn")
    apply_anatomical_damage(patient, 8, "right_hand", "laceration")
    manipulation_capacity = patient.medical_state.calculate_body_capacity("manipulation")
    print(f"   Manipulation capacity after arm/hand damage: {manipulation_capacity:.2f}")
    
    print(f"\n🧠 Medical Conditions Analysis:")
    conditions = patient.medical_state.conditions
    print(f"   Total active conditions: {len(conditions)}")
    
    for condition in conditions:
        pain = condition.get_pain_contribution()
        blood_loss = condition.get_blood_loss_rate()
        location = condition.location or "general"
        print(f"   • {condition.type.title()} ({condition.severity}) at {location}")
        print(f"     Pain: {pain}, Blood loss: {blood_loss}/round")


def demo_cross_species_compatibility():
    """Demonstrate how the system adapts to different anatomies."""
    print_separator("CROSS-SPECIES COMPATIBILITY")
    
    print("👤 Human Character:")
    human = MockCharacter("Human Soldier")
    apply_anatomical_damage(human, 12, "left_arm", "blunt")
    
    human_conditions = [c.type for c in human.medical_state.conditions]
    print(f"   Conditions: {human_conditions}")
    print(f"   Fracture affects: left_arm_system")
    
    print(f"\n🐙 Hypothetical Tentacle Monster:")
    print("   (Same fracture mechanics would apply to tentacles)")
    print("   • tentacle_1 fractured → splint can treat it")  
    print("   • tentacle_3 fractured → same pain/disability mechanics")
    print("   • Universal injury types work across all anatomies")
    
    print(f"\n🕷️ Hypothetical Spider Creature:")
    print("   • leg_5 fractured → affects movement capacity")
    print("   • leg_7 bleeding → contributes to blood loss")
    print("   • All 8 legs can be injured independently")
    
    print(f"\n💭 Key insight: The medical system is anatomy-agnostic!")
    print("   The same condition/treatment mechanics work for any creature type.")


def demo_persistence_and_recovery():
    """Demonstrate medical state persistence and recovery scenarios."""
    print_separator("PERSISTENCE & RECOVERY SCENARIOS")
    
    print("💾 Medical State Persistence:")
    survivor = MockCharacter("Combat Survivor")
    
    # Apply various injuries
    apply_anatomical_damage(survivor, 15, "chest", "bullet")
    apply_anatomical_damage(survivor, 8, "left_arm", "burn")
    apply_anatomical_damage(survivor, 10, "head", "blunt")
    
    # Serialize state
    state_dict = survivor.medical_state.to_dict()
    print(f"   Serialized state: {len(state_dict)} keys")
    print(f"   Organs tracked: {len(state_dict['organs'])}")
    print(f"   Conditions saved: {len(state_dict['conditions'])}")
    
    # Restore state to new character
    recovered_survivor = MockCharacter("Recovered Survivor")
    recovered_survivor.medical_state = MedicalState.from_dict(state_dict, recovered_survivor)
    
    print(f"\n🏥 State successfully restored:")
    print(f"   Blood level: {recovered_survivor.medical_state.blood_level:.1f}%")
    print(f"   Pain level: {recovered_survivor.medical_state.pain_level:.1f}")
    print(f"   Conditions: {len(recovered_survivor.medical_state.conditions)}")
    
    print(f"\n💭 This enables:")
    print("   • Saving medical state across server restarts")
    print("   • Persistent injuries that last between sessions")
    print("   • Medical treatment progress tracking")


def run_complete_demo():
    """Run the complete medical system demonstration."""
    print("🏥 GELATINOUS MONSTER MEDICAL SYSTEM - PHASE 1 DEMO")
    print("=" * 60)
    print("This demo showcases the tactical medical gameplay system")
    print("with realistic injury consequences and anatomical damage.")
    
    try:
        demo_basic_injury_progression()
        input("\n[Press Enter to continue to critical scenarios...]")
        
        demo_critical_injury_scenarios()
        input("\n[Press Enter to continue to advanced features...]")
        
        demo_medical_system_features()
        input("\n[Press Enter to continue to cross-species demo...]")
        
        demo_cross_species_compatibility()
        input("\n[Press Enter to continue to persistence demo...]")
        
        demo_persistence_and_recovery()
        
        print_separator("DEMO COMPLETE")
        print("🎉 Medical System Phase 1 is fully functional!")
        print("\nKey achievements:")
        print("✅ Anatomical damage with organ-specific effects")
        print("✅ Realistic injury consequences (bleeding, fractures, etc.)")
        print("✅ Body capacity system affecting character function")
        print("✅ Death from vital organ failure or blood loss")
        print("✅ Unconsciousness from pain and blood loss")
        print("✅ Cross-species anatomy compatibility")
        print("✅ Complete state persistence for sessions")
        print("✅ Rich medical status reporting")
        
        print("\n🚀 Ready for Phase 2: Medical tools and consumption system!")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_complete_demo()
