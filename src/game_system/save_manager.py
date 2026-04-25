"""Save/load helpers aligned with current game data models."""

import json
import os
from typing import Dict, List, Optional

from battle_system.enemy import Boss, boss_list, generate_boss, generate_enemy
from battle_system.item import create_item_from_name
from battle_system.skill import BOSS_SKILLS, PLAYER_SKILLS
from battle_system.weapon import Weapon
from map_system.map import Map

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
DEFAULT_SAVE_PATH = os.path.join(SAVE_DIR, "save_game.json")


def _ensure_save_dir() -> None:
    os.makedirs(SAVE_DIR, exist_ok=True)


def _skill_lookup() -> Dict[str, object]:
    lookup = {}
    lookup.update(PLAYER_SKILLS)
    lookup.update(BOSS_SKILLS)
    return lookup


def _safe_pos_from_enemy(enemy) -> Dict[str, int]:
    if hasattr(enemy, "pos") and isinstance(enemy.pos, tuple) and len(enemy.pos) == 2:
        x, y = enemy.pos
        return {"x": int(x), "y": int(y)}
    if hasattr(enemy, "x") and hasattr(enemy, "y"):
        return {"x": int(enemy.x), "y": int(enemy.y)}
    return {"x": 0, "y": 0}


def create_save_state(game) -> Dict:
    """Create a save payload from the current game state."""
    hero = game.hero
    game_map = getattr(game, "map", None)

    save_state = {
        "seed": getattr(game, "seed", None),
        "cycle": getattr(game, "cycle", 0),
        "boss_defeated": getattr(game, "boss_defeated", 0),
        "defeated_bosses": sorted(Boss.defeated_bosses),
        "player": {
            "position": {
                "x": int(getattr(hero, "player_pos", (1, 1))[0]),
                "y": int(getattr(hero, "player_pos", (1, 1))[1]),
            },
            "stats": {
                "name": hero.name,
                "health": hero.health,
                "health_max": hero.health_max,
                "mp": getattr(hero, "mp", 0),
                "mp_max": getattr(hero, "mp_max", 0),
                "cashpile": getattr(hero, "cashpile", 0),
                "level": getattr(hero, "level", 1),
                "experience": getattr(hero, "experience", 0),
                "experience_to_next_level": getattr(hero, "experience_to_next_level", 100),
                "enemies_killed": getattr(hero, "enemies_killed", 0),
            },
            "weapon": {
                "name": hero.weapon.name,
                "weapon_type": hero.weapon.weapon_type,
                "damage": hero.weapon.damage,
                "value": hero.weapon.value,
                "tier": hero.weapon.tier,
            },
            "skills": [
                {"name": skill.name, "cooldown": skill.cooldown, "mp_cost": skill.mp_cost}
                for skill in getattr(hero, "skills", [])
            ],
            "stolen_skills": [
                {"name": skill.name, "cooldown": skill.cooldown, "mp_cost": skill.mp_cost}
                for skill in getattr(hero, "stolen_skills", [])
            ],
        },
        "inventory": [
            {
                "name": item.name,
                "type": item.__class__.__name__,
                "description": getattr(item, "description", ""),
            }
            for item in getattr(hero, "items", [])
        ],
        "enemies": [],
        "map": {},
    }

    if game_map is not None:
        save_state["enemies"] = [
            {
                "name": enemy.name,
                "type": enemy.__class__.__name__,
                "tier": getattr(enemy, "tier", "mid"),
                "position": _safe_pos_from_enemy(enemy),
                "health": enemy.health,
                "health_max": enemy.health_max,
            }
            for enemy in getattr(game_map, "enemies", [])
        ]

        save_state["map"] = {
            "width": game_map.width,
            "height": game_map.height,
            "seed": getattr(game_map, "seed", getattr(game, "seed", None)),
            "visited_tiles": [
                [getattr(tile, "visited", False) for tile in row]
                for row in game_map.map_data
            ],
            "looted_tiles": [
                [getattr(tile, "looted", False) for tile in row]
                for row in game_map.map_data
            ],
        }

    return save_state


def save_game_state(game, save_path: Optional[str] = None) -> None:
    """Persist the current game state to disk."""
    _ensure_save_dir()
    target_path = save_path or DEFAULT_SAVE_PATH
    with open(target_path, "w", encoding="utf-8") as save_file:
        json.dump(create_save_state(game), save_file)


def load_raw_save_state(save_path: Optional[str] = None) -> Optional[Dict]:
    """Load raw save JSON from disk."""
    target_path = save_path or DEFAULT_SAVE_PATH
    if not os.path.exists(target_path):
        return None
    with open(target_path, "r", encoding="utf-8") as save_file:
        return json.load(save_file)


def _resolve_boss_index(saved_enemy: Dict) -> int:
    if isinstance(saved_enemy.get("boss_index"), int):
        return saved_enemy["boss_index"]

    boss_name = saved_enemy.get("name")
    for idx, boss_data in enumerate(boss_list):
        if boss_data.get("name") == boss_name:
            return idx

    return 0


def _restore_enemy(saved_enemy: Dict, cycle: int):
    enemy_type = str(saved_enemy.get("type", "")).lower()
    enemy_tier = str(saved_enemy.get("tier", "mid")).lower()

    if "boss" in enemy_type or enemy_tier in {"boss", "final_boss"}:
        enemy = generate_boss(_resolve_boss_index(saved_enemy))
    else:
        tier = enemy_tier if enemy_tier in {"low", "mid", "high"} else "mid"
        enemy = generate_enemy(tier, cycle=max(cycle, 0))

    enemy.name = saved_enemy.get("name", enemy.name)
    enemy.health = int(saved_enemy.get("health", enemy.health))
    enemy.health_max = int(saved_enemy.get("health_max", enemy.health_max))
    enemy.health_bar.update()
    return enemy


