# battle_system/skill.py

import random
from typing import List, Dict, Any, Callable

class Skill:
    """Class representing a skill or ability that can be used in battle."""
    
    def __init__(self, name: str, description: str, skill_type: str, effect_func: Callable, 
                 cooldown: int = 0, mp_cost: int = 0, targeting: str = "single", 
                 stealable: bool = False, stat_cost: Dict[str, int] = None):
        self.name = name
        self.description = description
        self.skill_type = skill_type  # heal, attack, buff, debuff, etc.
        self.effect_func = effect_func  # The function that implements the skill's effect
        self.cooldown = cooldown  # Number of turns before skill can be used again
        self.current_cooldown = 0  # Current cooldown counter
        self.mp_cost = mp_cost  # Magic points cost
        self.targeting = targeting  # single, all, self, etc.
        self.stealable = stealable  # Whether the skill can be stolen from a boss
        self.stat_cost = stat_cost if stat_cost else {}  # Stat cost for stealing the skill
    
    def use(self, user, targets, battle_state):
        """Use the skill if not on cooldown and user has enough MP."""
        if self.current_cooldown > 0:
            print(f"{self.name} is on cooldown. {self.current_cooldown} turns remaining.")
            return False
            
        # Check if user has enough MP if it's a Hero
        if hasattr(user, 'mp') and user.mp < self.mp_cost:
            print(f"Not enough MP to use {self.name}.")
            return False
            
        # Deduct MP if applicable
        if hasattr(user, 'mp'):
            user.mp -= self.mp_cost
            
        # Execute the skill effect
        self.effect_func(user, targets, battle_state)
        
        # Set cooldown
        self.current_cooldown = self.cooldown
        return True
    
    def tick_cooldown(self):
        """Reduce the cooldown by 1 turn."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
            
    def get_display_info(self):
        """Return formatted information about the skill for display."""
        cooldown_info = f"Cooldown: {self.cooldown}" if self.cooldown > 0 else "No cooldown"
        mp_info = f"MP Cost: {self.mp_cost}" if self.mp_cost > 0 else ""
        
        cost_info = ""
        if self.stealable and self.stat_cost:
            costs = ", ".join(f"{k}: {v}" for k, v in self.stat_cost.items())
            cost_info = f" | Stat cost: {costs}"
            
        return f"{self.name} - {self.description} ({cooldown_info}, {mp_info}{cost_info})"


# ==================== SKILL EFFECT FUNCTIONS ====================

# ===== Player Skills =====

def basic_heal(user, targets, battle_state):
    """Heals the target for a small amount."""
    # If no specific targets provided, heal the user
    targets = targets if targets else [user]
    
    for target in targets:
        heal_amount = 30 + (user.level * 3)  # Increased base healing and level scaling
        old_health = target.health
        target.health = min(target.health_max, target.health + heal_amount)
        actual_heal = target.health - old_health
        print(f"{user.name} heals {target.name} for {actual_heal} HP.")

def mega_heal(user, targets, battle_state):
    """Heals the target for a large amount."""
    # If no specific targets provided, heal the user
    targets = targets if targets else [user]
    
    for target in targets:
        heal_amount = 60 + (user.level * 5)  # Increased base healing and level scaling
        old_health = target.health
        target.health = min(target.health_max, target.health + heal_amount)
        actual_heal = target.health - old_health
        print(f"{user.name} uses Mega Heal on {target.name} for {actual_heal} HP.")

def power_strike(user, targets, battle_state):
    """Deals heavy damage to a single target with a chance to critical hit."""
    target = targets[0]
    base_damage = int(user.weapon.damage * 2.0)  # Increased from 1.5x to 2.0x
    level_bonus = user.level * 2
    damage = base_damage + level_bonus
    
    # 25% chance for a critical hit (up from default critical chance)
    if random.randint(1, 100) <= 25:
        damage = int(damage * 1.5)
        print(f"CRITICAL HIT!")
    
    # Apply damage reduction from armor
    damage = max(1, damage - target.armor)
    
    target.take_damage(damage)
    print(f"{user.name} uses Power Strike on {target.name} for {damage} damage!")
    
    # Add a chance to reduce target's defense
    if random.randint(1, 100) <= 20:
        armor_reduction = 2
        target.armor = max(0, target.armor - armor_reduction)
        print(f"{target.name}'s armor was reduced by {armor_reduction}!")

def multi_strike(user, targets, battle_state):
    """Deals moderate damage to multiple targets with increased hit count."""
    base_damage = int(user.weapon.damage * 0.8)  # Increased from 0.7x
    level_bonus = int(user.level * 1.5)
    damage = base_damage + level_bonus
    
    # Get number of hits (2-3 hits)
    hit_count = random.randint(2, 3)
    print(f"{user.name} unleashes a flurry of {hit_count} strikes!")
    
    for target in targets:
        total_damage = 0
        for i in range(hit_count):
            # Apply damage reduction from armor for each hit
            hit_damage = max(1, damage - target.armor)
            target.take_damage(hit_damage)
            total_damage += hit_damage
        
        print(f"{target.name} takes {total_damage} total damage from Multi Strike!")

def defensive_stance(user, targets, battle_state):
    """Increases user's defense for 3 turns and provides damage reduction."""
    buff_amount = 8 + (user.level // 2)  # Increased from 5
    user.armor += buff_amount
    
    # Store the buff in battle state to track duration
    if 'buffs' not in battle_state:
        battle_state['buffs'] = []
        
    battle_state['buffs'].append({
        'name': 'defensive_stance',
        'target': user,
        'stat': 'armor',
        'amount': buff_amount,
        'duration': 3
    })
    
    # Add damage reduction effect
    if 'effects' not in battle_state:
        battle_state['effects'] = {}
    
    battle_state['effects']['damage_reduction'] = {
        'owner': user.name,
        'amount': 25,  # 25% damage reduction
        'duration': 3
    }
    
    print(f"{user.name} assumes a defensive stance! Defense increased by {buff_amount} and damage taken reduced by 25% for 3 turns.")

# ===== Boss Skills =====

def goblins_greed(user, targets, battle_state):
    """Steals gold and heals the user significantly."""
    target = targets[0]
    gold_stolen = min(30, getattr(target, 'cashpile', 0))  # Increased from 20
    
    # Only steal if target has a cashpile attribute
    if hasattr(target, 'cashpile'):
        target.cashpile -= gold_stolen
        target.cashpile = max(0, target.cashpile)  # Ensure cashpile doesn't go negative
    
    heal_amount = int(gold_stolen * 1.0)  # Increased from 0.5x
    user.health = min(user.health_max, user.health + heal_amount)
    print(f"{user.name} steals {gold_stolen} gold and heals for {heal_amount} HP!")
    
    # Add a debuff to target
    if random.randint(1, 100) <= 40:  # 40% chance
        print(f"{target.name} feels demoralized from the theft, reducing their attack power!")
        # In a full implementation, this would apply an attack debuff

def prideful_armor(user, targets, battle_state):
    """Boosts defense based on damage taken with increased scaling."""
    damage_taken = user.health_max - user.health
    defense_boost = int(damage_taken * 0.15)  # Increased from 0.1x
    
    # Store original armor value if not already stored
    if not hasattr(user, 'base_armor'):
        user.base_armor = user.armor
    
    user.armor = user.base_armor + defense_boost
    print(f"{user.name}'s Prideful Armor strengthens! Defense is now {user.armor} (+{defense_boost}).")
    
    # Add thorns effect - damage reflection
    if 'effects' not in battle_state:
        battle_state['effects'] = {}
    
    battle_state['effects']['prideful_reflection'] = {
        'owner': user.name,
        'amount': int(defense_boost * 0.5),  # Reflect damage based on defense boost
        'duration': 3
    }
    
    print(f"{user.name} now reflects {int(defense_boost * 0.5)} damage back to attackers!")

def arcane_pulse(user, targets, battle_state):
    """Deals magic damage to all targets with improved armor penetration."""
    base_damage = 60  # Increased from 40
    
    for target in targets:
        # Magic damage ignores more armor now
        damage = max(1, base_damage - (target.armor // 3))
        target.take_damage(damage)
        print(f"{user.name} hits {target.name} with Arcane Pulse for {damage} damage!")
    
    # Add magic vulnerability debuff
    if 'status_effects' not in battle_state:
        battle_state['status_effects'] = {}
        
    for target in targets:
        if target.name not in battle_state['status_effects']:
            battle_state['status_effects'][target.name] = []
            
        battle_state['status_effects'][target.name].append({
            'effect': 'magic_vulnerable',
            'duration': 2,
            'magnitude': 25  # 25% more magic damage
        })
        
        print(f"{target.name} is vulnerable to magic for 2 turns!")

def shattering_screech(user, targets, battle_state):
    """Stuns all targets for 1 turn and deals sonic damage."""
    # Add damage component
    base_damage = 30 + (getattr(user, 'level', 1) * 3)
    
    for target in targets:
        # Sonic damage ignores some armor
        damage = max(1, base_damage - (target.armor // 2))
        target.take_damage(damage)
        
        # Add stunned status to battle state
        if 'status_effects' not in battle_state:
            battle_state['status_effects'] = {}
            
        if target.name not in battle_state['status_effects']:
            battle_state['status_effects'][target.name] = []
            
        battle_state['status_effects'][target.name].append({
            'effect': 'stunned',
            'duration': 1
        })
        
        print(f"{target.name} takes {damage} sonic damage and is stunned by {user.name}'s Shattering Screech!")

def madness_shout(user, targets, battle_state):
    """Confuses all targets for 2 turns and reduces their defense."""
    for target in targets:
        # Add confusion effect to battle state
        if 'status_effects' not in battle_state:
            battle_state['status_effects'] = {}
            
        if target.name not in battle_state['status_effects']:
            battle_state['status_effects'][target.name] = []
            
        battle_state['status_effects'][target.name].append({
            'effect': 'confused',
            'duration': 2
        })
        
        # New: Add defense reduction
        armor_reduction = 3
        target.armor = max(0, target.armor - armor_reduction)
        
        print(f"{target.name} is confused by {user.name}'s Madness Shout and loses {armor_reduction} defense!")

def life_drain(user, targets, battle_state):
    """Drains health from the target to heal the user with increased effectiveness."""
    target = targets[0]
    damage = 40  # Increased from 25
    
    # Apply damage reduction from armor
    damage = max(1, damage - (target.armor // 2))
    
    # Deal damage
    target.take_damage(damage)
    
    # Heal user for 80% of damage dealt
    heal_amount = int(damage * 0.8)  # Increased from 75%
    user.health = min(user.health_max, user.health + heal_amount)
    
    print(f"{user.name} drains {damage} HP from {target.name} and heals for {heal_amount} HP!")
    
    # Add weakening effect
    if random.randint(1, 100) <= 40:  # 40% chance
        print(f"{target.name} feels weakened from the life drain!")
        # In a full implementation, this would add a stat debuff

def shadow_strike(user, targets, battle_state):
    """Strikes from the shadows for massive damage and ignores some armor."""
    target = targets[0]
    
    # Calculate base damage
    if hasattr(user, 'weapon'):
        damage = user.weapon.damage * 2.5  # Increased from 2.0x
    else:
        damage = 50  # Increased from 30
    
    level_bonus = getattr(user, 'level', 1) * 3
    damage += level_bonus
    
    # Shadow Strike ignores 30% of target's armor
    armor_ignored = int(target.armor * 0.3)
    effective_armor = target.armor - armor_ignored
    
    # Apply damage reduction from remaining armor
    damage = max(1, damage - effective_armor)
    
    target.take_damage(damage)
    print(f"{user.name} emerges from the shadows and strikes {target.name} for {damage} damage!")
    print(f"Shadow Strike ignored {armor_ignored} armor!")

def goblin_horde(user, targets, battle_state):
    """Summons goblin minions to attack with improved damage and effects."""
    damage_per_goblin = 15  # Increased from 10
    num_goblins = random.randint(3, 5)  # Increased from 2-4
    
    print(f"{user.name} summons {num_goblins} goblin minions!")
    
    for target in targets:
        total_damage = 0
        
        for i in range(num_goblins):
            # Each goblin does damage reduced by armor
            goblin_damage = max(1, damage_per_goblin - (target.armor // 2))
            total_damage += goblin_damage
            
            # Each goblin has a chance to apply a small debuff
            if random.randint(1, 100) <= 15:  # 15% chance per goblin
                print(f"Goblin #{i+1} slashes at {target.name}'s defenses!")
                # In a full implementation, this would apply a small temporary debuff
            
        target.take_damage(total_damage)
        print(f"The goblin horde attacks {target.name} for {total_damage} damage!")

# ===== Troll Champion Skills =====

def troll_blood(user, targets, battle_state):
    """Passively heals the Troll Champion each turn with improved healing."""
    heal_amount = int(user.health_max * 0.08)  # Increased from 5%
    old_health = user.health
    user.health = min(user.health_max, user.health + heal_amount)
    actual_heal = user.health - old_health
    print(f"{user.name}'s Troll Blood regenerates {actual_heal} HP!")

def bonecrusher_fist(user, targets, battle_state):
    """Deals damage and reduces the target's armor significantly."""
    target = targets[0]
    damage = 60  # Increased from 45
    
    # Apply damage reduction from armor
    damage = max(1, damage - target.armor)
    
    # Deal damage
    target.take_damage(damage)
    
    # Reduce target's armor
    armor_reduction = 7  # Increased from 5
    target.armor = max(0, target.armor - armor_reduction)
    
    # Store the armor reduction in battle state for display purposes
    if 'stats_debuffs' not in battle_state:
        battle_state['stats_debuffs'] = {}
    
    if target.name not in battle_state['stats_debuffs']:
        battle_state['stats_debuffs'][target.name] = []
    
    battle_state['stats_debuffs'][target.name].append({
        'stat': 'armor',
        'amount': -armor_reduction,
        'source': 'bonecrusher_fist',
        'duration': -1  # Permanent
    })
    
    print(f"{user.name} hits {target.name} with Bonecrusher Fist for {damage} damage! {target.name}'s armor reduced by {armor_reduction}.")
    
    # Add stagger effect with a chance
    if random.randint(1, 100) <= 30:  # 30% chance
        print(f"{target.name} is staggered by the powerful blow!")
        # In a full implementation, this would add a "staggered" status effect

def frenzied_counter(user, targets, battle_state):
    """Counters an attack with a powerful strike and has a chance to stun."""
    target = targets[0]
    damage = 45  # Increased from 30
    
    # Apply damage reduction from armor
    damage = max(1, damage - target.armor)
    
    target.take_damage(damage)
    print(f"{user.name} counters {target.name}'s attack with Frenzied Counter for {damage} damage!")
    
    # Add chance to briefly stun the target
    if random.randint(1, 100) <= 25:  # 25% chance
        # Add stunned status to battle state
        if 'status_effects' not in battle_state:
            battle_state['status_effects'] = {}
            
        if target.name not in battle_state['status_effects']:
            battle_state['status_effects'][target.name] = []
            
        battle_state['status_effects'][target.name].append({
            'effect': 'stunned',
            'duration': 1
        })
        
        print(f"{target.name} is briefly stunned by the counter attack!")

def vengeful_roar(user, targets, battle_state):
    """Increases attack power as health drops with improved scaling."""
    health_ratio = user.health / user.health_max
    attack_boost = int((1 - health_ratio) * 30)  # Increased from 20
    
    # For display purposes - show effect
    print(f"{user.name} lets out a Vengeful Roar, drawing strength from their wounds!")
    print(f"{user.name}'s attack increases proportionally to damage taken!")
    
    # This is a passive effect that will be calculated when the boss attacks
    # We'll store this information in the battle state
    if 'boss_effects' not in battle_state:
        battle_state['boss_effects'] = {}
    
    battle_state['boss_effects']['vengeful_roar'] = {
        'active': True,
        'attack_boost': attack_boost
    }
    
    # Add a self-buff to crit chance
    crit_boost = int((1 - health_ratio) * 15)  # Up to 15% crit chance boost at low health
    
    if 'buffs' not in battle_state:
        battle_state['buffs'] = []
        
    battle_state['buffs'].append({
        'name': 'vengeful_crit',
        'target': user,
        'stat': 'crit_ch',
        'amount': crit_boost,
        'duration': 3
    })
    
    print(f"Current attack boost: +{attack_boost} damage")
    print(f"Critical hit chance increased by {crit_boost}% for 3 turns!")

def brutal_slam(user, targets, battle_state):
    """Stuns the target with a powerful ground slam and deals significant damage."""
    target = targets[0]
    damage = 50  # Increased from 35
    
    # Apply damage reduction from armor
    damage = max(1, damage - target.armor)
    
    # Deal damage
    target.take_damage(damage)
    
    # Apply stun status effect
    if 'status_effects' not in battle_state:
        battle_state['status_effects'] = {}
        
    if target.name not in battle_state['status_effects']:
        battle_state['status_effects'][target.name] = []
        
    battle_state['status_effects'][target.name].append({
        'effect': 'stunned',
        'duration': 2
    })
    
    print(f"{user.name} slams {target.name} with a ground-shaking blow for {damage} damage!")
    print(f"{target.name} is stunned for 2 turns!")
    
    # Area effect damage to other targets (if any)
    area_damage = int(damage * 0.4)
    area_targets = [t for t in targets if t != target]
    
    if area_targets:
        for area_target in area_targets:
            # Apply damage reduction from armor
            final_area_damage = max(1, area_damage - area_target.armor)
            area_target.take_damage(final_area_damage)
            print(f"The shockwave hits {area_target.name} for {final_area_damage} damage!")

# ===== Pannocchia Skills =====

def greed_harvest(user, targets, battle_state):
    """
    Greed's Harvest: Steals health and resources from the enemy.
    Drains a portion of the target's health and, if available,
    steals a portion of a resource (e.g. gold, mana).
    """
    target = targets[0]
    # Steal 20% of target's current health, minimum 1.
    steal_amount = max(1, int(target.health * 0.2))
    target.take_damage(steal_amount)
    user.health = min(user.health_max, user.health + steal_amount)
    print(f"{user.name} uses Greed's Harvest on {target.name}, stealing {steal_amount} HP.")
    # If the target has an attribute 'resource', steal 10% of it.
    if hasattr(target, 'mp'):
        resource_stolen = max(1, int(target.mp * 0.1))
        target.mp = max(0, target.mp - resource_stolen)
        if hasattr(user, 'mp'):
            user.mp = min(getattr(user, 'mp_max', user.mp + 100), user.mp + resource_stolen)
        print(f"{user.name} also steals {resource_stolen} MP from {target.name}.")

def entropic_bloom(user, targets, battle_state):
    """
    Entropic Bloom: Releases a burst of corrupted energy, damaging all enemies.
    """
    base_damage = 50
    print(f"{user.name} unleashes Entropic Bloom!")
    for target in targets:
        # Damage calculation: basic damage reduced by one-fourth of target armor.
        damage = max(1, base_damage - (target.armor // 4))
        target.take_damage(damage)
        print(f"{target.name} takes {damage} corrupted damage from Entropic Bloom!")

def rooted_despair(user, targets, battle_state):
    """
    Rooted Despair: Immobilizes all enemies and saps their health.
    Each enemy loses a fixed amount of health and is immobilized for 2 turns.
    """
    drain_amount = 30
    for target in targets:
        target.take_damage(drain_amount)
        # Apply the immobilize effect to the target.
        if 'status_effects' not in battle_state:
            battle_state['status_effects'] = {}
        if target.name not in battle_state['status_effects']:
            battle_state['status_effects'][target.name] = []
        battle_state['status_effects'][target.name].append({
            'effect': 'immobilized',
            'duration': 2
        })
        print(f"{user.name} uses Rooted Despair on {target.name}: draining {drain_amount} HP and immobilizing for 2 turns.")

def thorned_armor(user, targets, battle_state):
    """
    Thorned Armor: Increases defense while dealing damage to attackers.
    Boosts the boss's armor immediately and sets a reflective effect for 3 turns.
    """
    defense_boost = 15
    user.armor += defense_boost
    # Register a reflect effect into the battle state.
    if 'effects' not in battle_state:
        battle_state['effects'] = {}
    battle_state['effects']['thorned_armor'] = {
        'owner': user.name,
        'reflect_damage': int(defense_boost * 0.5),
        'duration': 3
    }
    print(f"{user.name} uses Thorned Armor, increasing defense by {defense_boost} and reflecting damage for 3 turns.")

def siphon_life(user, targets, battle_state):
    """
    Siphon Life: Drains the life force of enemies over time.
    Applies a damage-over-time effect on a single enemy.
    """
    duration = 3
    dot_damage = 20  # Damage dealt per turn.
    target = targets[0]
    if 'status_effects' not in battle_state:
        battle_state['status_effects'] = {}
    if target.name not in battle_state['status_effects']:
        battle_state['status_effects'][target.name] = []
    battle_state['status_effects'][target.name].append({
        'effect': 'siphon_life',
        'duration': duration,
        'dot_damage': dot_damage,
        'source': user.name
    })
    print(f"{user.name} applies Siphon Life on {target.name}, draining {dot_damage} HP per turn for {duration} turns.")

# ===== Rat King of the Lemurs Skills =====

def pestilent_wave(user, targets, battle_state):
    """
    Pestilent Wave: Summons a wave of rats that carry disease to enemies.
    Damages all targets and applies a 'diseased' debuff for 2 turns.
    """
    base_damage = 40
    print(f"{user.name} unleashes Pestilent Wave!")
    for target in targets:
        # Damage is reduced slightly by the target's armor.
        damage = max(1, base_damage - (target.armor // 5))
        target.take_damage(damage)
        
        # Apply disease status effect: damage over time for 2 turns.
        if "status_effects" not in battle_state:
            battle_state["status_effects"] = {}
        if target.name not in battle_state["status_effects"]:
            battle_state["status_effects"][target.name] = []
        battle_state["status_effects"][target.name].append({
            "effect": "diseased",
            "duration": 2,
            "dot_damage": 10  # Damage per turn due to disease
        })
        print(f"{target.name} takes {damage} damage and is afflicted with disease for 2 turns.")

def rat_kings_wrath(user, targets, battle_state):
    """
    Rat King's Wrath: Deals a flurry of blows with increased damage to a single target.
    Performs multiple rapid hits.
    """
    target = targets[0]
    hits = 3
    total_damage = 0
    print(f"{user.name} launches Rat King's Wrath!")
    for i in range(hits):
        # Each hit factors in base damage, user level, and a slight reduction from target armor.
        hit_damage = max(1, 25 + (user.level * 2) - (target.armor // 3))
        target.take_damage(hit_damage)
        total_damage += hit_damage
        print(f"Hit {i+1}: {target.name} takes {hit_damage} damage.")
    print(f"{user.name} deals a total of {total_damage} damage with Rat King's Wrath!")

def swarm_call(user, targets, battle_state):
    """
    Swarm Call: Summons a swarm of rats to overwhelm the enemy.
    The swarm consists of several rat minions that each deal a small amount of damage.
    """
    target = targets[0]
    num_rats = random.randint(4, 7)
    per_rat_damage = 5
    total_damage = 0
    print(f"{user.name} summons a swarm of {num_rats} rats!")
    for _ in range(num_rats):
        rat_damage = max(1, per_rat_damage - (target.armor // 10))
        target.take_damage(rat_damage)
        total_damage += rat_damage
    print(f"The rat swarm deals a total of {total_damage} damage to {target.name}!")

def infectious_bite(user, targets, battle_state):
    """
    Infectious Bite: Deals a poison attack that spreads to other enemies over time.
    Applies immediate damage and inflicts a poison debuff for 3 turns.
    """
    target = targets[0]
    immediate_damage = 15
    target.take_damage(immediate_damage)
    print(f"{user.name} bites {target.name} for {immediate_damage} initial poison damage!")
    
    # Apply a poison status effect with a chance to spread.
    if "status_effects" not in battle_state:
        battle_state["status_effects"] = {}
    if target.name not in battle_state["status_effects"]:
        battle_state["status_effects"][target.name] = []
    battle_state["status_effects"][target.name].append({
        "effect": "poisoned",
        "duration": 3,
        "dot_damage": 10,  # Damage over time due to poison
        "spread": True     # Indicates potential to spread to nearby enemies
    })
    print(f"{target.name} is now poisoned for 3 turns, with potential to spread to others!")

def rats_gluttony(user, targets, battle_state):
    """
    Rat's Gluttony: Gains health for each enemy killed.
    Deals minor damage to enemies and heals the user for each enemy that falls.
    """
    total_heal = 0
    for target in targets:
        damage = 20
        target.take_damage(damage)
        # Check if the target is killed by this damage.
        if target.health == 0:
            heal_amount = 30
            total_heal += heal_amount
            print(f"{target.name} has been killed by Rat's Gluttony!")
        else:
            print(f"{target.name} takes {damage} damage from Rat's Gluttony!")
    if total_heal > 0:
        user.health = min(user.health_max, user.health + total_heal)
        print(f"{user.name} gains {total_heal} HP from the fallen enemies!")

# ===== African Turtle Skills =====

def crushing_claw(user, targets, battle_state):
    """
    Crushing Claw: Strikes the enemy with immense force, breaking armor.
    Deals damage based on base damage plus level scaling and reduces enemy armor.
    """
    target = targets[0]
    # Calculate damage: a base damage plus level bonus.
    base_damage = 70
    level_bonus = user.level * 3
    raw_damage = base_damage + level_bonus
    # Apply standard damage reduction: final_damage = max(1, raw_damage - target.armor)
    final_damage = max(1, raw_damage - target.armor)
    target.take_damage(final_damage)
    # "Breaking armor": reduce enemy armor by a fixed value (e.g., 5).
    if hasattr(target, 'armor'):
        target.armor = max(0, target.armor - 5)
    print(f"{user.name} uses Crushing Claw on {target.name} dealing {final_damage} damage and reducing their armor by 5.")

def oceanic_devastation(user, targets, battle_state):
    """
    Oceanic Devastation: Unleashes a cataclysmic wave that damages all enemies.
    Each target receives damage calculated against its armor.
    """
    base_damage = 80  # A strong base damage representing the devastating wave.
    print(f"{user.name} unleashes Oceanic Devastation!")
    for target in targets:
        # Damage calculation considers half of enemy's armor.
        damage = max(1, base_damage - (target.armor // 2))
        target.take_damage(damage)
        print(f"{target.name} suffers {damage} damage from Oceanic Devastation.")

def saltwater_healing(user, targets, battle_state):
    """
    Saltwater Healing: Activates a regeneration effect that heals the Turtle over time when in water.
    The effect lasts for a set duration and heals a fixed amount each turn.
    """
    duration = 3     # Effect lasts for 3 turns.
    heal_per_turn = 25  # Heals 25 HP each turn.
    
    # Add immediate healing for instant feedback
    immediate_heal = 12
    old_health = user.health
    user.health = min(user.health_max, user.health + immediate_heal)
    actual_heal = user.health - old_health
    
    # Register the regeneration effect in the battle state for subsequent turn processing.
    if "regeneration" not in battle_state:
        battle_state["regeneration"] = {}
    battle_state["regeneration"][user.name] = {
        "heal_per_turn": heal_per_turn,
        "duration": duration
    }
    return f"{user.name} activates Saltwater Healing, healing {actual_heal} HP immediately and {heal_per_turn} HP per turn for {duration} turns."

def shell_counter(user, targets, battle_state):
    """
    Shell Counter: Every time the Turtle is hit, it counters with a defensive strike.
    Deals a fixed amount of counter damage to the attacker.
    """
    # In this simulation, we treat the counter as an active skill for demo purposes.
    attacker = targets[0]
    counter_damage = 30  # Fixed counter damage.
    attacker.take_damage(counter_damage)
    print(f"{user.name} triggers Shell Counter, dealing {counter_damage} counter damage to {attacker.name}!")

def unbreakable_defense(user, targets, battle_state):
    """
    Unbreakable Defense: Greatly increases the Turtle's defense for a short period.
    Increases armor immediately and registers a buff effect in the battle state.
    """
    defense_boost = 20  # A significant boost to armor.
    user.armor += defense_boost
    if "buffs" not in battle_state:
        battle_state["buffs"] = []
    battle_state["buffs"].append({
        "name": "Unbreakable Defense",
        "target": user,
        "stat": "armor",
        "amount": defense_boost,
        "duration": 3
    })
    print(f"{user.name} activates Unbreakable Defense, increasing armor by {defense_boost} for 3 turns.")

# ==================== Ultras Penguin's Skill Effect Functions ====================

def penguin_smash(user, targets, battle_state):
    """
    Penguin Smash: Deals a powerful physical attack that shatters enemy defenses.
    A high-damage strike with level scaling and partial armor ignore.
    """
    target = targets[0]
    # Calculate damage: base plus level bonus. This attack ignores 20% of the target's armor.
    base_damage = 80
    level_bonus = user.level * 4 if hasattr(user, 'level') else 20
    raw_damage = base_damage + level_bonus
    armor_ignored = int(target.armor * 0.2)
    effective_armor = max(0, target.armor - armor_ignored)
    final_damage = max(1, raw_damage - effective_armor)
    target.take_damage(final_damage)
    return f"{user.name} uses Penguin Smash on {target.name} dealing {final_damage} damage (ignores {armor_ignored} armor)."

def glacial_volley(user, targets, battle_state):
    """
    Glacial Volley: Sends out a sweeping volley of freezing energy hitting all enemies.
    Each enemy takes damage reduced slightly by its armor.
    """
    base_damage = 60
    messages = [f"{user.name} unleashes Glacial Volley!"]
    for target in targets:
        # Damage is reduced by one-third of the target's armor.
        damage = max(1, base_damage - (target.armor // 3))
        target.take_damage(damage)
        messages.append(f"{target.name} suffers {damage} damage from Glacial Volley.")
    return "\n".join(messages)

def frozen_huddle(user, targets, battle_state):
    """
    Frozen Huddle: Recovers health over time as ultras rally in a frigid group huddle.
    Registers a regeneration effect in the battle state.
    """
    duration = 3      # Lasts 3 turns.
    heal_per_turn = 20  # Heals 20 HP per turn.
    
    # Add immediate healing for instant feedback
    immediate_heal = 10
    old_health = user.health
    user.health = min(user.health_max, user.health + immediate_heal)
    actual_heal = user.health - old_health
    
    # Store the regeneration in battle_state.
    if "regeneration" not in battle_state:
        battle_state["regeneration"] = {}
    battle_state["regeneration"][user.name] = {
        "heal_per_turn": heal_per_turn,
        "duration": duration
    }
    return f"{user.name} enters a Frozen Huddle, healing {actual_heal} HP immediately and {heal_per_turn} HP per turn for {duration} turns."

def ultras_pride(user, targets, battle_state):
    """
    Ultras' Pride: Boosts attack and defense when health is below half.
    Activated when the boss is under pressure, channeling ultra chants.
    """
    if user.health < (user.health_max // 2):
        attack_boost = 10  # Flat boost to attack.
        defense_boost = 15  # Flat boost to defense.
        
        # Register the buff in battle state
        if "buffs" not in battle_state:
            battle_state["buffs"] = []
        battle_state["buffs"].append({
            "name": "Ultras' Pride",
            "target": user,
            "stats": {"armor": defense_boost},
            "duration": 3
        })
        
        # Apply armor buff directly
        user.armor += defense_boost
        
        return f"{user.name} channels Ultras' Pride! Attack increased by {attack_boost} and defense by {defense_boost} for 3 turns."
    else:
        return f"{user.name}'s health is above half; Ultras' Pride is not activated."

def icy_counter_chant(user, targets, battle_state):
    """
    Icy Counter-Chant: Automatically retaliates against an attacker with a burst of freezing energy.
    In this simulation, it deals fixed damage to a single enemy target.
    """
    attacker = targets[0]
    counter_damage = 25  # Fixed counter damage.
    attacker.take_damage(counter_damage)
    return f"{user.name} triggers Icy Counter-Chant, dealing {counter_damage} counter damage to {attacker.name}."

# ==================== Bard Gargoyle's Skill Effect Functions ====================

def bard_wrath(user, targets, battle_state):
    """
    Bard's Wrath: Deals massive damage to a single enemy caught in a sonic blast.
    Combines a high base damage with level scaling.
    """
    target = targets[0]
    base_damage = 100
    level_bonus = user.level * 5 if hasattr(user, 'level') else 25
    raw_damage = base_damage + level_bonus
    # Apply standard damage reduction
    final_damage = max(1, raw_damage - target.armor)
    target.take_damage(final_damage)
    return f"{user.name} unleashes Bard's Wrath on {target.name}, dealing {final_damage} damage!"

def soundwave_burst(user, targets, battle_state):
    """
    Soundwave Burst: Emits a broad sonic blast that damages all enemies.
    Each enemy takes damage reduced by a fraction of their armor.
    """
    base_damage = 70
    messages = [f"{user.name} releases a Soundwave Burst!"]
    for target in targets:
        damage = max(1, base_damage - (target.armor // 2))
        target.take_damage(damage)
        messages.append(f"{target.name} takes {damage} damage from the Soundwave Burst.")
    return "\n".join(messages)

def echo_of_life(user, targets, battle_state):
    """
    Echo of Life: Restores health over time by absorbing echoes of past battles.
    Registers a regeneration effect in the battle state.
    """
    duration = 3            # Lasts for 3 turns.
    heal_per_turn = 30      # Heals 30 HP per turn.
    
    # Add immediate healing for instant feedback
    immediate_heal = 15
    old_health = user.health
    user.health = min(user.health_max, user.health + immediate_heal)
    actual_heal = user.health - old_health
    
    if "regeneration" not in battle_state:
        battle_state["regeneration"] = {}
    battle_state["regeneration"][user.name] = {
        "heal_per_turn": heal_per_turn,
        "duration": duration
    }
    return f"{user.name} activates Echo of Life, healing {actual_heal} HP immediately and {heal_per_turn} HP per turn for {duration} turns."

def reverberating_strike(user, targets, battle_state):
    """
    Reverberating Strike: Automatically retaliates against an incoming attack with a burst of sonic damage.
    For demonstration, this function deals fixed counter damage to a single attacker.
    """
    attacker = targets[0]
    counter_damage = 25  # Fixed counter damage.
    attacker.take_damage(counter_damage)
    return f"{user.name} counters with Reverberating Strike, dealing {counter_damage} damage to {attacker.name}."

def dissonance(user, targets, battle_state):
    """
    Dissonance: Lowers the attack and defense of all enemies with a discordant sound.
    Reduces enemy attack and defense for a few turns.
    """
    reduction_attack = 5
    reduction_armor = 3
    duration = 3  # Lasts 3 turns.
    messages = [f"{user.name} plays Dissonance, unsettling all foes!"]
    
    for target in targets:
        # Apply debuffs to stats if they exist
        if hasattr(target, 'attack'):
            target.attack = max(0, target.attack - reduction_attack)
        if hasattr(target, 'armor'):
            target.armor = max(0, target.armor - reduction_armor)
        
        # Register a status effect on the target
        if "status_effects" not in battle_state:
            battle_state["status_effects"] = {}
        if target.name not in battle_state["status_effects"]:
            battle_state["status_effects"][target.name] = []
        
        battle_state["status_effects"][target.name].append({
            "effect": "dissonance",
            "duration": duration,
            "attack_reduction": reduction_attack,
            "armor_reduction": reduction_armor
        })
        
        messages.append(f"{target.name}'s attack reduced by {reduction_attack} and armor by {reduction_armor} for {duration} turns.")
    
    return "\n".join(messages)

# ==================== Sexy Fox's Skill Effect Functions ====================

def fox_wrath(user, targets, battle_state):
    """
    Fox's Wrath (Special):
    Unleashes a powerful sonic attack that devastates the target and leaves them charmed.
    The damage scales with the boss's level and partially ignores the target's armor.
    """
    target = targets[0]
    base_damage = 90
    level_bonus = user.level * 5 if hasattr(user, 'level') else 25
    raw_damage = base_damage + level_bonus
    # Ignore 20% of the target's armor
    armor_ignored = int(target.armor * 0.2)
    effective_armor = max(0, target.armor - armor_ignored)
    final_damage = max(1, raw_damage - effective_armor)
    target.take_damage(final_damage)
    # Apply a charm effect
    if "status_effects" not in battle_state:
        battle_state["status_effects"] = {}
    if target.name not in battle_state["status_effects"]:
        battle_state["status_effects"][target.name] = []
    battle_state["status_effects"][target.name].append({
        "effect": "charmed",
        "duration": 2
    })
    return f"{user.name} uses Fox's Wrath on {target.name}, dealing {final_damage} damage and charming the target!"

def seductive_flame(user, targets, battle_state):
    """
    Seductive Flame (Magic):
    Summons a magical fire that burns the enemy and partially charms them,
    reducing their attack power for a brief period.
    """
    target = targets[0]
    base_damage = 70
    level_bonus = user.level * 3 if hasattr(user, 'level') else 15
    raw_damage = base_damage + level_bonus
    final_damage = max(1, raw_damage - target.armor)
    target.take_damage(final_damage)
    # Apply a debuff that reduces target's attack power.
    if "status_effects" not in battle_state:
        battle_state["status_effects"] = {}
    if target.name not in battle_state["status_effects"]:
        battle_state["status_effects"][target.name] = []
    battle_state["status_effects"][target.name].append({
        "effect": "charmed",
        "duration": 2,
        "attack_reduction": 5
    })
    return f"{user.name} launches Seductive Flame at {target.name}, dealing {final_damage} damage and reducing their attack power!"

def allure_of_life(user, targets, battle_state):
    """
    Allure of Life (Regeneration):
    Activates a regeneration effect by absorbing the life force of admiring foes.
    The boss will heal a fixed amount every turn for a set duration.
    """
    duration = 3      # Regeneration lasts for 3 turns.
    heal_per_turn = 30  # Heals 30 HP each turn.
    
    # Apply immediate healing to demonstrate the effect
    immediate_heal = 15  # Small immediate heal to show the effect working
    user.health = min(user.health_max, user.health + immediate_heal)
    
    # Set up regeneration effect as before
    if "regeneration" not in battle_state:
        battle_state["regeneration"] = {}
    battle_state["regeneration"][user.name] = {
        "heal_per_turn": heal_per_turn,
        "duration": duration
    }
    
    return f"{user.name} activates Allure of Life, healing {immediate_heal} HP immediately and {heal_per_turn} HP per turn for {duration} turns."

def charming_counter(user, targets, battle_state):
    """
    Charming Counter (Counter):
    When struck, the boss retaliates by charming the attacker and dealing a burst of damage.
    """
    attacker = targets[0]
    counter_damage = 20  # Fixed counter damage.
    attacker.take_damage(counter_damage)
    # Apply a charm effect to the attacker.
    if "status_effects" not in battle_state:
        battle_state["status_effects"] = {}
    if attacker.name not in battle_state["status_effects"]:
        battle_state["status_effects"][attacker.name] = []
    battle_state["status_effects"][attacker.name].append({
        "effect": "charmed",
        "duration": 1
    })
    return f"{user.name} triggers Charming Counter, dealing {counter_damage} damage and charming {attacker.name}."

def love_drain(user, targets, battle_state):
    """
    Love Drain (Drain):
    Absorbs health from the enemy, transferring a portion of the damage as healing to the boss.
    This only affects enemies already charmed by the boss.
    """
    target = targets[0]
    drain_damage = 30  # Base damage that triggers the drain.
    target.take_damage(drain_damage)
    heal_amount = int(drain_damage * 0.8)  # Boss heals for 80% of damage dealt.
    user.health = min(user.health_max, user.health + heal_amount)
    return f"{user.name} uses Love Drain on {target.name}, dealing {drain_damage} damage and healing for {heal_amount} HP."

# ==================== Broken Salamander's Skill Effect Functions ====================

def salamanders_wrath(user, targets, battle_state):
    """
    Salamander's Wrath (Special):
    Unleashes the full power of fire on a single enemy.
    Damage is calculated with a high base and level scaling,
    subtracting the target's armor.
    """
    target = targets[0]
    base_damage = 120
    level_bonus = user.level * 6 if hasattr(user, 'level') else 30
    raw_damage = base_damage + level_bonus
    final_damage = max(1, raw_damage - target.armor)
    target.take_damage(final_damage)
    return f"{user.name} unleashes Salamander's Wrath on {target.name}, dealing {final_damage} damage!"

def volcanic_eruption(user, targets, battle_state):
    """
    Volcanic Eruption (Area):
    Triggers a volcanic explosion that damages all enemies.
    Each enemy takes damage that is reduced by a portion of its armor.
    """
    base_damage = 100
    messages = [f"{user.name} causes a Volcanic Eruption!"]
    for target in targets:
        damage = max(1, base_damage - (target.armor // 2))
        target.take_damage(damage)
        messages.append(f"{target.name} takes {damage} damage from the eruption.")
    return "\n".join(messages)

def phoenix_rebirth(user, targets, battle_state):
    """
    Phoenix Rebirth (Regeneration):
    Fully heals the boss when its health is critically low (below 30% of max).
    This effect can be used once per battle.
    """
    # Check if the ability has already been used.
    if battle_state.get("phoenix_rebirth_used", False):
        return f"{user.name} has already used Phoenix Rebirth this battle!"

    # Trigger only if health is below 30% of maximum.
    if user.health < (0.3 * user.health_max):
        user.health = user.health_max
        battle_state["phoenix_rebirth_used"] = True
        return f"{user.name} activates Phoenix Rebirth and is fully healed!"
    else:
        return f"{user.name}'s health is too high to trigger Phoenix Rebirth."

def flame_retaliation(user, targets, battle_state):
    """
    Flame Retaliation (Counter):
    When hit, the boss counters with a burst of fire.
    Here we simulate it as a skill that deals fixed counter damage to a single attacker.
    """
    attacker = targets[0]
    counter_damage = 30
    attacker.take_damage(counter_damage)
    return f"{user.name} counters with Flame Retaliation, dealing {counter_damage} fire damage to {attacker.name}!"

def fire_drain(user, targets, battle_state):
    """
    Fire Drain (Drain):
    Deals fire damage to an enemy and heals the boss by 80% of the damage dealt.
    Intended to trigger after the enemy is already burning.
    """
    target = targets[0]
    drain_damage = 40
    target.take_damage(drain_damage)
    heal_amount = int(drain_damage * 0.8)
    user.health = min(user.health_max, user.health + heal_amount)
    return f"{user.name} uses Fire Drain on {target.name}, dealing {drain_damage} damage and healing for {heal_amount} HP!"

# ==================== Gargololo's Skill Effect Functions ====================

def cosmic_dissonance(user, targets, battle_state):
    """
    Cosmic Dissonance (Debuff):
    Unleashes an otherworldly discord that lowers the attack and defense of all enemies.
    """
    reduction_attack = 7
    reduction_defense = 5
    duration = 3
    messages = [f"{user.name} emits Cosmic Dissonance!"]
    for target in targets:
        if hasattr(target, 'attack'):
            target.attack = max(0, target.attack - reduction_attack)
        if hasattr(target, 'armor'):
            target.armor = max(0, target.armor - reduction_defense)
        # Register status effect in battle_state
        if "status_effects" not in battle_state:
            battle_state["status_effects"] = {}
        if target.name not in battle_state["status_effects"]:
            battle_state["status_effects"][target.name] = []
        battle_state["status_effects"][target.name].append({
            "effect": "cosmic_dissonance",
            "duration": duration,
            "attack_reduction": reduction_attack,
            "defense_reduction": reduction_defense
        })
        messages.append(f"{target.name} loses {reduction_attack} attack and {reduction_defense} defense for {duration} turns.")
    return "\n".join(messages)

def abyssal_dominion(user, targets, battle_state):
    """
    Abyssal Dominion (Curse):
    Marks a single enemy with a binding curse that causes them to take an additional 20% damage.
    """
    target = targets[0]
    duration = 3
    if "curses" not in battle_state:
        battle_state["curses"] = {}
    if target.name not in battle_state["curses"]:
        battle_state["curses"][target.name] = []
    battle_state["curses"][target.name].append({
        "effect": "abyssal_dominion",
        "duration": duration,
        "extra_damage_pct": 20
    })
    return f"{user.name} imposes Abyssal Dominion on {target.name}, increasing all damage they take by 20% for {duration} turns."

def titanic_rebirth(user, targets, battle_state):
    """
    Titanic Rebirth (Regeneration):
    When Gargololo's health falls below 25%, this once-per-battle ability fully restores its health.
    """
    if battle_state.get("titanic_rebirth_used", False):
        return f"{user.name} has already used Titanic Rebirth!"
    if user.health < (0.25 * user.health_max):
        user.health = user.health_max
        battle_state["titanic_rebirth_used"] = True
        return f"{user.name} activates Titanic Rebirth and is fully restored!"
    else:
        return f"{user.name}'s health is too high for Titanic Rebirth."

def molten_vortex(user, targets, battle_state):
    """
    Molten Vortex (Area Attack):
    Conjures a swirling vortex that deals blended fire and poison damage to all enemies.
    """
    base_damage = 80
    level_bonus = user.level * 4 if hasattr(user, 'level') else 40
    total_damage = base_damage + level_bonus
    duration = 2  # effect duration for burn/poison
    messages = [f"{user.name} summons a Molten Vortex!"]
    for target in targets:
        damage = max(1, total_damage - (target.armor // 2))
        target.take_damage(damage)
        # Apply a combined burn/poison debuff in battle_state.
        if "status_effects" not in battle_state:
            battle_state["status_effects"] = {}
        if target.name not in battle_state["status_effects"]:
            battle_state["status_effects"][target.name] = []
        battle_state["status_effects"][target.name].append({
            "effect": "molten_vortex",
            "duration": duration,
            "burn_damage": 10  # additional damage per turn
        })
        messages.append(f"{target.name} takes {damage} damage and suffers burn for {duration} turns.")
    return "\n".join(messages)

def spectral_onslaught(user, targets, battle_state):
    """
    Spectral Onslaught (Summon/Special):
    Summons ghostly minions that barrage all enemies; the attack deals damage based on a fraction of the boss's level.
    Additionally, Gargololo recovers a small amount of health for each enemy hit.
    """
    num_spectres = random.randint(3, 5)
    damage_per_spectre = 15 + user.level if hasattr(user, 'level') else 30
    total_damage = 0
    total_heal = 0
    messages = [f"{user.name} summons spectral forces for a Spectral Onslaught!"]
    for target in targets:
        target_total = 0
        for _ in range(num_spectres):
            dmg = max(1, damage_per_spectre - (target.armor // 4))
            target.take_damage(dmg)
            target_total += dmg
        total_damage += target_total
        total_heal += int(target_total * 0.3)  # heals 30% of damage dealt
        messages.append(f"{target.name} takes a total of {target_total} damage from spectral strikes.")
    user.health = min(user.health_max, user.health + total_heal)
    messages.append(f"{user.name} absorbs {total_heal} HP from the onslaught.")
    return "\n".join(messages)

def infernal_chorus(user, targets, battle_state):
    """
    Infernal Chorus (Magic):
    Unleashes a diabolic chorus that deals damage to all enemies and charms them,
    while healing Gargololo for 25% of the total damage dealt.
    """
    base_damage = 65
    total_damage = 0
    messages = [f"{user.name} sings the Infernal Chorus!"]
    for target in targets:
        damage = max(1, base_damage + (user.level * 3 if hasattr(user, 'level') else 30) - (target.armor // 3))
        target.take_damage(damage)
        total_damage += damage
        # Apply a charm effect for 2 turns.
        if "status_effects" not in battle_state:
            battle_state["status_effects"] = {}
        if target.name not in battle_state["status_effects"]:
            battle_state["status_effects"][target.name] = []
        battle_state["status_effects"][target.name].append({
            "effect": "charmed",
            "duration": 2
        })
        messages.append(f"{target.name} is charmed and takes {damage} damage.")
    heal_amount = int(total_damage * 0.25)
    user.health = min(user.health_max, user.health + heal_amount)
    messages.append(f"{user.name} heals for {heal_amount} HP from the Infernal Chorus.")
    return "\n".join(messages)

def primordial_fury(user, targets, battle_state):
    """
    Primordial Fury (Attack/Special):
    A massive single-target attack whose damage increases as Gargololo's health decreases.
    """
    target = targets[0]
    base_damage = 100
    missing_health_pct = (user.health_max - user.health) / user.health_max
    bonus_damage = int(base_damage * 1.5 * missing_health_pct)
    raw_damage = base_damage + bonus_damage + (user.level * 5 if hasattr(user, 'level') else 50)
    final_damage = max(1, raw_damage - target.armor)
    target.take_damage(final_damage)
    return f"{user.name} unleashes Primordial Fury on {target.name}, dealing {final_damage} damage (bonus damage: {bonus_damage})."

def nightmare_reflection(user, targets, battle_state):
    """
    Nightmare Reflection (Counter):
    Reflects incoming damage with amplified force and applies a fear effect,
    slowing the enemy (reducing their attack speed for 2 turns).
    """
    attacker = targets[0]
    # For demonstration, assume counter returns 150% of a base counter value.
    base_counter = 30
    reflected_damage = int(base_counter * 1.5)
    attacker.take_damage(reflected_damage)
    # Apply a fear debuff (reducing attack speed)
    if "status_effects" not in battle_state:
        battle_state["status_effects"] = {}
    if attacker.name not in battle_state["status_effects"]:
        battle_state["status_effects"][attacker.name] = []
    battle_state["status_effects"][attacker.name].append({
        "effect": "feared",
        "duration": 2,
        "attack_speed_reduction": 20  # percentage reduction
    })
    return f"{user.name} triggers Nightmare Reflection, reflecting {reflected_damage} damage and stunning {attacker.name} with fear."

def cosmic_siphon(user, targets, battle_state):
    """
    Cosmic Siphon (Drain):
    Drains health from a single enemy; the boss heals for 80% of the damage dealt.
    """
    target = targets[0]
    drain_damage = 50
    target.take_damage(drain_damage)
    heal_amount = int(drain_damage * 0.8)
    user.health = min(user.health_max, user.health + heal_amount)
    return f"{user.name} uses Cosmic Siphon on {target.name}, dealing {drain_damage} damage and healing for {heal_amount} HP."

def final_eulogy(user, targets, battle_state):
    """
    Final Eulogy (Buff/Special):
    Delivers a resounding final declaration that bolsters Gargololo's attack and defense for the remainder
    of the battle and saps the morale of all enemies, lowering their stats.
    """
    attack_boost = 15
    defense_boost = 20
    duration = 4
    messages = [f"{user.name} uses Final Eulogy, gaining +{attack_boost} attack and +{defense_boost} defense, while enemies are weakened."]
    
    # Increase Gargololo's own stats.
    if hasattr(user, 'attack'):
        user.attack += attack_boost
    if hasattr(user, 'armor'):
        user.armor += defense_boost
        
    # Register buff in battle_state.
    if "buffs" not in battle_state:
        battle_state["buffs"] = []
    battle_state["buffs"].append({
        "name": "Final Eulogy",
        "target": user.name,
        "attack_boost": attack_boost,
        "defense_boost": defense_boost,
        "duration": duration
    })
    
    # Apply debuff to all enemy targets.
    for target in targets:
        if hasattr(target, 'attack'):
            target.attack = max(0, target.attack - 10)
        if hasattr(target, 'armor'):
            target.armor = max(0, target.armor - 8)
        if "status_effects" not in battle_state:
            battle_state["status_effects"] = {}
        if target.name not in battle_state["status_effects"]:
            battle_state["status_effects"][target.name] = []
        battle_state["status_effects"][target.name].append({
            "effect": "demoralized",
            "duration": duration,
            "attack_reduction": 10,
            "defense_reduction": 8
        })
        messages.append(f"{target.name} is demoralized by the Final Eulogy, losing 10 attack and 8 defense for {duration} turns.")
    return "\n".join(messages)

# ==================== Mute Smigol's Skill Effect Functions ====================

def silent_pulse(user, targets, battle_state):
    """
    Releases a wave of silence that damages and silences all enemies.
    """
    base_damage = 55
    for target in targets:
        damage = max(1, base_damage - (target.armor // 3))
        target.take_damage(damage)
        print(f"{target.name} takes {damage} damage from Silent Pulse!")
    if 'status_effects' not in battle_state:
        battle_state['status_effects'] = {}
    for target in targets:
        battle_state['status_effects'].setdefault(target.name, []).append({
            'effect': 'silenced',
            'duration': 2  # Enemies lose some magic ability for 2 turns
        })
    print("All enemies are silenced for 2 turns!")

def silent_slash(user, targets, battle_state):
    """
    Strikes quickly from the shadows for high single-target damage.
    """
    target = targets[0]
    damage = int(user.weapon.damage * 2.0)  # 2.0x weapon damage multiplier
    target.take_damage(damage)
    print(f"{user.name} strikes {target.name} silently for {damage} damage!")

def cloak_of_silence(user, targets, battle_state):
    """
    Buffs the boss by increasing its evasion due to a shroud of silence.
    """
    evasion_boost = 10  # Increase evade chance by 10%
    user.evade_ch += evasion_boost
    print(f"{user.name} is shrouded in a Cloak of Silence, increasing evasion by {evasion_boost}!")

def echoes_of_silence(user, targets, battle_state):
    """
    Counters an incoming attack by dealing a burst of silent damage.
    """
    attacker = targets[0]
    counter_damage = 30  # Fixed counter damage value
    attacker.take_damage(counter_damage)
    print(f"{user.name} counterattacks silently, dealing {counter_damage} damage to {attacker.name}!")

def void_drain(user, targets, battle_state):
    """
    Drains the life force from a target by absorbing ambient silence,
    dealing damage and healing the boss for 80% of the damage dealt.
    """
    target = targets[0]
    drain_damage = 40
    target.take_damage(drain_damage)
    heal_amount = int(drain_damage * 0.8)
    user.health = min(user.health_max, user.health + heal_amount)
    print(f"{user.name} drains {drain_damage} damage from {target.name} and heals for {heal_amount} HP!")

# Dictionary of available skills
PLAYER_SKILLS = {
    "basic_heal": Skill("Basic Heal", "Heals target for a small amount", "heal", basic_heal, mp_cost=10),
    "mega_heal": Skill("Mega Heal", "Heals target for a large amount", "heal", mega_heal, cooldown=3, mp_cost=25),
    "power_strike": Skill("Power Strike", "Powerful attack against one enemy", "attack", power_strike, mp_cost=5),
    "multi_strike": Skill("Multi Strike", "Attacks all enemies", "attack", multi_strike, cooldown=2, mp_cost=15, targeting="all"),
    "defensive_stance": Skill("Defensive Stance", "Increases defense for 3 turns", "buff", defensive_stance, cooldown=4, mp_cost=10, targeting="self")
}

BOSS_SKILLS = {
    # Goblin Supreme skills
    "goblins_greed": Skill("Goblin's Greed", "Steals gold and heals", "heal", goblins_greed, cooldown=2, 
                          stealable=True, stat_cost={"mp_max": -10}),
    "life_drain": Skill("Life Drain", "Drains health from target", "heal", life_drain, cooldown=3, 
                       stealable=True, stat_cost={"health_max": -15}),
    "prideful_armor": Skill("Prideful Armor", "Boosts defense with damage taken", "status", prideful_armor,
                           stealable=True, stat_cost={"crit_ch": -5}),
    "arcane_pulse": Skill("Arcane Pulse", "AOE magic blast", "magic", arcane_pulse, cooldown=1, targeting="all",
                         stealable=True, stat_cost={"mp_max": -15}),
    "shattering_screech": Skill("Shattering Screech", "Stuns all enemies", "attack", shattering_screech, cooldown=3, targeting="all",
                               stealable=True, stat_cost={"evade_ch": -3}),
    "madness_shout": Skill("Madness Shout", "Confuses all enemies", "control", madness_shout, cooldown=3, targeting="all"),
    "shadow_strike": Skill("Shadow Strike", "Deals double damage from shadows", "attack", shadow_strike, cooldown=2,
                          stealable=True, stat_cost={"armor": -2}),
    "goblin_horde": Skill("Goblin Horde", "Summons goblin reinforcements", "summon", goblin_horde, cooldown=4, targeting="all"),
    # Troll Champion skills
    "troll_blood": Skill("Troll Blood", "Heals passively every turn", "heal", troll_blood, cooldown=0, targeting="self",
                         stealable=True, stat_cost={"health_max": -20}),
    "bonecrusher_fist": Skill("Bonecrusher Fist", "Deals damage and reduces defense", "attack", bonecrusher_fist, cooldown=1,
                              stealable=True, stat_cost={"defense": -3}),
    "frenzied_counter": Skill("Frenzied Counter", "Counters enemy attacks", "counter", frenzied_counter, cooldown=2,
                              stealable=True, stat_cost={"evade_ch": -4}),
    "vengeful_roar": Skill("Vengeful Roar", "Increases attack as health drops", "buff", vengeful_roar, cooldown=2, targeting="self",
                           stealable=True, stat_cost={"mp_max": -15}),
    "brutal_slam": Skill("Brutal Slam", "Stuns the target with a powerful slam", "control", brutal_slam, cooldown=3,
                         stealable=True, stat_cost={"crit_ch": -5}),
    # Pannocchia skills
    "greeds_harvest": Skill("Greed's Harvest", "Steals health and resources from the enemy", "heal", greed_harvest, cooldown=2,
                           stealable=True, stat_cost={"mp_max": -10}),
    "entropic_bloom": Skill("Entropic Bloom", "Releases a burst of corrupted energy", "magic", entropic_bloom, cooldown=3, targeting="all",
                           stealable=True, stat_cost={"health_max": -15}),
    "rooted_despair": Skill("Rooted Despair", "Immobilizes enemies and saps health", "curse", rooted_despair, cooldown=4, targeting="all",
                           stealable=True, stat_cost={"evade_ch": -4}),
    "thorned_armor": Skill("Thorned Armor", "Increases defense and reflects damage", "status", thorned_armor, cooldown=4, targeting="self",
                           stealable=True, stat_cost={"crit_ch": -5}),
    "siphon_life": Skill("Siphon Life", "Drains life force over time", "special", siphon_life, cooldown=5,
                         stealable=True, stat_cost={"health_max": -20}),
    # Rat King of the Lemurs skills
    "pestilent_wave": Skill("Pestilent Wave", "Summons a wave of rats that carry disease to enemies", "magic", 
                           pestilent_wave, cooldown=3, mp_cost=30, targeting="all",
                           stealable=True, stat_cost={"mp_max": -15}),
    "rat_kings_wrath": Skill("Rat King's Wrath", "Deals a flurry of blows with increased damage", "attack", 
                            rat_kings_wrath, cooldown=2, mp_cost=25,
                            stealable=True, stat_cost={"crit_ch": -4}),
    "swarm_call": Skill("Swarm Call", "Summons a swarm of rats to overwhelm the enemy", "summon", 
                       swarm_call, cooldown=4, mp_cost=20,
                       stealable=True, stat_cost={"evade_ch": -3}),
    "infectious_bite": Skill("Infectious Bite", "Deals a poison attack that spreads to other enemies", "special", 
                            infectious_bite, cooldown=3, mp_cost=30,
                            stealable=True, stat_cost={"health_max": -12}),
    "rats_gluttony": Skill("Rat's Gluttony", "Gains health for each enemy killed", "drain", 
                          rats_gluttony, cooldown=5, mp_cost=35, targeting="all",
                          stealable=True, stat_cost={"health_max": -18}),
    # African Turtle skills
    "crushing_claw": Skill(
        name="Crushing Claw",
        description="Strikes the enemy with immense force, breaking armor.",
        skill_type="attack",
        effect_func=crushing_claw,
        cooldown=2,
        mp_cost=20,
        targeting="single",
        stealable=True,
        stat_cost={"armor": -3}
    ),
    "oceanic_devastation": Skill(
        name="Oceanic Devastation",
        description="Unleashes a cataclysmic wave that damages all enemies.",
        skill_type="special",
        effect_func=oceanic_devastation,
        cooldown=5,
        mp_cost=40,
        targeting="all",
        stealable=True,
        stat_cost={"health_max": -15}
    ),
    "saltwater_healing": Skill(
        name="Saltwater Healing",
        description="Heals over time when standing in water.",
        skill_type="regeneration",
        effect_func=saltwater_healing,
        cooldown=3,
        mp_cost=25,
        targeting="self",
        stealable=True,
        stat_cost={"mp_max": -10}
    ),
    "shell_counter": Skill(
        name="Shell Counter",
        description="Every time the Turtle is hit, it counters with a defensive strike.",
        skill_type="counter",
        effect_func=shell_counter,
        cooldown=2,  # Changed from 0 to make it more balanced when stolen
        mp_cost=15,
        targeting="single",
        stealable=True,
        stat_cost={"evade_ch": -3}
    ),
    "unbreakable_defense": Skill(
        name="Unbreakable Defense",
        description="Greatly increases defense for a short time.",
        skill_type="status",
        effect_func=unbreakable_defense,
        cooldown=4,
        mp_cost=30,
        targeting="self",
        stealable=True,
        stat_cost={"crit_ch": -5}
    ),
    # Ultras Penguin skills
    "penguin_smash": Skill(
        name="Penguin Smash",
        description="A bone-crushing physical attack that shatters enemy defenses.",
        skill_type="special",
        effect_func=penguin_smash,
        cooldown=3,
        mp_cost=30,
        targeting="single",
        stealable=True
    ),
    "glacial_volley": Skill(
        name="Glacial Volley",
        description="Sends out a volley of freezing energy, striking all enemies.",
        skill_type="magic",
        effect_func=glacial_volley,
        cooldown=4,
        mp_cost=35,
        targeting="all",
        stealable=True
    ),
    "frozen_huddle": Skill(
        name="Frozen Huddle",
        description="Recovers health over time as ultras rally in a frigid group huddle.",
        skill_type="heal",
        effect_func=frozen_huddle,
        cooldown=3,
        mp_cost=25,
        targeting="self",
        stealable=True
    ),
    "ultras_pride": Skill(
        name="Ultras' Pride",
        description="Boosts attack and defense when health is below half via raucous ultra chants.",
        skill_type="status",
        effect_func=ultras_pride,
        cooldown=4,
        mp_cost=20,
        targeting="self",
        stealable=True,
        stat_cost={"health_max": -20}  # Cost for stealing this skill
    ),
    "icy_counter_chant": Skill(
        name="Icy Counter-Chant",
        description="Automatically retaliates against incoming strikes with a freezing blast.",
        skill_type="counter",
        effect_func=icy_counter_chant,
        cooldown=0,
        mp_cost=0,
        targeting="single",
        stealable=True,
        stat_cost={"mp_max": -15}  # Cost for stealing this skill
    ),
    # Bard Gargoyle skills
    "bard_wrath": Skill(
        name="Bard's Wrath",
        description="Deals massive damage to a single enemy caught in a sonic blast.",
        skill_type="special",
        effect_func=bard_wrath,
        cooldown=4,
        mp_cost=40,
        targeting="single",
        stealable=True,
        stat_cost={"health_max": -18}
    ),
    "soundwave_burst": Skill(
        name="Soundwave Burst",
        description="Emits a wide sonic blast that damages all enemies.",
        skill_type="magic",
        effect_func=soundwave_burst,
        cooldown=3,
        mp_cost=35,
        targeting="all",
        stealable=True,
        stat_cost={"mp_max": -15}
    ),
    "echo_of_life": Skill(
        name="Echo of Life",
        description="Restores health over time by absorbing echoes of past battles.",
        skill_type="regeneration",
        effect_func=echo_of_life,
        cooldown=3,
        mp_cost=30,
        targeting="self",
        stealable=True,
        stat_cost={"crit_ch": -4}
    ),
    "reverberating_strike": Skill(
        name="Reverberating Strike",
        description="Counters incoming attacks with a burst of sonic damage.",
        skill_type="counter",
        effect_func=reverberating_strike,
        cooldown=0,
        mp_cost=0,
        targeting="single",
        stealable=True,
        stat_cost={"evade_ch": -5}
    ),
    "dissonance": Skill(
        name="Dissonance",
        description="Lowers enemy attack and defense with a discordant sound.",
        skill_type="debuff",
        effect_func=dissonance,
        cooldown=4,
        mp_cost=25,
        targeting="all",
        stealable=True,
        stat_cost={"armor": -3}
    ),
    # Sexy Fox skills
    "fox_wrath": Skill(
        name="Fox's Wrath",
        description="Unleashes a powerful attack that devastates and charms the enemy.",
        skill_type="special",
        effect_func=fox_wrath,
        cooldown=4,
        mp_cost=40,
        targeting="single",
        stealable=True,
        stat_cost={"health_max": -20}
    ),
    "seductive_flame": Skill(
        name="Seductive Flame",
        description="Summons magical fire that damages and partially charms the target.",
        skill_type="magic",
        effect_func=seductive_flame,
        cooldown=3,
        mp_cost=35,
        targeting="single",
        stealable=True,
        stat_cost={"mp_max": -15}
    ),
    "allure_of_life": Skill(
        name="Allure of Life",
        description="Heals the boss over time by absorbing the life force of charmed enemies.",
        skill_type="regeneration",
        effect_func=allure_of_life,
        cooldown=3,
        mp_cost=30,
        targeting="self",
        stealable=True,
        stat_cost={"crit_ch": -4}
    ),
    "charming_counter": Skill(
        name="Charming Counter",
        description="Automatically counters attacks by charming the attacker and dealing damage.",
        skill_type="counter",
        effect_func=charming_counter,
        cooldown=0,
        mp_cost=0,
        targeting="single",
        stealable=True,
        stat_cost={"evade_ch": -5}
    ),
    "love_drain": Skill(
        name="Love Drain",
        description="Absorbs health from a charmed enemy, healing the boss.",
        skill_type="drain",
        effect_func=love_drain,
        cooldown=4,
        mp_cost=40,
        targeting="single",
        stealable=True,
        stat_cost={"armor": -3}
    ),
    # Broken Salamander skills
    "salamanders_wrath": Skill(
        name="Salamander's Wrath",
        description="Unleashes the full power of fire, dealing massive damage to a single enemy.",
        skill_type="special",
        effect_func=salamanders_wrath,
        cooldown=4,
        mp_cost=40,
        targeting="single",
        stealable=True,
        stat_cost={"health_max": -20}
    ),
    "volcanic_eruption": Skill(
        name="Volcanic Eruption",
        description="Causes a massive volcanic burst that damages all enemies.",
        skill_type="area",
        effect_func=volcanic_eruption,
        cooldown=5,
        mp_cost=50,
        targeting="all",
        stealable=True,
        stat_cost={"mp_max": -18}
    ),
    "phoenix_rebirth": Skill(
        name="Phoenix Rebirth",
        description="Fully heals the boss when health falls below 30%, usable once per battle.",
        skill_type="regeneration",
        effect_func=phoenix_rebirth,
        cooldown=0,
        mp_cost=0,
        targeting="self",
        stealable=True,
        stat_cost={"crit_ch": -6}
    ),
    "flame_retaliation": Skill(
        name="Flame Retaliation",
        description="Counters incoming attacks with a burst of fire dealing fixed damage.",
        skill_type="counter",
        effect_func=flame_retaliation,
        cooldown=0,
        mp_cost=0,
        targeting="single",
        stealable=True,
        stat_cost={"evade_ch": -4}
    ),
    "fire_drain": Skill(
        name="Fire Drain",
        description="Absorbs life from a burning enemy, healing for 80% of damage dealt.",
        skill_type="drain",
        effect_func=fire_drain,
        cooldown=4,
        mp_cost=40,
        targeting="single",
        stealable=True,
        stat_cost={"armor": -3}
    ),
    # Gargololo skills
    "cosmic_dissonance": Skill(
        name="Cosmic Dissonance",
        description="Unleashes an otherworldly discord that lowers enemy attack and defense.",
        skill_type="debuff",
        effect_func=cosmic_dissonance,
        cooldown=5,
        mp_cost=45,
        targeting="all",
        stealable=True,
        stat_cost={"health_max": -25, "mp_max": -20}
    ),
    "abyssal_dominion": Skill(
        name="Abyssal Dominion",
        description="Curses a target to take 20% more damage for a few turns.",
        skill_type="curse",
        effect_func=abyssal_dominion,
        cooldown=4,
        mp_cost=40,
        targeting="single",
        stealable=True,
        stat_cost={"health_max": -20, "crit_ch": -5}
    ),
    "titanic_rebirth": Skill(
        name="Titanic Rebirth",
        description="When health falls below 25%, fully restores Gargololo's HP (once per battle).",
        skill_type="regeneration",
        effect_func=titanic_rebirth,
        cooldown=0,
        mp_cost=0,
        targeting="self",
        stealable=True,
        stat_cost={"health_max": -30, "mp_max": -25}
    ),
    "molten_vortex": Skill(
        name="Molten Vortex",
        description="Summons a swirling vortex that deals fire and poison damage to all enemies.",
        skill_type="area",
        effect_func=molten_vortex,
        cooldown=5,
        mp_cost=50,
        targeting="all",
        stealable=True,
        stat_cost={"health_max": -25, "armor": -5}
    ),
    "spectral_onslaught": Skill(
        name="Spectral Onslaught",
        description="Summons ghostly minions that strike all enemies and restore health to Gargololo.",
        skill_type="summon",
        effect_func=spectral_onslaught,
        cooldown=6,
        mp_cost=55,
        targeting="all",
        stealable=True,
        stat_cost={"health_max": -22, "evade_ch": -6}
    ),
    "infernal_chorus": Skill(
        name="Infernal Chorus",
        description="Unleashes a diabolic chorus that damages, charms all enemies, and heals Gargololo.",
        skill_type="magic",
        effect_func=infernal_chorus,
        cooldown=4,
        mp_cost=50,
        targeting="all",
        stealable=True,
        stat_cost={"mp_max": -20, "crit_ch": -5}
    ),
    "primordial_fury": Skill(
        name="Primordial Fury",
        description="A massive single-target attack that grows stronger as Gargololo loses health.",
        skill_type="special",
        effect_func=primordial_fury,
        cooldown=4,
        mp_cost=45,
        targeting="single",
        stealable=True,
        stat_cost={"health_max": -22, "armor": -4}
    ),
    "nightmare_reflection": Skill(
        name="Nightmare Reflection",
        description="Reflects damage back to the attacker with amplified force and slows them.",
        skill_type="counter",
        effect_func=nightmare_reflection,
        cooldown=0,
        mp_cost=0,
        targeting="single",
        stealable=True,
        stat_cost={"evade_ch": -7, "armor": -5}
    ),
    "cosmic_siphon": Skill(
        name="Cosmic Siphon",
        description="Drains health from an enemy, healing Gargololo for 80% of the damage dealt.",
        skill_type="drain",
        effect_func=cosmic_siphon,
        cooldown=4,
        mp_cost=40,
        targeting="single",
        stealable=True,
        stat_cost={"health_max": -18, "mp_max": -15}
    ),
    "final_eulogy": Skill(
        name="Final Eulogy",
        description="Unleashes a rousing final buff that boosts Gargololo's power and weakens all enemies.",
        skill_type="buff",
        effect_func=final_eulogy,
        cooldown=6,
        mp_cost=60,
        targeting="all",
        stealable=True,
        stat_cost={"health_max": -25, "mp_max": -20, "crit_ch": -5}
    ),
    # Mute Smigol skills
    "silent_pulse": Skill(
        name="Silent Pulse",
        description="Releases a wave of silence that damages and silences all enemies.",
        skill_type="magic",
        effect_func=silent_pulse,
        cooldown=3,
        mp_cost=30,
        targeting="all",
        stealable=True,
        stat_cost={"mp_max": -15}
    ),
    "silent_slash": Skill(
        name="Silent Slash",
        description="A precise strike from the shadows that deals high damage.",
        skill_type="attack",
        effect_func=silent_slash,
        cooldown=2,
        mp_cost=20,
        targeting="single",
        stealable=True,
        stat_cost={"armor": -2}
    ),
    "cloak_of_silence": Skill(
        name="Cloak of Silence",
        description="Enshrouds the boss in silence, increasing its evasion.",
        skill_type="buff",
        effect_func=cloak_of_silence,
        cooldown=4,
        mp_cost=25,
        targeting="self",
        stealable=True,
        stat_cost={"crit_ch": -3}
    ),
    "echoes_of_silence": Skill(
        name="Echoes of Silence",
        description="Counters incoming attacks with a burst of silent damage.",
        skill_type="counter",
        effect_func=echoes_of_silence,
        cooldown=0,
        mp_cost=0,
        targeting="single",
        stealable=True,
        stat_cost={"evade_ch": -4}
    ),
    "void_drain": Skill(
        name="Void Drain",
        description="Absorbs silence from the enemy to drain energy and heal itself.",
        skill_type="drain",
        effect_func=void_drain,
        cooldown=4,
        mp_cost=30,
        targeting="single",
        stealable=True,
        stat_cost={"health_max": -10}
    )
}

def get_boss_skills_by_name(boss_name):
    """Return a list of skills for a specific boss."""
    if boss_name == "Goblin Supreme":
        return [
            BOSS_SKILLS["goblins_greed"],
            BOSS_SKILLS["life_drain"],
            BOSS_SKILLS["prideful_armor"],
            BOSS_SKILLS["arcane_pulse"],
            BOSS_SKILLS["shattering_screech"],
            BOSS_SKILLS["madness_shout"],
            BOSS_SKILLS["shadow_strike"],
            BOSS_SKILLS["goblin_horde"]
        ]
    elif boss_name == "Troll Champion Boxeur":
        return [
            BOSS_SKILLS["troll_blood"],
            BOSS_SKILLS["bonecrusher_fist"],
            BOSS_SKILLS["frenzied_counter"],
            BOSS_SKILLS["vengeful_roar"],
            BOSS_SKILLS["brutal_slam"]
        ]
    elif boss_name == "Pannocchia":
        return [
            BOSS_SKILLS["greeds_harvest"],
            BOSS_SKILLS["entropic_bloom"],
            BOSS_SKILLS["rooted_despair"],
            BOSS_SKILLS["thorned_armor"],
            BOSS_SKILLS["siphon_life"]
        ]
    elif boss_name == "Rat King of the Lemurs":
        return [
            BOSS_SKILLS["pestilent_wave"],
            BOSS_SKILLS["rat_kings_wrath"],
            BOSS_SKILLS["swarm_call"],
            BOSS_SKILLS["infectious_bite"],
            BOSS_SKILLS["rats_gluttony"]
        ]
    elif boss_name == "African Turtle":
        return [
            BOSS_SKILLS["crushing_claw"],
            BOSS_SKILLS["oceanic_devastation"],
            BOSS_SKILLS["saltwater_healing"],
            BOSS_SKILLS["shell_counter"],
            BOSS_SKILLS["unbreakable_defense"]
        ]
    elif boss_name == "Ultras Penguin":
        return [
            BOSS_SKILLS["penguin_smash"],
            BOSS_SKILLS["glacial_volley"],
            BOSS_SKILLS["frozen_huddle"],
            BOSS_SKILLS["ultras_pride"],
            BOSS_SKILLS["icy_counter_chant"]
        ]
    elif boss_name == "Bard Gargoyle":
        return [
            BOSS_SKILLS["bard_wrath"],
            BOSS_SKILLS["soundwave_burst"],
            BOSS_SKILLS["echo_of_life"],
            BOSS_SKILLS["reverberating_strike"],
            BOSS_SKILLS["dissonance"]
        ]
    elif boss_name == "Sexy Fox":
        return [
            BOSS_SKILLS["fox_wrath"],
            BOSS_SKILLS["seductive_flame"],
            BOSS_SKILLS["allure_of_life"],
            BOSS_SKILLS["charming_counter"],
            BOSS_SKILLS["love_drain"]
        ]
    elif boss_name == "Broken Salamander":
        return [
            BOSS_SKILLS["salamanders_wrath"],
            BOSS_SKILLS["volcanic_eruption"],
            BOSS_SKILLS["phoenix_rebirth"],
            BOSS_SKILLS["flame_retaliation"],
            BOSS_SKILLS["fire_drain"]
        ]
    elif boss_name == "Gargololo":
        return [
            BOSS_SKILLS["cosmic_dissonance"],
            BOSS_SKILLS["abyssal_dominion"],
            BOSS_SKILLS["titanic_rebirth"],
            BOSS_SKILLS["molten_vortex"],
            BOSS_SKILLS["spectral_onslaught"],
            BOSS_SKILLS["infernal_chorus"],
            BOSS_SKILLS["primordial_fury"],
            BOSS_SKILLS["nightmare_reflection"],
            BOSS_SKILLS["cosmic_siphon"],
            BOSS_SKILLS["final_eulogy"]
        ]
    elif boss_name == "Mute Smigol":
        return [
            BOSS_SKILLS["silent_pulse"],
            BOSS_SKILLS["silent_slash"],
            BOSS_SKILLS["cloak_of_silence"],
            BOSS_SKILLS["echoes_of_silence"],
            BOSS_SKILLS["void_drain"]
        ]
    # Add other bosses here
    return []
