# battle_system/enemy.py

import json
import os
import random
from random import choice, randint

from battle_system.character import Character
from battle_system.weapon import Weapon, generate_weapon
from battle_system.item import create_item_from_name
from battle_system.health_bar import HealthBar
from battle_system.skill import BOSS_SKILLS, get_boss_skills_by_name

# ==========================================
# 1. PATH RESOLUTION & DATA LOADING
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'data')

with open(os.path.join(DATA_DIR, 'enemies.json'), 'r') as f:
    enemy_names = json.load(f)

with open(os.path.join(DATA_DIR, 'bosses.json'), 'r') as f:
    boss_list = json.load(f)


# ==========================================
# 2. CLASS DEFINITIONS
# ==========================================
class EnemyDisplay:
    """Class for enemy display features."""
    @staticmethod
    def format_enemy_name(enemy):
        """String representation of the enemy."""
        return f"{enemy.name}"

class Enemy(Character):
    """Base class for all enemies."""
    def __init__(self, name, health, weapon, evade_ch, crit_ch, armor, tier):
        super().__init__(name=name, health=health, evade_ch=evade_ch, crit_ch=crit_ch, armor=armor)
        self.weapon = weapon
        self.tier = tier
        self.base_armor = armor
        self.health_bar = HealthBar(self, color="red")
        
        # Map display attributes
        self.symbol = "\033[31mE\033[0m"
        self.symbol_raw = 'E'
        self.walkable = False
        
        # Position tracking
        self.pos = None
        self.underlying_tile = None

    def __str__(self):
        return f"{self.name}"

    def set_position(self, x: int, y: int, underlying_tile):
        self.pos = (x, y)
        self.underlying_tile = underlying_tile

    def scale_stats(self, multiplier):
        self.health = int(self.health * multiplier)
        self.health_max = self.health
        self.weapon.damage = int(self.weapon.damage * multiplier)
        self.armor = int(self.armor * multiplier)
        self.health_bar.update()

class Boss(Enemy):
    """Boss characters with special abilities."""
    defeated_bosses = set()

    def __init__(self, name, health, weapon, evade_ch, crit_ch, armor, tier, skills, drops):
        super().__init__(name=name, health=health, weapon=weapon, evade_ch=evade_ch, crit_ch=crit_ch, armor=armor, tier=tier)
        self.skills = skills
        self.drops = drops
        self.base_armor = armor

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def was_defeated(cls, boss_name):
        return boss_name in cls.defeated_bosses

    @classmethod
    def mark_defeated(cls, boss_name):
        cls.defeated_bosses.add(boss_name)

    def choose_skill(self, targets, battle_state=None):
        available_skills = [s for s in self.skills if s.current_cooldown == 0]
        if not available_skills:
            return None

        if self.name == "Troll Champion Boxeur":
            troll_blood_skill = next((s for s in self.skills if s.name == "Troll Blood"), None)
            if troll_blood_skill:
                troll_blood_skill.use(self, [self], battle_state)
            
            if self.health < self.health_max * 0.3:
                vengeful_roar_skill = next((s for s in available_skills if s.name == "Vengeful Roar"), None)
                if vengeful_roar_skill:
                    return vengeful_roar_skill

            brutal_slam_skill = next((s for s in available_skills if s.name == "Brutal Slam"), None)
            if brutal_slam_skill:
                return brutal_slam_skill

        if self.health < self.health_max * 0.4:
            heal_skills = [s for s in available_skills if s.skill_type == 'heal']
            if heal_skills:
                return choice(heal_skills)

        if battle_state and 'status_effects' in battle_state:
            status_skills = [s for s in available_skills if s.skill_type in ['control', 'debuff']]
            affected_targets = sum(1 for t in targets if t.name in battle_state['status_effects'])
            if status_skills and affected_targets < len(targets) // 2:
                return choice(status_skills)

        return choice(available_skills)

    def take_turn(self, targets, battle_state=None):
        for skill in self.skills:
            skill.tick_cooldown()

        chosen_skill = self.choose_skill(targets, battle_state)
        
        if chosen_skill:
            print(f"{self.name} uses {chosen_skill.name}!")
            chosen_skill.use(self, targets, battle_state)
            return

        damage_bonus = 0
        if battle_state and 'boss_effects' in battle_state and 'vengeful_roar' in battle_state['boss_effects']:
            effect = battle_state['boss_effects']['vengeful_roar']
            if effect['active']:
                damage_bonus = effect['attack_boost']
                print(f"{self.name}'s attack is empowered by Vengeful Roar! (+{damage_bonus} damage)")

        original_damage = self.weapon.damage
        if damage_bonus > 0:
            self.weapon.damage += damage_bonus

        print(f"{self.name} attacks with {self.weapon.name}!")
        self.attack(targets[0])

        if damage_bonus > 0:
            self.weapon.damage = original_damage

    def attack(self, target, attack_type="normal", is_counter: bool = False) -> str:
        result = super().attack(target, attack_type, is_counter)

        if self.name == "Troll Champion Boxeur" and not is_counter and random.randint(1, 100) <= 30:
            frenzied_counter_skill = next((s for s in self.skills if s.name == "Frenzied Counter"), None)
            if frenzied_counter_skill and frenzied_counter_skill.current_cooldown == 0:
                frenzied_counter_skill.use(self, [target], {})
                frenzied_counter_skill.current_cooldown = frenzied_counter_skill.cooldown

        return result


