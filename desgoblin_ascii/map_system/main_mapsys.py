import sys
import os

# Add the project root directory to the path to resolve module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from map_system.map import Map
from map_system.tiles import Tile, plains, forest, brush, mountain, water

os.system("")


def run() -> None:
    while True:
        game_map.display_map()
        input("> ")

if __name__ == "__main__":
    map_w, map_h = 30, 15
    game_map = Map(map_w, map_h)
    run()
