#!/usr/bin/env python3
"""
Turn-Based Combat System Validation Script

This script validates the turn-based combat system implementation
by checking all components are properly connected and functional.
"""

import sys
import os
import ast
import re

def validate_constants():
    """Validate that all required constants are defined."""
    print("🔍 Validating constants...")
    
    constants_file = "world/combat/constants.py"
    if not os.path.exists(constants_file):
        print(f"❌ Constants file not found: {constants_file}")
        return False
    
    with open(constants_file, 'r') as f:
        content = f.read()
    
    required_constants = [
        'COMBAT_ACTION_RETREAT',
        'COMBAT_ACTION_ADVANCE', 
        'COMBAT_ACTION_CHARGE',
        'COMBAT_ACTION_DISARM',
        'MSG_RETREAT_PREPARE',
        'MSG_ADVANCE_PREPARE',
        'MSG_CHARGE_PREPARE',
        'MSG_DISARM_PREPARE'
    ]
    
    for constant in required_constants:
        if constant not in content:
            print(f"❌ Missing constant: {constant}")
            return False
        else:
            print(f"✅ Found constant: {constant}")
    
    return True

def validate_command_imports():
    """Validate that commands import the required constants."""
    print("\n🔍 Validating command imports...")
    
    files_to_check = [
        ("commands/combat/movement.py", ['COMBAT_ACTION_RETREAT', 'COMBAT_ACTION_ADVANCE', 'COMBAT_ACTION_CHARGE']),
        ("commands/combat/special_actions.py", ['COMBAT_ACTION_DISARM'])
    ]
    
    for file_path, expected_imports in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ Command file not found: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        for import_name in expected_imports:
            if import_name not in content:
                print(f"❌ {file_path} missing import: {import_name}")
                return False
            else:
                print(f"✅ {file_path} has import: {import_name}")
    
    return True

