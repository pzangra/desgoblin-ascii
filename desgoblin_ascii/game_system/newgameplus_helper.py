"""
Helper module for managing New Game+ cycles in the game.
Contains functions to scale difficulty, adjust enemy stats, and handle weapon progression.
"""

import random
from battle_system.weapon import generate_weapon

def get_difficulty_scaling(cycle):
    """
    Returns the difficulty multiplier based on current cycle.
    
    Args:
        cycle: The current New Game+ cycle (0 for base game)
        
    Returns:
        float: Multiplier for enemy stats
    """
    # Base scaling is 1.0, with 20% increase per cycle
    return 1.0 + (cycle * 0.2)

def get_weapon_scaling(cycle):
    """
    Returns the weapon damage multiplier based on current cycle.
    
    Args:
        cycle: The current New Game+ cycle (0 for base game)
        
    Returns:
        float: Multiplier for weapon damage
    """
    # Base scaling is 1.0, with 15% increase per cycle
    return 1.0 + (cycle * 0.15)

def generate_scaled_weapon(tier, cycle):
    """
    Generates a weapon of the given tier, scaled for the current cycle.
    
    Args:
        tier: The weapon tier ('low', 'mid', 'high')
        cycle: The current New Game+ cycle
        
    Returns:
        Weapon: A scaled weapon object
    """
    weapon = generate_weapon(tier)
    if cycle > 0:
        # Scale weapon damage based on cycle
        scale_factor = get_weapon_scaling(cycle)
        weapon.damage = int(weapon.damage * scale_factor)
        weapon.value = int(weapon.value * scale_factor)
        
        # Add cycle indicator to weapon name for higher cycles
        if cycle >= 3:
            weapon.name = f"{weapon.name} +{cycle}"
    
    return weapon

def adjust_enemy_counts_for_cycle(base_low, base_mid, base_high, cycle):
    """
    Adjusts the number of enemies for each tier based on the cycle,
    ensuring the total is exactly 10 enemies.
    
    Args:
        base_low: Base number of low tier enemies
        base_mid: Base number of mid tier enemies
        base_high: Base number of high tier enemies
        cycle: Current New Game+ cycle
        
    Returns:
        tuple: (low_count, mid_count, high_count)
    """
    total_enemies = 10  # Fixed total number of enemies
    
    if cycle <= 3:  # Early cycles (0-3)
        # Start with more low-tier enemies, gradually introducing mid and high
        high_count = min(1 + cycle, 3)  # 1-3 high tier
        remaining = total_enemies - high_count
        mid_count = min(2 + cycle, 4)  # 2-4 mid tier
        low_count = remaining - mid_count
    elif cycle <= 7:  # Mid cycles (4-7)
        # Balanced distribution with increasing high-tier
        high_count = min(3 + (cycle - 3), 5)  # 3-5 high tier
        remaining = total_enemies - high_count
        # Ensure at least 1 low tier enemy
        low_count = max(1, 5 - (cycle - 3))  # Decreasing from 5 to 1
        mid_count = remaining - low_count
    else:  # Late cycles (8+)
        # More high-tier enemies, minimal low-tier
        high_count = 6  # Fixed at 6 high tier for late cycles
        mid_count = 3   # Fixed at 3 mid tier for late cycles
        low_count = 1   # Always keep at least 1 low tier enemy
    
    # Safeguard to ensure exactly 10 enemies total
    # If sum isn't 10, adjust mid_count
    current_total = low_count + mid_count + high_count
    if current_total != total_enemies:
        mid_count += (total_enemies - current_total)
    
    # Ensure no negative counts
    low_count = max(0, low_count)
    mid_count = max(0, mid_count)
    high_count = max(0, high_count)
    
    return (low_count, mid_count, high_count)

def get_final_boss_bonus(cycle):
    """
    Returns special bonuses for the final boss based on cycle.
    
    Args:
        cycle: Current New Game+ cycle
        
    Returns:
        dict: Dictionary of bonus stats
    """
    return {
        'health_multiplier': 1.5 + (cycle * 0.1),
        'damage_multiplier': 1.3 + (cycle * 0.1),
        'armor_bonus': cycle * 2,
        'special_attacks': min(cycle, 3)  # Up to 3 special attacks
    }
