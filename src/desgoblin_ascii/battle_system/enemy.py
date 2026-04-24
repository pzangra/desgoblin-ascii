# battle_system/enemy.py

import random
from random import choice, randint
from battle_system.character import Enemy, Character
from battle_system.weapon import Weapon, generate_weapon
from battle_system.item import create_item_from_name
from battle_system.skill import BOSS_SKILLS, get_boss_skills_by_name
from battle_system.health_bar import HealthBar

enemy_names = {
    "low": [
        "Slime", "Rat", "Goblin", "Spider", "Bat", "Snake", "Kobold", "Imp", "Bandit",
        "Skeleton", "Zombie", "Giant Rat", "Cave Beetle", "Mud Crab", "Shadow Cat", "Wild Dog",
        "Giant Centipede", "Boggart", "Mimicling", "Pixie", "Grelling", "Dust Mephit", "Giant Spider",
        "Stirge", "Ghoul", "Darkling", "Wisp", "Crowfolk", "Carrion Beetle", "Vermling", "Giant Ant",
        "Kappa", "Mud Elemental", "Scavenger", "Fire Beetle", "Crimson Bat", "Hagling", "Feral Boar",
        "Dire Rabbit", "Raven", "Young Harpy", "Wood Sprite", "Giant Snail", "Frost Beetle", "Shade",
        "Cursed Doll", "Gloomling", "Thornling", "Drudge", "Forest Imp", "Scarecrow", "Gutter Rat",
        "Young Basilisk", "Giant Leech", "Dark Fairy", "Ash Crawler", "Thieving Monkey", "Dire Mole",
        "Muck Dweller", "Fungal Sprite", "Will-o'-Rat", "Briar Beast", "Rusted Automaton", "Rotten Hound",
        "Pond Scum", "Grave Mite", "Lesser Djinn", "Hedge Gremlin", "Nettle Stalker", "Wicker Man",
        "Black Cat", "Lesser Kobold", "Gloom Bat", "Mist Lurker", "Bog Imp", "Weasel", "Hedgehog",
        "Ragged Ghoul", "Young Hobgoblin", "Firefly Swarm", "Ashen Wisp", "Plague Rat", "Grotto Crab",
        "Dire Toad", "Crag Lizard", "Bramble Elemental", "Shadow Hare", "Sewer Slime", "Wild Goat",
        "Rubble Sprite", "Rock Grub", "Night Roach", "Giant Worm", "Lost Soul", "Gutter Snipe",
        "Broken Puppet"
    ],
    "mid": [
        "Big Goblin", "Hobgoblin", "Orc", "Gnoll", "Wight", "Troll", "Ogre", "Minotaur", "Centaur",
        "Werewolf", "Harpy", "Griffon", "Cyclops", "Gargoyle", "Rakshasa", "Sea Hag", "Doppelganger",
        "Dark Knight", "Redcap", "Chimera", "Banshee", "Dire Wolf", "Will-o'-Wisp", "Revenant", "Barghest",
        "Manticore", "Gorgon", "Siren", "Dryad", "Basilisk", "Cursed Armor", "Grendel", "Bone Naga",
        "Keres", "Anubian Guardian", "Fomorian", "Kelpie", "Wendigo", "Blood Hunter", "Nymph", "Spriggan",
        "Werebear", "Wyrmling", "Shadow Mastiff", "Peryton", "Phantom Knight", "Headless Horseman",
        "Sand Wraith", "Storm Elemental", "Spectral Archer", "Voidwalker", "Night Hag", "Ghoul Lord",
        "Moroi", "Ghul", "Stone Golem", "Hellhound", "Ashen Revenant", "Pit Fiendling", "Fire Djinn",
        "Crocotta", "Ceryneian Hind", "Myrmidon", "Bog Witch", "Fiery Salamander", "Onyx Gargoyle",
        "Frost Troll", "Infernal Imp", "Cave Troll", "Sewer King", "Giant Scorpion", "Silverback Ape",
        "Myrkalfar", "Black Annis", "Ash Wraith", "Desert Ghoul", "Clockwork Soldier", "Vodyanoi",
        "Rusalka", "Draugr", "Half-Orc Brute", "Hill Giant", "Fenrir Pup", "Marble Statue", "Bugbear",
        "Horned Devil", "Spectral Swordsman", "Harlequin Shade", "Cacodaemon", "Gloom Weaver",
        "Blood Shade", "Black Knight"
    ],
    "high": [
        "Wyvern", "Drake", "Titan", "Lich", "Vampire", "Dragon", "Behemoth", "Balor", "Kraken",
        "Nightmare", "Elder Brain", "Shoggoth", "Star Spawn", "Demon Lord", "Pit Fiend", "Moloch",
        "Hydra", "Hellhound Alpha", "Aboleth", "Elder Deep One", "Phoenix", "Archdemon", "Leviathan",
        "Seraphim", "Bone Dragon", "Storm Giant", "Sphinx", "Charybdis", "Scylla", "Thanatos",
        "Hecatoncheires", "Tarrasque", "Frost Wyrm", "Chernobog", "Anubis", "Fenrir", "Jormungandr",
        "Nemean Lion", "Yamata-no-Orochi", "Ifrit", "Djinn Lord", "Nephilim", "Archon", "Astaroth",
        "Beelzebub", "Belial", "Asmodeus", "Lilith", "Ziz", "Mammon", "Azazel", "Bael", "Qliphoth Beast",
        "The Black Goat", "Great Unclean One", "Prince of Darkness", "Yaldabaoth", "Abyssal Wyrm",
        "Ereshkigal", "Vritra", "Kali", "Garuda", "Ravana", "The Morrigan", "Baphomet", "Chimera Prime",
        "Typhon", "Echidna", "Pontianak", "Black Tortoise", "Gugalanna", "Zuul", "Kukulkan", "The Erlking",
        "Archlich", "Death Knight", "Lord of Change", "Archfiend", "Ashura", "Demogorgon", "Nyarlathotep",
        "Ithaqua", "Yog-Sothoth", "Cthulhu", "Apep", "Set", "Geryon", "Aegir", "Kronos", "Hyperion",
        "Atlas", "The Sorrow", "Father of Serpents", "Celestial Dragon", "The Devourer", "The False Prophet"
    ]
}

