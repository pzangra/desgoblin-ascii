# map_system/tiles.py

# ANSI escape sequences for colors
ansi_colors = {
    'reset': '\033[0m',
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'bright_black': '\033[90m',
    'bright_red': '\033[91m',
    'bright_green': '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue': '\033[94m',
    'bright_magenta': '\033[95m',
    'bright_cyan': '\033[96m',
    'bright_white': '\033[97m',
}

class Tile:
    """Class to represent a map tile."""

    def __init__(self, symbol: str, color: str, colored: bool = True, walkable: bool = True, visited = False, looted = False, name = None):
        self.symbol_raw = symbol
        self.symbol = f"{color}{symbol}{ansi_colors['reset']}" if colored else symbol
        self.walkable = walkable  # Indicates if the tile can be walked on or have enemies
        self.visited = visited    # For tiles like villages that can be visited
        self.looted = looted      # For treasure tiles that have been looted
        self.name = name if name else f"{symbol} Tile"  # Default name if none provided
        
    def create_looted_version(self):
        """Creates a looted version of this tile (for treasures)"""
        return Tile(
            symbol="t",  # Lowercase 't' for looted treasure
            color=ansi_colors['bright_black'],  # Grey color
            walkable=True,
            visited=True,
            looted=True,
            name=f"Looted {self.name}"
        )

# Terrain tiles
plains = Tile(";", ansi_colors['yellow'], walkable=True, name="Plains")
forest = Tile("8", ansi_colors['green'], walkable=True, name="Forest")
dense_forest = Tile("♣", ansi_colors['bright_green'], walkable=True, name="Dense Forest")  # Alternative forest tile
brush = Tile("^", ansi_colors['magenta'], walkable=True, name="Brush")
mountain = Tile("A", ansi_colors['white'], walkable=True, name="Mountain")   # walkable
water = Tile("~", ansi_colors['blue'], walkable=False, name="Water")      # Impassable terrain
lake = Tile("§", ansi_colors['cyan'], walkable=False, name="Lake")       # Impassable terrain
desert = Tile(".", ansi_colors['bright_yellow'], walkable=True, name="Desert")
swamp = Tile("&", ansi_colors['bright_green'], walkable=True, name="Swamp")
snow = Tile("*", ansi_colors['bright_white'], walkable=True, name="Snow")
hill = Tile("m", ansi_colors['bright_magenta'], walkable=True, name="Hill")
river = Tile("≈", ansi_colors['bright_blue'], walkable=False, name="River")
beach = Tile("_", ansi_colors['yellow'], walkable=True, name="Beach")
cave = Tile("C", ansi_colors['bright_black'], walkable=True, name="Cave")
ruins = Tile("R", ansi_colors['red'], walkable=True, name="Ruins")
shrine = Tile("S", ansi_colors['bright_magenta'], walkable=False, name="Shrine")
default = Tile("#", ansi_colors['black'], walkable=True, name="Default")
player = Tile("P", ansi_colors['white'], walkable=False, name="Player")
#village = Tile("V", ansi_colors['green'], walkable=False, visited=False, name="Village")
treasure = Tile("T", ansi_colors['yellow'], walkable=False, looted=False, name="Treasure")

# Treasure tiles
# Pre-create a looted treasure tile for consistent appearance
looted_treasure = Tile("t", ansi_colors['bright_black'], walkable=True, looted=True, name="Looted Treasure")

# Function to create unique treasure tile instances
def create_new_treasure():
    """Creates a new unique treasure tile instance.
    Always use this function instead of a shared treasure tile to ensure
    each treasure on the map is independently trackable.
    """
    return Tile("T", ansi_colors['yellow'], walkable=False, looted=False, name="Treasure")

# Add new detail tiles
flower_tile = Tile("f", ansi_colors['bright_magenta'], walkable=True, name="Flowers")
rock_tile = Tile("r", ansi_colors['bright_black'], walkable=True, name="Rocks")
log_tile = Tile("l", ansi_colors['bright_yellow'], walkable=True, name="Log")
mushroom_tile = Tile("m", ansi_colors['bright_cyan'], walkable=True, name="Mushrooms")
cactus_tile = Tile("c", ansi_colors['green'], walkable=True, name="Cactus")
mud_tile = Tile(",", ansi_colors['bright_black'], walkable=True, name="Mud")
path_tile = Tile("-", ansi_colors['bright_yellow'], walkable=True, name="Path")