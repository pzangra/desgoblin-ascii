class Item:
    """Base class for all items."""

    def __init__(self, name: str, description: str, tier: str, value: int):
        self.name = name
        self.description = description
        self.tier = tier
        self.value = value

    def use(self, target):
        """Defines what happens when the item is used."""
        pass


class Cure(Item):
    """Cure items that heal the target."""

    heal_percentages = {
        "small": 15,
        "mids": 30,
        "midh": 50,
        "large": 70,
        "superior": 100
    }

    def __init__(self, name: str, description: str, tier: str, value: int):
        super().__init__(name, description, tier, value)
        self.heal_percent = self.heal_percentages.get(tier, 0)

    def use(self, target):
        """Heals the target by a percentage of their max health."""
        heal_amount = int(target.health_max * self.heal_percent / 100)
        old_health = target.health
        target.health = min(target.health + heal_amount, target.health_max)
        actual_heal = target.health - old_health
        
        print(f"{target.name} used {self.name} and healed {actual_heal} HP!")
        
        # Update health bar if it exists
        if hasattr(target, 'health_bar') and hasattr(target.health_bar, 'update'):
            target.health_bar.update()
        
        # Show updated health
        print(f"{target.name}'s health: {target.health}/{target.health_max}")
        
        return True


class Throwable(Item):
    """Throwable items that deal damage to the enemy."""

    def __init__(self, name: str, description: str, tier: str, value: int, damage: int):
        super().__init__(name, description, tier, value)
        self.damage = damage

    def use(self, target):
        """Deals damage to the target."""
        target.take_damage(self.damage)
        print(f"{target.name} took {self.damage} damage from {self.name}!")
        return True


def generate_cure(tier: str) -> Cure:
    """Generates a cure item based on the tier."""
    cure_names = {
        "small": "Small Health Potion",
        "mids": "Medium Health Potion",
        "midh": "Strong Health Potion",
        "large": "Large Health Potion",
        "superior": "Superior Health Potion"
    }
    name = cure_names.get(tier, "Unknown Potion")
    description = f"Heals {Cure.heal_percentages.get(tier, 0)}% of max health."
    value = {
        "small": 10,
        "mids": 20,
        "midh": 35,
        "large": 50,
        "superior": 75
    }.get(tier, 0)
    return Cure(name, description, tier, value)


def generate_throwable(tier: str) -> Throwable:
    """Generates a throwable item based on the tier."""
    throwable_names = {
        "small": "Throwing Knife",
        "mids": "Bomb",
        "midh": "Fire Flask",
        "large": "Poison Dart",
        "superior": "Explosive Charge"
    }
    name = throwable_names.get(tier, "Unknown Throwable")
    description = "Deals damage to an enemy."
    damage = {
        "small": 10,
        "mids": 20,
        "midh": 35,
        "large": 50,
        "superior": 75
    }.get(tier, 0)
    value = damage  # For simplicity, value equals damage
    return Throwable(name, description, tier, value, damage)


def create_item_from_name(name):
    """Creates an item instance based on the item name."""
    # Map item names to generated items
    name_to_item = {
        # Cures
        "Small Health Potion": generate_cure("small"),
        "Medium Health Potion": generate_cure("mids"),
        "Strong Health Potion": generate_cure("midh"),
        "Large Health Potion": generate_cure("large"),
        "Superior Health Potion": generate_cure("superior"),
        # Throwables
        "Throwing Knife": generate_throwable("small"),
        "Bomb": generate_throwable("mids"),
        "Fire Flask": generate_throwable("midh"),
        "Poison Dart": generate_throwable("large"),
        "Explosive Charge": generate_throwable("superior"),
        # Add more items as needed
    }
    return name_to_item.get(name)