class EnemyDisplay:
    """Class for enemy display features."""

    @staticmethod
    def format_enemy_name(enemy):
        """String representation of the enemy."""
        return f"{enemy.name}"  # Removed weapon name display

def generate_enemy(tier: str, cycle: int = 0) -> Enemy:
    """Generates an enemy based on the specified tier."""
    names = enemy_names.get(tier)
    if not names:
        raise ValueError("Invalid tier for enemy generation")
    name = choice(names)
    health_ranges = {
        "low": (10, 30),
        "mid": (40, 80),
        "high": (80, 120)
    }
    
    evade_ch_ranges = {
        "low": (0, 5),
        "mid": (5, 10),
        "high": (10, 15)
    }
    
    crit_ch_ranges = {
        "low": (5, 8),
        "mid": (8, 12),
        "high": (12, 20)
    }
    
    armor_ranges = {
        "low": (0, 2),
        "mid": (2, 6),
        "high": (6, 12)
    }

    # Assign initial values
    health = randint(*health_ranges[tier])
    evade_ch = randint(*evade_ch_ranges[tier])
    crit_ch = randint(*crit_ch_ranges[tier])
    armor = randint(*armor_ranges[tier])
    # Scale stats based on cycle
    health = int(health * (1 + 0.2 * cycle))
    evade_ch = int(evade_ch * (1 + 0.1 * cycle))
    crit_ch = int(crit_ch * (1 + 0.1 * cycle))
    armor = int(armor * (1 + 0.1 * cycle))
    weapon = generate_weapon(tier, cycle)
    # Create the enemy instance
    enemy = Enemy(name=name, health=health, weapon=weapon, 
                  evade_ch=evade_ch, crit_ch=crit_ch, 
                  armor=armor, tier=tier)
    # Add required map display attributes
    enemy.symbol = "\033[31mE\033[0m"  # Red E for enemy
    enemy.symbol_raw = 'E'  # Enemies block movement
    enemy.walkable = False  # Enemies block movement
    return enemy

