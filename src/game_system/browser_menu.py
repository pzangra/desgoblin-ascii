"""Browser-friendly menu input and display for PyScript / JS integration."""

from typing import Optional, List

from game_system.browser_input import get_next_key
from game_system.browser_display import set_screen, is_browser_display


def render_menu(title: str, options: List[str], selected_index: int = 0, footer: str = "") -> str:
    """Render a menu as a string. Works for both terminal and browser."""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append(title.center(60))
    lines.append("=" * 60 + "\n")

    for idx, option in enumerate(options):
        marker = ">>> " if idx == selected_index else "    "
        lines.append(f"{marker}{idx + 1}. {option}")

    lines.append("")
    if footer:
        lines.append(footer)
    else:
        lines.append("Press number key or use arrow keys to select, Enter to confirm.")

    return "\n".join(lines)


def get_menu_choice(title: str, options: List[str], timeout: float = None) -> Optional[int]:
    """
    Get a menu choice (0-indexed) using Enter-confirmed input.
    Works in both terminal and browser mode.
    """
    while True:
        if is_browser_display():
            set_screen(render_menu(title, options, footer="Type a number and press Enter. Esc cancels."))
            buffered = []
            while True:
                typed = "".join(buffered) if buffered else ""
                set_screen(render_menu(title, options, footer=f"Choice: {typed}_\nType a number and press Enter. Esc cancels."))
                key = get_next_key(timeout=0.05)

                if key is None:
                    continue
                if key == "esc":
                    return None
                if key == "backspace":
                    buffered = buffered[:-1]
                    continue
                if key == "enter":
                    if not buffered:
                        continue
                    user_input = "".join(buffered).strip()
                    break
                if key.isdigit():
                    buffered.append(key)
            
            if user_input.isdigit():
                choice_idx = int(user_input) - 1
                if 0 <= choice_idx < len(options):
                    return choice_idx
            set_screen(render_menu(title, options, footer="Invalid choice. Type a valid number and press Enter."))
        else:
            display_menu_terminal(title, options)
            user_input = input("> ").strip()
            if user_input.isdigit():
                choice_idx = int(user_input) - 1
                if 0 <= choice_idx < len(options):
                    return choice_idx
            elif user_input.lower() in ("esc", "q"):
                return None
            print("Invalid input. Please enter a number and press Enter.")
            input("Press Enter to continue...")


def display_menu_terminal(title: str, options: List[str], selected_index: int = 0):
    """Display menu in terminal mode with clear screen."""
    import os
    os.system("cls" if os.name == "nt" else "clear")
    print(render_menu(title, options, selected_index))


def get_text_input(prompt: str, max_length: int = 100) -> Optional[str]:
    """
    Get text input from user.
    Browser: uses key polling with visual feedback
    Terminal: uses traditional input()
    """
    if is_browser_display():
        result = []
        while True:
            display_text = "".join(result)
            set_screen(f"{prompt}\n\n{display_text}_\n\nEnter to confirm, Backspace to delete, Esc to cancel")

            key = get_next_key(timeout=0.05)
            if key is None:
                continue

            if key == "enter":
                return "".join(result) if result else None
            elif key == "backspace":
                result = result[:-1]
            elif key == "esc":
                return None
            elif len(key) == 1 and len(result) < max_length:
                result.append(key)
    else:
        return input(prompt).strip() or None


def show_message(title: str, message: str, button_text: str = "Continue") -> None:
    """Show a message dialog and wait for confirmation."""
    if is_browser_display():
        set_screen(f"\n{'=' * 60}\n{title.center(60)}\n{'=' * 60}\n\n{message}\n\n Press any key to {button_text}...")
        get_next_key(timeout=None)
    else:
        import os
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\n{'=' * 60}")
        print(title.center(60))
        print(f"{'=' * 60}\n")
        print(message)
        input(f"\nPress Enter to {button_text}...")


def show_yes_no_prompt(title: str, message: str) -> bool:
    """Show a yes/no prompt. Returns True for yes, False for no."""
    if is_browser_display():
        while True:
            set_screen(
                f"\n{'=' * 60}\n{title.center(60)}\n{'=' * 60}\n\n"
                f"{message}\n\n"
                f"Press Y for Yes, N for No"
            )
            key = get_next_key(timeout=0.05)
            if key in ("y", "yes"):
                return True
            elif key in ("n", "no"):
                return False
    else:
        import os
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\n{'=' * 60}")
        print(title.center(60))
        print(f"{'=' * 60}\n")
        print(message)
        while True:
            response = input("\n(y/n): ").lower().strip()
            if response in ("y", "yes"):
                return True
            elif response in ("n", "no"):
                return False
            else:
                print("Please enter 'y' or 'n'.")
