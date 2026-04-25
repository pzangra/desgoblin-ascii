"""Browser display helpers for PyScript / JS terminal rendering."""

import os

try:
    from js import document  # type: ignore
    _HAS_BROWSER_DISPLAY = True
except Exception:
    _HAS_BROWSER_DISPLAY = False


def is_browser_display() -> bool:
    return _HAS_BROWSER_DISPLAY


def clear_terminal() -> None:
    """Clear the terminal/browser display."""
    if _HAS_BROWSER_DISPLAY:
        terminal = document.getElementById("terminal")
        if terminal:
            terminal.textContent = ""
    else:
        os.system("cls" if os.name == "nt" else "clear")


def _get_terminal_element():
    if not _HAS_BROWSER_DISPLAY:
        return None
    terminal = document.getElementById("terminal")
    return terminal


def set_screen(text: str) -> bool:
    """Replace the entire terminal content with text."""
    terminal = _get_terminal_element()
    if terminal is None:
        return False
    terminal.textContent = text
    terminal.scrollTop = 0
    return True


def append_screen(text: str) -> bool:
    """Append text to the terminal without changing the scroll position."""
    terminal = _get_terminal_element()
    if terminal is None:
        return False
    terminal.textContent += text
    return True


def clear_screen() -> bool:
    terminal = _get_terminal_element()
    if terminal is None:
        return False
    terminal.textContent = ""
    return True
