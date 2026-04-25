# src/battlesys.py

import random

from battle_system.character import Hero
from battle_system.enemy import Enemy, Boss
from battle_system.health_bar import HealthBar
from battle_system.item import *
from battle_system.weapon import Weapon
from game_system.cli_utils import clear_console, flush_input_buffer

class BattleSystem:
    """Class to manage battles between the hero and enemies."""

    def __init__(self, hero: Hero, enemy: Enemy):
        self.flush_input_buffer()
        self.hero = hero
        self.enemy = enemy
        self.running = True
        self.battle_log = []  # Initialize battle log
        self.battle_state = {
            'turn': 1,
            'status_effects': {},
            'buffs': []
        }

    def flush_input_buffer(self):
        """Clear any pending keystrokes from the console buffer."""
        flush_input_buffer()

    def start_battle(self):
        """Starts the battle loop."""
        self.hero.health_bar.update()
        self.enemy.health_bar.update()
        self.clear_screen()

        while self.running and self.hero.alive and self.enemy.alive:
            # Process status effects and buffs at the start of each turn
            self.process_status_effects()
            
            # Tick all skill cooldowns for hero
            self.hero.tick_skill_cooldowns()
            
            # Display battle status
            self.display_battle_status()

            # Player's turn if not affected by status effects
            if not self.is_affected_by_status(self.hero, 'stunned'):
                action = input("\nChoose your action: [a]ttack, [s]kills, [i]tems, [e]scape: ").strip().lower()

                if action == 'a':
                    self.attack()
                elif action == 's':
                    self.use_skill()
                elif action == 'i':
                    self.use_item()
                elif action == 'e':
                    if self.escape():
                        break
                else:
                    self.battle_log.append("Invalid action. Choose again.")
                    continue
            else:
                self.battle_log.append(f"{self.hero.name} is stunned and cannot act!")

            # Enemy's turn if still alive
            if self.enemy.alive and self.running:
                if isinstance(self.enemy, Boss):
                    # Boss uses skills
                    self.enemy.take_turn([self.hero], self.battle_state)
                else:
                    # Regular enemy attacks
                    self.enemy_attack()

            # Increment turn counter
            self.battle_state['turn'] += 1

            # Check for end of battle
            if not self.hero.alive:
                self.battle_log.append("You have been defeated! Game Over.")
                self.running = False
                return
            elif not self.enemy.alive:
                self.battle_log.append(f"{self.enemy} has been defeated!")
                experience_gained = self.calculate_experience(self.enemy)
                self.hero.gain_experience(experience_gained)
                
                # Recover some MP after victory
                mp_recovery = int(self.hero.mp_max * 0.2)  # Recover 20% of max MP
                self.hero.recover_mp(mp_recovery)
                self.battle_log.append(f"{self.hero.name} recovers {mp_recovery} MP!")
                
                # Leave boss skill selection to the shrine victory flow in main.py.
                if not isinstance(self.enemy, Boss):
                    # Handle treasure encounter for non-boss enemies
                    self.handle_treasure_encounter()
                
                self.running = False

    def display_battle_status(self):
        """Displays the current status of the battle."""
        self.clear_screen()
        
        # Add New Game+ cycle information if applicable
        cycle_info = ""
        if hasattr(self.hero, 'cycle') and self.hero.cycle > 0:
            cycle_info = f" | NG+ Cycle: {self.hero.cycle}"
            
        print(f"{self.hero.name} HP: {self.hero.health}/{self.hero.health_max} | MP: {self.hero.mp}/{self.hero.mp_max}{cycle_info}")
        print(f"Weapon: {self.hero.weapon.name} (Damage: {self.hero.weapon.damage}) | Cash: {self.hero.cashpile}")
        self.hero.health_bar.draw()
        
        print(f"{self.enemy} - HP: {self.enemy.health}/{self.enemy.health_max}")
        print(f"Weapon: {self.enemy.weapon.name} (Damage: {self.enemy.weapon.damage})")
        if hasattr(self.enemy, 'skills') and len(self.enemy.skills) > 0:
            print(f"Type: Boss | Skills: {len(self.enemy.skills)}")
            
            if self.enemy.name == "Troll Champion Boxeur":
                if 'boss_effects' in self.battle_state and 'vengeful_roar' in self.battle_state['boss_effects']:
                    effect = self.battle_state['boss_effects']['vengeful_roar']
                    if effect['active']:
                        print(f"Vengeful Roar Active: Attack +{effect['attack_boost']}")
            
        self.enemy.health_bar.draw()
        
        # Display status effects
        status_effects = self.battle_state.get('status_effects', {})
        if self.hero.name in status_effects and status_effects[self.hero.name]:
            effects = [f"{e['effect']}({e['duration']})" for e in status_effects[self.hero.name]]
            print(f"{self.hero.name} Status: {', '.join(effects)}")
        
        if self.enemy.name in status_effects and status_effects[self.enemy.name]:
            effects = [f"{e['effect']}({e['duration']})" for e in status_effects[self.enemy.name]]
            print(f"{self.enemy.name} Status: {', '.join(effects)}")
        
        # Display stat debuffs
        if 'stats_debuffs' in self.battle_state:
            for char_name, debuffs in self.battle_state['stats_debuffs'].items():
                if debuffs:
                    effect_msgs = []
                    for debuff in debuffs:
                        effect_msgs.append(f"{debuff['stat']} {debuff['amount']}")
                    if effect_msgs:
                        print(f"{char_name} Stat Changes: {', '.join(effect_msgs)}")
        
        print("\nBattle Log:")
        for log_entry in self.battle_log[-5:]:  # Display the last 5 entries
            print(log_entry)

    def attack(self):
        """Handles the hero's attack action."""
        damage_info = self.hero.attack(self.enemy)
        self.battle_log.append(damage_info)

    def use_skill(self):
        """Handles the hero using a skill."""
        available_skills = self.hero.get_available_skills()
        
        if not available_skills:
            print("You have no skills available to use.")
            input("Press Enter to continue.")
            return
        
        print("\nAvailable Skills:")
        for idx, skill in enumerate(available_skills, 1):
            mp_cost = f"MP Cost: {skill.mp_cost}" if skill.mp_cost > 0 else ""
            cooldown = f"Cooldown: {skill.cooldown}" if skill.cooldown > 0 else ""
            stolen = " (Stolen)" if skill in self.hero.stolen_skills else ""
            print(f"{idx}. {skill.name}{stolen} - {skill.description} ({mp_cost}, {cooldown})")
        
        choice = input("Select a skill to use or 'b' to go back: ").strip()
        
        if choice.lower() == 'b':
            return
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available_skills):
                skill = available_skills[idx]
                # Get the actual index in the combined list
                all_skills = self.hero.skills + self.hero.stolen_skills
                skill_idx = all_skills.index(skill)
                
                # Determine targets based on skill targeting
                targets = []
                if skill.targeting == "self":
                    targets = [self.hero]
                elif skill.targeting == "all":
                    targets = [self.enemy]  # In a full game with multiple enemies, this would be all enemies
                else:  # Default to single target
                    targets = [self.enemy]
                
                self.hero.use_skill(skill_idx, targets, self.battle_state)
            else:
                print("Invalid selection.")
        else:
            print("Invalid input.")
        
        input("Press Enter to continue.")

    def use_item(self):
        """Handles the hero using an item."""
        if not self.hero.items:
            print("You have no items to use.")
            input("Press Enter to continue.")
            return

        # Group items by name and count them
        item_counts = {}
        for item in self.hero.items:
            if item.name in item_counts:
                item_counts[item.name]["count"] += 1
            else:
                item_counts[item.name] = {
                    "item": item,
                    "count": 1
                }
        
        # Display the grouped items with counts
        print("\nItems:")
        for idx, (name, data) in enumerate(item_counts.items(), 1):
            print(f"{idx}: {name} x{data['count']} - {data['item'].description}")
        
        choice = input("Select an item to use or 'b' to go back: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(item_counts):
                # Get the item name selected
                selected_item_name = list(item_counts.keys())[idx]
                selected_item_data = item_counts[selected_item_name]
                
                # Find the actual item in the inventory
                for i, item in enumerate(self.hero.items):
                    if item.name == selected_item_name:
                        # Use the item
                        if isinstance(item, Cure):
                            item.use(self.hero)
                        elif isinstance(item, Throwable):
                            item.use(self.enemy)
                        else:
                            print("Item cannot be used.")
                        
                        # Remove the item from inventory
                        self.hero.items.pop(i)
                        break
                
                # Inform the user how many of this item remain
                remaining = selected_item_data["count"] - 1
                if remaining > 0:
                    print(f"You have {remaining} {selected_item_name}(s) remaining.")
                else:
                    print(f"That was your last {selected_item_name}.")
                
                input("Press Enter to continue.")
            else:
                print("Invalid selection.")
                input("Press Enter to continue.")
        elif choice.lower() == 'b':
            return
        else:
            print("Invalid input.")
            input("Press Enter to continue.")

    def escape(self):
        """Attempts to escape from the battle."""
        escape_chance = {"low": 60, "mid": 40, "high": 20}
        chance = escape_chance.get(self.enemy.tier, 0)
        if random.randint(1, 100) <= chance:
            print("Escape successful!")
            self.running = False
            return True
        else:
            print("Escape failed!")
            return False

    def enemy_attack(self):
        """Handles the enemy's attack action."""
        damage_info = self.enemy.attack(self.hero)
        self.battle_log.append(damage_info)

    def calculate_experience(self, enemy):
        """Calculates experience gained from defeating an enemy."""
        tier_experience = {"low": 50, "mid": 100, "high": 200}
        base_xp = tier_experience.get(enemy.tier, 0)
        
        # Get the game cycle from the hero's associated game instance
        # If not available, default to standard experience
        cycle_multiplier = 1.0
        if hasattr(self.hero, 'game') and hasattr(self.hero.game, 'cycle'):
            cycle_multiplier = 1.0 + (self.hero.game.cycle * 0.1)  # 10% increase per cycle
            
        return int(base_xp * cycle_multiplier)

    # Helper methods for status effects
    def process_status_effects(self):
        """Process status effects at the start of a turn."""
        if 'status_effects' not in self.battle_state:
            self.battle_state['status_effects'] = {}
        
        # Process status effects for all characters
        for name, effects in list(self.battle_state['status_effects'].items()):
            for effect in effects[:]:  # Create a copy to safely modify during iteration
                effect['duration'] -= 1
                if effect['duration'] <= 0:
                    effects.remove(effect)
                    self.battle_log.append(f"{name} is no longer affected by {effect['effect']}!")
            
            # If all effects are gone, remove the entry
            if not effects:
                del self.battle_state['status_effects'][name]
        
        # Process buffs
        if 'buffs' in self.battle_state:
            for buff in self.battle_state['buffs'][:]:  # Create a copy to safely modify
                buff['duration'] -= 1
                if buff['duration'] <= 0:
                    # Remove the buff effect
                    target = buff['target']
                    stat = buff['stat']
                    amount = buff['amount']
                    
                    # Revert the stat
                    setattr(target, stat, getattr(target, stat) - amount)
                    
                    self.battle_log.append(f"{target.name}'s {stat} boost has ended!")
                    self.battle_state['buffs'].remove(buff)

    def is_affected_by_status(self, character, status_type):
        """Check if a character is affected by a specific status effect."""
        if 'status_effects' in self.battle_state:
            if character.name in self.battle_state['status_effects']:
                return any(e['effect'] == status_type for e in self.battle_state['status_effects'][character.name])
        return False

    def clear_screen(self):
        """Clears the console screen."""
        clear_console()

    def offer_skill_stealing(self):
        """Offers the player a chance to steal a skill from the defeated boss."""
        # Check if this boss has already had skills stolen
        if self.enemy.tier == 'boss' and Boss.was_defeated(self.enemy.name):
            print(f"\nYou have already stolen a skill from {self.enemy.name}.")
            input("Press Enter to continue...")
            return
            
        stealable_skills = [s for s in self.enemy.skills if s.stealable]
        
        if not stealable_skills:
            print(f"{self.enemy.name} has no skills that can be stolen.")
            return
        
        print(f"\n{self.enemy.name} has been defeated! You can steal one of their skills:")
        for i, skill in enumerate(stealable_skills, 1):
            cost_info = ", ".join(f"{k}: {v}" for k, v in skill.stat_cost.items())
            print(f"{i}. {skill.name} - {skill.description}")
            print(f"   Cooldown: {skill.cooldown}, MP Cost: {skill.mp_cost}")
            print(f"   Cost to steal: {cost_info}")
        
        print("0. Don't steal any skill")
        
        while True:
            try:
                choice = int(input("Enter your choice: "))
                if choice == 0:
                    print("You decided not to steal any skills.")
                    break
                elif 1 <= choice <= len(stealable_skills):
                    selected_skill = stealable_skills[choice - 1]
                    
                    # Confirm the choice due to permanent stat penalties
                    costs = ", ".join(f"{k}: {v}" for k, v in selected_skill.stat_cost.items())
                    print(f"\nWARNING: Stealing {selected_skill.name} will permanently affect your stats: {costs}")
                    confirm = input("Are you sure you want to proceed? (y/n): ").lower()
                    
                    if confirm == 'y':
                        self.hero.steal_skill(selected_skill)
                        # Mark this boss as having had a skill stolen
                        Boss.mark_defeated(self.enemy.name)
                        break
                    else:
                        print("You decided not to steal this skill.")
                        # Give another chance to choose
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        # Wait for user acknowledgment
        input("\nPress Enter to continue...")

    def handle_treasure_encounter(self):
        """Handles random treasure encounters after battles."""
        self.flush_input_buffer()
        # Generate a random number to determine if treasure is found
        if random.randint(1, 100) <= 60:  # 60% chance to find treasure
            print("\nYou found a treasure chest!")
            
            # Determine the type of treasure (weapon or item)
            treasure_type = random.choice(["weapon", "item", "gold"])
            
            if treasure_type == "weapon":
                # Generate a random weapon
                weapons = [
                    Weapon(name="Iron Sword", weapon_type="sword", damage=15),
                    Weapon(name="Steel Axe", weapon_type="axe", damage=18),
                    Weapon(name="Magic Staff", weapon_type="staff", damage=12),
                    Weapon(name="Hunter's Bow", weapon_type="bow", damage=14),
                    Weapon(name="Demon Blade", weapon_type="sword", damage=20)
                ]
                
                # Apply cycle bonus if available
                damage_modifier = 1.0
                if hasattr(self.hero, 'cycle') and self.hero.cycle > 0:
                    damage_modifier = 1.0 + (self.hero.cycle * 0.15)  # 15% more damage per cycle
                
                found_weapon = random.choice(weapons)
                found_weapon.damage = int(found_weapon.damage * damage_modifier)
                
                print(f"You found a {found_weapon.name} (Damage: {found_weapon.damage})!")
                print(f"Your current weapon: {self.hero.weapon.name} (Damage: {self.hero.weapon.damage})")
                
                choice = input("Take the weapon? (y/n): ").lower()
                if choice == 'y':
                    self.hero.equip(found_weapon)  # Changed from equip_weapon to equip
                    print(f"You equipped {found_weapon.name}.")
                else:
                    # Convert to gold if scrapped
                    gold_gained = found_weapon.damage * 5
                    self.hero.cashpile += gold_gained
                    print(f"You scrapped the weapon for {gold_gained} gold.")
                    
            elif treasure_type == "item":
                # Generate a random item using methods from item.py
                # Select a tier based on probability or cycle
                tier_options = ["small", "mids", "midh", "large", "superior"]
                tier_weights = [40, 30, 15, 10, 5]  # Default weights
                
                # Adjust weights based on cycle if applicable
                if hasattr(self.hero, 'cycle') and self.hero.cycle > 0:
                    # Increase chances for better tiers in higher cycles
                    cycle_modifier = min(self.hero.cycle, 5)  # Cap at cycle 5
                    tier_weights = [
                        max(40 - cycle_modifier * 5, 15),  # small
                        max(30 - cycle_modifier * 2, 15),  # mids
                        15 + cycle_modifier * 2,           # midh
                        10 + cycle_modifier * 2,           # large
                        5 + cycle_modifier * 3             # superior
                    ]
                
                selected_tier = random.choices(tier_options, weights=tier_weights)[0]
                
                # 50/50 chance for cure or throwable
                if random.randint(1, 2) == 1:
                    found_item = generate_cure(selected_tier)
                    item_type = "healing potion"
                else:
                    found_item = generate_throwable(selected_tier)
                    item_type = "throwable weapon"
                
                self.hero.items.append(found_item)
                print(f"You found and picked up a {found_item.name} ({item_type})!")
                
            else:  # Gold
                gold_amount = random.randint(10, 50)
                if hasattr(self.hero, 'cycle') and self.hero.cycle > 0:
                    gold_amount = int(gold_amount * (1.0 + self.hero.cycle * 0.2))  # 20% more gold per cycle
                self.hero.cashpile += gold_amount
                print(f"You found {gold_amount} gold!")
        
        input("Press Enter to continue...")