# ==========================================
# 3. GENERATION FUNCTIONS
# ==========================================
def generate_enemy(tier: str, cycle: int = 0) -> Enemy:
    names = enemy_names.get(tier)
    if not names:
        raise ValueError("Invalid tier for enemy generation")
    name = choice(names)
    
    health_ranges = {"low": (10, 30), "mid": (40, 80), "high": (80, 120)}
    evade_ch_ranges = {"low": (0, 5), "mid": (5, 10), "high": (10, 15)}
    crit_ch_ranges = {"low": (5, 8), "mid": (8, 12), "high": (12, 20)}
    armor_ranges = {"low": (0, 2), "mid": (2, 6), "high": (6, 12)}

    health = randint(*health_ranges[tier])
    evade_ch = randint(*evade_ch_ranges[tier])
    crit_ch = randint(*crit_ch_ranges[tier])
    armor = randint(*armor_ranges[tier])

    health = int(health * (1 + 0.2 * cycle))
    evade_ch = int(evade_ch * (1 + 0.1 * cycle))
    crit_ch = int(crit_ch * (1 + 0.1 * cycle))
    armor = int(armor * (1 + 0.1 * cycle))
    
    weapon = generate_weapon(tier, cycle)
    
    enemy = Enemy(name=name, health=health, weapon=weapon, evade_ch=evade_ch, crit_ch=crit_ch, armor=armor, tier=tier)
    enemy.symbol = "\033[31mE\033[0m"
    enemy.symbol_raw = 'E'
    enemy.walkable = False
    return enemy

def generate_boss(boss_index: int) -> Boss:
    boss_data = boss_list[boss_index % len(boss_list)].copy()

    # Safely unpack the weapon JSON dictionary back into a Weapon object
    w_data = boss_data['weapon']
    boss_weapon = Weapon(
        name=w_data['name'], 
        weapon_type=w_data['weapon_type'], 
        damage=w_data.get('damage', 10),
        value=50 # Assigning the 50 gold value requirement here
    )

    # Note: Ensure get_boss_skills_by_name is imported successfully at the top!
    skills = get_boss_skills_by_name(boss_data['name'])

    if not skills:
        default_skills = [
            BOSS_SKILLS.get("arcane_pulse"),
            BOSS_SKILLS.get("shattering_screech")
        ]
        skills = [s for s in default_skills if s]

    return Boss(
        name=boss_data['name'],
        health=boss_data['health'],
        weapon=boss_weapon,
        evade_ch=boss_data['evade_ch'],
        crit_ch=boss_data['crit_ch'],
        armor=boss_data['armor'],
        tier=boss_data['tier'],
        skills=skills,
        drops=boss_data['drops']
    )
