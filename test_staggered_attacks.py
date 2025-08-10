#!/usr/bin/env python3
"""
Quick test to demonstrate the staggered attack timing calculation.
"""

def calculate_attack_delay(attacker_position, max_attackers=4):
    """
    Calculate attack delay to stagger combat messages within a round.
    
    Args:
        attacker_position: Position in initiative order (0-based)
        max_attackers: Maximum number of attackers to test
        
    Returns:
        float: Delay in seconds for this attacker's attack
    """
    # Stagger attacks by 1.5 seconds each within the round
    # First attacker goes immediately, subsequent attackers are delayed
    base_delay = attacker_position * 1.5
    
    # Cap at 4.5 seconds to ensure all attacks complete before next round
    return min(base_delay, 4.5)

def test_timing():
    """Test the timing system with different numbers of attackers."""
    print("=== STAGGERED ATTACK TIMING TEST ===")
    print("6-second rounds with staggered attacks:\n")
    
    for num_attackers in [2, 3, 4, 5, 6]:
        print(f"Combat with {num_attackers} attackers:")
        total_time = 0
        
        for pos in range(num_attackers):
            delay = calculate_attack_delay(pos)
            attacker_name = f"Attacker_{pos+1}"
            print(f"  {attacker_name}: {delay}s delay")
            total_time = max(total_time, delay)
        
        print(f"  → All attacks complete by: {total_time}s")
        print(f"  → Time remaining in round: {6.0 - total_time}s")
        print()

if __name__ == "__main__":
    test_timing()
