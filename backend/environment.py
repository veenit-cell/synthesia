import numpy as np
import random
from typing import List, Dict
import noise

class Environment:
    def __init__(self, width: float = 1000, height: float = 1000, max_nodes: int = 150):
        self.width = width
        self.height = height
        self.max_nodes = max_nodes
        self.nodes: List[Dict] = []
        self.pheromones: Dict[tuple[int, int], float] = {}  # Grid-based
        self.tick = 0

        # Initialize with some nodes
        self._seed_environment()

    def _seed_environment(self, count: int = 50):
        """Create initial information nodes using Perlin noise for clustering"""
        for i in range(count):
            # Use Perlin noise to create clusters
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)

            # Determine type based on position (creates regions)
            type_noise = noise.pnoise2(x/300, y/300)
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

    def update(self):
        """Environmental dynamics"""
        self.tick += 1

        # Spawn new nodes occasionally (higher chance in active areas)
        if len(self.nodes) < self.max_nodes and random.random() < 0.1:
            self._spawn_node()

        # Regenerate depleted nodes slowly
        for node in self.nodes:
            if node['depleted']:
                node['value'] = min(node['max_value'], node['value'] + 0.05)
                if node['value'] > node['max_value'] * 0.3:
                    node['depleted'] = False

        # Decay pheromones
        to_remove = []
        for key, strength in self.pheromones.items():
            self.pheromones[key] = strength * 0.98
            if self.pheromones[key] < 0.01:
                to_remove.append(key)
        for key in to_remove:
            del self.pheromones[key]

    def _spawn_node(self):
        """Spawn a new information node, preferring cluster areas"""
        # 70% chance to spawn near existing nodes (clustering)
        if random.random() < 0.7 and self.nodes:
            parent = random.choice(self.nodes)
            x = np.clip(parent['x'] + random.gauss(0, 100), 0, self.width)
            y = np.clip(parent['y'] + random.gauss(0, 100), 0, self.height)
        else:
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)

        type_noise = noise.pnoise2(x/300, y/300, base=self.tick)
        node_type = self._noise_to_type(type_noise)

        self.nodes.append({
            'id': f"node_{self.tick}_{random.randint(0, 1000)}",
            'x': x,
            'y': y,
            'type': node_type,
            'value': random.uniform(40, 100),
            'max_value': 100,
            'depleted': False
        })

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
            'by_type': by_type
        }
