import sys
import os
import asyncio

# Safely add the 'src' directory to Python's path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from map_system.map import Map
from map_system.tiles import Tile, plains, forest, brush, mountain, water
from game_system.browser_input import async_input

os.system("")

async def run() -> None:
    while True:
        game_map.display_map()
        await async_input("> ")
        await asyncio.sleep(0)

if __name__ == "__main__":
    map_w, map_h = 30, 15
    game_map = Map(map_w, map_h)
    asyncio.run(run())
