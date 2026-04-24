# game_system/main.py

import sys
import os
import time
import traceback

# Fix path to make imports work properly regardless of where the script is executed from
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import keyboard
    import random as rand
    
    from map_system.map import Map
    from map_system.tiles import plains, forest, water, mountain, desert, default  # Import tile types
    from game_system.menu import handle_menu_input
    from battle_system.battlesys import BattleSystem
    from battle_system.character import Hero
    from battle_system.enemy import generate_boss, boss_list, generate_enemy
    from battle_system.health_bar import HealthBar
    from battle_system.item import *
    from battle_system.weapon import Weapon, generate_weapon, low_tier_weapons, mid_tier_weapons, high_tier_weapons
    # Import shrine from tiles module instead of map module
    from map_system.tiles import shrine
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running the game from the project root directory or game_system directory")
    print(f"Current directory: {os.getcwd()}")
    print(f"Project root directory: {project_root}")
    print("\nDetailed error:")
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)

class Game:
    """Main Game class to manage game flow and state."""
    MAX_SEED_VALUE = 1000000 # Maximum integer value allowed for seed

    def __init__(self):
        self.running = True
        self.hero = Hero(name="Hero", health=150)
        self.hero.health_bar = HealthBar(self.hero, color="green")
        self.current_village_tile = None  # For village interaction
        self.cycle = 0 #initializes game cycle
        self.boss_defeated = 0  #counts boss defeated, initializes
        self.game_over_count = {}  # Dictionary to track retries for each seed
        # Fixed total count of enemies (10 total)
        self.total_enemy_count = 10
        self.enemy_distribution = self._calculate_enemy_distribution()
        self.total_bosses = 10  # Total bosses to defeat
        self.boss_summoned = False  # Track if boss shrine has been summoned
        self.difficulty_multiplier = 1.0  # Base difficulty multiplier
        # Initialize enemy count attributes for New Game+
        self.current_low_tier_enemies = 6  # Default number of low tier enemies
        self.current_mid_tier_enemies = 4  # Default number of mid tier enemies
        self.current_high_tier_enemies = 3  # Default number of high tier enemies

    def clear(self) -> None:
        """Clears the console screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def run(self) -> None:
        """Runs the main game loop, offering options for new game or seed-based game."""
        try:
            while True:
                self.clear()
                menu_choice = handle_menu_input()
                self.clear()
                if menu_choice == "1":  # New game
                    self.seed = rand.randint(0, self.MAX_SEED_VALUE)
                    self.start_game()
                elif menu_choice == "2":  # Options -> Set Seed Game
                    self.set_seed()
                    self.start_game()
                elif menu_choice == "3":  # Exit (handled in handle_menu_input())
                    break
        except Exception as e:
            self.clear()
            print(f"An error occurred: {e}")
            print("\nDetailed error information:")
            traceback.print_exc()
            input("\nPress Enter to exit...")
            sys.exit(1)

    def set_seed(self):
        """Sets a seed value for the map, with validation for the seed range."""
        while True:
            try:
                seed_input = int(input(f"Enter seed (0 - {self.MAX_SEED_VALUE}): "))
                if 0 <= seed_input <= self.MAX_SEED_VALUE:
                    self.seed = seed_input
                    break
                else:
                    print(f"Please enter a value between 0 and {self.MAX_SEED_VALUE}.")
            except ValueError:
                print("Invalid input. Please enter an integer.")

    def _calculate_enemy_distribution(self):
        """Calculate the distribution of enemy tiers based on current cycle."""
        # Early cycles: more low-tier enemies
        # Late cycles: more high-tier enemies
        if self.cycle <= 3:  # Early cycles
            high_tier = 2
            mid_tier = 4
            low_tier = 4
        elif self.cycle <= 7:  # Mid cycles
            high_tier = min(3 + (self.cycle - 3), 4)  # 3-4 high tier
            remaining = self.total_enemy_count - high_tier
            mid_tier = remaining // 2
            low_tier = remaining - mid_tier
        else:  # Late cycles
            high_tier = 6
            mid_tier = 2
            low_tier = 2
        return {
            "low": low_tier,
            "mid": mid_tier,
            "high": high_tier
        }

    def start_game(self, new_game=True):
        """Starts a new game or level, initializing the map with a seed."""
        if new_game:
            self.hero = Hero(name="Hero", health=150)
            self.hero.health_bar = HealthBar(self.hero, color="green")
            # Explicitly initialize hero attributes to prevent crashes
            self.hero.player_pos = (1, 1)  # Initialize player position
            self.hero.enemies_killed = 0  # Initialize enemies killed counter
            self.hero.items = []  # Initialize items list
            self.hero.cashpile = 0  # Initialize gold
            self.boss_defeated = 0  # Reset boss count for a new game
            self.cycle = 0  # Reset cycle count for a new game
            self.difficulty_multiplier = 1.0  # Reset difficulty
            self.enemy_distribution = self._calculate_enemy_distribution()
            self.boss_summoned = False  # Reset boss summoned flag
        try:
            print(f"Using seed: {self.seed}")
            print("Initializing map...")
            # Create the map using the given seed
            map_w, map_h = 35, 25
            game_map = Map.generate_map_with_seed(map_w, map_h, self.seed)
            print("Map initialized")
            # Place player on map - ensure player_pos is already initialized
            game_map.place_player(self.hero)
            print("Player placed")
            # Select enemies with updated distribution
            selected_enemies = []
            selected_enemies.extend([generate_enemy("low") for _ in range(self.enemy_distribution["low"])])
            selected_enemies.extend([generate_enemy("mid") for _ in range(self.enemy_distribution["mid"])])
            selected_enemies.extend([generate_enemy("high") for _ in range(self.enemy_distribution["high"])])
            # Scale enemy stats for New Game+ cycles
            if self.cycle > 0:
                for enemy in selected_enemies:
                    self.scale_enemy_stats(enemy)
            print(f"{len(selected_enemies)} enemies selected")
            game_map.place_enemies_on_map(selected_enemies)
            print("Enemies placed on map")
            self.hero.enemies_killed = 0  # Reset kill counter for new map
            
            # Main game loop
            self.continue_game_with_map(game_map)
        except Exception as e:
            print(f"Error during game initialization: {str(e)}")
            print("Returning to main menu...")
            input("Press Enter to continue...")
            return

    def display_player_stats(self, game_map):
        """Displays player stats including kill counter."""
        print(f"\nPlayer Stats: {self.hero.name} | HP: {self.hero.health}/{self.hero.health_max} | Gold: {self.hero.cashpile}")
        print(f"Level: {self.hero.level} | XP: {self.hero.experience}/{self.hero.experience_to_next_level}")
        print(f"Enemies Killed: {self.hero.enemies_killed}/{len(game_map.enemies) + self.hero.enemies_killed}")
        print(f"Bosses Defeated: {self.boss_defeated}/{self.total_bosses}")

    def handle_game_over(self) -> None:
        """Handles the game-over logic, allowing retries with the same or different seed."""
        if self.seed not in self.game_over_count:
            self.game_over_count[self.seed] = 0
        self.game_over_count[self.seed] += 1
        retry_allowed = self.game_over_count[self.seed] <= 5

        # Game over screen
        self.clear()
        print("Game Over!")
        print(f"You have died {self.game_over_count[self.seed]} times on this seed.")
        if self.game_over_count[self.seed] > 5:
            print("Retry limit exceeded for this seed. You must select a new seed.")

        # Ask for retry or new seed
        while True:
            if retry_allowed:
                choice = input("Would you like to retry with the same seed (r) or enter a new one (n)? ").lower()
            else:
                choice = input("Please enter a new seed (n): ").lower()
            if choice == 'r' and retry_allowed:
                self.running = True
                break
            elif choice == 'n':
                self.set_seed()
                self.running = True
                break
            else:
                print("Invalid input. Please try again.")

    def display_victory_screen(self):
        """Displays the victory screen."""
        self.clear()
        print("Congratulations! You defeated all enemies.")
        input("Press Enter to exit...")
        self.running = False

    def move_player(self, game_map: Map):
        """Handles player movement and interactions on the map in real-time."""
        x, y = self.hero.player_pos  # Use hero's position to determine starting point
        print("Use W/A/S/D to move the player, 'I' to access inventory. Press Q to quit.")
        while True:
            # Check if the game is still running
            if not self.running:
                return  # Exit the movement loop if game is over
                
            new_x, new_y = x, y
                
            # Wait for a key event from the user
            key_event = keyboard.read_event(suppress=True)
            if key_event.event_type == keyboard.KEY_DOWN:
                key = key_event.name.lower()
                # Determine new position based on input
                if key == 'w':
                    new_x, new_y = x - 1, y
                elif key == 's':
                    new_x, new_y = x + 1, y
                elif key == 'a':
                    new_x, new_y = x, y - 1
                elif key == 'd':
                    new_x, new_y = x, y + 1
                elif key == 'i':
                    self.access_inventory()
                    self.clear()
                    game_map.display_map(self.hero)
                    continue
                elif key == 'q':
                    print("Quitting game...")
                    self.running = False
                    return
                # Debug command handling - only available when the game is in debug mode
                elif key == '/':
                    self.handle_debug_command(game_map)
                    self.clear()
                    game_map.display_map(self.hero)
                    continue
                else:
                    # If an invalid key is pressed, ignore it and continue waiting
                    continue

                # Validate movement within map bounds
                if new_x < 0 or new_x >= game_map.height or new_y < 0 or new_y >= game_map.width:
                    print("Invalid move. Stay within bounds.")
                    self.invalid_move(game_map, x, y)
                    time.sleep(0.3)
                    continue

                # Get the tile at the new position
                tile = game_map.map_data[new_x][new_y]
                tile_symbol = tile.symbol_raw

                # Modular encounter system using a dictionary of encounters
                encounter_handlers = {
                    'E': self.enemy_encounter,
                    'S': self.shrine_encounter,
                    '~': self.invalid_move,
                    '§': self.invalid_move,
                    'B': self.boss_encounter,
                    'N': self.npc_encounter,
                    'V': self.village_encounter,
                    'T': self.treasure_encounter,  # Unlooted treasure
                    't': self.invalid_move         # Looted treasure (prevent interaction)
                }
                
                # Initialize moved flag
                moved = False
                
                # Check if the tile requires an encounter
                if tile_symbol in encounter_handlers:
                    moved = encounter_handlers[tile_symbol](game_map, new_x, new_y)
                else:
                    # If no encounter, move the player
                    game_map.update_player_position(x, y, new_x, new_y)
                    moved = True

                if moved:
                    # Update player position after movement or encounter
                    x, y = new_x, new_y
                    self.hero.player_pos = (x, y)  # Update hero's position
                # Clear the screen and display the updated map
                self.clear()
                game_map.display_map(self.hero)
                # Small delay to prevent multiple key presses being read at once
                time.sleep(0.1)

    def handle_debug_command(self, game_map):
        """Handles debug commands entered by the user."""
        self.clear()
        print("DEBUG MODE ACTIVATED")
        print("Available commands:")
        print("  new_game_debug - Start a new game cycle")
        print("  boss_spawn_debug - Spawn boss shrine")
        print("  steal_skill_boss - Choose a boss skill to steal")  
        print("  op_init - Give player a high-tier weapon, gold, XP, and items") # New option
        print("  exit - Return to game")
        debug_cmd = input("Enter debug command: ").strip().lower()
        if debug_cmd == "new_game_debug":
            self.debug_new_game_cycle(game_map)
        elif debug_cmd == "boss_spawn_debug":
            self.debug_spawn_boss(game_map)
        elif debug_cmd == "steal_skill_boss":  
            self.debug_steal_skill()
        elif debug_cmd == "op_init":  # New command
            self.debug_op_init()
        elif debug_cmd == "exit":
            return
        else:
            print("Unknown debug command")
            input("Press Enter to continue...")

    def debug_new_game_cycle(self, game_map):
        """Debug function to simulate completion of a cycle and start a new one."""
        print("DEBUG: Simulating a boss defeat and starting a new game cycle")
        # Increment boss defeated counter
        self.boss_defeated += 1
        # Reset boss summoned flag
        self.boss_summoned = False
        # Update difficulty for next level
        self.current_low_tier_enemies = max(1, self.current_low_tier_enemies - 1)
        self.current_mid_tier_enemies += 1
        # Generate new seed for variety
        old_seed = self.seed
        self.seed = rand.randint(0, self.MAX_SEED_VALUE)
        # Update difficulty multiplier for next cycle
        self.difficulty_multiplier = 1.0 + ((self.cycle + 1) * 0.2)
        print(f"DEBUG: Boss #{self.boss_defeated} defeated")
        print(f"DEBUG: Changing seed from {old_seed} to {self.seed}")
        print(f"DEBUG: Setting difficulty multiplier to {self.difficulty_multiplier:.2f}x")
        input("Press Enter to start the new game cycle...")
        # Start the new level with incremented cycle
        self.start_new_level()

    def debug_spawn_boss(self, game_map):
        """Debug function to spawn the boss shrine."""
        print("DEBUG: Spawning boss shrine")
        # Clear any existing enemies to simulate all enemies defeated
        for enemy in game_map.enemies[:]:  # Create a copy of the list to safely remove items
            x, y = enemy.pos
            game_map.map_data[x][y] = enemy.underlying_tile
            game_map.enemies.remove(enemy)
        # Set boss summoned flag to avoid double spawning
        self.boss_summoned = False
        # Spawn the shrine
        is_final_boss = (self.boss_defeated == self.total_bosses - 1)
        shrine_coords = self.spawn_shrine(game_map)
        print(f"DEBUG: Shrine spawned at {shrine_coords}")
        print(f"DEBUG: Is final boss: {is_final_boss}")
        input("Press Enter to continue...")

    def debug_steal_skill(self):
        """Debug function to steal any boss skill without defeating the boss."""
        from battle_system.skill import BOSS_SKILLS
        self.clear()
        print("DEBUG: Steal any boss skill")
        # Get all available boss skills
        all_boss_skills = list(BOSS_SKILLS.values())
        # Display available skills
        print("\nAvailable Boss Skills:")
        for idx, skill in enumerate(all_boss_skills, 1):
            cost_info = ", ".join(f"{k}: {v}" for k, v in skill.stat_cost.items()) if skill.stat_cost else "None"
            print(f"{idx}. {skill.name} - {skill.description}")
            print(f"   Type: {skill.skill_type}, Cooldown: {skill.cooldown}, MP Cost: {skill.mp_cost}")
            print(f"   Cost to steal: {cost_info}")
        print("0. Cancel")
        # Get user choice
        while True:
            try:
                choice = int(input("\nEnter your choice: "))
                if choice == 0:
                    print("No skill stolen.")
                    break
                elif 1 <= choice <= len(all_boss_skills):
                    selected_skill = all_boss_skills[choice - 1]
                    # Confirm stealing due to potential stat penalties
                    costs = ", ".join(f"{k}: {v}" for k, v in selected_skill.stat_cost.items()) if selected_skill.stat_cost else "None"
                    print(f"\nWARNING: Stealing {selected_skill.name} will affect your stats: {costs}")
                    confirm = input("Are you sure you want to proceed? (y/n): ").lower()
                    if confirm == 'y':
                        result = self.hero.steal_skill(selected_skill)
                        if result:
                            print(f"DEBUG: Successfully stolen skill {selected_skill.name}")
                        else:
                            print(f"DEBUG: Failed to steal skill {selected_skill.name}")
                        break
                    else:
                        print("Skill steal cancelled.")
                        break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
        input("Press Enter to continue...")

    def debug_op_init(self):
        """Debug function to give the player powerful starting items."""
        self.clear()
        print("DEBUG: Initializing player with overpowered equipment and stats")
        # Give player a high tier weapon
        weapon = generate_weapon("high")
        self.hero.equip_weapon(weapon)
        print(f"Equipped {weapon.name} (Damage: {weapon.damage})")
        # Add gold
        self.hero.cashpile += 300
        print(f"Added 300 gold. Current gold: {self.hero.cashpile}")
        # Add experience
        self.hero.experience += 1000
        # Update level if experience threshold is reached
        while self.hero.experience >= self.hero.experience_to_next_level:
            self.hero.level_up()
        print(f"Added 1000 XP. Current level: {self.hero.level}")
        # Add health potions
        for _ in range(6):
            potion = generate_cure("large")  # "large" is a strong health potion
            self.hero.items.append(potion)
        print("Added 6 strong health potions")
        # Add poison knives
        for _ in range(6):
            knife = generate_throwable("large")  # "large" creates high-damage throwables
            self.hero.items.append(knife)
        print("Added 6 poison knives")
        print("\nPlayer is now overpowered and ready for battle!")
        input("Press Enter to continue...")

    def access_inventory(self):
        """Allows the player to view and use items from their inventory."""
        self.flush_input_buffer()  # Add this line to clear input buffer
        # Use the hero's built-in inventory display method
        self.hero.display_inventory()

    def enemy_encounter(self, game_map: Map, x: int, y: int) -> bool:
        """Handles encounters with enemies."""
        self.clear()  # Clear screen at start of encounter
        self.flush_input_buffer()  # Add this line to clear input buffer
        print("Encountered an enemy!")
        enemy = next((e for e in game_map.enemies if e.pos == (x, y)), None)
        if enemy:
            battle_system = BattleSystem(self.hero, enemy)
            battle_system.start_battle()
            if not self.hero.alive:
                self.display_game_over_screen()  
                return False  # Never reached if running is False
            # If enemy is defeated, remove it and handle loot.
            if not enemy.alive:
                # Ensure enemy has an underlying_tile attribute
                if not hasattr(enemy, 'underlying_tile') or enemy.underlying_tile is None:
                    # Default to plains tile if underlying_tile is not set
                    enemy.underlying_tile = plains
                    print("Warning: Enemy missing underlying tile, using default.")
                game_map.map_data[x][y] = enemy.underlying_tile
                game_map.enemies.remove(enemy)
                self.hero.enemies_killed += 1  # Increment kill counter
                self.handle_loot(enemy)
                # Update the player's position on the map after defeating the enemy
                game_map.update_player_position(self.hero.player_pos[0], self.hero.player_pos[1], x, y)
                self.hero.player_pos = (x, y)  # Update hero's position
                # Check if all enemies are defeated and spawn shrine if needed
                if len(game_map.enemies) == 0 and not self.boss_summoned:
                    self.clear()
                    print("\n" + "*"*50)
                    print("A malevolent shrine appears in the distance...".center(50))
                    print("An ancient evil stirs...".center(50))
                    print("*"*50 + "\n")
                    shrine_coords = self.spawn_shrine(game_map)
                    input("Press Enter to continue...")
                    # Find a suitable location for the shrine - place only ONE shrine
                    self.boss_summoned = True
                    # Redraw the map to show the shrine
                    self.clear()
                    game_map.display_map(self.hero)
                    if shrine_coords:
                        print(f"\nA shrine has appeared at position {shrine_coords}!")
                        print("Seek it out to challenge the boss!")
                    input("Press Enter to continue...")
                return True  # Player moves onto the tile
            else:
                # Player failed to defeat the enemy or escaped.
                return False
        else:
            print("Error: Enemy not found at this position.")
            return False

    def boss_encounter(self, game_map: Map, x: int, y: int):
        """Handles encounters with bosses."""
        print("A mighty boss appears!")
        print("\nNEED TO IMPLEMENT IN FUTURE!")

    def npc_encounter(self, game_map: Map, x: int, y: int):
        """Handles encounters with NPCs."""
        print("You encounter a friendly NPC!")
        print("\nNEED TO IMPLEMENT IN FUTURE!")

    def invalid_move(self, game_map: Map, x: int, y: int) -> bool:
        """Handles attempts to move to invalid tiles (e.g., water or lake)."""
        print("You cannot move there.")
        game_map.display_map(self.hero)
        time.sleep(0.3)
        return False  # Player does not move onto the tile

    def handle_loot(self, enemy):
        """Handles looting after defeating an enemy."""
        self.clear()  # Clear screen at start of loot
        # Handle random item drop
        item = self.enemy_drop_item(enemy)
        if item:
            print(f"The enemy dropped {item.name}!")
            # Add to hero's inventory
            self.hero.items.append(item)
        else:
            print("The enemy did not drop any items.")
        # Existing weapon loot code
        print(f"You found {enemy.weapon.name} (Tier: {enemy.tier.capitalize()}) (Damage: {enemy.weapon.damage}). Value: {enemy.weapon.value} gold.")
        choice = input("Do you want to pick it up or scrap it for gold? (p/s): ").strip().lower()
        if choice == 'p':
            print(f"You picked up {enemy.weapon.name}.")
            self.hero.equip_weapon(enemy.weapon)
        elif choice in ['s', 'a']:  # Accept 's' or 'a' for scrapping
            print(f"Scrapped {enemy.weapon.name} for {enemy.weapon.value} gold.")
            self.hero.cashpile += enemy.weapon.value
            print(f"Your cashpile now contains {self.hero.cashpile} gold.")

    def enemy_drop_item(self, enemy):
        """Determines if an enemy drops an item and returns it."""
        # Dynamic drop rates based on game cycle
        if self.cycle <= 3:
            # Early game: Higher drop rates to help players build arsenal
            total_drop_chance = 70 - (self.cycle * 5)  # 70% in cycle 0, decreasing by 5% per cycle
        elif self.cycle <= 7:
            # Mid game: Moderate drop rates
            total_drop_chance = 55 - (self.cycle - 3) * 5  # 55% in cycle 4, decreasing by 5% per cycle
        else:
            # Late game: Lower drop rates to force resource management
            total_drop_chance = 40  # 40% in cycles 8+
        # Determine if an item drops at all
        if rand.randint(1, 100) > total_drop_chance:
            return None  # No item dropped
        # Determine item type
        item_type_chances = {
            'cure': 50,        # If an item drops, 50% chance it's a cure
            'throwable': 50    # If an item drops, 50% chance it's a throwable
        }
        # Determine item type
        rand_val = rand.randint(1, 100)
        cumulative = 0
        item_type = None
        for key, chance in item_type_chances.items():
            cumulative += chance
            if rand_val <= cumulative:
                item_type = key
                break
        # Dynamic tier probabilities
        tier_roll = rand.randint(1, 100)
        # As game progresses, adjust tier probabilities
        if self.cycle <= 3:
            # Early game: More low-tier items
            if tier_roll <= 50:
                item_tier = 'small'  # low tier
            elif tier_roll <= 85:
                item_tier = rand.choice(['mids', 'midh'])  # mid tier
            else:
                item_tier = 'large'  # high tier
        elif self.cycle <= 7:
            # Mid game: More balanced distribution
            if tier_roll <= 40:
                item_tier = 'small'  # low tier
            elif tier_roll <= 75:
                item_tier = rand.choice(['mids', 'midh'])  # mid tier
            else:
                item_tier = 'large'  # high tier
        else:
            # Late game: More high-tier items, but lower overall drop rate
            if tier_roll <= 30:
                item_tier = 'small'  # low tier
            elif tier_roll <= 60:
                item_tier = rand.choice(['mids', 'midh'])  # mid tier
            else:
                item_tier = 'large'  # high tier
        # Boss enemies always drop superior items
        if enemy.tier == 'boss':
            item_tier = 'superior'
        # Generate the item
        if item_type == 'cure':
            item = generate_cure(item_tier)
        elif item_type == 'throwable':
            item = generate_throwable(item_tier)
        else:
            item = None
        return item

    def village_encounter(self, game_map: Map, x: int, y: int) -> bool:
        """Handles encounters with villages."""
        self.clear()  # Clear screen at start of encounter
        self.flush_input_buffer()  # Add this line to clear input buffer
        village_tile = game_map.map_data[x][y]
        if village_tile.visited:
            print("You have already visited this village.")
            time.sleep(1)
            return False  # Do not move onto the tile again
        else:
            print("You have entered a village!")
            # Store the current village tile before entering the menu
            self.current_village_tile = village_tile
            # Move the player to the village tile first
            game_map.update_player_position(self.hero.player_pos[0], self.hero.player_pos[1], x, y)
            self.hero.player_pos = (x, y)
            # Now handle the village menu
            self.village_menu()
            # Mark the village as visited after interaction
            village_tile.visited = True
            village_tile.symbol = f"\033[90mV\033[0m"  # Change to gray color
            village_tile.symbol_raw = 'v'  # Lowercase to indicate visited
            return True  # Player is already on the tile

    def village_menu(self):
        """Displays the village menu and handles interactions."""
        print("Welcome to the village!")
        while True:
            print("\nVillage Menu:")
            print(f"Your gold: {self.hero.cashpile}")  # Show player's gold here
            print("1. Rest (heal all HP)")
            print("2. Visit Weapon Shop")
            print("3. Visit Item Shop")
            print("4. Leave Village")
            choice = input("Choose an action: ").strip()
            if choice == '1':
                # Rest and heal the hero
                self.hero.health = self.hero.health_max
                print("You are fully healed!")
            elif choice == '2':
                # Visit the weapon shop
                self.weapon_shop()
            elif choice == '3':
                # Visit the item shop
                self.item_shop()
            elif choice == '4':
                # Leave the village
                print("Leaving the village.")
                return
            else:
                print("Invalid choice. Try again.")

    def weapon_shop(self):
        """Handles the weapon shop interactions."""
        print("\nWelcome to the Weapon Shop!")
        print(f"Your gold: {self.hero.cashpile}")  # Show player's gold here
        # Generate weapons for sale
        weapons_for_sale = (
            [generate_weapon("low") for _ in range(5)] +
            [generate_weapon("mid") for _ in range(4)] +
            [generate_weapon("high") for _ in range(2)]
        )
        # Display available weapons
        for idx, weapon in enumerate(weapons_for_sale, 1):
            print(f"{idx}. {weapon.name} (Tier: {weapon.tier.capitalize()}) - Damage: {weapon.damage} - {weapon.value} gold")
        while True:
            choice = input("\nSelect a weapon to buy or 'b' to go back: ").strip()
            if choice.lower() == 'b':
                return
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(weapons_for_sale):
                    weapon = weapons_for_sale[idx]
                    # Since weapons are unique equipment, we don't need quantity selection
                    if self.hero.cashpile >= weapon.value:
                        confirm = input(f"Buy {weapon.name} for {weapon.value} gold? (y/n): ").strip().lower()
                        if confirm == 'y':
                            self.hero.cashpile -= weapon.value
                            self.hero.equip_weapon(weapon)
                            print(f"You bought and equipped {weapon.name}.")
                            print(f"Remaining gold: {self.hero.cashpile}")
                        else:
                            print("Purchase canceled.")
                    else:
                        print(f"You don't have enough gold. You need {weapon.value} gold but only have {self.hero.cashpile}.")
                else:
                    print("Invalid selection.")
            else:
                print("Invalid input.")
            # Ask if player wants to buy another weapon
            another = input("Would you like to buy another weapon? (y/n): ").strip().lower()
            if another != 'y':
                break

    def item_shop(self):
        """Handles the item shop interactions."""
        print("\nWelcome to the Item Shop!")
        print(f"Your gold: {self.hero.cashpile}")  # Show player's gold here
        # Generate items for sale
        items_for_sale = [
            generate_cure("small"),
            generate_cure("mids"),
            generate_cure("midh"),
            generate_throwable("small"),
            generate_throwable("mids")
        ]
        # Display available items
        for idx, item in enumerate(items_for_sale, 1):
            print(f"{idx}. {item.name} - {item.description} - {item.value} gold")
        while True:
            choice = input("\nSelect an item to buy or 'b' to go back: ").strip()
            if choice.lower() == 'b':
                return
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items_for_sale):
                    item = items_for_sale[idx]
                    # Ask for quantity
                    try:
                        quantity = int(input(f"How many {item.name} would you like to buy? ").strip())
                        if quantity <= 0:
                            print("Please enter a positive number.")
                            continue
                        total_cost = item.value * quantity
                        if self.hero.cashpile >= total_cost:
                            confirm = input(f"Buy {quantity} {item.name} for {total_cost} gold? (y/n): ").strip().lower()
                            if confirm == 'y':
                                self.hero.cashpile -= total_cost
                                for _ in range(quantity):
                                    # Create new instances of the item based on its class type
                                    if isinstance(item, Cure):
                                        new_item = generate_cure(item.tier)
                                    elif isinstance(item, Throwable):
                                        new_item = generate_throwable(item.tier)
                                    else:
                                        # Fallback if type can't be determined
                                        new_item = item
                                    self.hero.items.append(new_item)
                                print(f"You bought {quantity} {item.name}.")
                                print(f"Remaining gold: {self.hero.cashpile}")
                            else:
                                print("Purchase canceled.")
                        else:
                            print(f"You don't have enough gold. You need {total_cost} gold but only have {self.hero.cashpile}.")
                    except ValueError:
                        print("Please enter a valid number.")
                else:
                    print("Invalid selection.")
            else:
                print("Invalid input.")
            # Ask if player wants to buy another item
            another = input("Would you like to buy another item? (y/n): ").strip().lower()
            if another != 'y':
                break

    def treasure_encounter(self, game_map: Map, x: int, y: int) -> bool:
        """Handles encounters with treasures."""
        self.clear()  # Clear screen at start of encounter
        self.flush_input_buffer()  # Add this line to clear input buffer
        treasure_tile = game_map.map_data[x][y]
        if treasure_tile.visited:
            print("This treasure chest has already been looted.")
            time.sleep(1)
            return False  # Do not move onto the tile again
        else:
            print("You found a treasure chest!")
            # Move the player to the treasure tile first
            game_map.update_player_position(self.hero.player_pos[0], self.hero.player_pos[1], x, y)
            self.hero.player_pos = (x, y)
            
            # Generate random treasure reward
            reward_type = rand.choice(["weapon", "item", "gold"])
            
            if reward_type == "weapon":
                # Determine weapon tier based on cycle
                if self.cycle <= 2:
                    tier_weights = [60, 30, 10]  # [low, mid, high] for early cycles
                elif self.cycle <= 5:
                    tier_weights = [40, 40, 20]  # More balanced for mid cycles
                else:
                    tier_weights = [20, 40, 40]  # Better weapons for later cycles
                
                tier = rand.choices(["low", "mid", "high"], weights=tier_weights)[0]
                weapon = generate_weapon(tier)
                
                # Apply cycle bonus if available
                if self.cycle > 0:
                    damage_modifier = 1.0 + (self.cycle * 0.15)  # 15% more damage per cycle
                    weapon.damage = int(weapon.damage * damage_modifier)
                
                print(f"\nYou found a {weapon.name} (Damage: {weapon.damage})!")
                print(f"Your current weapon: {self.hero.weapon.name} (Damage: {self.hero.weapon.damage})")
                
                choice = input("Take the weapon? (y/n): ").lower()
                if choice == 'y':
                    self.hero.equip_weapon(weapon)
                    print(f"You equipped {weapon.name}.")
                else:
                    # Convert to gold if scrapped
                    gold_gained = weapon.damage * 5
                    self.hero.cashpile += gold_gained
                    print(f"You scrapped the weapon for {gold_gained} gold.")
            
            elif reward_type == "item":
                # Select a tier based on cycle
                tier_options = ["small", "mids", "midh", "large", "superior"]
                
                if self.cycle <= 2:
                    tier_weights = [50, 30, 15, 5, 0]
                elif self.cycle <= 5:
                    tier_weights = [30, 30, 25, 10, 5]
                else:
                    tier_weights = [20, 25, 25, 20, 10]
                
                selected_tier = rand.choices(tier_options, weights=tier_weights)[0]
                
                # 50/50 chance for cure or throwable
                if rand.randint(1, 2) == 1:
                    found_item = generate_cure(selected_tier)
                    item_type = "healing potion"
                else:
                    found_item = generate_throwable(selected_tier)
                    item_type = "throwable weapon"
                
                self.hero.items.append(found_item)
                print(f"\nYou found and picked up a {found_item.name} ({item_type})!")
            
            else:  # Gold
                base_gold = rand.randint(20, 100)
                gold_amount = base_gold
                if self.cycle > 0:
                    gold_amount = int(base_gold * (1.0 + self.cycle * 0.2))  # 20% more gold per cycle
                self.hero.cashpile += gold_amount
                print(f"\nYou found {gold_amount} gold!")
            
            # After the player has looted the treasure, mark it as looted
            treasure_tile.looted = True
            treasure_tile.visited = True
            treasure_tile.symbol = f"\033[90mt\033[0m"  # Change to gray lowercase t
            treasure_tile.symbol_raw = 't'  # Lowercase to indicate looted
            
            # Add a pause so the player can read the message
            input("\nPress Enter to continue...")
            return True

    def spawn_shrine(self, game_map):
        """Places the shrine on the map at a ruins tile if possible and returns its coordinates."""
        is_final_boss = (self.boss_defeated == self.total_bosses - 1)
        # Call the map's place_shrine method with is_final_boss flag
        shrine, shrine_coords = game_map.place_shrine(is_final_boss=is_final_boss)
        if shrine_coords is None:
            print("Warning: Failed to place shrine properly.")
            return None
        # Update the boss_spawned flag
        game_map.boss_spawned = True
        # Message based on whether it's the final boss
        if is_final_boss:
            print("The ancient golden shrine has appeared! The final challenge awaits...")
        else:
            print("A mysterious shrine has appeared on the map!")
        return shrine_coords

    def shrine_encounter(self, game_map: Map, x: int, y: int) -> bool:
        """Handles the shrine encounter leading to a boss battle."""
        try:
            self.clear()  # Clear screen at start of encounter
            self.flush_input_buffer()  # Add this line to clear input buffer
            # First check if coordinates are within bounds
            if x < 0 or x >= game_map.height or y < 0 or y >= game_map.width:
                print(f"Warning: Attempted to access shrine at invalid coordinates ({x}, {y})")
                return False
            # Fixed coordinate order - should be map_data[x][y] not map_data[y][x]
            if game_map.map_data[x][y].symbol_raw == 'S':
                print("You have discovered the shrine!")
                # Special message for final boss
                if self.boss_defeated == self.total_bosses - 1:
                    print("You've reached the final challenge! The ultimate boss awaits...")
                boss = generate_boss(self.boss_defeated % len(boss_list))  # Loop through bosses
                # Enhanced boss scaling based on cycle
                if self.cycle > 0:
                    # Calculate boss difficulty multiplier with progressive toughness
                    if self.cycle <= 5:
                        # Early cycles: Moderate linear increases
                        boss_multiplier = 1 + (self.cycle * 0.2)  # 20% increase per cycle
                    else:
                        # Late cycles: Extra difficulty multiplier
                        # Base linear scaling + exponential component
                        linear_part = 1 + (self.cycle * 0.2)
                        extra_multiplier = 1 + ((self.cycle - 5) * 0.08)  # Additional 8% per cycle after 5
                        boss_multiplier = linear_part * extra_multiplier
                        # Final boss in late cycles gets an additional boost
                        if self.boss_defeated == self.total_bosses - 1 and self.cycle >= 8:
                            boss_multiplier *= 1.2  # Additional 20% for final boss in late cycles
                    # Scale boss stats with enhanced multiplier in later cycles (if applicable)
                    boss.scale_stats(boss_multiplier)
                    print(f"{boss.name}'s stats have been scaled by {boss_multiplier:.2f}x for New Game+{self.cycle}")
                    # Adjust boss skill cooldowns in later cycles (if applicable)
                    if self.cycle >= 6 and hasattr(boss, 'skills'):
                        for skill in boss.skills:
                            if hasattr(skill, 'cooldown') and skill.cooldown > 1:
                                # Reduce cooldowns by up to 1 turn based on cycle
                                cooldown_reduction = min(1, self.cycle * 0.1)
                                skill.cooldown = max(1, skill.cooldown - cooldown_reduction)
                battle_system = BattleSystem(self.hero, boss)
                battle_system.start_battle()
                if not self.hero.alive:
                    self.display_game_over_screen()
                    return False
                if not boss.alive:
                    self.clear()
                    print("\n" + "*"*50)
                    print(f"VICTORY! You have defeated {boss.name}!".center(50))
                    print("*"*50 + "\n")
                    # Handle boss weapon drop first:
                    if hasattr(boss, 'weapon') and boss.weapon:
                        print(f"The boss dropped its weapon: {boss.weapon.name} (Damage: {boss.weapon.damage}) (Value: {boss.weapon.value} gold)")
                        choice = input("Do you want to pick it up or scrap it for gold? (p/s): ").strip().lower()
                        if choice == 'p':
                            print(f"You picked up {boss.weapon.name}.")
                            self.hero.equip_weapon(boss.weapon)
                        elif choice in ['s', 'a']:  # Accept 's' or 'a' for scrapping
                            print(f"Scrapped {boss.weapon.name} for {boss.weapon.value} gold.")
                            self.hero.cashpile += boss.weapon.value
                            print(f"Your cashpile now contains {self.hero.cashpile} gold.")
                    stealable_skills = [s for s in boss.skills if s.stealable]
                    if stealable_skills:
                        print("\nYou can steal one of the boss's skills:")
                        for i, skill in enumerate(stealable_skills, 1):
                            cost_info = ", ".join(f"{k}: {v}" for k, v in skill.stat_cost.items()) if hasattr(skill, 'stat_cost') and skill.stat_cost else "None"
                            print(f"{i}. {skill.name} - {skill.description}")
                            print(f"   Cooldown: {skill.cooldown}, MP Cost: {skill.mp_cost}")
                            print(f"   Cost to steal: {cost_info}")
                        print("0. Don't steal any skill")
                        while True:
                            try:
                                choice = int(input("\nEnter your choice: "))
                                if choice == 0:
                                    print("You decided not to steal any skills.")
                                    break
                                elif 1 <= choice <= len(stealable_skills):
                                    selected_skill = stealable_skills[choice - 1]
                                    # Confirm the choice due to permanent stat penalties
                                    if hasattr(selected_skill, 'stat_cost') and selected_skill.stat_cost:
                                        costs = ", ".join(f"{k}: {v}" for k, v in selected_skill.stat_cost.items())
                                        print(f"\nWARNING: Stealing {selected_skill.name} will permanently affect your stats: {costs}")
                                        confirm = input("Are you sure you want to proceed? (y/n): ").lower()
                                        if confirm == 'y':
                                            self.hero.steal_skill(selected_skill)
                                            break
                                        else:
                                            print("You decided not to steal this skill.")
                                            break
                                    else:
                                        # If no stat cost, just steal it
                                        self.hero.steal_skill(selected_skill)
                                        break
                                else:
                                    print("Invalid choice. Please try again.")
                            except ValueError:
                                print("Please enter a number.")
                    # Give a random item from the boss drops
                    if hasattr(boss, 'drops') and boss.drops:
                        drop_item_name = rand.choice(boss.drops)
                        item = create_item_from_name(drop_item_name)
                        if item:
                            self.hero.items.append(item)
                            print(f"\nYou received {item.name} from the boss's treasures!")
                    self.boss_defeated += 1
                    self.boss_summoned = False  # Reset for next level
                    # If all bosses defeated, show final victory screen and end game
                    if self.boss_defeated >= self.total_bosses:
                        self.display_final_victory_screen()
                        self.running = False
                        return True
                    # Transition message to next map
                    self.clear()
                    print("\n" + "*"*50)
                    print("The world around you begins to shift and change...".center(50))
                    print("The air grows heavier with ancient magic...".center(50))
                    print(f"You feel yourself growing stronger for New Game+{self.cycle + 1}".center(50))
                    print("*"*50 + "\n")
                    # Progress to next map with adjusted enemy counts
                    self.display_level_up_message()
                    self.seed = rand.randint(0, self.MAX_SEED_VALUE)  # Generate new seed for next level
                    # Update difficulty for next level
                    self.current_low_tier_enemies = max(1, self.current_low_tier_enemies - 1)
                    self.current_mid_tier_enemies += 1
                    # Update difficulty multiplier based on next cycle
                    self.difficulty_multiplier = 1.0 + ((self.cycle + 1) * 0.2)  # Increases by 20% per cycle
                    print(f"Generating new map with seed: {self.seed}")
                    # Don't increment cycle here - it will be done in start_new_level
                    self.start_new_level()  # This will increment cycle and create new map
                    return False  # Return false to prevent normal movement processing
                return False
        except IndexError as e:
            print(f"Error accessing shrine at position ({x}, {y}): {e}")
            print("Please report this bug with the seed number.")
            input("Press Enter to continue...")
            return False
        except Exception as e:
            print(f"Unexpected error in shrine encounter: {e}")
            traceback.print_exc()
            input("Press Enter to continue...")
            return False

    def scale_enemy_stats(self, enemy):
        """Scales enemy stats based on current New Game+ cycle using nonlinear scaling."""
        if self.cycle > 0:
            # Implement a piecewise function for enemy stats
            if self.cycle <= 5:
                # Cycles 1-5: Linear phase
                multiplier = 1 + (self.cycle * 0.15)
            else:
                # Cycles 6+: Exponential phase
                # Base linear scaling + exponential component
                linear_part = 1 + (self.cycle * 0.15)
                exponential_part = 0.02 * (self.cycle ** 2)
                multiplier = linear_part + exponential_part
            # Apply scaling to enemy stats
            enemy.scale_stats(multiplier)
            print(f"{enemy.name}'s stats have been scaled by {multiplier:.2f}x for New Game+{self.cycle}")

    def display_final_victory_screen(self):
        """Displays the final victory screen after defeating all bosses."""
        self.clear()
        print("""
        ****************************************************
        *                                                  *
        *        CONGRATULATIONS! YOU BEAT THE GAME!       *
        *                                                  *
        *          All 10 bosses have been defeated!       *
        *                                                  *
        *           You are the ultimate champion!         *
        *                                                  *
        ****************************************************
        """)
        input("Press Enter to quit...")

    def start_new_level(self):
        """Starts a new level with increased difficulty."""
        self.cycle += 1  # Increment cycle once here
        self.clear()
        print("\n" + "*"*50)
        print(f"Starting New Game+{self.cycle}".center(50))
        print("*"*50 + "\n")
        # Update enemy distribution based on new cycle
        self.enemy_distribution = self._calculate_enemy_distribution()
        self.difficulty_multiplier = 1.0 + ((self.cycle + 1) * 0.2)  # Increases by 20% per cycle
        print(f"Using seed: {self.seed}")
        print("Initializing map...")
        # Create the map using the given seed
        map_w, map_h = 35, 25
        game_map = Map.generate_map_with_seed(map_w, map_h, self.seed)
        print("Map initialized")
        # Place player on new map
        self.hero.player_pos = (1, 1)  # Reset player position
        game_map.place_player(self.hero)
        print("Player placed on new map")
        # Generate enemies for new map with adjusted distribution
        selected_enemies = []
        selected_enemies.extend([generate_enemy("low") for _ in range(self.enemy_distribution["low"])])
        selected_enemies.extend([generate_enemy("mid") for _ in range(self.enemy_distribution["mid"])])
        selected_enemies.extend([generate_enemy("high") for _ in range(self.enemy_distribution["high"])])
        # Scale enemy stats for New Game+ cycles
        for enemy in selected_enemies:
            self.scale_enemy_stats(enemy)
        print(f"{len(selected_enemies)} enemies selected")
        game_map.place_enemies_on_map(selected_enemies)
        print("Enemies placed on new map")
        self.hero.enemies_killed = 0  # Reset kill counter for new map

        # Display the new map
        self.clear()
        game_map.display_map(self.hero)
        self.display_player_stats(game_map)
        print("\nWelcome to the next level! Use WASD to move.")
        input("Press Enter to continue...")
        
        # Continue the game with the new map
        self.continue_game_with_map(game_map)

    def continue_game_with_map(self, game_map):
        """Continues the game with the provided map."""
        # Main game loop for the new map
        while self.running:
            self.clear()
            game_map.display_map(self.hero)  # Display the map
            # Show player stats including enemy kill count
            self.display_player_stats(game_map)
            self.move_player(game_map)  # Handle player movement
            self.after_turn(self.hero, game_map)
        print("Game Over. Thanks for playing!")

    def display_level_up_message(self):
        """Displays a message after defeating a boss."""
        self.clear()
        print(f"You have defeated {self.boss_defeated} out of {self.total_bosses} bosses.")
        if self.boss_defeated < self.total_bosses:
            print("Prepare yourself for the next challenge!")
        else:
            print("Congratulations! You have defeated all the bosses!")
        input("Press Enter to continue...")

    def display_game_over_screen(self):
        self.clear()
        print("""
        ******************************************************
        *                                                    *
        *         The hero has fallen..... GAME OVER!        *
        *                                                    *
        ******************************************************
        """)
        input("Press Enter to return to the main menu...")
        self.running = False
        self.hero = Hero(name="Hero", health=150)
        self.hero.health_bar = HealthBar(self.hero, color="green")

    def after_turn(self, player, game_map):
        """Check conditions after a turn."""
        # We now handle this directly in enemy_encounter, so this method can be empty
        pass

    def boss_defeat_handler(self, boss):
        """Handle boss defeat, skill learning, and loot drops."""
        print(f"You have defeated {boss.name}!")
        # 1. Offer skill choice first
        learned = self.offer_boss_skill(boss)
        # 2. Handle weapon drop and other loot
        self.handle_boss_loot(boss)
        # 3. Update boss counter and prepare for next cycle if needed
        self.bosses_defeated += 1
        if self.bosses_defeated >= 10:  # All bosses defeated
            self.start_new_game_plus()
        else:
            print(f"You have defeated {self.bosses_defeated} out of 10 bosses.")
            print("Prepare yourself for the next challenge!")
        return learned

    def offer_boss_skill(self, boss):
        """Offer the player a choice of skills to learn from the defeated boss."""
        if not boss.skills:
            print("This boss had no skills to learn.")
            return False
        print("\nYou can learn one skill from the defeated boss:")
        # Show available skills
        valid_skills = []
        for i, skill in enumerate(boss.skills):
            if skill and skill.stealable:
                valid_skills.append(skill)
                print(f"{i+1}: {skill.name} - {skill.description if hasattr(skill, 'description') else ''}")
        if not valid_skills:
            print("No learnable skills available.")
            return False
        choice = input("\nChoose a skill to learn (or press Enter to skip): ")
        if not choice.strip():
            print("You chose not to learn any skill.")
            return False
        try:
            skill_idx = int(choice) - 1
            if 0 <= skill_idx < len(valid_skills):
                selected_skill = valid_skills[skill_idx]
                # Apply the skill to the hero
                if self.hero.learn_skill(selected_skill):
                    print(f"You learned {selected_skill.name}!")
                    # Apply any stat costs for stealing the skill
                    if hasattr(selected_skill, 'stat_cost'):
                        for stat, cost in selected_skill.stat_cost.items():
                            if hasattr(self.hero, stat):
                                setattr(self.hero, stat, getattr(self.hero, stat) + cost)
                                print(f"Your {stat} was affected by {cost}.")
                    return True
                else:
                    print("You already know this skill!")
                    return self.offer_boss_skill(boss)  # Recursive call to offer choice again
            else:
                print("Invalid choice.")
                return self.offer_boss_skill(boss)  # Recursive call to offer choice again
        except ValueError:
            print("Invalid input.")
            return self.offer_boss_skill(boss)  # Recursive call to offer choice again

    def handle_boss_loot(self, boss):
        """Handle loot drops from the boss."""
        # Handle boss weapon - ensure it has value scaled by cycle
        if hasattr(boss, 'weapon') and boss.weapon:
            # Scale weapon value by cycle
            base_value = 50  # Base value for boss weapons
            boss.weapon.value = int(base_value * (1 + 0.2 * self.cycle))
            print(f"\nThe boss dropped: {boss.weapon.name}")
            print(f"Value: {boss.weapon.value} gold")
            print(f"Damage: {boss.weapon.damage}")
            choice = input("Do you want to pick up this weapon? (y/n): ").lower()
            if choice == 'y':
                self.hero.equip_weapon(boss.weapon)
            else:
                # Add gold instead
                self.hero.cashpile += boss.weapon.value
                print(f"You gained {boss.weapon.value} gold instead.")
        # Handle other drops
        if hasattr(boss, 'drops') and boss.drops:
            # ... existing code for other drops...
            pass

    def flush_input_buffer(self):
        """Clear any pending keystrokes from the console buffer."""
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()  # Read and discard the character
        except (ImportError, AttributeError):
            # Fallback for non-Windows systems
            pass


if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Fatal error occurred: {e}")
        print("\nDetailed error information:")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)