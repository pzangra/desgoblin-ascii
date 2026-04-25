"""Browser-friendly input helpers for PyScript / JS key event integration."""

import asyncio
import os
import sys
import time
from typing import Optional

try:
    from js import window  # type: ignore
    _HAS_BROWSER_QUEUE = True
except Exception:
    _HAS_BROWSER_QUEUE = False


def _init_queue() -> None:
    if not _HAS_BROWSER_QUEUE:
        return
    if not hasattr(window, "keyQueue") or window.keyQueue is None:
        window.keyQueue = []


def _normalize_key(key: str) -> str:
    key = str(key).lower()
    if key in ("escape", "esc", "\x1b"):
        return "esc"
    return key


def _read_console_key(timeout: float = None) -> Optional[str]:
    """Read a single key from the local terminal without requiring Enter."""
    if os.name == "nt":
        try:
            import msvcrt

            if timeout is None:
                return _normalize_key(msvcrt.getwch())

            start = time.time()
            while True:
                if msvcrt.kbhit():
                    return _normalize_key(msvcrt.getwch())
                if (time.time() - start) >= timeout:
                    return None
                time.sleep(0.02)
        except Exception:
            return None

    try:
        import select
        import termios
        import tty

        if not sys.stdin.isatty():
            value = input("Press a key: ").strip().lower()
            return _normalize_key(value[:1] if value else "")

        stdin_fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(stdin_fd)
        try:
            tty.setcbreak(stdin_fd)
            if timeout is not None:
                ready, _, _ = select.select([sys.stdin], [], [], timeout)
                if not ready:
                    return None
            else:
                while not select.select([sys.stdin], [], [], 0)[0]:
                    time.sleep(0.02)
            key = sys.stdin.read(1)
            if key == "\x1b":
                return "esc"
            return _normalize_key(key)
        finally:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
    except Exception:
        try:
            value = input("Press a key: ").strip().lower()
            return _normalize_key(value[:1] if value else "")
        except Exception:
            return None


async def get_next_key_async(timeout: float = None) -> Optional[str]:
    """Wait for the next queued browser key or fallback to console input asynchronously."""
    if _HAS_BROWSER_QUEUE:
        _init_queue()
        start = asyncio.get_event_loop().time()
        while True:
            if int(window.keyQueue.length) > 0:
                return _normalize_key(window.keyQueue.shift())
            if timeout is not None and (asyncio.get_event_loop().time() - start) >= timeout:
                return None
            await asyncio.sleep(0.02)

    return _read_console_key(timeout)


async def async_input(prompt: str = "") -> str:
    """Non-blocking input wrapper for browser and local environments."""
    if _HAS_BROWSER_QUEUE:
        from game_system.browser_display import set_screen

        buffer = []
        while True:
            display_text = prompt + "\n" + "".join(buffer) + "_"
            set_screen(display_text)
            key = await get_next_key_async(timeout=0.05)
            if key is None:
                continue
            if key == "enter":
                return "".join(buffer)
            if key == "backspace":
                buffer = buffer[:-1]
                continue
            if key == "esc":
                return ""
            if len(key) == 1:
                buffer.append(key)
    else:
        return input(prompt)


def get_next_key(timeout: float = None) -> Optional[str]:
    """Wait for the next queued browser key, or fallback to console input."""
    if _HAS_BROWSER_QUEUE:
        _init_queue()
        start = time.time()
        while True:
            if int(window.keyQueue.length) > 0:
                return _normalize_key(window.keyQueue.shift())
            if timeout is not None and (time.time() - start) >= timeout:
                return None
            time.sleep(0.02)

    return _read_console_key(timeout)


def peek_key() -> Optional[str]:
    """Peek at the next queued key without removing it from the queue."""
    if not _HAS_BROWSER_QUEUE:
        return None
    _init_queue()
    if int(window.keyQueue.length) > 0:
        return _normalize_key(window.keyQueue[0])
    return None
