from abc import ABC
from typing import Tuple
import random

from battle_system.weapon import Weapon, generate_weapon
from battle_system.health_bar import HealthBar
from battle_system.weapon import *
from battle_system.skill import PLAYER_SKILLS, Skill

class Character(ABC):
    """Base class for all characters in the game."""

    counter_ch: int = 20  # Counter-attack chance percentage

    def __init__(self, name: str, health: int, evade_ch: int, crit_ch: int, armor: int) -> None:
        self.name = name
        self.health = health
        self.health_max = health
        self.mana_max = 50
        self.mana = self.mana_max
        self.evade_ch = evade_ch  # Evade chance percentage
        self.crit_ch = crit_ch    # Critical hit chance percentage
        self.armor = armor        # Damage reduction
        self.weapon = generate_weapon("low")  # Default weapon
        self.health_bar = HealthBar(self, color="default")

    @property
    def alive(self) -> bool:
        """Returns True if the character is alive."""
        return self.health > 0

    def attack(self, target, attack_type="normal", is_counter: bool = False) -> str:
        """Performs an attack on the target."""
        messages = []

        if not self.alive:
            messages.append(f"{self.name} cannot attack because they are defeated.")
            return "\n".join(messages)

        if self.roll_event(target.evade_ch):
            messages.append(f"{target.name} evaded the attack!")
            return "\n".join(messages)

        base_damage = self.calculate_base_damage(attack_type)
        damage_after_crit, crit_message = self.deal_crit(base_damage)
        if crit_message:
            messages.append(crit_message)
        final_damage = max(damage_after_crit - target.armor, 1)

        target.take_damage(final_damage)
        messages.append(f"{self.name} attacked {target.name} with {self.weapon.name} for {final_damage} damage.")

        # Counter-attack logic
        if not is_counter and target.alive and self.roll_event(target.counter_ch):
            messages.append(f"{target.name} initiated a counter-attack!")
            counter_attack_info = target.attack(self, is_counter=True)
            messages.append(counter_attack_info)

        return "\n".join(messages)

    def calculate_base_damage(self, attack_type="normal") -> int:
        """Calculates base damage based on attack type."""
        min_damage = int(self.weapon.damage * 0.6) if attack_type == "quick" else int(self.weapon.damage * 0.8)
        max_damage = int(self.weapon.damage * 1.5) if attack_type == "heavy" else int(self.weapon.damage * 1.2)
        if max_damage <= min_damage:
            max_damage = min_damage + 1
        return random.randint(min_damage, max_damage)

    @staticmethod
    def roll_event(chance: int) -> bool:
        """Determines if an event occurs based on chance percentage."""
        return random.randint(1, 100) <= chance

    # In the Character class
    def deal_crit(self, base_damage: int) -> Tuple[int, str]:
        """Calculates critical hit damage."""
        if self.roll_event(self.crit_ch):
            crit_damage = int(base_damage * 1.5)
            crit_message = f"Critical hit! {self.name} deals {crit_damage} damage!"
            return crit_damage, crit_message
        return base_damage, ""

    def take_damage(self, damage: int) -> None:
        """Applies damage to the character."""
        self.health -= damage
        self.health = max(self.health, 0)
        self.health_bar.update()