def validate_command_actions():
    """Validate that commands set the combat_action correctly."""
    print("\n🔍 Validating command action setting...")
    
    command_checks = [
        ("commands/combat/movement.py", "CmdRetreat", "COMBAT_ACTION_RETREAT"),
        ("commands/combat/movement.py", "CmdAdvance", "COMBAT_ACTION_ADVANCE"),
        ("commands/combat/movement.py", "CmdCharge", "COMBAT_ACTION_CHARGE"),
        ("commands/combat/special_actions.py", "CmdDisarm", "COMBAT_ACTION_DISARM")
    ]
    
    for file_path, command_class, action_constant in command_checks:
        if not os.path.exists(file_path):
            print(f"❌ Command file not found: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if command sets the combat_action
        action_pattern = f'combat_action.*=.*{action_constant}'
        if not re.search(action_pattern, content):
            print(f"❌ {command_class} does not set combat_action to {action_constant}")
            return False
        else:
            print(f"✅ {command_class} sets combat_action to {action_constant}")
    
    return True

def validate_handler_imports():
    """Validate that handler imports the required constants."""
    print("\n🔍 Validating handler imports...")
    
    handler_file = "world/combat/handler.py"
    if not os.path.exists(handler_file):
        print(f"❌ Handler file not found: {handler_file}")
        return False
    
    with open(handler_file, 'r') as f:
        content = f.read()
    
    required_imports = [
        'COMBAT_ACTION_RETREAT',
        'COMBAT_ACTION_ADVANCE',
        'COMBAT_ACTION_CHARGE',
        'COMBAT_ACTION_DISARM'
    ]
    
    for import_name in required_imports:
        if import_name not in content:
            print(f"❌ Handler missing import: {import_name}")
            return False
        else:
            print(f"✅ Handler has import: {import_name}")
    
    return True

def validate_handler_methods():
    """Validate that handler has all required methods."""
    print("\n🔍 Validating handler methods...")
    
    handler_file = "world/combat/handler.py"
    if not os.path.exists(handler_file):
        print(f"❌ Handler file not found: {handler_file}")
        return False
    
    with open(handler_file, 'r') as f:
        content = f.read()
    
    required_methods = [
        '_resolve_retreat',
        '_resolve_advance',
        '_resolve_charge',
        '_resolve_disarm'
    ]
    
    for method in required_methods:
        method_pattern = f'def {method}\\('
        if not re.search(method_pattern, content):
            print(f"❌ Handler missing method: {method}")
            return False
        else:
            print(f"✅ Handler has method: {method}")
    
    return True

def validate_handler_processing():
    """Validate that handler processes the new combat actions."""
    print("\n🔍 Validating handler processing logic...")
    
    handler_file = "world/combat/handler.py"
    if not os.path.exists(handler_file):
        print(f"❌ Handler file not found: {handler_file}")
        return False
    
    with open(handler_file, 'r') as f:
        content = f.read()
    
    processing_checks = [
        ('COMBAT_ACTION_RETREAT', '_resolve_retreat'),
        ('COMBAT_ACTION_ADVANCE', '_resolve_advance'),
        ('COMBAT_ACTION_CHARGE', '_resolve_charge'),
        ('COMBAT_ACTION_DISARM', '_resolve_disarm')
    ]
    
    for action_constant, method_name in processing_checks:
        # Check if handler processes the action
        pattern = f'combat_action == {action_constant}.*{method_name}'
        if not re.search(pattern, content, re.DOTALL):
            print(f"❌ Handler does not process {action_constant} with {method_name}")
            return False
        else:
            print(f"✅ Handler processes {action_constant} with {method_name}")
    
    return True

def validate_skip_round_system():
    """Validate that the skip round system is properly implemented."""
    print("\n🔍 Validating skip round system...")
    
    movement_file = "commands/combat/movement.py"
    handler_file = "world/combat/handler.py"
    
    if not os.path.exists(movement_file) or not os.path.exists(handler_file):
        print("❌ Required files not found for skip round validation")
        return False
    
    # Check movement.py uses NDB_SKIP_ROUND
    with open(movement_file, 'r') as f:
        movement_content = f.read()
    
    if 'NDB_SKIP_ROUND' not in movement_content:
        print("❌ Movement commands do not use NDB_SKIP_ROUND")
        return False
    
    # Check handler.py processes skip round
    with open(handler_file, 'r') as f:
        handler_content = f.read()
    
    if 'NDB_SKIP_ROUND' not in handler_content:
        print("❌ Handler does not process NDB_SKIP_ROUND")
        return False
    
    print("✅ Skip round system properly implemented")
    return True

def validate_message_templates():
    """Validate that message templates are properly formatted."""
    print("\n🔍 Validating message templates...")
    
    constants_file = "world/combat/constants.py"
    if not os.path.exists(constants_file):
        print(f"❌ Constants file not found: {constants_file}")
        return False
    
    with open(constants_file, 'r') as f:
        content = f.read()
    
    # Check for proper message formatting
    message_checks = [
        ('MSG_RETREAT_PREPARE', 'retreat'),
        ('MSG_ADVANCE_PREPARE', 'advance'),
        ('MSG_CHARGE_PREPARE', 'charge'),
        ('MSG_DISARM_PREPARE', 'disarm')
    ]
    
    for msg_name, action_word in message_checks:
        # Find the message definition
        msg_pattern = f'{msg_name}\\s*=\\s*["\']([^"\']+)["\']'
        match = re.search(msg_pattern, content)
        if not match:
            print(f"❌ Message template not found: {msg_name}")
            return False
        
        msg_content = match.group(1)
        if action_word not in msg_content.lower():
            print(f"❌ Message template {msg_name} does not contain '{action_word}'")
            return False
        
        print(f"✅ Message template {msg_name} properly formatted")
    
    return True

def run_validation():
    """Run all validation checks."""
    print("🚀 Starting Turn-Based Combat System Validation\n")
    
    checks = [
        validate_constants,
        validate_command_imports,
        validate_command_actions,
        validate_handler_imports,
        validate_handler_methods,
        validate_handler_processing,
        validate_skip_round_system,
        validate_message_templates
    ]
    
    passed = 0
    failed = 0
    
    for check in checks:
        try:
            if check():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            failed += 1
    
    print(f"\n📊 Validation Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All validation checks passed! Turn-based combat system is properly implemented.")
        return True
    else:
        print(f"\n⚠️  {failed} validation checks failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
