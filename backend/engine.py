import asyncio
import random
import time
from typing import List, Dict
import numpy as np
from scipy.spatial import KDTree

from agent import Forager
from environment import Environment

class SynthesiaEngine:
    def __init__(self, num_agents: int = 30):
        self.agents: List[Forager] = [Forager() for _ in range(num_agents)]
        self.environment = Environment()
        self.running = False
        self.tick = 0
        self.callback = None

        # Spatial indexing
        self.kdtree = None
        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild spatial index for fast queries"""
        positions = [[a.position.x, a.position.y] for a in self.agents]
        if positions:
            self.kdtree = KDTree(positions)

    def get_nearby_nodes(self, agent: Forager, radius: float = 100) -> List[Dict]:
        """Get nodes within radius"""
        nodes = self.environment.get_nodes()
        nearby = []
        for node in nodes:
            dist = np.sqrt((node['x'] - agent.position.x)**2 +
                          (node['y'] - agent.position.y)**2)
            if dist < radius:
                nearby.append(node)
        return nearby

    def get_nearby_agents(self, agent: Forager, radius: float = 50) -> List[Forager]:
        """Get agents within communication radius using KD-tree"""
        if self.kdtree is None:
            return []

        indices = self.kdtree.query_ball_point([agent.position.x, agent.position.y], radius)
        return [self.agents[i] for i in indices if self.agents[i].id != agent.id]

    def check_harvest(self, agent: Forager) -> bool:
        """Check if agent can harvest a node it's near"""
        for node in self.environment.get_nodes():
            dist = np.sqrt((node['x'] - agent.position.x)**2 +
                          (node['y'] - agent.position.y)**2)
            if dist < 15 and not node['depleted'] and agent.energy < 100:
                harvested = self.environment.harvest_node(node['id'], 20)
                if harvested > 0:
                    agent.harvest(node)
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

        # Simple clustering: agents within 150 of each other
        communities = []
        visited = set()

        for agent in self.agents:
            if agent.id in visited:
                continue

            community = []
            stack = [agent]

            while stack:
                current = stack.pop()
                if current.id in visited:
                    continue
                visited.add(current.id)
                community.append(current.id)

                # Find neighbors
                for other in self.agents:
                    if other.id not in visited:
                        dist = np.sqrt((current.position.x - other.position.x)**2 +
                                     (current.position.y - other.position.y)**2)
                        if dist < 150:
                            stack.append(other)

            if len(community) >= 2:
                communities.append(community)

        return communities

    def calculate_metrics(self) -> Dict:
        """Calculate emergent system metrics"""
        # Clustering coefficient approximation
        communities = self.detect_communities()

        # Knowledge diversity (entropy of discoveries)
        all_memories = []
        for agent in self.agents:
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

        # Strategy distribution
        exploration_dist = [a.exploration_rate for a in self.agents]
        avg_exploration = np.mean(exploration_dist)

        return {
            'agent_count': len(self.agents),
            'communities': len(communities),
            'largest_community': max([len(c) for c in communities]) if communities else 0,
            'knowledge_entropy': round(entropy, 2),
            'total_memories': len(all_memories),
            'avg_exploration': round(avg_exploration, 2),
            'avg_energy': round(np.mean([a.energy for a in self.agents]), 1),
            'avg_reputation': round(np.mean([a.reputation for a in self.agents]), 1)
        }

    def step(self):
        """Single simulation step"""
        self.tick += 1

        # Environment update
        self.environment.update()

        # Agent updates
        for agent in self.agents:
            # Update needs
            agent.update_needs()

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

            if action in ['approach', 'wander'] and nearby_agents:
                self.check_communication(agent)

        # Periodic strategy evolution
        if self.tick % 100 == 0:
            for agent in self.agents:
                # Agents with high energy+reputation reproduce (copy to random agent)
                fitness = (agent.energy + agent.reputation) / 200
                if fitness > 0.7 and random.random() < 0.1:
                    # Find agent with lowest fitness
                    weakest = min(self.agents, key=lambda a: a.energy + a.reputation)
                    weakest.exploration_rate = agent.exploration_rate
                    weakest.sociability = agent.sociability
                    weakest.risk_tolerance = agent.risk_tolerance

        self._rebuild_index()

    def get_state(self) -> Dict:
        """Get full system state for visualization"""
        return {
            'tick': self.tick,
            'agents': [a.to_dict() for a in self.agents],
            'nodes': self.environment.get_nodes(),
            'pheromones': self.environment.get_pheromones(),
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
        elif event_type == 'remove_agent':
            if self.agents:
                self.agents.pop(random.randrange(len(self.agents)))
        elif event_type == 'add_agent':
            self.agents.append(Forager())