class Hero(Character):
    """Player-controlled hero character."""

    def __init__(self, name: str, health: int):        
        super().__init__(name=name, health=health, evade_ch=10, crit_ch=15, armor=5)
        self.cashpile = 0
        self.items = []         # Inventory for consumable items
        self.equipment = []     # Inventory for equipment (armor, accessories)
        self.weapon = Weapon(name="Fists", weapon_type="blunt", damage=2, value=0)
        self.health_bar = HealthBar(self, color="green")
        self.player_pos = (1, 1)
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        self.enemies_killed = 0  # Track number of enemies killed
        self.boss_summoned = False  # Track if boss has been summoned
        
        # Add MP for skills
        self.mp = 50
        self.mp_max = 50
        
        # Starting skills
        self.skills = [
            PLAYER_SKILLS["basic_heal"],
            PLAYER_SKILLS["power_strike"]
        ]
        
        # Add stolen skills list
        self.stolen_skills = []
 
    def attack(self, target, attack_type="normal", is_counter: bool = False) -> str:
        """Performs an attack on the target."""
        messages = []

        if not self.alive:
            messages.append(f"{self.name} cannot attack because they are defeated.")
            return "\n".join(messages)

        if self.roll_event(target.evade_ch):
            messages.append(f"{target.name} evaded the attack!")
            return "\n".join(messages)

        base_damage = self.calculate_base_damage(attack_type)
        damage_after_crit, crit_message = self.deal_crit(base_damage)
        if crit_message:
            messages.append(crit_message)
        final_damage = max(damage_after_crit - target.armor, 1)

        target.take_damage(final_damage)
        messages.append(f"{self.name} attacked {target.name} with {self.weapon.name} for {final_damage} damage.")

        # Counter-attack logic
        if not is_counter and target.alive and self.roll_event(target.counter_ch):
            messages.append(f"{target.name} initiated a counter-attack!")
            counter_attack_info = target.attack(self, is_counter=True)
            messages.append(counter_attack_info)

        return "\n".join(messages)
    
    def equip_weapon(self, new_weapon: Weapon) -> None:
        # Add current weapon's value to cashpile before switching
        self.cashpile += self.weapon.value
        print(f"Scrapped your previous weapon '{self.weapon.name}' for {self.weapon.value} gold.")
        # Equip the new weapon
        self.weapon = new_weapon
        print(f"You equipped '{self.weapon.name}' (Tier: {self.get_weapon_tier(self.weapon)})") 
    
    def equip(self, new_weapon: Weapon) -> None:
        """Alias for equip_weapon for compatibility."""
        return self.equip_weapon(new_weapon)
        
    def gain_experience(self, amount):
        """Adds experience points and checks for level up."""
        self.experience += amount
        print(f"{self.name} gained {amount} experience points.")
        while self.experience >= self.experience_to_next_level:
            self.level_up()

    def get_weapon_tier(self, weapon: Weapon) -> str:
        """Determine weapon tier based on weapon name"""
        if weapon.name in [w.name for w in low_tier_weapons]:
            return "Low"
        elif weapon.name in [w.name for w in mid_tier_weapons]:
            return "Mid"
        elif weapon.name in [w.name for w in high_tier_weapons]:
            return "High"
        return "Unknown"

    def level_up(self):
        """Levels up the hero, increasing stats."""
        self.experience -= self.experience_to_next_level
        self.level += 1
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        self.health_max += 15
        self.health = self.health_max
        self.mana_max += 5
        self.mana = self.mana_max
        self.evade_ch += 1
        self.crit_ch += 1
        self.armor += 2
        print(f"{self.name} leveled up to level {self.level}!")
        print("Stats increased: Health +15, MP +5, Evade Chance +1%, Crit Chance +1%, Armor +2")
        
        # Learn new skills at specific levels
        if self.level == 3:
            self.learn_skill("multi_strike")
        elif self.level == 5:
            self.learn_skill("defensive_stance")
        elif self.level == 7:
            self.learn_skill("mega_heal")
    
    def learn_skill(self, skill_name):
        """Learn a new skill if available."""
        if skill_name in PLAYER_SKILLS:
            # Check if hero already knows this skill
            if any(s.name == PLAYER_SKILLS[skill_name].name for s in self.skills):
                print(f"{self.name} already knows {PLAYER_SKILLS[skill_name].name}.")
                return False
            
            self.skills.append(PLAYER_SKILLS[skill_name])
            print(f"{self.name} learned {PLAYER_SKILLS[skill_name].name}!")
            return True
        else:
            print(f"Skill {skill_name} not found.")
            return False
    
    def get_available_skills(self):
        """Return all skills (regular and stolen) that are not on cooldown."""
        regular_skills = [skill for skill in self.skills if skill.current_cooldown == 0]
        stolen_skills = [skill for skill in self.stolen_skills if skill.current_cooldown == 0]
        return regular_skills + stolen_skills
    
    def use_skill(self, skill_index, targets, battle_state=None):
        """Use a skill by index from the combined skills list."""
        all_skills = self.skills + self.stolen_skills
        if 0 <= skill_index < len(all_skills):
            skill = all_skills[skill_index]
            if skill.current_cooldown > 0:
                print(f"{skill.name} is on cooldown. {skill.current_cooldown} turns remaining.")
                return False
            
            if self.mp < skill.mp_cost:
                print(f"Not enough MP to use {skill.name}.")
                return False
            
            print(f"{self.name} uses {skill.name}!")
            
            # Initialize battle state if not provided
            if battle_state is None:
                battle_state = {}
            
            # Apply skill effects and get result
            result = skill.use(self, targets, battle_state)
            
            # If skill was used successfully, deduct MP cost and apply cooldown
            if result:
                self.mp -= skill.mp_cost
                
                # Check for New Game+ cycle damage bonus if available
                if hasattr(self, 'cycle') and self.cycle > 0:
                    cycle_bonus = 1.0 + (self.cycle * 0.15)  # 15% more damage per cycle
                    print(f"New Game+ bonus: Skill effectiveness increased by {(cycle_bonus-1)*100:.0f}%")
                
            return result
        else:
            print("Invalid skill index.")
            return False
    
    def tick_skill_cooldowns(self):
        """Reduce cooldown of all skills by 1 turn."""
        for skill in self.skills + self.stolen_skills:
            skill.tick_cooldown()
    
    def recover_mp(self, amount=None):
        """Recover MP, either a specific amount or a percentage of max MP."""
        if amount is None:
            # Recover 10% of max MP by default
            amount = int(self.mp_max * 0.1)
        
        self.mp = min(self.mp_max, self.mp + amount)
    
    def display_inventory(self):
        """Display the inventory menu and handle user navigation."""
        current_menu = "main"
        
        while True:
            print("\n" + "="*50)
            print(f"{self.name}'s Inventory".center(50))
            print("="*50)
            
            if current_menu == "main":
                print("\nSelect a menu:")
                print("1: Player Stats")
                print("2: Equipment")
                print("3: Satchel")
                print("4: Skills")  # New option for skills
                print("0: Exit Inventory")
                
                choice = input("\nEnter your choice: ")
                
                if choice == "1":
                    current_menu = "stats"
                elif choice == "2":
                    current_menu = "equipment"
                elif choice == "3":
                    current_menu = "satchel"
                elif choice == "4":
                    current_menu = "skills"  # New option handler
                elif choice == "0":
                    print("Closing inventory...")
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
            elif current_menu == "stats":
                self.display_stats_menu()
                current_menu = "main"
                
            elif current_menu == "equipment":
                self.display_equipment_menu()
                current_menu = "main"
                
            elif current_menu == "satchel":
                self.display_satchel_menu()
                current_menu = "main"
                
            elif current_menu == "skills":
                self.display_skills_menu()  # New skills menu
                current_menu = "main"
    
    def display_stats_menu(self):
        """Display player stats menu."""
        print("\n" + "-"*50)
        print(f"{self.name}'s Stats".center(50))
        print("-"*50)
        print(f"Level: {self.level}")
        print(f"Experience: {self.experience}/{self.experience_to_next_level}")
        print(f"Health: {self.health}/{self.health_max}")
        print(f"MP: {self.mp}/{self.mp_max}")
        print(f"Evade chance: {self.evade_ch}%")
        print(f"Critical hit chance: {self.crit_ch}%")
        print(f"Armor: {self.armor}")
        print(f"Gold: {self.cashpile}")
        print(f"\nEnemies defeated: {self.enemies_killed}")
        print(f"Boss summoned: {'Yes' if self.boss_summoned else 'No'}")
        
        input("\nPress Enter to return to main menu...")
    
    def display_skills_menu(self):
        """Display skills menu with regular and stolen skills."""
        print("\n" + "-"*50)
        print("Skills".center(50))
        print("-"*50)
        
        # Display regular skills
        if self.skills:
            print("\nRegular Skills:")
            for i, skill in enumerate(self.skills, 1):
                print(f"{i}. {skill.name} - {skill.description}")
                print(f"   Type: {skill.skill_type}, Cooldown: {skill.cooldown}, MP Cost: {skill.mp_cost}")
                if skill.current_cooldown > 0:
                    print(f"   Currently on cooldown: {skill.current_cooldown} turns remaining")
        else:
            print("No regular skills available.")
        
        # Display stolen skills
        if self.stolen_skills:
            print("\nStolen Boss Skills:")
            for i, skill in enumerate(self.stolen_skills, 1):
                print(f"{i}. {skill.name} - {skill.description}")
                print(f"   Type: {skill.skill_type}, Cooldown: {skill.cooldown}, MP Cost: {skill.mp_cost}")
                if skill.current_cooldown > 0:
                    print(f"   Currently on cooldown: {skill.current_cooldown} turns remaining")
        else:
            print("\nNo stolen skills yet. Defeat bosses to steal their skills.")
        
        input("\nPress Enter to return to inventory menu...")
    
    def display_equipment_menu(self):
        """Display equipment menu."""
        print("\n" + "-"*50)
        print("Equipment".center(50))
        print("-"*50)
        
        print(f"Current weapon: {self.weapon.name}")
        print(f"  Type: {self.weapon.weapon_type}")
        print(f"  Damage: {self.weapon.damage}")
        print(f"  Value: {self.weapon.value} gold")
        print(f"  Tier: {self.get_weapon_tier(self.weapon)}")
        
        if self.equipment:
            print("\nOther equipped items:")
            for i, item in enumerate(self.equipment, 1):
                print(f"{i}: {item.name} - {item.description if hasattr(item, 'description') else ''}")
        else:
            print("\nNo additional equipment.")
            
        input("\nPress Enter to return to main menu...")
    
    def display_satchel_menu(self):
        """Display satchel/inventory items menu."""
        print("\n" + "-"*50)
        print("Satchel".center(50))
        print("-"*50)
        
        if self.items:
            print("Your items:")
            for i, item in enumerate(self.items, 1):
                print(f"{i}: {item.name} - {item.description if hasattr(item, 'description') else ''}")
            
            print("\nEnter item number to use it, or 0 to go back")
            choice = input("Choice: ")
            
            try:
                item_index = int(choice) - 1
                if 0 <= item_index < len(self.items):
                    # Here you would implement item usage logic
                    print(f"Using {self.items[item_index].name}...")
                    # self.use_item(item_index)
                elif int(choice) != 0:
                    print("Invalid item number.")
            except ValueError:
                print("Invalid input.")
        else:
            print("Your satchel is empty.")
            input("\nPress Enter to return to main menu...")
    
    def check_all_enemies_defeated(self, game_map):
        """Check if all enemies are defeated and spawn shrine if needed."""
        # This method is now handled directly in enemy_encounter in main.py
        # to ensure it's called immediately after defeating an enemy
        return False

    def spawn_shrine(self, game_map):
        """Spawn a shrine on the map."""
        # Just use the map's place_shrine method - it now handles ruins placement
        shrine, coords = game_map.place_shrine()
        self.boss_summoned = True
        return shrine, coords
    
    def steal_skill(self, skill):
        """Steal a skill from a defeated boss, applying any stat penalties."""
        # Check if already has this skill
        if any(s.name == skill.name for s in self.stolen_skills + self.skills):
            print(f"You already know {skill.name}.")
            return False
        
        # Create a copy of the skill to avoid reference issues
        stolen = Skill(
            name=skill.name,
            description=skill.description,
            skill_type=skill.skill_type,
            effect_func=skill.effect_func,
            cooldown=skill.cooldown,
            mp_cost=skill.mp_cost,
            targeting=skill.targeting,
            stealable=False  # Can't steal a stolen skill
        )
        
        # Apply stat costs
        stats_affected = []
        for stat, value in skill.stat_cost.items():
            if hasattr(self, stat):
                current_value = getattr(self, stat)
                # Don't allow stats to go below minimum thresholds
                min_thresholds = {
                    "health_max": 10,
                    "armor": 0,
                    "evade_ch": 1,
                    "crit_ch": 1,
                    "mp_max": 5
                }
                min_val = min_thresholds.get(stat, 0)
                new_value = max(min_val, current_value + value)
                setattr(self, stat, new_value)
                stats_affected.append(f"{stat} {value}")
                
                # If health_max is reduced, also reduce current health
                if stat == "health_max" and value < 0:
                    self.health = min(self.health, self.health_max)
                # If mp_max is reduced, also reduce current mp
                if stat == "mp_max" and value < 0:
                    self.mp = min(self.mp, self.mp_max)
        
        self.stolen_skills.append(stolen)
        print(f"You have stolen the skill '{stolen.name}'!")
        if stats_affected:
            print(f"This comes at a cost: {', '.join(stats_affected)}")
        return True

