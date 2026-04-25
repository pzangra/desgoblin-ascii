# battle_system/health_bar.py

import os

# Enable ANSI escape sequences in terminal
os.system("")

class HealthBar:
    """Class to represent a health bar for characters."""

    symbol_remaining: str = "█"
    symbol_lost: str = "_"
    barrier: str = "|"
    colors: dict = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "default": "\033[0m"
    }

    def __init__(self, entity, length: int = 20, color: str = "default") -> None:
        self.entity = entity
        self.length = length
        self.max_value = entity.health_max
        self.current_value = entity.health
        self.color = self.colors.get(color, self.colors["default"])

    def update(self) -> None:
        """Updates the health bar based on the entity's current health."""
        self.current_value = self.entity.health

    def draw(self) -> None:
        """Draws the health bar in the console."""
        # Calculate the number of filled and lost bars
        remaining_bars = round(self.current_value / self.max_value * self.length)
        lost_bars = self.length - remaining_bars

        # Construct the health bar string
        health_bar = (
            f"{self.barrier}"
            f"{self.color}"
            f"{self.symbol_remaining * remaining_bars}"
            f"{self.colors['default']}"
            f"{self.symbol_lost * lost_bars}"
            f"{self.barrier}"
        )

        # Display the health bar
        print(f"{self.entity.name}'s HEALTH: {self.entity.health}/{self.entity.health_max}")
        print(health_bar)