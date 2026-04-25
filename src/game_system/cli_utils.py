"""Shared CLI helpers for console control and input buffering."""

import os
import sys


def clear_console() -> None:
    """Clear the terminal in a cross-platform way."""
    os.system("cls" if os.name == "nt" else "clear")


def flush_input_buffer() -> None:
    """Best-effort non-blocking input-buffer flush for Windows and POSIX."""
    if os.name == "nt":
        try:
            import msvcrt

            while msvcrt.kbhit():
                msvcrt.getch()
        except (ImportError, AttributeError):
            pass
        return

    try:
        import select
        import termios
        import tty

        if not sys.stdin.isatty():
            return

        stdin_fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(stdin_fd)
        try:
            tty.setcbreak(stdin_fd)
            while select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.read(1)
        finally:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
    except Exception:
        # Keep this helper fail-safe for environments where terminal APIs differ.
        try:
            sys.stdout.flush()
        except Exception:
            pass