class Enemy(Character):
    """Base class for all enemies."""
    def __init__(self, name, health, weapon, evade_ch, crit_ch, armor, tier):
        super().__init__(name=name, health=health, evade_ch=evade_ch, crit_ch=crit_ch, armor=armor)
        self.weapon = weapon
        self.tier = tier
        self.base_armor = armor  # Store base armor for skill effects
        self.health_bar = HealthBar(self, color="red")
        # Add required map display attributes
        self.symbol = "\033[31mE\033[0m"  # Red E for enemy
        self.symbol_raw = 'E'
        self.walkable = False  # Enemies cannot be walked on
        # Initialize position tracking
        self.pos = None
        self.underlying_tile = None

    def __str__(self):
        """String representation of the enemy."""
        return f"{self.name}"  # Removed weapon display
    
    def set_position(self, x: int, y: int, underlying_tile):
        """Sets the enemy's position on the map."""
        self.pos = (x, y)
        self.underlying_tile = underlying_tile
        
    def scale_stats(self, multiplier):
        """Scales the enemy's stats by the given multiplier."""
        self.health = int(self.health * multiplier)
        self.health_max = self.health
        self.weapon.damage = int(self.weapon.damage * multiplier)
        self.armor = int(self.armor * multiplier)
        self.health_bar.update()

