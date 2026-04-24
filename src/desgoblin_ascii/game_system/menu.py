# game_system/menu.py

import os
import json
import keyboard
import sys
import random as rand

# Add the parent directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
OPTIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game_options.json")

# Ensure the saves directory exists
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def display_title():
    """Displays the game title and menu options."""
    print("\n" + "="*50)
    print("Welcome to the Chronicles of Desgoblin!".center(50))
    print("="*50 + "\n")
    
    # Check if a save file exists
    has_save = os.path.exists(os.path.join(SAVE_DIR, "save_game.json"))
    
    print("1. New Game")
    if has_save:
        print("2. Continue Game")
    print("3. Start with Seed")
    print("4. Options")
    print("5. Exit")

def handle_menu_input():
    """Handles input from the main menu and returns the player's choice and parameters."""
    while True:
        display_title()
        choice = input("> ").strip()
        
        if choice == "1":
            print("Starting New Game...")
            # Import game modules here to avoid circular imports
            from game_system.main import Game
            game = Game()
            # Set a random seed
            game.seed = rand.randint(0, game.MAX_SEED_VALUE)
            # Start the game directly
            game.start_game(new_game=True)
            # After game ends, return to menu
            continue
        
        elif choice == "2" and os.path.exists(os.path.join(SAVE_DIR, "save_game.json")):
            print("Loading saved game...")
            from game_system.main import Game
            from game_system.save_manager import load_saved_game
            game = Game()
            if load_saved_game(game):
                # Run the game with loaded state
                game.continue_game_with_map(game.map)
            else:
                print("Failed to load game. Returning to menu.")
                input("Press Enter to continue...")
            # Return to menu after game ends
            continue
        
        elif choice == "3":
            seed = input("Enter seed: ").strip()
            if seed:
                try:
                    seed_number = int(seed)
                    print(f"Starting game with seed: {seed}...")
                    from game_system.main import Game
                    game = Game()
                    game.seed = seed_number
                    game.start_game(new_game=True)
                    # Return to menu after game ends
                    continue
                except ValueError:
                    print("Invalid seed. Please enter a number.")
                    input("Press Enter to try again.")
            else:
                print("Invalid seed.")
                input("Press Enter to try again.")
        
        elif choice == "4":
            show_options_menu()
            # Continue the loop after showing options
            continue
        
        elif choice == "5":
            print("Exiting...")
            exit()
        
        else:
            print("Invalid input. Please enter a valid option.")
            input("Press Enter to try again.")

def show_options_menu():
    """Display and handle options menu."""
    # Load current options or use defaults
    options = load_options()
    
    while True:
        print("\nOptions Menu:")
        print("1. Sound: " + ("On" if options.get("sound", True) else "Off"))
        print("2. Difficulty: " + options.get("difficulty", "Normal"))
        print("3. Back to Main Menu")
        
        choice = input("> ").strip()
        
        if choice == "1":
            options["sound"] = not options.get("sound", True)
            save_options(options)
            print(f"Sound is now {'On' if options['sound'] else 'Off'}")
        
        elif choice == "2":
            print("Select Difficulty:")
            print("1. Easy")
            print("2. Normal")
            print("3. Hard")
            
            diff_choice = input("> ").strip()
            if diff_choice == "1":
                options["difficulty"] = "Easy"
            elif diff_choice == "2":
                options["difficulty"] = "Normal"
            elif diff_choice == "3":
                options["difficulty"] = "Hard"
            else:
                print("Invalid choice. Keeping current difficulty.")
            
            save_options(options)
            print(f"Difficulty set to {options['difficulty']}")
        
        elif choice == "3":
            return
        
        else:
            print("Invalid input. Please enter a valid option.")

def load_options():
    """Load options from file or return defaults."""
    try:
        if os.path.exists(OPTIONS_PATH):
            with open(OPTIONS_PATH, "r") as f:
                return json.load(f)
    except:
        pass
    
    # Default options
    return {"sound": True, "difficulty": "Normal"}

