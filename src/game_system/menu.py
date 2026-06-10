# game_system/menu.py

import os
import json
from game_system.browser_menu import get_menu_choice, get_text_input, show_message, show_yes_no_prompt, render_menu
from game_system.browser_display import is_browser_display, clear_terminal
from game_system.browser_input import peek_key
from game_system.save_manager import has_saved_game, load_raw_save_state, save_game_state, list_saves, save_path_for_name

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
OPTIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game_options.json")

# Ensure the saves directory exists
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def get_main_menu_options():
    options = ["New Game"]
    if has_saved_game():
        options.append("Continue Game")  # loads default/autosave
    saves = list_saves()
    if saves:
        options.append("Load Save")      # pick from named saves
    options.extend(["Start with Seed", "Options", "Exit"])
    return options

async def handle_menu_input():
    """Handles input from the main menu and returns the player's choice and parameters."""
    while True:
        options = get_main_menu_options()
        choice_idx = await get_menu_choice("Welcome to the Chronicles of Desgoblin!", options)

        if choice_idx is None:
            continue

        # Map choice index to action
        has_save = has_saved_game()
        option_map = {
            0: "new_game",
            1: "continue_game" if has_save else "start_with_seed",
            2: "start_with_seed" if has_save else "options",
            3: "options" if has_save else "exit",
            4: "exit"
        }

        action = option_map.get(choice_idx)

        if action == "new_game":
            return {"action": "new_game"}

        elif action == "continue_game":
            return {"action": "continue_game"}
        
        elif action == "load_save":
            saves = list_saves()
            if not saves:
                await show_message("No Saves", "No save files found.")
                continue
            load_choice = await get_menu_choice("Select save", saves + ["Cancel"])
            if load_choice is None or load_choice == len(saves):
                continue
            return {"action": "load_save", "save_name": saves[load_choice]}

        elif action == "start_with_seed":
            seed_input = await get_text_input("Enter seed (numbers only): ", max_length=10)
            if seed_input and seed_input.isdigit():
                return {"action": "start_with_seed", "seed": int(seed_input)}
            else:
                await show_message("Invalid Seed", "Please enter a valid number.")

        elif action == "options":
            await show_options_menu()

        elif action == "exit":
            return {"action": "exit"}

async def show_options_menu():
    """Display and handle options menu."""
    options = load_options()

    while True:
        difficulty_text = options.get("difficulty", "Normal")
        menu_options = [
            f"Sound: {'On' if options.get('sound', True) else 'Off'}",
            f"Difficulty: {difficulty_text}",
            "Back to Main Menu"
        ]

        choice_idx = await get_menu_choice("Options Menu", menu_options)

        if choice_idx is None or choice_idx == 2:
            return

        if choice_idx == 0:
            options["sound"] = not options.get("sound", True)
            save_options(options)
            await show_message("Sound Updated", f"Sound is now {'On' if options['sound'] else 'Off'}")

        elif choice_idx == 1:
            diff_options = ["Easy", "Normal", "Hard"]
            diff_choice = await get_menu_choice("Select Difficulty", diff_options)
            if diff_choice is not None:
                difficulties = ["Easy", "Normal", "Hard"]
                options["difficulty"] = difficulties[diff_choice]
                save_options(options)
                await show_message("Difficulty Updated", f"Difficulty set to {options['difficulty']}")

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

async def in_game_menu(game):
    """Display the in-game menu when Q is pressed."""
    while True:
        menu_options = [
            "Return to game",
            "Save with name",
            "Save and quit",
            "Load save",
            "Exit without saving",
        ]
        choice_idx = await get_menu_choice("Game Menu", menu_options)

        if choice_idx is None or choice_idx == 0:
            return {"action": "resume"}

        elif choice_idx == 1:  # Save with name
            name = await get_text_input("Enter save name: ", max_length=30)
            if name and name.strip():
                path = save_path_for_name(name.strip())
                save_game_state(game, save_path=path)
                await show_message("Saved", f"Game saved as '{name.strip()}'.")
            else:
                await show_message("Cancelled", "Save cancelled.")
            # Stay in menu after saving

        elif choice_idx == 2:  # Save and quit
            name = await get_text_input("Enter save name (leave blank for 'autosave'): ", max_length=30)
            save_name = name.strip() if name and name.strip() else "autosave"
            path = save_path_for_name(save_name)
            save_game_state(game, save_path=path)
            await show_message("Saved", f"Game saved as '{save_name}'. Returning to menu.")
            return {"action": "save_and_exit"}

        elif choice_idx == 3:  # Load save
            saves = list_saves()
            if not saves:
                await show_message("No Saves", "No save files found.")
                continue
            load_choice = await get_menu_choice("Select save to load", saves + ["Cancel"])
            if load_choice is None or load_choice == len(saves):
                continue  # Cancelled
            selected_name = saves[load_choice]
            path = save_path_for_name(selected_name)
            from game_system.save_manager import load_saved_game
            if load_saved_game(game, save_path=path):
                await show_message("Loaded", f"'{selected_name}' loaded. Resuming game.")
                return {"action": "reload"}
            else:
                await show_message("Error", "Failed to load save.")

        elif choice_idx == 4:  # Exit without saving
            if await show_yes_no_prompt("Confirm Exit", "Exit to main menu without saving?"):
                return {"action": "exit_without_saving"}

def save_game(game):
    """Save current game state to file."""
    save_game_state(game)

async def load_game():
    """Load game state from save file."""
    save_data = load_raw_save_state()
    if save_data is None and not is_browser_display():
        await show_message("Load Error", "Error loading saved game.")
    return save_data

async def check_for_esc_key(game):
    """Check if ESC key is pressed and show in-game menu if it is."""
    key = peek_key()
    if key == "esc":
        result = await in_game_menu(game)
        if result["action"] in {"exit_without_saving", "save_and_exit"}:
            # Set running to False to exit the game loop and return to main menu
            game.running = False
            return result
        elif result["action"] == "resume":
            # This will continue the game loop
            return {"action": "continue"}
        return result
    return {"action": "continue"}

if __name__ == "__main__":
    import asyncio
    asyncio.run(handle_menu_input())