def _restore_skills(saved_names: List[str]) -> List[object]:
    lookup = _skill_lookup()
    restored = []
    for skill_name in saved_names:
        if skill_name in lookup:
            restored.append(lookup[skill_name])
    return restored


def load_saved_game(game, save_path: Optional[str] = None) -> bool:
    """Load a saved game state into an existing Game instance."""
    try:
        save_data = load_raw_save_state(save_path)
        if save_data is None:
            print("No save file found.")
            return False

        # Core game state
        if save_data.get("seed") is not None:
            game.seed = save_data["seed"]
        game.cycle = int(save_data.get("cycle", getattr(game, "cycle", 0)))
        game.boss_defeated = int(save_data.get("boss_defeated", getattr(game, "boss_defeated", 0)))

        # Hero state
        player_data = save_data.get("player", {})
        stats = player_data.get("stats", {})

        hero = game.hero
        hero.name = stats.get("name", hero.name)
        hero.health = int(stats.get("health", hero.health))
        hero.health_max = int(stats.get("health_max", hero.health_max))
        hero.mp = int(stats.get("mp", getattr(hero, "mp", 0)))
        hero.mp_max = int(stats.get("mp_max", getattr(hero, "mp_max", 0)))
        hero.cashpile = int(stats.get("cashpile", getattr(hero, "cashpile", 0)))
        hero.level = int(stats.get("level", getattr(hero, "level", 1)))
        hero.experience = int(stats.get("experience", getattr(hero, "experience", 0)))
        hero.experience_to_next_level = int(
            stats.get("experience_to_next_level", getattr(hero, "experience_to_next_level", 100))
        )
        hero.enemies_killed = int(stats.get("enemies_killed", getattr(hero, "enemies_killed", 0)))

        weapon_data = player_data.get("weapon", {})
        if weapon_data:
            hero.weapon = Weapon(
                name=weapon_data.get("name", hero.weapon.name),
                weapon_type=weapon_data.get("weapon_type", getattr(hero.weapon, "weapon_type", "blunt")),
                damage=int(weapon_data.get("damage", hero.weapon.damage)),
                value=int(weapon_data.get("value", hero.weapon.value)),
                tier=weapon_data.get("tier", hero.weapon.tier),
            )

        # Skills: support both old list shape and new separate regular/stolen shape.
        saved_regular_skills = [
            item.get("name")
            for item in player_data.get("skills", [])
            if isinstance(item, dict) and item.get("name")
        ]
        saved_stolen_skills = [
            item.get("name")
            for item in player_data.get("stolen_skills", [])
            if isinstance(item, dict) and item.get("name")
        ]

        hero.skills = _restore_skills(saved_regular_skills)
        hero.stolen_skills = _restore_skills(saved_stolen_skills)

        # Inventory
        hero.items = []
        for item_data in save_data.get("inventory", []):
            item_name = item_data.get("name") if isinstance(item_data, dict) else None
            if not item_name:
                continue
            item = create_item_from_name(item_name)
            if item is not None:
                hero.items.append(item)

        # Map state
        map_data = save_data.get("map", {})
        map_w = int(map_data.get("width", 35))
        map_h = int(map_data.get("height", 25))
        map_seed = map_data.get("seed", save_data.get("seed"))

        if map_seed is None:
            game_map = Map(map_w, map_h)
        else:
            game_map = Map.generate_map_with_seed(map_w, map_h, int(map_seed))

        player_pos = player_data.get("position", {})
        px = int(player_pos.get("x", 1))
        py = int(player_pos.get("y", 1))
        if 0 < px < game_map.height - 1 and 0 < py < game_map.width - 1:
            hero.player_pos = (px, py)
            game_map.player_pos = (px, py)

        game_map.place_player(hero)

        # Restore tile metadata if present.
        visited_tiles = map_data.get("visited_tiles", [])
        looted_tiles = map_data.get("looted_tiles", [])
        for x in range(min(game_map.height, len(visited_tiles))):
            row = visited_tiles[x]
            for y in range(min(game_map.width, len(row))):
                tile = game_map.map_data[x][y]
                if hasattr(tile, "visited"):
                    tile.visited = bool(row[y])

        for x in range(min(game_map.height, len(looted_tiles))):
            row = looted_tiles[x]
            for y in range(min(game_map.width, len(row))):
                tile = game_map.map_data[x][y]
                if hasattr(tile, "looted"):
                    tile.looted = bool(row[y])

        # Enemies
        game_map.enemies = []
        for saved_enemy in save_data.get("enemies", []):
            if not isinstance(saved_enemy, dict):
                continue

            enemy = _restore_enemy(saved_enemy, cycle=game.cycle)
            pos = saved_enemy.get("position", {})
            ex = int(pos.get("x", 0))
            ey = int(pos.get("y", 0))

            if not (0 < ex < game_map.height - 1 and 0 < ey < game_map.width - 1):
                continue

            underlying_tile = game_map.map_data[ex][ey]
            if hasattr(enemy, "set_position"):
                enemy.set_position(ex, ey, underlying_tile)
            else:
                enemy.pos = (ex, ey)
                enemy.underlying_tile = underlying_tile

            game_map.map_data[ex][ey] = enemy
            game_map.enemies.append(enemy)

        # Boss progression flags
        Boss.defeated_bosses.clear()
        for boss_name in save_data.get("defeated_bosses", []):
            if isinstance(boss_name, str):
                Boss.mark_defeated(boss_name)

        game.map = game_map
        hero.health_bar.update()
        return True
    except Exception as exc:
        print(f"Error loading game: {exc}")
        return False