def save_options(options):
    """Save options to file."""
    with open(OPTIONS_PATH, "w") as f:
        json.dump(options, f)

def in_game_menu(game):
    """Display the in-game menu when ESC is pressed."""
    menu_active = True
    
    while menu_active:
        print("\n" + "="*50)
        print("Game Menu".center(50))
        print("="*50 + "\n")
        print("1. Resume Game")
        print("2. Save Game")
        print("3. Options")
        print("4. Return to Main Menu")
        
        choice = input("> ").strip()
        
        if choice == "1":
            return {"action": "resume"}
        
        elif choice == "2":
            save_game(game)
            print("Game saved successfully!")
            input("Press Enter to continue...")
        
        elif choice == "3":
            show_options_menu()
            # Stay in the menu after showing options
        
        elif choice == "4":
            confirm = input("Any unsaved progress will be lost. Are you sure? (y/n): ").lower()
            if confirm == 'y':
                return {"action": "main_menu"}
        
        else:
            print("Invalid input. Please enter a valid option.")

def save_game(game):
    """Save current game state to file."""
    save_data = create_save_state(game)
    with open(os.path.join(SAVE_DIR, "save_game.json"), "w") as f:
        json.dump(save_data, f)

def load_game():
    """Load game state from save file."""
    try:
        with open(os.path.join(SAVE_DIR, "save_game.json"), "r") as f:
            return json.load(f)
    except:
        print("Error loading saved game.")
        return None

def create_save_state(game):
    """Create a dictionary with all necessary game state information."""
    save_state = {
        "cycle": getattr(game.hero, "cycle", 0),
        "seed": game.seed if hasattr(game, "seed") else None,
        "defeated_bosses": [],  # You'll need to populate this from your boss system
        "player": {
            "position": {"x": game.hero.x, "y": game.hero.y},
            "stats": {
                "name": game.hero.name,
                "health": game.hero.health,
                "health_max": game.hero.health_max,
                "mp": game.hero.mp,
                "mp_max": game.hero.mp_max,
                "cashpile": game.hero.cashpile
            },
            "weapon": {
                "name": game.hero.weapon.name,
                "damage": game.hero.weapon.damage,
                "value": game.hero.weapon.value,
                "tier": game.hero.weapon.tier
            },
            "skills": [{"name": skill.name, "cooldown": skill.cooldown, "mp_cost": skill.mp_cost} 
                      for skill in game.hero.skills] if hasattr(game.hero, "skills") else []
        },
        "enemies": [
            {
                "name": enemy.name,
                "type": enemy.__class__.__name__,
                "position": {"x": enemy.x, "y": enemy.y},
                "health": enemy.health,
                "health_max": enemy.health_max
            } for enemy in game.map.enemies
        ],
        "map": {
            "width": game.map.width,
            "height": game.map.height,
            "visited_tiles": [[tile.visited for tile in row] for row in game.map.grid],
            "revealed_tiles": [[tile.revealed if hasattr(tile, 'revealed') else False for tile in row] for row in game.map.grid],
            "tile_types": [[tile.__class__.__name__ for tile in row] for row in game.map.grid]
        },
        "inventory": [
            {
                "name": item.name,
                "type": item.__class__.__name__,
                "description": item.description
            } for item in game.hero.items
        ]
    }
    
    # Try to add boss defeated status if available
    from battle_system.enemy import Boss
    try:
        save_state["defeated_bosses"] = Boss.get_defeated_bosses()
    except:
        pass
        
    return save_state

def check_for_esc_key(game):
    """Check if ESC key is pressed and show in-game menu if it is."""
    if keyboard.is_pressed('esc'):
        # Give a short delay to prevent multiple menu triggers
        keyboard.wait('esc', suppress=True)  # Wait for key release
        result = in_game_menu(game)
        if result["action"] == "main_menu":
            # Set running to False to exit the game loop and return to main menu
            game.running = False
            return result
        elif result["action"] == "resume":
            # This will continue the game loop
            return {"action": "continue"}
        return result
    return {"action": "continue"}

if __name__ == "__main__":
    handle_menu_input()