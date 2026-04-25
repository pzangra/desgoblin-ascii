# map_system/map.py

import random
from collections import Counter
from random import randint

from noise import pnoise2

from map_system.tiles import *
from map_system.tiles import default
from battle_system.enemy import generate_enemy
from game_system.cli_utils import clear_console, flush_input_buffer

class Map:
    """Class to represent the game map."""

    def __init__(self, width: int, height: int, seed: int = None):
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)

        # Create elevation and moisture maps for more natural biome distribution
        self.elevation_map = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.moisture_map = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.map_data = [[default for _ in range(self.width)] for _ in range(self.height)]
        self.enemies = []
        self.entities = []
        self.boss_spawned = False
        self.player_pos = (1, 1)
        self.player_previous_tile = self.map_data[self.player_pos[0]][self.player_pos[1]]

        # Generate terrain using balanced distribution instead of noise-based approach
        self.create_frame()
        self.generate_balanced_terrain()  # Replace generate_terrain() with this new method
        self.generate_rivers_improved()
        self.add_beaches()
        self.place_structures()
        self.add_details()

    @classmethod
    def generate_map_with_seed(cls, width: int, height: int, seed: int):
        """Generates a map with a specific seed value."""
        return cls(width, height, seed)
    
    def place_player(self, hero):
        """Places the player on the map."""
        x, y = self.player_pos  # Use the initialized player position
        self.map_data[x][y] = player

    def refill_tile(self, x: int, y: int):
        # Logic to refill the tile previously occupied by the player or an enemy
        adjacent_tiles = []

        # Loop to gather adjacent tile types
        for i in range(max(0, x - 1), min(self.height, x + 2)):
            for j in range(max(0, y - 1), min(self.width, y + 2)):
                if (i, j) != (x, y):  # Exclude the current position
                    if self.map_data[i][j] is not None:
                        adjacent_tiles.append(self.map_data[i][j])

        # Find the most common adjacent tile to determine what tile should replace the player's old position
        if adjacent_tiles:
            tile_counts = Counter([tile.symbol_raw for tile in adjacent_tiles])
            most_common_tile_symbol = tile_counts.most_common(1)[0][0]

            # Set the tile object back based on the symbol
            for tile in [plains, forest, mountain, brush, default]:
                if tile.symbol_raw == most_common_tile_symbol:
                    return tile

        # If no adjacent tile or in case of error, return the default tile
        return default

    def create_frame(self):
        """Creates a boundary frame around the map."""
        for x in range(self.height):
            for y in range(self.width):
                if x == 0 or x == self.height - 1:
                    self.map_data[x][y] = Tile("=", "\033[37m")  # Top and bottom borders
                elif y == 0 or y == self.width - 1:
                    self.map_data[x][y] = Tile("|", "\033[37m")  # Left and right borders

    def fill_default(self):
        """Fills the internal part of the map with default tiles."""
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                self.map_data[x][y] = default

    def generate_patches(self):
        """Generates biome patches on the map."""
        biome_types = [
            (plains, 20, 5, 15),
            (forest, 15, 3, 12),
            (mountain, 10, 4, 10),
            (lake, 7, 4, 8),
            (brush, 12, 3, 10),
            (desert, 10, 4, 12),
            (swamp, 8, 3, 10),
            (snow, 5, 4, 10),
            (hill, 10, 3, 10),
        ]
        for tile, num_patches, min_size, max_size in biome_types:
            self.generate_patch(tile, num_patches, min_size, max_size)

    def generate_patch(self, tile: Tile, num_patches: int, min_size: int, max_size: int):
        """Generates individual patches of a specific biome."""
        for _ in range(num_patches):
            patch_size = randint(min_size, max_size)
            x_start = randint(1, self.height - 2)
            y_start = randint(1, self.width - 2)

            for _ in range(patch_size):
                x_new, y_new = x_start, y_start
                for _ in range(patch_size):
                    direction = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
                    x_new = min(max(1, x_new + direction[0]), self.height - 2)
                    y_new = min(max(1, y_new + direction[1]), self.width - 2)

                    if self.map_data[x_new][y_new] == default:
                        self.map_data[x_new][y_new] = tile

    def generate_rivers(self, num_rivers=3):
        """Generates rivers on the map."""
        for _ in range(num_rivers):
            # Start from a random mountain tile or edge of the map
            x = randint(1, self.height - 2)
            y = randint(1, self.width - 2)
            while self.map_data[x][y] != mountain:
                x = randint(1, self.height - 2)
                y = randint(1, self.width - 2)
            # Create a river path
            length = randint(10, 20)
            for _ in range(length):
                self.map_data[x][y] = river
                direction = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
                x = min(max(1, x + direction[0]), self.height - 2)
                y = min(max(1, y + direction[1]), self.width - 2)

    def place_structures(self):
        """Places structures like villages on the map."""
        # Place villages preferably on plains
        plains_locations = []
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                if self.map_data[x][y] == plains:
                    plains_locations.append((x, y))
        
        # Place 2-3 villages
        for _ in range(random.randint(2, 3)):
            if plains_locations:
                x, y = random.choice(plains_locations)
                plains_locations.remove((x, y))
                self.map_data[x][y] = Tile("V", ansi_colors['green'], walkable=False, visited=False)
                
                # Create roads/paths around villages
                self.create_paths_from_village(x, y)
            else:
                # Fallback if no plains
                while True:
                    x = randint(1, self.height - 2)
                    y = randint(1, self.width - 2)
                    if self.map_data[x][y].walkable and self.map_data[x][y] not in [lake, river, water]:
                        self.map_data[x][y] = Tile("V", ansi_colors['green'], walkable=False, visited=False)
                        break

        # Place caves in mountains
        mountain_locations = []
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                if self.map_data[x][y] == mountain:
                    mountain_locations.append((x, y))
        
        # Place 2-4 caves
        for _ in range(min(random.randint(2, 4), len(mountain_locations))):
            if mountain_locations:
                x, y = random.choice(mountain_locations)
                mountain_locations.remove((x, y))
                self.map_data[x][y] = cave
            
        # Place ruins in various biomes with preference for plains and desert
        potential_ruin_locations = []
        for x in range(2, self.height - 2):
            for y in range(2, self.width - 2):
                if self.map_data[x][y] in [plains, desert]:
                    potential_ruin_locations.append((x, y, 3))  # Higher weight for plains/desert
                elif self.map_data[x][y] in [forest, hill, brush]:
                    potential_ruin_locations.append((x, y, 1))  # Lower weight for other biomes
        
        # Place 2-3 ruins
        if potential_ruin_locations:
            weighted_locations = []
            for x, y, weight in potential_ruin_locations:
                weighted_locations.extend([(x, y)] * weight)
                
            for _ in range(min(random.randint(2, 3), len(potential_ruin_locations))):
                if weighted_locations:
                    x, y = random.choice(weighted_locations)
                    # Remove all instances of this location
                    weighted_locations = [loc for loc in weighted_locations if loc != (x, y)]
                    self.map_data[x][y] = ruins
        
        # Place treasure chests in interesting locations (caves, forests, etc.)
        for _ in range(random.randint(1, 3)):
            for attempt in range(20):  # Try up to 20 times to find a suitable location
                x = randint(1, self.height - 2)
                y = randint(1, self.width - 2)
                current_tile = self.map_data[x][y]
                
                # Place treasure in caves, forests, or other interesting places
                if current_tile in [cave, forest, ruins, mountain] and current_tile.walkable:
                    self.map_data[x][y] = treasure
                    break

    def place_shrine(self, x=None, y=None, is_final_boss=False):
        """Place a shrine on the map, preferably on a ruins tile."""
        shrine_placed = False
        shrine_coords = None
        
        # First try to find a ruins tile (symbol_raw = 'R')
        ruins_locations = []
        for i in range(1, self.height-1):
            for j in range(1, self.width-1):
                if self.map_data[i][j].symbol_raw == 'R':  # Check for ruins
                    ruins_locations.append((j, i))  # Store as (x,y) format
        
        # If we found ruins locations, randomly select one
        if ruins_locations:
            x, y = random.choice(ruins_locations)
            shrine_placed = True
            print(f"A shrine has appeared on the ancient ruins at ({x}, {y})!")
        # If no ruins found or coordinates are specified, use the original logic
        elif x is None or y is None:
            for _ in range(100):  # Try up to 100 times to find a suitable location
                x = random.randint(2, self.width - 3)
                y = random.randint(2, self.height - 3)
                
                # Check if the location is a valid floor tile with no entities
                if self.is_floor(x, y) and not self.get_entity_at(x, y):
                    shrine_placed = True
                    print(f"A shrine has appeared at coordinates ({x}, {y})!")
                    break
            else:
                # If no suitable location found after 100 tries, use center of map
                x, y = self.width // 2, self.height // 2
                shrine_placed = True
                print(f"A shrine has appeared at the center of the map ({x}, {y})!")
        
        # Create a shrine tile with appropriate color
        if shrine_placed:
            # Gold color for final boss, bright purple for regular bosses
            color = "\033[93m" if is_final_boss else "\033[95m"
            self.map_data[y][x] = Tile("S", color, walkable=True)
            shrine = {"type": "shrine", "x": x, "y": y, "activated": False, "is_final": is_final_boss}
            self.entities.append(shrine)
            shrine_coords = (x, y)
        
        return shrine, shrine_coords  # Return the shrine object and its coordinates

    def is_floor(self, x, y):
        """Check if the specified location is a floor tile (passable)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.map_data[x][y] == default
        return False

    def get_entity_at(self, x, y):
        """Get entity at specified coordinates."""
        for entity in self.entities:
            if isinstance(entity, dict) and entity.get('x') == x and entity.get('y') == y:
                return entity
        return None

    def display_map(self, hero=None):
        """Display the map with the player's position."""
        # Always display seed at the top, even without hero
        print(f"Seed: {self.seed}", end="")
        
        # Display player stats if hero is provided
        if hero:
            weapon_name = hero.weapon.name if hasattr(hero, 'weapon') and hero.weapon else "None"
            weapon_damage = hero.weapon.damage if hasattr(hero, 'weapon') and hero.weapon else 0
            cash = hero.cashpile if hasattr(hero, 'cashpile') else 0
            print(f" | Hero HP: {hero.health}/{hero.health_max} | MP: {hero.mp}/{hero.mp_max} | Weapon: {weapon_name} (Damage: {weapon_damage}) | Cash: {cash}")
        else:
            print()  # Just a newline if no hero data
        
        # Remove the "#map" label line that was here
        
        # Continue with map display
        for i in range(self.height):
            for j in range(self.width):
                # Check if this position is the player's position
                if hero and hero.player_pos == (i, j):
                    print(f"\033[93m@\033[0m", end="")
                    
                    # Store underlying tile info for display in status area
                    tile = self.player_previous_tile  # Use the underlying tile instead of player tile
                    if not hasattr(hero, 'current_tile_info'):
                        hero.current_tile_info = {}
                    
                    # Set current tile info on hero object
                    tile_name = self.get_tile_name(tile.symbol_raw)
                    hero.current_tile_info = {
                        'symbol': tile.symbol_raw,
                        'name': tile_name,
                        'visited': getattr(tile, 'visited', False),
                        'looted': getattr(tile, 'looted', False)
                    }
                else:
                    # Just print the tile symbol as normal
                    print(self.map_data[i][j].symbol, end="")
            print()
        
        # Display underlying tile information if player is on a tile
        if hero and hasattr(hero, 'current_tile_info'):
            tile_info = hero.current_tile_info
            status = "Visited" if tile_info.get('visited', False) else "Not Visited"
            if 'looted' in tile_info and tile_info['looted']:
                status += ", Looted"
            
            print(f"\nYou are standing on {tile_info.get('name', 'Unknown')} at position {hero.player_pos[1]}, {hero.player_pos[0]}")

    def render_map(self, hero=None):
        """Render the map into a text string for browser redraws."""
        lines = []
        header = f"Seed: {self.seed}"
        if hero:
            weapon_name = hero.weapon.name if hasattr(hero, 'weapon') and hero.weapon else "None"
            weapon_damage = hero.weapon.damage if hasattr(hero, 'weapon') and hero.weapon else 0
            cash = hero.cashpile if hasattr(hero, 'cashpile') else 0
            header += f" | Hero HP: {hero.health}/{hero.health_max} | MP: {hero.mp}/{hero.mp_max} | Weapon: {weapon_name} (Damage: {weapon_damage}) | Cash: {cash}"
        lines.append(header)

        for i in range(self.height):
            row = []
            for j in range(self.width):
                if hero and hero.player_pos == (i, j):
                    row.append("@")
                    tile = self.player_previous_tile
                    if not hasattr(hero, 'current_tile_info'):
                        hero.current_tile_info = {}
                    tile_name = self.get_tile_name(tile.symbol_raw)
                    hero.current_tile_info = {
                        'symbol': tile.symbol_raw,
                        'name': tile_name,
                        'visited': getattr(tile, 'visited', False),
                        'looted': getattr(tile, 'looted', False)
                    }
                else:
                    row.append(self.map_data[i][j].symbol)
            lines.append("".join(row))

        if hero and hasattr(hero, 'current_tile_info'):
            tile_info = hero.current_tile_info
            status = "Visited" if tile_info.get('visited', False) else "Not Visited"
            if 'looted' in tile_info and tile_info['looted']:
                status += ", Looted"
            lines.append("")
            lines.append(f"You are standing on {tile_info.get('name', 'Unknown')} at position {hero.player_pos[1]}, {hero.player_pos[0]}")

        return "\n".join(lines)

    def get_tile_name(self, x, y=None):
        """Returns a friendly name for a tile.
        
        Can be called in two ways:
        - get_tile_name(symbol_raw) - Pass just the symbol
        - get_tile_name(x, y) - Pass the x, y coordinates
        """
        # Case 1: If y is None, assume x is the symbol_raw
        if y is None:
            symbol_raw = x
            # Use the simple tile name mapping
            tile_names = {
                '.': "Floor",
                '~': "Water",
                '#': "Wall", 
                'T': "Treasure",
                't': "Looted Treasure",
                'S': "Shrine", 
                'V': "Village",
                'v': "Visited Village",
                'E': "Enemy",
                'R': "Ruins",
                '§': "Lake",
                # Add other necessary tile mappings from both implementations
                ';': "Plains",
                '8': "Forest",
                '^': "Brush",
                'A': "Mountain",
                '&': "Swamp",
                '*': "Snow",
                'm': "Hill",
                '≈': "River",
                '_': "Beach",
                'C': "Cave",
                'P': "Player"
            }
            return tile_names.get(symbol_raw, "Unknown")
        
        # Case 2: Use the x, y coordinates to get the tile
        if 0 <= x < self.width and 0 <= y < self.height:
            # Check if this is the player's position
            if (y, x) == self.player_pos:  # Note: player_pos is stored as (y, x)
                # Use the underlying tile that the player is standing on
                tile = self.player_previous_tile
            else:
                # Otherwise, get the tile from the map
                tile = self.map_data[y][x]
            
            # Map symbols to readable names
            # ... existing code with tile_names dictionary ...
            
            return tile_names.get(tile.symbol_raw, "Unknown")
        return "Out of bounds"

    def clear_screen(self):
        """Clears the console screen and flushes input buffer."""
        clear_console()
        flush_input_buffer()

    def handle_treasure_encounter(self, hero):
        """Handle player interaction with a treasure tile."""
        x, y = hero.player_pos
        if self.player_previous_tile.symbol_raw == 'T':
            # Generate a random item or gold as treasure
            from random import choice, randint, random
            from battle_system.item import create_item_from_name
            from battle_system.weapon import generate_weapon
            
            # List of possible item rewards
            possible_items = [
                "Small Health Potion", 
                "Medium Health Potion", 
                "Throwing Knife", 
                "Bomb"
            ]
            
            # Choose reward type with weapon now as an option
            reward_type = choice(["item", "gold", "weapon"])
            
            if reward_type == "item":
                item_name = choice(possible_items)
                item = create_item_from_name(item_name)
                hero.inventory.append(item)
                print(f"\nYou found a treasure chest! Inside is: {item.name}")
                
            elif reward_type == "weapon":
                # Determine weapon tier based on probabilities (45% low, 35% mid, 20% high)
                roll = random()
                if roll < 0.45:  # 45% chance for low tier
                    weapon_tier = "low"
                elif roll < 0.80:  # 35% chance for mid tier (0.45 + 0.35 = 0.80)
                    weapon_tier = "mid" 
                else:  # 20% chance for high tier
                    weapon_tier = "high"
                
                # Generate the weapon
                weapon = generate_weapon(weapon_tier)
                hero.inventory.append(weapon)
                print(f"\nYou found a treasure chest! Inside is: {weapon.name} ({weapon_tier} tier)")
                
            else:  # Gold reward
                gold_amount = randint(50, 200)
                hero.cashpile += gold_amount
                print(f"\nYou found a treasure chest! Inside is: {gold_amount} gold")
            
            # Prompt for input to continue
            input("\nPress Enter to continue...")
            
            # Convert the treasure tile to a looted treasure tile (grey and uninteractive)
            self.player_previous_tile = Tile("t", ansi_colors['bright_black'], walkable=True, looted=True)
            
            return True
        return False

    def update_player_position(self, old_x, old_y, new_x, new_y):
        """Updates the player's position on the map."""
        self.map_data[old_x][old_y] = self.player_previous_tile  # Restore the tile under the player
        # Save the underlying tile before moving the player
        self.player_previous_tile = self.map_data[new_x][new_y]
        self.map_data[new_x][new_y] = player
        self.player_pos = (new_x, new_y)
        
        # Check if the player moved onto a treasure tile and handle it if needed
        # Note: This should be called by whatever code controls player movement

    def select_enemies(self, boss_defeated, cycle):
        """Selects a list of enemies to place on the map."""
        level_multiplier = 1 + (boss_defeated * 0.2) + (cycle * 0.2)
        enemies_list = []
        for _ in range(6):
            enemy = generate_enemy("low", cycle)
            enemy.scale_stats(level_multiplier)
            enemies_list.append(enemy)
        for _ in range(4):
            enemy = generate_enemy("mid", cycle)
            enemy.scale_stats(level_multiplier)
            enemies_list.append(enemy)
        for _ in range(3):
            enemy = generate_enemy("high", cycle)
            enemy.scale_stats(level_multiplier)
            enemies_list.append(enemy)
        return enemies_list

    def clear_map(self):
        """Clears the current map."""
        self.map_data = [[default for _ in range(self.width)] for _ in range(self.height)]
        self.create_frame()
        self.fill_default()
        self.generate_patches()
        self.place_structures()
        self.enemies = []
        self.entities = []
        self.boss_spawned = False

    def is_tile_empty(self, x, y):
        """Check if a tile is empty and suitable for enemy placement."""
        tile = self.map_data[x][y]
        # A tile is empty if it's walkable and not occupied by 'E' or 'P'
        return tile.walkable and tile.symbol_raw not in ['E', 'P']

    def place_enemies_on_map(self, enemies_list):
        """Places enemies on the map in valid locations."""
        import random
        
        # Track already occupied positions
        occupied_positions = set()
        
        # Add player position to occupied positions
        if hasattr(self, 'player_pos'):
            occupied_positions.add(self.player_pos)
        
        for enemy in enemies_list:
            placed = False
            max_attempts = 100  # Prevent infinite loops if map is very constrained
            attempts = 0
            
            while not placed and attempts < max_attempts:
                # Generate random coordinates
                x = random.randint(1, self.height - 2)  # Avoid map edges
                y = random.randint(1, self.width - 2)
                
                # Check if the position is valid (not a wall and not occupied)
                if (x, y) not in occupied_positions and self.is_valid_enemy_position(x, y):
                    # Get the tile at this position
                    tile = self.map_data[x][y]
                    
                    # Only place on walkable tiles that aren't special (like shrine)
                    if tile.walkable and tile.symbol_raw not in ['S', 'E', 'P', 'B']:
                        # Position is valid, place the enemy
                        enemy.set_position(x, y, tile)
                        self.map_data[x][y] = enemy
                        self.enemies.append(enemy)
                        occupied_positions.add((x, y))
                        placed = True
                
                attempts += 1
        
        # If we couldn't place all enemies, log a warning
        if any(enemy not in self.enemies for enemy in enemies_list):
            print("WARNING: Could not place all enemies on the map. The map might be too constrained.")

    def is_valid_enemy_position(self, x, y):
        """Checks if a position is valid for enemy placement."""
        # Check if coordinates are within map bounds
        if x < 0 or x >= self.height or y < 0 or y >= self.width:
            return False
        
        # Check if the tile at this position is walkable (not a wall)
        tile = self.map_data[x][y]
        return getattr(tile, 'walkable', False)

    def generate_terrain(self):
        """Generates the base terrain using noise functions for elevation and moisture."""
        self.create_frame()  # First create the frame
        
        # Generate elevation using noise
        elevation_seed = self.seed % 1000
        moisture_seed = (self.seed // 1000) % 1000
        
        scale = 0.1  # Adjust for different terrain scales
        
        # Generate elevation and moisture maps
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                # Generate elevation noise
                nx = x / self.height - 0.5
                ny = y / self.width - 0.5
                elevation = pnoise2(nx * scale, ny * scale, octaves=6, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024, base=elevation_seed)
                # Normalize to 0-1 range
                elevation = (elevation + 1) / 2
                self.elevation_map[x][y] = elevation
                
                # Generate moisture noise with a different seed
                moisture = pnoise2(nx * scale, ny * scale, octaves=4, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024, base=moisture_seed)
                # Normalize to 0-1 range
                moisture = (moisture + 1) / 2
                self.moisture_map[x][y] = moisture
                
                # Determine biome based on elevation and moisture
                self.map_data[x][y] = self.get_biome_from_elevation_moisture(elevation, moisture)
                
    def get_biome_from_elevation_moisture(self, elevation, moisture):
        """Returns a biome tile based on elevation and moisture values."""
        # Very high elevation = mountains
        if elevation > 0.8:
            return mountain
        # High elevation
        elif elevation > 0.6:
            if moisture < 0.5:  # Increased threshold from 0.3 to 0.5
                return hill  # Dry high elevation = hills
            else:
                # Add randomization to further reduce forest frequency
                if random.random() < 0.4:  # Only 40% chance for forest even in high moisture areas
                    return forest  # Wet high elevation = forest
                else:
                    return hill    # Otherwise still hills
        # Medium-high elevation
        elif elevation > 0.5:
            if moisture < 0.4:
                return desert  # Dry medium elevation = desert
            elif moisture < 0.8:  # Increased threshold from 0.7 to 0.8
                return plains  # Medium moisture = plains
            else:
                # Add randomization to further reduce forest frequency
                if random.random() < 0.5:  # Only 50% chance for forest in very wet areas
                    return forest  # Very wet medium elevation = forest
                else:
                    return brush   # Otherwise brush
        # Medium-low elevation
        elif elevation > 0.3:
            if moisture < 0.4:
                return plains  # Dry medium-low = plains
            elif moisture < 0.7:
                return brush  # Medium moisture = brush
            else:
                return swamp  # Wet medium-low = swamp
        # Low elevation 
        elif elevation > 0.2:
            if moisture < 0.5:
                return beach  # Potential beach areas
            else:
                return swamp  # Wet low elevation = swamp
        # Very low elevation = water
        else:
            return lake

    def generate_rivers_improved(self, num_rivers=5):
        """Generates more realistic rivers flowing from mountains to low elevations."""
        mountain_positions = []
        
        # Find all mountain positions as potential river sources
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                if self.map_data[x][y] == mountain:
                    mountain_positions.append((x, y))
        
        # If no mountains found, fall back to random positions
        if not mountain_positions:
            mountain_positions = [(randint(1, self.height - 2), randint(1, self.width - 2)) for _ in range(3)]
        
        # Generate rivers from random mountain positions
        for _ in range(min(num_rivers, len(mountain_positions))):
            if not mountain_positions:
                break
                
            # Select a random mountain as the river source
            start_x, start_y = random.choice(mountain_positions)
            mountain_positions.remove((start_x, start_y))
            
            # Create river path
            self.create_river_path(start_x, start_y)

    def create_river_path(self, start_x, start_y):
        """Creates a single river path from the starting point, following elevation gradient."""
        x, y = start_x, start_y
        river_length = randint(10, 25)  # Increased potential length
        path = [(x, y)]
        
        # Place the river source
        self.map_data[x][y] = river
        
        for _ in range(river_length):
            # Get elevation of neighboring cells
            neighbors = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.height - 1 and 1 <= ny < self.width - 1:
                    # Prefer flowing to lower elevations and avoid crossing own path
                    if (nx, ny) not in path:
                        # Get elevation or use high value if out of bounds
                        elevation = self.elevation_map[nx][ny] if 0 <= nx < self.height and 0 <= ny < self.width else 1.0
                        neighbors.append((nx, ny, elevation))
            
            if not neighbors:
                break
                
            # Sort by elevation (prefer lower elevation)
            neighbors.sort(key=lambda n: n[2])
            
            # Add some randomness - sometimes pick the 2nd or 3rd best option
            if len(neighbors) > 1 and random.random() < 0.3:  # 30% chance to not pick lowest
                next_x, next_y, _ = neighbors[min(1, len(neighbors) - 1)]
            else:
                next_x, next_y, _ = neighbors[0]
            
            # Check if river reached a lake or the edge of the map
            if self.map_data[next_x][next_y] == lake or next_x <= 0 or next_x >= self.height - 1 or next_y <= 0 or next_y >= self.width - 1:
                break
                
            # Add the river segment
            self.map_data[next_x][next_y] = river
            path.append((next_x, next_y))
            x, y = next_x, next_y
            
            # Occasionally create a river delta or fork
            if random.random() < 0.1:  # 10% chance
                for dx, dy in random.sample([(0, 1), (1, 0), (0, -1), (-1, 0)], 2):
                    fork_x, fork_y = x + dx, y + dy
                    if 1 <= fork_x < self.height - 1 and 1 <= fork_y < self.width - 1:
                        if (fork_x, fork_y) not in path and self.map_data[fork_x][fork_y] != river:
                            self.map_data[fork_x][fork_y] = river

    def add_beaches(self):
        """Adds beach tiles where land meets water."""
        # Look for land tiles adjacent to water
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                if self.map_data[x][y] not in [lake, river, water, beach]:
                    # Check if this tile is adjacent to water
                    adjacent_to_water = False
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.height and 0 <= ny < self.width:
                            if self.map_data[nx][ny] in [lake, water, river]:
                                adjacent_to_water = True
                                break
                    
                    # If adjacent to water, convert to beach with some probability
                    if adjacent_to_water and random.random() < 0.7:  # 70% chance
                        self.map_data[x][y] = beach

    def add_details(self):
        """Adds detailed features to the map based on biome types."""
        # Add small ponds, flowers, rocks, etc.
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                current_tile = self.map_data[x][y]
                
                # Only add details to walkable tiles that aren't already special
                if current_tile.walkable and current_tile not in [cave, ruins, river, beach]:
                    # Different details for different biomes
                    if current_tile == plains and random.random() < 0.05:
                        # Add small flowers to plains
                        self.map_data[x][y] = flower_tile
                    elif current_tile == forest:
                        # For forest tiles, occasionally convert to dense_forest or add details
                        if random.random() < 0.2:  # 20% chance to convert to dense forest
                            self.map_data[x][y] = dense_forest
                        elif random.random() < 0.08:
                            # Add fallen logs or mushrooms to forests
                            self.map_data[x][y] = mushroom_tile if random.random() < 0.5 else log_tile
                    elif current_tile == desert and random.random() < 0.03:
                        # Add cactus to deserts
                        self.map_data[x][y] = cactus_tile
                    elif current_tile == swamp and random.random() < 0.07:
                        # Add mud pools to swamps
                        self.map_data[x][y] = mud_tile
                    elif current_tile == mountain and random.random() < 0.1:
                        # Add caves to mountains (additional caves beyond the existing placement)
                        if random.random() < 0.3:  # 30% of the time
                            self.map_data[x][y] = cave
                        else:
                            # Add rock formations the rest of the time
                            self.map_data[x][y] = rock_tile

    def create_paths_from_village(self, village_x, village_y):
        """Creates paths radiating outward from villages."""
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        
        # Create 2-3 paths from the village
        for i in range(random.randint(2, 3)):
            if i < len(directions):
                dx, dy = directions[i]
                path_length = randint(3, 7)
                x, y = village_x + dx, village_y + dy
                
                # Create the path
                for _ in range(path_length):
                    if 1 <= x < self.height - 1 and 1 <= y < self.width - 1:
                        # Only place paths on walkable terrain
                        if self.map_data[x][y].walkable and self.map_data[x][y] not in [river, lake, water]:
                            self.map_data[x][y] = path_tile
                        
                        # Randomly adjust direction slightly for winding paths
                        if random.random() < 0.3:
                            if random.random() < 0.5:
                                dx, dy = dy, dx  # 90 degree turn
                            else:
                                dx, dy = -dy, -dx  # 90 degree turn opposite direction
                        
                        x, y = x + dx, y + dy

    def generate_balanced_terrain(self):
        """Generates the map using a balanced distribution of biomes."""
        # First fill the entire map with plains (base biome)
        self.fill_with_base_biome()
        
        # Define biomes with their weights and patch parameters
        # Format: (tile, num_patches, min_patch_size, max_patch_size, weight)
        # Weight is used to determine relative frequency - higher weight = more common
        biomes = [
            (forest, 12, 4, 10, 8),   # Forests: medium frequency, medium patches
            (mountain, 8, 3, 8, 6),    # Mountains: lower frequency, medium patches
            (lake, 5, 4, 8, 5),       # Lakes: low frequency, medium patches
            (desert, 6, 6, 12, 7),     # Deserts: medium frequency, larger patches
            (swamp, 4, 3, 7, 4),      # Swamps: lower frequency, medium patches
            (brush, 10, 3, 8, 7),     # Brush: medium-high frequency, medium patches
            (hill, 9, 3, 7, 7),       # Hills: medium frequency, smaller patches
            (snow, 3, 5, 10, 3),      # Snow: very low frequency, larger patches
        ]
        
        # Generate patches for each biome
        for biome, num_patches, min_size, max_size, _ in biomes:
            self.generate_biome_patches(biome, num_patches, min_size, max_size)
            
        # Now that we have our base terrain, generate elevation and moisture maps for future use
        # by other functions that depend on these
        self.generate_elevation_moisture_maps()
    
    def fill_with_base_biome(self):
        """Fills the internal part of the map with the base biome (plains)."""
        for x in range(1, self.height - 1):
            for y in range(1, self.width - 1):
                self.map_data[x][y] = plains
    
    def generate_biome_patches(self, tile, num_patches, min_size, max_size):
        """Generates patches of a specific biome using a more natural pattern."""
        for _ in range(num_patches):
            # Choose a random starting point for the patch
            start_x = random.randint(1, self.height - 2)
            start_y = random.randint(1, self.width - 2)
            
            # Determine patch size
            patch_size = random.randint(min_size, max_size)
            
            # Create the patch using a cellular-like growth pattern
            cells = [(start_x, start_y)]
            placed_cells = set(cells)
            
            for _ in range(patch_size):
                if not cells:
                    break
                    
                # Take the first cell from the list
                x, y = cells.pop(0)
                
                # Place the biome tile
                self.map_data[x][y] = tile
                
                # Try to expand in four directions
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    new_x, new_y = x + dx, y + dy
                    
                    # Check boundaries
                    if 1 <= new_x < self.height - 1 and 1 <= new_y < self.width - 1:
                        # Add some randomness to make natural-looking borders
                        if random.random() < 0.7:  # 70% chance to expand
                            new_pos = (new_x, new_y)
                            if new_pos not in placed_cells:
                                cells.append(new_pos)
                                placed_cells.add(new_pos)
    
    def generate_elevation_moisture_maps(self):
        """Generates elevation and moisture maps based on the placed biomes."""
        # Assign elevation and moisture values based on biome types
        biome_values = {
            plains.symbol_raw: (0.5, 0.5),    # plains: medium elevation, medium moisture
            forest.symbol_raw: (0.6, 0.8),    # forest: higher elevation, high moisture
            mountain.symbol_raw: (0.9, 0.4),  # mountain: very high elevation, medium-low moisture
            lake.symbol_raw: (0.1, 1.0),      # lake: very low elevation, very high moisture
            desert.symbol_raw: (0.5, 0.2),    # desert: medium elevation, low moisture
            swamp.symbol_raw: (0.2, 0.9),     # swamp: low elevation, high moisture
            brush.symbol_raw: (0.4, 0.6),     # brush: medium-low elevation, medium moisture
            hill.symbol_raw: (0.7, 0.5),      # hill: high elevation, medium moisture
            snow.symbol_raw: (0.8, 0.3),      # snow: high elevation, low-medium moisture
            river.symbol_raw: (0.3, 1.0)      # river: low elevation, maximum moisture
        }
        
        # Fill the elevation and moisture maps
        for x in range(self.height):
            for y in range(self.width):
                tile_symbol = self.map_data[x][y].symbol_raw
                # Get default values if biome not in the dictionary
                elevation, moisture = biome_values.get(tile_symbol, (0.5, 0.5))
                
                # Add some noise for natural variation
                elevation += (random.random() - 0.5) * 0.1
                moisture += (random.random() - 0.5) * 0.1
                
                # Clamp values to 0-1 range
                elevation = max(0.0, min(1.0, elevation))
                moisture = max(0.0, min(1.0, moisture))
                
                self.elevation_map[x][y] = elevation
                self.moisture_map[x][y] = moisture
