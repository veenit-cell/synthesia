import numpy as np
import random
from typing import List, Dict

# Simple Perlin noise fallback (since noise library requires C++ compiler)
def _simple_noise(x: float, y: float, base: int = 0) -> float:
    """Simple deterministic noise function using sine waves"""
    import math
    return math.sin(x * 0.01 + base) * math.cos(y * 0.01 + base) + \
           math.sin(x * 0.02 + y * 0.015) * 0.5

class Environment:
    def __init__(self, width: float = 1000, height: float = 1000, max_nodes: int = 150):
        self.width = width
        self.height = height
        self.max_nodes = max_nodes
        self.nodes: List[Dict] = []
        self.pheromones: Dict[tuple[int, int], float] = {}  # Grid-based
        self.tick = 0

        # Season system (0=spring, 1=summer, 2=fall, 3=winter)
        self.season = 0
        self.season_duration = 1000  # ticks per season
        self.season_names = ['spring', 'summer', 'fall', 'winter']
        self.season_modifiers = {
            'spring': {'spawn_rate': 1.2, 'regen_rate': 1.5, 'value_mult': 1.0},
            'summer': {'spawn_rate': 1.5, 'regen_rate': 1.0, 'value_mult': 1.1},
            'fall': {'spawn_rate': 0.8, 'regen_rate': 1.2, 'value_mult': 1.2},
            'winter': {'spawn_rate': 0.4, 'regen_rate': 0.5, 'value_mult': 1.5}
        }

        # Catastrophe system
        self.catastrophe_active = False
        self.catastrophe_timer = 0
        self.affected_regions: List[Dict] = []

        # Initialize with some nodes
        self._seed_environment()

    def _seed_environment(self, count: int = 50):
        """Create initial information nodes using Perlin noise for clustering"""
        for i in range(count):
            # Use Perlin noise to create clusters
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)

            # Determine type based on position (creates regions)
            type_noise = _simple_noise(x/300, y/300)
            node_type = self._noise_to_type(type_noise)

            # Value varies
            value = random.uniform(30, 100)

            self.nodes.append({
                'id': f"node_{i}",
                'x': x,
                'y': y,
                'type': node_type,
                'value': value,
                'max_value': value,
                'depleted': False
            })

    def _noise_to_type(self, noise_val: float) -> str:
        """Map noise to knowledge domain"""
        if noise_val < -0.3:
            return 'science'
        elif noise_val < 0:
            return 'art'
        elif noise_val < 0.3:
            return 'history'
        else:
            return 'technology'

    def _spawn_special_node(self, node_type: str):
        """Spawn special node types (hazard, portal, mystery)"""
        x = random.uniform(100, self.width - 100)
        y = random.uniform(100, self.height - 100)

        if node_type == 'hazard':
            self.nodes.append({
                'id': f"hazard_{self.tick}_{random.randint(0, 1000)}",
                'x': x, 'y': y,
                'type': 'hazard',
                'value': random.uniform(20, 40),
                'max_value': 40,
                'depleted': False,
                'damage': random.uniform(5, 15)
            })
        elif node_type == 'portal':
            self.nodes.append({
                'id': f"portal_{self.tick}_{random.randint(0, 1000)}",
                'x': x, 'y': y,
                'type': 'portal',
                'value': 100,
                'max_value': 100,
                'depleted': False,
                'target_x': random.uniform(0, self.width),
                'target_y': random.uniform(0, self.height)
            })
        elif node_type == 'mystery':
            self.nodes.append({
                'id': f"mystery_{self.tick}_{random.randint(0, 1000)}",
                'x': x, 'y': y,
                'type': 'mystery',
                'value': random.uniform(50, 100),
                'max_value': 100,
                'depleted': False,
                'effect': random.choice(['boost', 'teleport', 'transform'])
            })

    def update(self):
        """Environmental dynamics"""
        self.tick += 1

        # Update season
        self.season = (self.tick // self.season_duration) % 4
        current_season = self.season_names[self.season]
        modifiers = self.season_modifiers[current_season]

        # Spawn new nodes occasionally (modified by season)
        base_spawn_chance = 0.1 * modifiers['spawn_rate']
        if len(self.nodes) < self.max_nodes and random.random() < base_spawn_chance:
            self._spawn_node(modifiers['value_mult'])

        # Occasional special nodes (5% chance)
        if random.random() < 0.05:
            special_type = random.choice(['hazard', 'portal', 'mystery'])
            self._spawn_special_node(special_type)

        # Regenerate depleted nodes slowly (modified by season)
        regen_rate = 0.05 * modifiers['regen_rate']
        for node in self.nodes:
            if node['depleted']:
                node['value'] = min(node['max_value'], node['value'] + regen_rate)
                if node['value'] > node['max_value'] * 0.3:
                    node['depleted'] = False

        # Handle catastrophes
        if self.catastrophe_active:
            self._update_catastrophe()

        # Decay pheromones
        to_remove = []
        for key, strength in self.pheromones.items():
            self.pheromones[key] = strength * 0.98
            if self.pheromones[key] < 0.01:
                to_remove.append(key)
        for key in to_remove:
            del self.pheromones[key]

    def _spawn_node(self, value_mult: float = 1.0):
        """Spawn a new information node, preferring cluster areas"""
        # 70% chance to spawn near existing nodes (clustering)
        if random.random() < 0.7 and self.nodes:
            parent = random.choice(self.nodes)
            x = np.clip(parent['x'] + random.gauss(0, 100), 0, self.width)
            y = np.clip(parent['y'] + random.gauss(0, 100), 0, self.height)
        else:
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)

        type_noise = _simple_noise(x/300, y/300, base=self.tick)
        node_type = self._noise_to_type(type_noise)

        base_value = random.uniform(40, 100) * value_mult
        self.nodes.append({
            'id': f"node_{self.tick}_{random.randint(0, 1000)}",
            'x': x,
            'y': y,
            'type': node_type,
            'value': base_value,
            'max_value': base_value,
            'depleted': False
        })

    def trigger_catastrophe(self, catastrophe_type: str = 'wildfire'):
        """Trigger an environmental catastrophe"""
        self.catastrophe_active = True
        self.catastrophe_timer = 200  # Lasts 200 ticks

        if catastrophe_type == 'wildfire':
            # Create spreading fire regions
            num_fires = random.randint(3, 6)
            for _ in range(num_fires):
                self.affected_regions.append({
                    'type': 'fire',
                    'x': random.uniform(100, self.width - 100),
                    'y': random.uniform(100, self.height - 100),
                    'radius': 50,
                    'spread_rate': 2.0,
                    'damage': 10
                })
        elif catastrophe_type == 'flood':
            # Create flooding zones
            self.affected_regions.append({
                'type': 'flood',
                'x': random.uniform(0, self.width),
                'y': random.uniform(0, self.height),
                'radius': 300,
                'spread_rate': 0.5,
                'damage': 5
            })
        elif catastrophe_type == 'drought':
            # Reduce all node values
            for node in self.nodes:
                node['value'] *= 0.5
            self.catastrophe_active = False

    def _update_catastrophe(self):
        """Update active catastrophe effects"""
        self.catastrophe_timer -= 1

        for region in self.affected_regions:
            region['radius'] += region['spread_rate']

            # Damage nodes in affected area
            for node in self.nodes:
                dist = np.sqrt((node['x'] - region['x'])**2 + (node['y'] - region['y'])**2)
                if dist < region['radius']:
                    node['value'] = max(0, node['value'] - region['damage'])
                    if node['value'] < 10:
                        node['depleted'] = True

        if self.catastrophe_timer <= 0:
            self.catastrophe_active = False
            self.affected_regions = []

    def harvest_node(self, node_id: str, amount: float) -> float:
        """Agent harvests from a node"""
        for node in self.nodes:
            if node['id'] == node_id:
                actual = min(amount, node['value'])
                node['value'] -= actual
                if node['value'] < 10:
                    node['depleted'] = True
                return actual
        return 0

    def deposit_pheromone(self, x: float, y: float, strength: float):
        """Agent marks location as interesting"""
        grid_key = (int(x/20), int(y/20))  # 20x20 grid cells
        self.pheromones[grid_key] = max(
            self.pheromones.get(grid_key, 0), strength)

    def get_nodes(self) -> List[Dict]:
        return self.nodes

    def get_pheromones(self) -> List[Dict]:
        """Return pheromones for visualization"""
        return [{'x': k[0]*20, 'y': k[1]*20, 'strength': v}
                for k, v in self.pheromones.items() if v > 0.1]

    def get_stats(self) -> Dict:
        """System metrics"""
        by_type = {}
        for node in self.nodes:
            by_type[node['type']] = by_type.get(node['type'], 0) + 1

        total_value = sum(n['value'] for n in self.nodes)

        return {
            'node_count': len(self.nodes),
            'total_value': round(total_value, 1),
            'pheromone_trails': len(self.pheromones),
            'by_type': by_type,
            'season': self.season_names[self.season],
            'season_progress': (self.tick % self.season_duration) / self.season_duration,
            'catastrophe_active': self.catastrophe_active,
            'affected_regions': len(self.affected_regions)
        }

    def get_catastrophe_regions(self) -> List[Dict]:
        """Return active catastrophe regions for visualization"""
        if not self.catastrophe_active:
            return []
        return [{
            'type': r['type'],
            'x': r['x'],
            'y': r['y'],
            'radius': r['radius']
        } for r in self.affected_regions]
