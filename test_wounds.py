#!/usr/bin/env python3
"""
Test script to validate wound system integration.

This script tests the wound description system without needing a full character
with medical state. It's designed to help debug integration issues.
"""

def test_wound_descriptions():
    """Test basic wound description functionality."""
    print("=== Testing Wound Description System ===")
    
    try:
        # Test basic wound description generation
        from world.medical.wounds import get_wound_description
        
        print("\n1. Testing basic wound description...")
        desc = get_wound_description(
            injury_type="bullet",
            location="chest",
            severity="Moderate",
            stage="fresh"
        )
        print(f"Basic wound description: {desc}")
        
        print("\n2. Testing cut wound...")
        desc = get_wound_description(
            injury_type="cut",
            location="left_arm",
            severity="Severe",
            stage="treated"
        )
        print(f"Cut wound description: {desc}")
        
        print("\n3. Testing blunt wound...")
        desc = get_wound_description(
            injury_type="blunt", 
            location="face",
            severity="Light",
            stage="healing"
        )
        print(f"Blunt wound description: {desc}")
        
        print("\n4. Testing location display function...")
        from world.medical.wounds.constants import get_location_display_name
        
        # Test without character (should use fallback)
        display_name = get_location_display_name("left_arm", None)
        print(f"Location display (no char): {display_name}")
        
        print("\n5. Testing medical colors...")
        from world.medical.wounds.constants import MEDICAL_COLORS
        print(f"Medical colors available: {list(MEDICAL_COLORS.keys())}")
        
        print("\n✅ Basic wound description system is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing wound descriptions: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_character_wounds():
    """Test wound system with a mock character."""
    print("\n=== Testing Mock Character Wounds ===")
    
    try:
        # Create a simple mock character for testing
        class MockCharacter:
            def __init__(self):
                self.medical_state = MockMedicalState()
                self.longdesc = {
                    "head": None,
                    "face": "a weathered face",
                    "chest": "broad chest",
                    "left_arm": None,
                    "right_arm": None,
                }
                self.db = MockDB()
                
            def is_location_covered(self, location):
                # Mock clothing coverage - nothing covered for testing
                return False
        
        class MockMedicalState:
            def __init__(self):
                self.organs = {
                    "left_lung": MockOrgan("left_lung", "chest", 80, 100),
                    "right_lung": MockOrgan("right_lung", "chest", 60, 100),
                    "face_skin": MockOrgan("face_skin", "face", 90, 100),
                }
        
        class MockOrgan:
            def __init__(self, name, container, current_hp, max_hp):
                self.name = name
                self.container = container
                self.current_hp = current_hp
                self.max_hp = max_hp
                self.conditions = []
        
        class MockDB:
            def __init__(self):
                self.skintone = "medium"
        
        # Test getting wounds from mock character
        from world.medical.wounds import get_character_wounds
        
        mock_char = MockCharacter()
        wounds = get_character_wounds(mock_char)
        
        print(f"Found {len(wounds)} wounds on mock character:")
        for wound in wounds:
            print(f"  - {wound['location']}: {wound['injury_type']} ({wound['severity']}, {wound['stage']})")
        
        if wounds:
            print("\n✅ Character wound detection is working!")
            
            # Test wound description with character
            from world.medical.wounds import get_wound_description
            wound = wounds[0]
            desc = get_wound_description(
                injury_type=wound['injury_type'],
                location=wound['location'],
                severity=wound['severity'],
                stage=wound['stage'],
                character=mock_char
            )
            print(f"Wound with character context: {desc}")
            
        else:
            print("⚠️  No wounds detected (organs all healthy enough)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing mock character wounds: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Wound System Integration Test")
    print("=" * 50)
    
    # Test basic functionality
    basic_ok = test_wound_descriptions()
    
    # Test with mock character
    mock_ok = test_mock_character_wounds()
    
    print("\n" + "=" * 50)
    if basic_ok and mock_ok:
        print("✅ All tests passed! Wound system appears to be working.")
        print("\nNext steps:")
        print("1. Test in-game with a character that has medical damage")
        print("2. Verify longdesc integration shows wounds")
        print("3. Test clothing concealment")
    else:
        print("❌ Some tests failed. Check the errors above.")