class Boss(Enemy):
    """Boss characters with special abilities."""
    # Class-level set to track bosses that have already had skills stolen
    defeated_bosses = set()
    
    def __init__(self, name, health, weapon, evade_ch, crit_ch, armor, tier, skills, drops):
        super().__init__(name=name, health=health, weapon=weapon, evade_ch=evade_ch, 
                         crit_ch=crit_ch, armor=armor, tier=tier)
        self.skills = skills
        self.drops = drops
        self.base_armor = armor  # Store base armor for skill effects

    def __str__(self):
        """String representation of the boss."""
        return f"{self.name}"  # Removed weapon display
        
    @classmethod
    def was_defeated(cls, boss_name):
        """Check if a boss with this name has already been defeated and had skills stolen."""
        return boss_name in cls.defeated_bosses
        
    @classmethod
    def mark_defeated(cls, boss_name):
        """Mark a boss as having had skills stolen."""
        cls.defeated_bosses.add(boss_name)

    def choose_skill(self, targets, battle_state=None):
        """Choose a skill to use based on current battle state."""
        available_skills = [s for s in self.skills if s.current_cooldown == 0]
        if not available_skills:
            return None
            
        # Special handling for Troll Champion Boxeur
        if self.name == "Troll Champion Boxeur":
            # Apply troll blood passive at the beginning of turn
            troll_blood_skill = next((s for s in self.skills if s.name == "Troll Blood"), None)
            if troll_blood_skill:
                troll_blood_skill.use(self, [self], battle_state)
            # If health is below 30%, prioritize Vengeful Roar
            if self.health < self.health_max * 0.3:
                vengeful_roar_skill = next((s for s in available_skills if s.name == "Vengeful Roar"), None)
                if vengeful_roar_skill:
                    return vengeful_roar_skill
            
            # Prioritize Brutal Slam if it's available (since it has the longest cooldown)
            brutal_slam_skill = next((s for s in available_skills if s.name == "Brutal Slam"), None)
            if brutal_slam_skill:
                return brutal_slam_skill
                
        # If health is low, prioritize healing skills
        if self.health < self.health_max * 0.4:
            heal_skills = [s for s in available_skills if s.skill_type == 'heal']
            if heal_skills:
                return choice(heal_skills)
        
        # Prioritize status effects if not already applied
        if battle_state and 'status_effects' in battle_state:
            status_skills = [s for s in available_skills if s.skill_type in ['control', 'debuff']]
            affected_targets = sum(1 for t in targets if t.name in battle_state['status_effects'])
            if status_skills and affected_targets < len(targets) // 2:
                return choice(status_skills)
        
        # Otherwise choose randomly
        return choice(available_skills)

    def take_turn(self, targets, battle_state=None):
        """Take a turn in battle, choosing and using a skill."""
        # First tick all skill cooldowns
        for skill in self.skills:
            skill.tick_cooldown()
            
        # Choose a skill to use
        chosen_skill = self.choose_skill(targets, battle_state)
        # If no skill is available, use regular attack
        if chosen_skill:
            # Use the skill
            print(f"{self.name} uses {chosen_skill.name}!")
            chosen_skill.use(self, targets, battle_state)
            return
        
        # Check for vengeful_roar effect (for Troll Champion)
        damage_bonus = 0
        if battle_state and 'boss_effects' in battle_state and 'vengeful_roar' in battle_state['boss_effects']:
            effect = battle_state['boss_effects']['vengeful_roar']
            if effect['active']:
                damage_bonus = effect['attack_boost']
                print(f"{self.name}'s attack is empowered by Vengeful Roar! (+{damage_bonus} damage)")
        
        # Apply damage bonus to weapon temporarily
        original_damage = self.weapon.damage
        if damage_bonus > 0:
            self.weapon.damage += damage_bonus
            
        print(f"{self.name} attacks with {self.weapon.name}!")
        self.attack(targets[0])
        
        # Restore original damage
        if damage_bonus > 0:
            self.weapon.damage = original_damage

    def attack(self, target, attack_type="normal", is_counter: bool = False) -> str:
        """Override to add special boss attack effects."""
        result = super().attack(target, attack_type, is_counter)
        
        # Special handling for Troll Champion Boxeur - chance to counter attack
        if self.name == "Troll Champion Boxeur" and not is_counter and random.randint(1, 100) <= 30:
            frenzied_counter_skill = next((s for s in self.skills if s.name == "Frenzied Counter"), None)
            if frenzied_counter_skill and frenzied_counter_skill.current_cooldown == 0:
                frenzied_counter_skill.use(self, [target], {})
                frenzied_counter_skill.current_cooldown = frenzied_counter_skill.cooldown
        
        return result

