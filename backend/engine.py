import asyncio
import random
import time
from typing import List, Dict, Set
import numpy as np

from agent import Forager
from environment import Environment


class SpatialHash:
    """Fast spatial indexing for neighbor queries"""
    def __init__(self, cell_size: float = 100):
        self.cell_size = cell_size
        self.cells: Dict[tuple[int, int], List[int]] = {}
        self._positions: np.ndarray = np.zeros((0, 2))

    def clear(self):
        self.cells.clear()

    def insert(self, agent_id: int, x: float, y: float):
        cell_x = int(x / self.cell_size)
        cell_y = int(y / self.cell_size)
        key = (cell_x, cell_y)
        if key not in self.cells:
            self.cells[key] = []
        self.cells[key].append(agent_id)

    def query_radius(self, x: float, y: float, radius: float) -> Set[int]:
        """Get all agent IDs within radius"""
        cell_radius = int(radius / self.cell_size) + 1
        cell_x = int(x / self.cell_size)
        cell_y = int(y / self.cell_size)

        result = set()
        radius_sq = radius ** 2

        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                key = (cell_x + dx, cell_y + dy)
                if key in self.cells:
                    result.update(self.cells[key])

        return result

class SynthesiaEngine:
    def __init__(self, num_agents: int = 30):
        self.agents: List[Forager] = [Forager() for _ in range(num_agents)]
        self.environment = Environment()
        self.running = False
        self.tick = 0
        self.callback = None

        # Fast spatial indexing
        self.spatial_hash = SpatialHash(cell_size=100)
        self._rebuild_index()

        # Batch processing
        self.batch_size = 10
        self._batch_index = 0

        # Pre-allocated arrays for metrics
        self._metrics_cache = {}
        self._metrics_tick = -50

    def _rebuild_index(self):
        """Rebuild spatial hash for fast queries"""
        self.spatial_hash.clear()
        for i, agent in enumerate(self.agents):
            if agent.health > 0:
                self.spatial_hash.insert(i, agent.position.x, agent.position.y)

    def get_nearby_nodes(self, agent: Forager, radius: float = 100) -> List[Dict]:
        """Get nodes within radius - optimized with early exit"""
        nodes = self.environment.get_nodes()
        nearby = []
        radius_sq = radius ** 2
        ax, ay = agent.position.x, agent.position.y

        for node in nodes:
            dx = node['x'] - ax
            dy = node['y'] - ay
            if dx * dx + dy * dy < radius_sq:
                nearby.append(node)
        return nearby

    def get_nearby_agents(self, agent: Forager, radius: float = 50) -> List[Forager]:
        """Get agents within communication radius using spatial hash"""
        indices = self.spatial_hash.query_radius(
            agent.position.x, agent.position.y, radius)
        return [self.agents[i] for i in indices if str(self.agents[i].id) != str(agent.id)]

    def check_harvest(self, agent: Forager) -> bool:
        """Check if agent can harvest a node it's near"""
        for node in self.environment.get_nodes():
            dist = np.sqrt((node['x'] - agent.position.x)**2 +
                          (node['y'] - agent.position.y)**2)
            if dist < 15 and not node['depleted'] and agent.energy < 100:
                # Calculate how much the agent can actually receive
                space_available = 100 - agent.energy
                harvest_amount = min(20, space_available)
                if harvest_amount <= 0:
                    return False
                harvested = self.environment.harvest_node(node['id'], harvest_amount)
                if harvested > 0:
                    agent.harvest(node, harvested)
                    # Mark with pheromone if valuable
                    if node['value'] > 60:
                        self.environment.deposit_pheromone(
                            agent.position.x, agent.position.y, node['value']/100)
                    return True
        return False

    def check_communication(self, agent: Forager):
        """Handle agent-agent communication"""
        nearby = self.get_nearby_agents(agent, radius=30)
        for other in nearby:
            # Both must want to communicate
            if (agent.sociability + other.sociability) / 2 > random.random():
                agent.communicate(other)

    def detect_communities(self) -> List[List[str]]:
        """Detect emergent agent clusters using proximity"""
        if len(self.agents) < 3:
            return []

        # Use spatial hash for faster clustering
        communities = []
        visited = set()
        threshold_sq = 150 ** 2

        for agent in self.agents:
            if agent.id in visited or agent.health <= 0:
                continue

            community = []
            stack = [agent]

            while stack:
                current = stack.pop()
                if current.id in visited:
                    continue
                visited.add(current.id)
                community.append(current.id)

                # Find neighbors using spatial hash
                nearby_indices = self.spatial_hash.query_radius(
                    current.position.x, current.position.y, 150)
                for idx in nearby_indices:
                    other = self.agents[idx]
                    if other.id not in visited and other.health > 0:
                        dx = current.position.x - other.position.x
                        dy = current.position.y - other.position.y
                        if dx * dx + dy * dy < threshold_sq:
                            stack.append(other)

            if len(community) >= 2:
                communities.append(community)

        return communities

    def calculate_metrics(self) -> Dict:
        """Calculate emergent system metrics with caching"""
        # Only recalculate every 10 ticks
        if self.tick - self._metrics_tick < 10 and self._metrics_cache:
            return self._metrics_cache

        self._metrics_tick = self.tick

        # Clustering coefficient approximation
        communities = self.detect_communities()

        # Knowledge diversity (entropy of discoveries) - sample for performance
        sample_agents = self.agents[::max(1, len(self.agents) // 20)]
        all_memories = []
        for agent in sample_agents:
            all_memories.extend(agent.memory.get_all_memories())

        type_counts = {}
        for mem in all_memories:
            t = mem.observation.node_type
            type_counts[t] = type_counts.get(t, 0) + 1

        total = sum(type_counts.values())
        entropy = 0
        if total > 0:
            for count in type_counts.values():
                p = count / total
                entropy -= p * np.log2(p) if p > 0 else 0

        # Pre-compute arrays for speed
        energies = [a.energy for a in self.agents]
        healths = [a.health for a in self.agents]
        reps = [a.reputation for a in self.agents]
        explorations = [a.exploration_rate for a in self.agents]
        aggressions = [a.aggression for a in self.agents]

        # Specialization counts
        spec_counts = {}
        for a in self.agents:
            spec_counts[a.specialization] = spec_counts.get(a.specialization, 0) + 1

        self._metrics_cache = {
            'agent_count': len(self.agents),
            'communities': len(communities),
            'largest_community': max([len(c) for c in communities]) if communities else 0,
            'knowledge_entropy': round(entropy, 2),
            'total_memories': len(all_memories) * (len(self.agents) // max(1, len(sample_agents))),
            'avg_exploration': round(sum(explorations) / len(explorations), 2) if explorations else 0,
            'avg_aggression': round(sum(aggressions) / len(aggressions), 2) if aggressions else 0,
            'avg_energy': round(sum(energies) / len(energies), 1) if energies else 0,
            'avg_health': round(sum(healths) / len(healths), 1) if healths else 0,
            'avg_reputation': round(sum(reps) / len(reps), 1) if reps else 0,
            'specializations': spec_counts
        }
        return self._metrics_cache

    def step(self):
        """Single simulation step with batch processing"""
        self.tick += 1

        # Environment update (every tick)
        self.environment.update()

        # Process agents in batches for smoother performance
        total_agents = len(self.agents)
        batch_start = self._batch_index
        batch_end = min(batch_start + self.batch_size, total_agents)

        for i in range(batch_start, batch_end):
            agent = self.agents[i]
            if agent.health <= 0:
                continue

            # Update needs and heal
            agent.update_needs()
            agent.heal()

            # Check for hazard damage (every 5 ticks to save CPU)
            if self.tick % 5 == 0:
                self._check_hazards(agent)

            # Perception
            nearby_nodes = self.get_nearby_nodes(agent)
            nearby_agents = self.get_nearby_agents(agent)
            observations = agent.observe_environment(nearby_nodes, nearby_agents)

            # Decision
            action, target, reason = agent.decide_action(observations)
            agent.last_decision_reason = reason

            # Action
            agent.execute_action(action, target, observations)

            # Interactions
            if action in ['seek', 'wander']:
                self.check_harvest(agent)
                self._check_portals(agent)

            if action in ['approach', 'wander'] and nearby_agents:
                self.check_communication(agent)
                self.check_combat(agent, nearby_agents)

        # Update batch index
        self._batch_index = batch_end if batch_end < total_agents else 0

        # Full cycle processing (every tick, but on all agents)
        if self._batch_index == 0:
            # Remove dead agents occasionally
            self.agents = [a for a in self.agents if a.health > 0 or random.random() > 0.01]

            # Replenish if too few agents
            while len(self.agents) < 20:
                self.agents.append(Forager())

            # Periodic strategy evolution
            if self.tick % 100 == 0:
                self._evolve_strategies()

        self._rebuild_index()

    def _evolve_strategies(self):
        """Evolve agent strategies based on fitness"""
        for agent in self.agents:
            fitness = (agent.energy + agent.reputation + agent.health) / 300
            if fitness > 0.7 and random.random() < 0.1:
                weakest = min(self.agents, key=lambda a: a.energy + a.reputation + a.health)
                weakest.exploration_rate = agent.exploration_rate
                weakest.sociability = agent.sociability
                weakest.risk_tolerance = agent.risk_tolerance
                weakest.aggression = agent.aggression

    def _check_hazards(self, agent: Forager):
        """Check if agent is near hazard nodes or catastrophe regions"""
        for node in self.environment.get_nodes():
            if node.get('type') == 'hazard' and not node.get('depleted'):
                dist = np.sqrt((node['x'] - agent.position.x)**2 +
                              (node['y'] - agent.position.y)**2)
                if dist < 20:
                    agent.take_damage(node.get('damage', 5))

        # Catastrophe damage
        if self.environment.catastrophe_active:
            for region in self.environment.affected_regions:
                dist = np.sqrt((region['x'] - agent.position.x)**2 +
                              (region['y'] - agent.position.y)**2)
                if dist < region['radius']:
                    agent.take_damage(region['damage'] * 0.1)

    def _check_portals(self, agent: Forager):
        """Check if agent entered a portal"""
        for node in self.environment.get_nodes():
            if node.get('type') == 'portal':
                dist = np.sqrt((node['x'] - agent.position.x)**2 +
                              (node['y'] - agent.position.y)**2)
                if dist < 15:
                    # Teleport!
                    agent.position.x = node.get('target_x', random.uniform(0, 1000))
                    agent.position.y = node.get('target_y', random.uniform(0, 1000))
                    agent.energy = max(0, agent.energy - 10)  # Cost to teleport
                    return

    def check_combat(self, agent: Forager, nearby_agents: List[Forager]):
        """Handle agent-agent combat"""
        for other in nearby_agents:
            if other.health <= 0:
                continue

            dist = np.sqrt((other.position.x - agent.position.x)**2 +
                          (other.position.y - agent.position.y)**2)
            if dist < 25:  # Combat range
                # Check for mutual attack or flee
                if agent.can_attack(other):
                    stolen = agent.attack(other)
                    if stolen > 0:
                        agent.spec_progress['fighter'] += 3
                elif other.can_attack(agent):
                    stolen = other.attack(agent)
                    if stolen > 0:
                        other.spec_progress['fighter'] += 3

    def get_state(self) -> Dict:
        """Get full system state for visualization"""
        return {
            'tick': self.tick,
            'agents': [a.to_dict() for a in self.agents],
            'nodes': self.environment.get_nodes(),
            'pheromones': self.environment.get_pheromones(),
            'catastrophe_regions': self.environment.get_catastrophe_regions(),
            'environment': self.environment.get_stats(),
            'metrics': self.calculate_metrics(),
            'communities': self.detect_communities()
        }

    async def run(self, fps: int = 30):
        """Main loop"""
        self.running = True
        interval = 1.0 / fps

        while self.running:
            start = time.time()
            self.step()

            if self.callback:
                await self.callback(self.get_state())

            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def inject_event(self, event_type: str, data: dict = None):
        """Allow external perturbations"""
        if event_type == 'gold_rush':
            # Spawn high-value nodes in random area
            cx, cy = random.uniform(200, 800), random.uniform(200, 800)
            for _ in range(10):
                self.environment.nodes.append({
                    'id': f"gold_{self.tick}_{random.randint(0,1000)}",
                    'x': cx + random.gauss(0, 100),
                    'y': cy + random.gauss(0, 100),
                    'type': 'gold',
                    'value': random.uniform(80, 100),
                    'max_value': 100,
                    'depleted': False
                })
        elif event_type == 'hazard_zone':
            # Spawn hazard nodes
            for _ in range(5):
                self.environment._spawn_special_node('hazard')
        elif event_type == 'portal_storm':
            # Spawn multiple portals
            for _ in range(3):
                self.environment._spawn_special_node('portal')
        elif event_type == 'wildfire':
            self.environment.trigger_catastrophe('wildfire')
        elif event_type == 'flood':
            self.environment.trigger_catastrophe('flood')
        elif event_type == 'drought':
            self.environment.trigger_catastrophe('drought')
        elif event_type == 'remove_agent':
            if self.agents:
                self.agents.pop(random.randrange(len(self.agents)))
        elif event_type == 'add_agent':
            self.agents.append(Forager())
        elif event_type == 'add_fighter':
            # Add an aggressive agent
            fighter = Forager()
            fighter.aggression = 0.8
            fighter.exploration_rate = 0.6
            self.agents.append(fighter)
        elif event_type == 'add_explorer':
            explorer = Forager()
            explorer.exploration_rate = 0.9
            explorer.aggression = 0.1
            self.agents.append(explorer)
