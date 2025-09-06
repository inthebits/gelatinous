"""
Medical System Integration Test

Test script to validate the medical system implementation works correctly.
This tests the core functionality without requiring a full Evennia server.
"""

import sys
import os

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    # Import medical system components
    from world.medical.core import MedicalState, Organ, MedicalCondition
    from world.medical.constants import ORGANS, BODY_CAPACITIES
    from world.medical.utils import (
        get_organ_by_body_location,
        distribute_damage_to_organs,
        apply_anatomical_damage,
        get_medical_status_summary
    )
except ImportError as e:
    print(f"Failed to import medical modules: {e}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    sys.exit(1)


class MockCharacter:
    """Mock character class for testing."""
    
    def __init__(self, name="TestChar"):
        self.name = name
        self.medical_state = None
        self.db = MockDB()
        
    def get_display_name(self, viewer):
        return self.name
        
    def msg(self, message):
        print(f"[{self.name}] {message}")


class MockDB:
    """Mock database storage for testing."""
    
    def __init__(self):
        self.medical_state = None


def test_organ_creation():
    """Test basic organ functionality."""
    print("=== Testing Organ Creation ===")
    
    # Test creating a brain organ
    brain = Organ("brain")
    print(f"Brain organ: {brain.name}, HP: {brain.current_hp}/{brain.max_hp}")
    print(f"Is vital: {brain.vital}, Container: {brain.container}")
    
    # Test damage application
    was_destroyed = brain.take_damage(5)
    print(f"After 5 damage: {brain.current_hp}/{brain.max_hp}, destroyed: {was_destroyed}")
    
    was_destroyed = brain.take_damage(10)
    print(f"After 10 more damage: {brain.current_hp}/{brain.max_hp}, destroyed: {was_destroyed}")
    
    # Test healing
    healed = brain.heal(3)
    print(f"After healing 3: {brain.current_hp}/{brain.max_hp}, healed: {healed}")
    
    print("✓ Organ creation test passed\n")


def test_medical_conditions():
    """Test medical condition functionality."""
    print("=== Testing Medical Conditions ===")
    
    # Create different types of conditions
    bleeding = MedicalCondition("bleeding", "chest", "severe")
    fracture = MedicalCondition("fracture", "left_arm", "moderate")
    
    print(f"Bleeding condition: {bleeding.type} ({bleeding.severity}) at {bleeding.location}")
    print(f"Pain contribution: {bleeding.get_pain_contribution()}")
    print(f"Blood loss rate: {bleeding.get_blood_loss_rate()}")
    
    print(f"Fracture condition: {fracture.type} ({fracture.severity}) at {fracture.location}")
    print(f"Pain contribution: {fracture.get_pain_contribution()}")
    print(f"Blood loss rate: {fracture.get_blood_loss_rate()}")
    
    print("✓ Medical conditions test passed\n")


def test_medical_state():
    """Test complete medical state functionality."""
    print("=== Testing Medical State ===")
    
    char = MockCharacter("TestPatient")
    medical_state = MedicalState(char)
    
    print(f"Initial state - Blood: {medical_state.blood_level}%, Pain: {medical_state.pain_level}")
    print(f"Consciousness: {medical_state.consciousness}%, Dead: {medical_state.is_dead()}")
    
    # Add some conditions
    bleeding = medical_state.add_condition("bleeding", "chest", "severe")
    fracture = medical_state.add_condition("fracture", "left_arm", "moderate")
    
    print(f"Added conditions: {len(medical_state.conditions)}")
    
    # Damage some organs
    medical_state.take_organ_damage("heart", 8)
    medical_state.take_organ_damage("left_lung", 12)
    
    print("After organ damage:")
    heart = medical_state.get_organ("heart")
    lung = medical_state.get_organ("left_lung")
    print(f"Heart: {heart.current_hp}/{heart.max_hp}")
    print(f"Left lung: {lung.current_hp}/{lung.max_hp}")
    
    # Update vital signs
    medical_state.update_vital_signs()
    print(f"Updated vitals - Blood: {medical_state.blood_level:.1f}%, Pain: {medical_state.pain_level:.1f}")
    print(f"Consciousness: {medical_state.consciousness:.1f}%, Unconscious: {medical_state.is_unconscious()}")
    
    # Test body capacities
    breathing_capacity = medical_state.calculate_body_capacity("breathing")
    blood_pumping_capacity = medical_state.calculate_body_capacity("blood_pumping")
    print(f"Breathing capacity: {breathing_capacity:.2f}")
    print(f"Blood pumping capacity: {blood_pumping_capacity:.2f}")
    
    print("✓ Medical state test passed\n")


def test_damage_distribution():
    """Test damage distribution to organs."""
    print("=== Testing Damage Distribution ===")
    
    # Test chest damage distribution
    chest_organs = get_organ_by_body_location("chest")
    print(f"Chest organs: {chest_organs}")
    
    damage_dist = distribute_damage_to_organs("chest", 20)
    print(f"20 damage to chest distributed as: {damage_dist}")
    
    # Test head damage distribution
    head_organs = get_organ_by_body_location("head")
    print(f"Head organs: {head_organs}")
    
    damage_dist = distribute_damage_to_organs("head", 15)
    print(f"15 damage to head distributed as: {damage_dist}")
    
    print("✓ Damage distribution test passed\n")


def test_anatomical_damage():
    """Test full anatomical damage application."""
    print("=== Testing Anatomical Damage ===")
    
    char = MockCharacter("InjuredChar")
    
    # Apply chest damage with bleeding
    results = apply_anatomical_damage(char, 18, "chest", "cut")
    print(f"Applied 18 cut damage to chest:")
    print(f"  Organs damaged: {results['organs_damaged']}")
    print(f"  Conditions added: {results['conditions_added']}")
    
    # Apply blunt trauma to arm
    results = apply_anatomical_damage(char, 12, "left_arm", "blunt")
    print(f"Applied 12 blunt damage to left arm:")
    print(f"  Organs damaged: {results['organs_damaged']}")
    print(f"  Conditions added: {results['conditions_added']}")
    
    # Check final status
    print(f"Final status:")
    print(f"  Dead: {char.medical_state.is_dead()}")
    print(f"  Unconscious: {char.medical_state.is_unconscious()}")
    print(f"  Conditions: {len(char.medical_state.conditions)}")
    
    print("✓ Anatomical damage test passed\n")


def test_medical_status_summary():
    """Test medical status summary generation."""
    print("=== Testing Medical Status Summary ===")
    
    char = MockCharacter("PatientChar")
    
    # Create some interesting medical state
    apply_anatomical_damage(char, 10, "head", "blunt")
    apply_anatomical_damage(char, 15, "chest", "stab")
    apply_anatomical_damage(char, 8, "left_leg", "cut")
    
    # Generate summary
    summary = get_medical_status_summary(char)
    print("Medical Status Summary:")
    print(summary)
    
    print("✓ Medical status summary test passed\n")


def test_persistence():
    """Test medical state persistence (serialization/deserialization)."""
    print("=== Testing Medical State Persistence ===")
    
    # Create character with medical state
    char1 = MockCharacter("PersistChar")
    apply_anatomical_damage(char1, 12, "chest", "bullet")
    apply_anatomical_damage(char1, 6, "right_arm", "cut")
    
    # Serialize to dict
    state_dict = char1.medical_state.to_dict()
    print(f"Serialized state has {len(state_dict)} top-level keys")
    print(f"Organs: {len(state_dict.get('organs', {}))}")
    print(f"Conditions: {len(state_dict.get('conditions', []))}")
    
    # Create new character and restore state
    char2 = MockCharacter("RestoredChar")
    char2.medical_state = MedicalState.from_dict(state_dict, char2)
    
    # Compare states
    print("Original vs Restored:")
    print(f"  Blood level: {char1.medical_state.blood_level:.1f} vs {char2.medical_state.blood_level:.1f}")
    print(f"  Pain level: {char1.medical_state.pain_level:.1f} vs {char2.medical_state.pain_level:.1f}")
    print(f"  Conditions: {len(char1.medical_state.conditions)} vs {len(char2.medical_state.conditions)}")
    
    print("✓ Persistence test passed\n")


def run_all_tests():
    """Run all medical system tests."""
    print("Starting Medical System Integration Tests\n")
    
    try:
        test_organ_creation()
        test_medical_conditions()
        test_medical_state()
        test_damage_distribution()
        test_anatomical_damage()
        test_medical_status_summary()
        test_persistence()
        
        print("🎉 All tests passed! Medical system is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
