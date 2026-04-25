import sys
import os
import asyncio
from random import randint

# Path fix for standalone running
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from map_system.map import Map
from map_system.tiles import *
from game_system.menu import handle_menu_input
from battle_system.character import Hero
from battle_system.enemy import generate_enemy
from battle_system.health_bar import HealthBar
from battle_system.item import create_item_from_name
from game_system.browser_input import async_input

class Game:
    def __init__(self):
        self.running = True
        self.hero = Hero(name="Hero", health=150)
        self.hero.health_bar = HealthBar(self.hero, color="green")

    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    async def run(self):
        # Start with the menu and wait for input
        print("Menu input called")
        menu_choice = await handle_menu_input()
        if menu_choice and menu_choice.get("action") in {"new_game", "continue_game", "start_with_seed"}:
            self.clear()
            print("Game starting...\nInitializing map...\n")

            # Initialize map and enemies
            map_w, map_h = 30, 15
            game_map = Map(map_w, map_h)
            print("Map initialized")
            game_map.place_player(self.hero)

            selected_enemies = [generate_enemy("low") for _ in range(5)] + \
                              [generate_enemy("mid") for _ in range(3)] + \
                              [generate_enemy("high") for _ in range(2)]
            game_map.place_enemies_on_map(selected_enemies)

            # Main game loop
            while self.running:
                self.clear()
                game_map.display_map()  # Display the map
                await self.move_player(game_map)  # Capture movement

                # Check if all enemies are defeated
                if not game_map.enemies:
                    self.display_victory_screen()
                    break

            print("Game Over. Thanks for playing!")
    
    async def display_victory_screen(self):
        self.clear()
        print("Congratulations! You defeated all enemies.")
        await async_input("Press any key to exit...")
        exit()
    
    async def move_player(self, game_map: Map):
        direction = (await async_input("Enter direction (w/a/s/d): ")).lower()
        x, y = game_map.player_pos
        new_x, new_y = x, y

        # Move the player based on direction
        if direction == 'w' and x > 0:
            new_x, new_y = x - 1, y
        elif direction == 's' and x < game_map.height - 1:
            new_x, new_y = x + 1, y
        elif direction == 'a' and y > 0:
            new_x, new_y = x, y - 1
        elif direction == 'd' and y < game_map.width - 1:
            new_x, new_y = x, y + 1
        else:
            print("Invalid input or move. Try again.")
            return  # Ask for input again

        # Check if player encounters an enemy
        if game_map.map_data[new_x][new_y].symbol_raw == 'E':
            print("Encountered an enemy!")
            await self.battle(game_map, new_x, new_y)
        else:
            # Update map: move player to new position
            game_map.move_player(new_x, new_y)
        
    async def battle(self, game_map: Map, enemy_x: int, enemy_y: int):
        enemy = game_map.get_enemy_at(enemy_x, enemy_y)

        if not enemy:
            print("No enemy found at this location.")
            return

        # Battle loop
        self.clear()
        print(f"Battle started between {self.hero.name} and {enemy.name}!")
        while self.hero.alive and enemy.alive:
            # Display both health bars
            self.hero.health_bar.draw()
            enemy.health_bar.draw()

            # Player's choice of action
            action = (await async_input("Choose your action: [a]ttack, [s]kills, [i]tems, [e]scape: ")).lower()

            if action == 'a':
                # Player attacks
                self.hero.attack(enemy)
                if enemy.alive:
                    enemy.attack(self.hero)
            elif action == 's':
                print("Skills to be implemented. Choose another action.")
                continue
            elif action == 'i':
                self.use_item()
            elif action == 'e':
                if self.attempt_escape(enemy):
                    return
            else:
                print("Invalid action. Try again.")
                continue

            await asyncio.sleep(1)

        if not enemy.alive:
            print(f"{enemy.name} has been defeated!")
            game_map.remove_enemy(enemy)
            await self.handle_loot(enemy)
        elif not self.hero.alive:
            print("You have been defeated! Game Over.")
            exit()
    
    async def handle_loot(self, enemy):
        print(f"You found {enemy.weapon.name}. Value: {enemy.weapon.value} gold.")
        choice = (await async_input("Do you want to pick it up or scrap it for gold? (p/s): ")).lower()
        if choice == 'p':
            print(f"You picked up {enemy.weapon.name}.")
            self.hero.scrap_current_weapon()
            self.hero.equip(enemy.weapon)
        elif choice == 's':
            print(f"Scrapped {enemy.weapon.name} for {enemy.weapon.value} gold.")
            self.hero.add_gold(enemy.weapon.value)

    def use_item(self):
        # Use an item during battle
        item = create_item_from_name("Small Health Potion")
        if item:
            print(f"Using {item.name}!")
            item.use(self.hero)

    def attempt_escape(self, enemy):
        escape_chance = {"low": 60, "mid": 40, "high": 20}
        chance = escape_chance.get(enemy.tier, 0)
        if randint(1, 100) <= chance:
            print("Escape successful!")
            return True
        else:
            print("Escape failed!")
            enemy.attack(self.hero)
            return False

if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())
