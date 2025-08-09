#!/usr/bin/env python3
"""
Quick test script for CmdJump parsing logic
"""

class MockCmdJump:
    """Mock version of CmdJump for testing parsing logic without Evennia"""
    
    def __init__(self, args):
        self.args = args
        self.explosive_name = None
        self.direction = None
        self.jump_type = None
        self.parse()
    
    def parse(self):
        """Parse jump command with syntax detection."""
        self.args = self.args.strip()
        
        # Initialize parsing results
        self.explosive_name = None
        self.direction = None
        self.jump_type = None  # 'on_explosive', 'off_edge', 'across_gap'
        
        if not self.args:
            return
        
        # Parse for "on" keyword - explosive sacrifice
        if self.args.startswith("on "):
            parts = self.args.split(" ", 1)
            if len(parts) == 2:
                self.explosive_name = parts[1].strip()
                self.jump_type = "on_explosive"
                return
        
        # Parse for "off" keyword - tactical descent
        if self.args.startswith("off "):
            parts = self.args.split(" ", 1)
            if len(parts) == 2:
                direction_part = parts[1].strip()
                if direction_part.endswith(" edge"):
                    self.direction = direction_part[:-5].strip()  # Remove " edge"
                    self.jump_type = "off_edge"
                    return
        
        # Parse for "across" keyword - gap jumping
        if self.args.startswith("across "):
            parts = self.args.split(" ", 1)
            if len(parts) == 2:
                direction_part = parts[1].strip()
                if direction_part.endswith(" edge"):
                    self.direction = direction_part[:-5].strip()  # Remove " edge"
                    self.jump_type = "across_gap"
                    return

def test_parsing():
    """Test the parsing logic with various inputs"""
    test_cases = [
        # Explosive sacrifice tests
        ("on grenade", "on_explosive", "grenade", None),
        ("on frag", "on_explosive", "frag", None),
        ("on flashbang", "on_explosive", "flashbang", None),
        
        # Edge descent tests
        ("off north edge", "off_edge", None, "north"),
        ("off south edge", "off_edge", None, "south"),
        ("off east edge", "off_edge", None, "east"),
        ("off west edge", "off_edge", None, "west"),
        
        # Gap jumping tests  
        ("across north edge", "across_gap", None, "north"),
        ("across east edge", "across_gap", None, "east"),
        ("across southeast edge", "across_gap", None, "southeast"),
        
        # Invalid cases
        ("", None, None, None),
        ("invalid syntax", None, None, None),
        ("off north", None, None, None),  # Missing "edge"
        ("across south", None, None, None),  # Missing "edge"
        ("on", None, None, None),  # Missing explosive name
    ]
    
    print("Testing CmdJump parsing logic:")
    print("=" * 50)
    
    for args, expected_type, expected_explosive, expected_direction in test_cases:
        cmd = MockCmdJump(args)
        
        # Check results
        success = (
            cmd.jump_type == expected_type and
            cmd.explosive_name == expected_explosive and
            cmd.direction == expected_direction
        )
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} '{args}' -> type:{cmd.jump_type}, explosive:{cmd.explosive_name}, direction:{cmd.direction}")
        
        if not success:
            print(f"    Expected: type:{expected_type}, explosive:{expected_explosive}, direction:{expected_direction}")

if __name__ == "__main__":
    test_parsing()
