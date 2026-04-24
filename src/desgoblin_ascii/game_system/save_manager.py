"""
Module to handle saving and loading game state.
"""

import os
import json
from battle_system.character import Hero
from battle_system.weapon import Weapon
from battle_system.enemy import generate_enemy, generate_boss
from map_system.map import Map
from battle_system.skill import SKILLS

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")

def load_saved_game(game):
    """
    Load a saved game state into the game object.
    
    Args:
        game: The Game instance to load the state into
        
    Returns:
        bool: True if game loaded successfully, False otherwise
    """
    try:
        with open(os.path.join(SAVE_DIR, "save_game.json"), "r") as f:
            save_data = json.load(f)
            
        # Restore seed if available
        if save_data.get("seed"):
            game.seed = save_data["seed"]
            
        # Restore cycle
        if "cycle" in save_data:
            game.hero.cycle = save_data["cycle"]
            
        # Create hero with saved stats
        player_data = save_data["player"]
        stats = player_data["stats"]
        
        # Update hero stats
        game.hero.name = stats["name"]
        game.hero.health = stats["health"]
        game.hero.health_max = stats["health_max"]
        game.hero.mp = stats["mp"]
        game.hero.mp_max = stats["mp_max"]
        game.hero.cashpile = stats["cashpile"]
        
        # Create and equip saved weapon
        weapon_data = player_data["weapon"]
        weapon = Weapon(
            name=weapon_data["name"], 
            damage=weapon_data["damage"], 
            value=weapon_data["value"],
            tier=weapon_data["tier"]
        )
        game.hero.equip_weapon(weapon)
        
        # Load skills
        if "skills" in player_data:
            game.hero.skills = []
            for skill_data in player_data["skills"]:
                skill_name = skill_data["name"]
                if skill_name in SKILLS:
                    game.hero.skills.append(SKILLS[skill_name])
        
        # Initialize map with saved dimensions
        map_data = save_data["map"]
        game_map = Map(map_data["width"], map_data["height"])
        
        # Restore tile states (visited, revealed)
        for y in range(map_data["height"]):
            for x in range(map_data["width"]):
                if y < len(map_data["visited_tiles"]) and x < len(map_data["visited_tiles"][y]):
                    game_map.grid[y][x].visited = map_data["visited_tiles"][y][x]
                
                if y < len(map_data.get("revealed_tiles", [])) and x < len(map_data["revealed_tiles"][y]):
                    if hasattr(game_map.grid[y][x], 'revealed'):
                        game_map.grid[y][x].revealed = map_data["revealed_tiles"][y][x]
        
        # Place player at saved position
        player_pos = player_data["position"]
        game_map.place_player(game.hero, player_pos["x"], player_pos["y"])
        
        # Spawn saved enemies
        for enemy_data in save_data["enemies"]:
            if "boss" in enemy_data["type"].lower():
                enemy = generate_boss(enemy_data["name"])
            else:
                enemy = generate_enemy(enemy_data.get("tier", "mid"))
                
            enemy.name = enemy_data["name"]
            enemy.health = enemy_data["health"]
            enemy.health_max = enemy_data["health_max"]
            enemy.x = enemy_data["position"]["x"]
            enemy.y = enemy_data["position"]["y"]
            game_map.enemies.append(enemy)
            game_map.grid[enemy.y][enemy.x].has_enemy = True
        
        # Restore inventory items
        game.hero.items = []
        for item_data in save_data["inventory"]:
            from battle_system.item import generate_item
            item = generate_item()  # You'll need to modify this to recreate the exact item
            if item:
                item.name = item_data["name"]
                item.description = item_data["description"]
                game.hero.items.append(item)
        
        # Set the map in the game
        game.map = game_map
        
        # Restore defeated bosses if possible
        try:
            from battle_system.enemy import Boss
            for boss_name in save_data.get("defeated_bosses", []):
                Boss.mark_defeated(boss_name)
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"Error loading game: {e}")
        return False