# Modify the boss_list to include skills
boss_list = [
    {
        'name': 'Dragon Lord',
        'health': 300,
        'weapon': Weapon(name='Flame Breath', weapon_type='natural', damage=25),
        'evade_ch': 5,
        'crit_ch': 20,
        'armor': 15,
        'tier': 'boss',
        'skills': [],  # Will be populated by generate_boss
        'drops': ['Legendary Sword', 'Dragon Scale']
    },
    {
        'name': 'Goblin Supreme',
        'health': 400,
        'weapon': Weapon(name='Eldritch Staff', weapon_type='staff', damage=30),
        'evade_ch': 10,
        'crit_ch': 15,
        'armor': 10,
        'tier': 'boss',
        'skills': [],  # Will be populated by generate_boss
        'drops': ['Eldritch Staff', 'Goblin Crown', 'Healing Potion']
    },
    {
        'name': 'Troll Champion Boxeur',
        'health': 1000,
        'weapon': Weapon(name='Spiked Gauntlets', weapon_type='blunt', damage=40),
        'evade_ch': 5,
        'crit_ch': 10,
        'armor': 15,
        'tier': 'boss',
        'skills': [],  # Will be populated by generate_boss
        'drops': ['Spiked Gauntlets', 'Troll Hide Armor', 'Strength Potion']
    },
    {
        'name': 'African Turtle',
        'health': 800,
        'weapon': Weapon(name='Shell Lance', weapon_type='spear', damage=35),
        'evade_ch': 3,
        'crit_ch': 8,
        'armor': 25,
        'tier': 'boss',
        'skills': [],  # Will be populated by generate_boss
        'drops': ['Shell Shield', 'Ocean Stone', 'Healing Potion']
    },
    {
        'name': 'Ultras Penguin',
        'health': 800,
        'weapon': Weapon(name='Glacier Beak', weapon_type='natural', damage=35),
        'evade_ch': 8,
        'crit_ch': 12,
        'armor': 18,
        'tier': 'boss',
        'skills': [],  # Will be populated by get_boss_skills_by_name
        'drops': ['Ice Shard Armor', 'Frozen Crystal', 'Penguin Feather Charm']
    },
    {
        'name': 'Bard Gargoyle',
        'health': 550,
        'weapon': Weapon(name='Ethereal Screech', weapon_type='natural', damage=32),
        'evade_ch': 7,
        'crit_ch': 15,
        'armor': 20,
        'tier': 'boss',
        'skills': [],  # Will be populated by get_boss_skills_by_name
        'drops': ['Stone Wing Fragment', 'Sonic Crystal', 'Musical Relic']
    },
    {
        'name': 'Sexy Fox',
        'health': 450,
        'weapon': Weapon(name='Enchanting Claws', weapon_type='natural', damage=30),
        'evade_ch': 12,
        'crit_ch': 10,
        'armor': 8,
        'tier': 'boss',
        'skills': [],  # Will be populated by get_boss_skills_by_name
        'drops': ['Fox Tail Charm', 'Alluring Perfume', 'Illusion Crystal']
    },
    {
        'name': 'Broken Salamander',
        'health': 650,
        'weapon': Weapon(name='Flame Claw', weapon_type='natural', damage=35),
        'evade_ch': 6,
        'crit_ch': 14,
        'armor': 22,
        'tier': 'boss',
        'skills': [],  # Will be populated by get_boss_skills_by_name
        'drops': ['Salamander Scale', 'Flame Essence', 'Phoenix Feather']
    },
    {
        'name': 'Gargololo',
        'health': 1200,
        'weapon': Weapon(name='Void Reaver', weapon_type='unique', damage=120),
        'evade_ch': 15,
        'crit_ch': 25,
        'armor': 35,
        'tier': 'final_boss',
        'skills': [],  # Will be populated by get_boss_skills_by_name
        'drops': ['Void Fragment', 'Cosmic Essence', 'Primordial Crystal']
    }
    # Define other bosses similarly...
]

def generate_boss(boss_index):
    """Generates a boss based on the index in the boss list."""
    boss_data = boss_list[boss_index].copy()  # Make a copy to avoid modifying the original
    
    # Assign skills based on boss name
    boss_data['skills'] = get_boss_skills_by_name(boss_data['name'])
    
    # Set the weapon value to 50 gold (will be scaled by cycle in the Game class)
    if hasattr(boss_data['weapon'], 'value'):
        boss_data['weapon'].value = 50
    
    # If no specific skills are found, assign some default skills
    if not boss_data['skills']:
        default_skills = [
            BOSS_SKILLS.get("arcane_pulse"),
            BOSS_SKILLS.get("shattering_screech")
        ]
        boss_data['skills'] = [s for s in default_skills if s]  # Filter out any None values
    
    boss = Boss(
        name=boss_data['name'],
        health=boss_data['health'],
        weapon=boss_data['weapon'],
        evade_ch=boss_data['evade_ch'],
        crit_ch=boss_data['crit_ch'],
        armor=boss_data['armor'],
        tier=boss_data['tier'],
        skills=boss_data['skills'],
        drops=boss_data['drops']
    )
    
    return boss