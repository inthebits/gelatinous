#!/usr/bin/env python3
"""
Quick test to demonstrate the staggered attack timing calculation.
"""

# Constants (mirrored from world/combat/constants.py for testing)
COMBAT_ROUND_INTERVAL = 6  # seconds - base combat round duration
STAGGER_DELAY_INTERVAL = 1.5  # seconds - delay between staggered attacks
MAX_STAGGER_DELAY = 4.5  # seconds - maximum delay to ensure completion before next round

def calculate_attack_delay(attacker_position, max_attackers=4):
    """
    Calculate attack delay to stagger combat messages within a round.
    
    Args:
        attacker_position: Position in initiative order (0-based)
        max_attackers: Maximum number of attackers to test
        
    Returns:
        float: Delay in seconds for this attacker's attack
    """
    # Stagger attacks using configurable interval
    # First attacker goes immediately, subsequent attackers are delayed
    base_delay = attacker_position * STAGGER_DELAY_INTERVAL
    
    # Cap at max delay to ensure all attacks complete before next round
    return min(base_delay, MAX_STAGGER_DELAY)

def test_timing():
    """Test the timing system with different numbers of attackers."""
    print("=== STAGGERED ATTACK TIMING TEST ===")
    print(f"{COMBAT_ROUND_INTERVAL}-second rounds with staggered attacks:\n")
    
    for num_attackers in [2, 3, 4, 5, 6]:
        print(f"Combat with {num_attackers} attackers:")
        total_time = 0
        
        for pos in range(num_attackers):
            delay = calculate_attack_delay(pos)
            attacker_name = f"Attacker_{pos+1}"
            print(f"  {attacker_name}: {delay}s delay")
            total_time = max(total_time, delay)
        
        print(f"  → All attacks complete by: {total_time}s")
        print(f"  → Time remaining in round: {COMBAT_ROUND_INTERVAL - total_time}s")
        print()

if __name__ == "__main__":
    test_timing()