class Enemy(Character):
    """Enemy characters controlled by the game."""

    def __init__(self, name: str, health: int, weapon: Weapon, evade_ch: int, crit_ch: int, armor: int, tier: str) -> None:
        super().__init__(name=name, health=health, evade_ch=evade_ch, crit_ch=crit_ch, armor=armor)
        self.weapon = weapon
        self.health_bar = HealthBar(self, color="red")
        self.tier = tier            # Enemy's tier (low, mid, high)
        self.pos = None             # Position on the map
        self.underlying_tile = None # Tile beneath the enemy (for map updates)
        
        # Add required map display attributes
        self.symbol = "\033[31mE\033[0m"  # Red E for enemy
        self.symbol_raw = 'E'
        self.walkable = False  # Enemies cannot be walked on

    def __str__(self):
        """String representation of the enemy, including their weapon."""
        weapon_name = f" [{self.weapon.name}]" if hasattr(self, 'weapon') and self.weapon else ""
        return f"{self.name}{weapon_name}"
    
    def set_position(self, x: int, y: int, underlying_tile):
        """Sets the enemy's position on the map."""
        self.pos = (x, y)
        self.underlying_tile = underlying_tile

    def drop_loot(self):
        """Defines the loot dropped by the enemy upon defeat."""
        # You can expand this method to include items or gold
        return self.weapon
    
    def scale_stats(self, multiplier):
        """Scales the enemy's stats by the given multiplier."""
        self.health = int(self.health * multiplier)
        self.health_max = self.health
        self.weapon.damage = int(self.weapon.damage * multiplier)
        self.armor = int(self.armor * multiplier)
        self.health_bar.update()
