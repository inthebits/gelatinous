#!/usr/bin/env python3
"""
Final Refactoring Validation Test

This script validates that all refactored modules can be imported successfully
and that all expected functions and classes are properly exposed.
"""

import sys
import os

# Add the world/combat directory to the path
sys.path.insert(0, '/Users/daiimus/Documents/Projects/Repositories/Evennia/gelatinous/world/combat')

def test_module_imports():
    """Test that all modules can be imported successfully."""
    print("🔍 Testing module imports...")
    
    try:
        # Test utils.py imports
        print("  📦 Testing utils.py...")
        from utils import (
            get_numeric_stat, log_combat_action, get_display_name_safe,
            roll_stat, opposed_roll, get_wielded_weapon, is_wielding_ranged_weapon,
            get_weapon_damage, add_combatant, remove_combatant, cleanup_combatant_state,
            cleanup_all_combatants, get_combatant_target, get_combatant_grappling_target,
            get_combatant_grappled_by, get_character_dbref, get_character_by_dbref
        )
        print("    ✅ utils.py imports successful")
        
        # Test grappling.py imports
        print("  🤼 Testing grappling.py...")
        from grappling import (
            break_grapple, establish_grapple, resolve_grapple_initiate,
            resolve_grapple_join, resolve_release_grapple, validate_and_cleanup_grapple_state,
            get_character_dbref
        )
        print("    ✅ grappling.py imports successful")
        
        # Test constants.py
        print("  🎯 Testing constants.py...")
        from constants import (
            DB_COMBATANTS, DB_GRAPPLING_DBREF, DB_GRAPPLED_BY_DBREF,
            SPLATTERCAST_CHANNEL, NDB_PROXIMITY
        )
        print("    ✅ constants.py imports successful")
        
        # Test proximity.py
        print("  📍 Testing proximity.py...")
        from proximity import establish_proximity, is_in_proximity
        print("    ✅ proximity.py imports successful")
        
        print("✅ All module imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_cross_module_compatibility():
    """Test that modules can work together without circular import issues."""
    print("\n🔗 Testing cross-module compatibility...")
    
    try:
        # Import modules that cross-reference each other
        from utils import add_combatant, remove_combatant
        from grappling import establish_grapple, break_grapple
        
        # Test that we can access functions that do cross-imports
        print("  📦 Utils functions accessible")
        print("  🤼 Grappling functions accessible")
        
        print("✅ Cross-module compatibility verified!")
        return True
        
    except Exception as e:
        print(f"❌ Cross-module error: {e}")
        return False


def test_function_signatures():
    """Test that moved functions have correct signatures."""
    print("\n📝 Testing function signatures...")
    
    try:
        from grappling import resolve_grapple_initiate, resolve_grapple_join, resolve_release_grapple
        from utils import add_combatant, remove_combatant
        
        import inspect
        
        # Check grappling function signatures
        grapple_funcs = {
            'resolve_grapple_initiate': resolve_grapple_initiate,
            'resolve_grapple_join': resolve_grapple_join,
            'resolve_release_grapple': resolve_release_grapple
        }
        
        for name, func in grapple_funcs.items():
            sig = inspect.signature(func)
            expected_params = ['char_entry', 'combatants_list', 'handler']
            actual_params = list(sig.parameters.keys())
            
            if actual_params == expected_params:
                print(f"    ✅ {name} signature correct")
            else:
                print(f"    ❌ {name} signature mismatch: expected {expected_params}, got {actual_params}")
                return False
        
        # Check utils function signatures  
        add_sig = inspect.signature(add_combatant)
        remove_sig = inspect.signature(remove_combatant)
        
        if 'handler' in add_sig.parameters and 'char' in add_sig.parameters:
            print("    ✅ add_combatant signature correct")
        else:
            print("    ❌ add_combatant signature incorrect")
            return False
            
        if 'handler' in remove_sig.parameters and 'char' in remove_sig.parameters:
            print("    ✅ remove_combatant signature correct")
        else:
            print("    ❌ remove_combatant signature incorrect")
            return False
        
        print("✅ All function signatures verified!")
        return True
        
    except Exception as e:
        print(f"❌ Function signature error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 Running Final Refactoring Validation Tests")
    print("=" * 50)
    
    tests = [
        test_module_imports,
        test_cross_module_compatibility,
        test_function_signatures
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - REFACTORING IS READY FOR COMMIT!")
    else:
        print("❌ SOME TESTS FAILED - PLEASE REVIEW BEFORE COMMIT")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
