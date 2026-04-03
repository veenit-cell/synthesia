from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np
import random
import uuid
from memory import DualMemorySystem, Observation

@dataclass
class Vector2D:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)

    def magnitude(self):
        return np.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector2D(self.x / mag, self.y / mag)
        return Vector2D(0, 0)

@dataclass
class Forager:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    position: Vector2D = field(default_factory=lambda: Vector2D(
        random.uniform(0, 1000), random.uniform(0, 1000)))
    velocity: Vector2D = field(default_factory=lambda: Vector2D(0, 0))

    # Needs
    curiosity: float = 100.0
    energy: float = 100.0
    reputation: float = 50.0

    # Strategy parameters (evolvable)
    exploration_rate: float = field(default_factory=lambda: random.uniform(0.3, 0.7))
    sociability: float = field(default_factory=lambda: random.uniform(0.3, 0.7))
    risk_tolerance: float = field(default_factory=lambda: random.uniform(0.3, 0.7))
    aggression: float = field(default_factory=lambda: random.uniform(0.0, 0.3))  # Combat tendency

    # Specialization (evolves based on behavior)
    specialization: str = field(default='generalist')  # generalist, explorer, harvester, social, fighter
    spec_progress: Dict[str, float] = field(default_factory=lambda: {
        'explorer': 0, 'harvester': 0, 'social': 0, 'fighter': 0
    })

    # Combat stats
    health: float = 100.0
    combat_cooldown: int = 0

    # Memory
    memory: DualMemorySystem = field(default_factory=lambda: DualMemorySystem())

    # State
    current_action: str = "idle"
    action_target: Optional[Tuple[float, float]] = None
    last_decision_reason: str = ""

    # Constants
    MAX_SPEED: float = 4.0
    VISION_RADIUS: float = 100.0
    COMM_RADIUS: float = 50.0
    ENERGY_DECAY: float = 0.2

    def update_needs(self):
        """Natural decay of needs"""
        self.curiosity = max(0, self.curiosity - 0.3)
        self.energy = max(0, self.energy - self.ENERGY_DECAY)

        # Recover curiosity slowly (innate drive)
        self.curiosity = min(100, self.curiosity + 0.1)

    def observe_environment(self, nodes: List[dict], other_agents: List['Forager']) -> dict:
        """Gather sensory information"""
        observations = {
            'nearby_nodes': [],
            'nearby_agents': [],
            'local_density': 0
        }

        for node in nodes:
            dist = np.sqrt((node['x'] - self.position.x)**2 + (node['y'] - self.position.y)**2)
            if dist < self.VISION_RADIUS:
                observations['nearby_nodes'].append({**node, 'distance': dist})

        for agent in other_agents:
            if agent.id != self.id:
                dist = np.sqrt((agent.position.x - self.position.x)**2 +
                              (agent.position.y - self.position.y)**2)
                if dist < self.COMM_RADIUS:
                    observations['nearby_agents'].append({'agent': agent, 'distance': dist})
                if dist < self.VISION_RADIUS:
                    observations['local_density'] += 1

        # Sort by distance
        observations['nearby_nodes'].sort(key=lambda n: n['distance'])
        observations['nearby_agents'].sort(key=lambda a: a['distance'])

        return observations

    def decide_action(self, observations: dict) -> Tuple[str, Optional[Tuple[float, float]], str]:
        """
        BDI: Belief-Desire-Intention
        Returns: (action, target_position, reason)
        """
        # DESIRE determination
        if self.energy < 25:
            desire = "SURVIVE"
            reason = f"Low energy ({self.energy:.1f}), seeking resources"
        elif self.curiosity > 75:
            desire = "EXPLORE"
            reason = f"High curiosity ({self.curiosity:.1f}), exploring"
        elif observations['nearby_agents'] and self.sociability > 0.5:
            desire = "SOCIALIZE"
            reason = f"Sociable ({self.sociability:.2f}), seeking knowledge exchange"
        elif random.random() < self.exploration_rate:
            desire = "EXPLORE"
            reason = f"Exploration strategy ({self.exploration_rate:.2f})"
        else:
            desire = "EXPLOIT"
            reason = f"Exploitation strategy ({1-self.exploration_rate:.2f})"

        # INTENTION: Convert desire to action
        if desire == "SURVIVE":
            # Seek nearest high-value node
            if observations['nearby_nodes']:
                best = max(observations['nearby_nodes'], key=lambda n: n['value'] / (n['distance'] + 1))
                return ("seek", (best['x'], best['y']), reason)
            else:
                # Check memory
                memories = self.memory.query_relevant((self.position.x, self.position.y))
                if memories:
                    mem = memories[0]
                    return ("seek", mem.observation.position, f"{reason} [from memory]")

        elif desire == "EXPLORE":
            # Random direction with memory influence
            memories = self.memory.query_relevant((self.position.x, self.position.y), radius=500)
            if memories and random.random() < 0.3:
                # Occasionally explore toward promising remembered areas
                mem = random.choice(memories[:3])
                return ("seek", mem.observation.position, f"{reason} [toward memory]")
            else:
                # True random exploration
                target = (random.uniform(0, 1000), random.uniform(0, 1000))
                return ("wander", target, reason)

        elif desire == "SOCIALIZE":
            if observations['nearby_agents']:
                agent_info = observations['nearby_agents'][0]
                agent = agent_info['agent']
                return ("approach", (agent.position.x, agent.position.y),
                       f"{reason} [target: {agent.id[:4]}]")

        elif desire == "EXPLOIT":
            # Use known good spots
            memories = self.memory.query_relevant((self.position.x, self.position.y))
            if memories:
                mem = max(memories, key=lambda m: m.importance)
                return ("seek", mem.observation.position, reason)
            elif observations['nearby_nodes']:
                best = max(observations['nearby_nodes'], key=lambda n: n['value'])
                return ("seek", (best['x'], best['y']), reason)

        return ("idle", None, "No clear objective")

    def execute_action(self, action: str, target: Optional[Tuple[float, float]],
                      observations: dict, dt: float = 1.0):
        """Execute chosen action, update physics"""
        if action == "idle":
            self.velocity = Vector2D(0, 0)

        elif action == "seek" and target:
            dx = target[0] - self.position.x
            dy = target[1] - self.position.y
            dist = np.sqrt(dx**2 + dy**2)

            if dist > 5:  # Arrival tolerance
                direction = Vector2D(dx/dist, dy/dist)
                self.velocity = direction * self.MAX_SPEED
            else:
                self.velocity = Vector2D(0, 0)

        elif action == "wander" and target:
            dx = target[0] - self.position.x
            dy = target[1] - self.position.y
            dist = np.sqrt(dx**2 + dy**2)

            if dist > 10:
                direction = Vector2D(dx/dist, dy/dist)
                # Slower wandering
                self.velocity = direction * (self.MAX_SPEED * 0.5)
            else:
                self.velocity = Vector2D(0, 0)

            # Track explorer progress
            self.spec_progress['explorer'] += 0.1
            self._update_specialization()

        elif action == "approach" and target:
            dx = target[0] - self.position.x
            dy = target[1] - self.position.y
            dist = np.sqrt(dx**2 + dy**2)

            if dist > 20:  # Stop before collision
                direction = Vector2D(dx/dist, dy/dist)
                self.velocity = direction * self.MAX_SPEED
            else:
                self.velocity = Vector2D(0, 0)

        # Update position
        self.position = self.position + self.velocity * dt

        # Boundary wrap (toroidal)
        self.position.x = self.position.x % 1000
        self.position.y = self.position.y % 1000

        # Energy cost of movement
        movement_cost = self.velocity.magnitude() * 0.05
        self.energy = max(0, self.energy - movement_cost)

        self.current_action = action
        self.action_target = target
        self.last_decision_reason = self.last_decision_reason or "executing"

    def harvest(self, node: dict, amount: float) -> float:
        """Harvest from a node"""
        self.energy = min(100, self.energy + amount)
        self.curiosity = min(100, self.curiosity + 10)

        # Learn from this
        import time
        obs = Observation(
            position=(node['x'], node['y']),
            node_type=node['type'],
            value=node['value'],
            timestamp=time.time(),
            source='direct'
        )
        self.memory.observe(obs)

        # Track specialization
        self.spec_progress['harvester'] += 1
        self._update_specialization()

        return amount

    def communicate(self, other: 'Forager'):
        """Share memories with another agent"""
        my_memories = self.memory.get_all_memories()
        their_memories = other.memory.get_all_memories()

        # Share top 3 memories
        shared = 0
        for mem in sorted(my_memories, key=lambda m: m.importance, reverse=True)[:3]:
            import time
            obs = Observation(
                position=mem.observation.position,
                node_type=mem.observation.node_type,
                value=mem.observation.value * 0.9,  # Degrade slightly
                timestamp=time.time(),
                source='shared'
            )
            other.memory.observe(obs)
            shared += 1

        # Reputation update
        if shared > 0:
            other.reputation = min(100, other.reputation + 2)
            self.reputation = min(100, self.reputation + 1)

        # Track specialization
        self.spec_progress['social'] += 1
        self._update_specialization()

    def can_attack(self, other: 'Forager') -> bool:
        """Determine if this agent will attack another"""
        if self.combat_cooldown > 0:
            return False
        # Attack if much stronger and other has resources
        power_diff = (self.energy + self.health) - (other.energy + other.health)
        if power_diff > 30 and other.energy > 50 and self.aggression > 0.5:
            return True
        return False

    def attack(self, other: 'Forager') -> float:
        """Attack another agent, steal some energy"""
        damage = random.uniform(10, 25) * (0.5 + self.aggression)
        stolen = min(other.energy * 0.3, 30)

        other.health -= damage
        other.energy -= stolen
        self.energy = min(100, self.energy + stolen * 0.7)  # 70% efficiency

        self.combat_cooldown = 50  # Can't attack for 50 ticks
        self.spec_progress['fighter'] += 5
        self._update_specialization()

        return stolen

    def take_damage(self, amount: float):
        """Take damage from hazards"""
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.energy = 0  # "Death" - can't act

    def heal(self):
        """Slow health regeneration"""
        self.health = min(100, self.health + 0.05)
        if self.combat_cooldown > 0:
            self.combat_cooldown -= 1

    def _update_specialization(self):
        """Update specialization based on behavior"""
        total = sum(self.spec_progress.values())
        if total > 100:  # Only update after significant activity
            max_spec = max(self.spec_progress, key=self.spec_progress.get)
            if self.spec_progress[max_spec] / total > 0.4:
                self.specialization = max_spec

    def mutate_strategy(self, mutation_rate: float = 0.1):
        """Evolve strategy parameters"""
        if random.random() < mutation_rate:
            self.exploration_rate = np.clip(
                self.exploration_rate + random.gauss(0, 0.1), 0, 1)
        if random.random() < mutation_rate:
            self.sociability = np.clip(
                self.sociability + random.gauss(0, 0.1), 0, 1)

    def to_dict(self) -> dict:
        """Serialize for transmission"""
        return {
            'id': self.id,
            'x': self.position.x,
            'y': self.position.y,
            'vx': self.velocity.x,
            'vy': self.velocity.y,
            'energy': self.energy,
            'health': self.health,
            'curiosity': self.curiosity,
            'reputation': self.reputation,
            'action': self.current_action,
            'reason': self.last_decision_reason,
            'strategy': {
                'exploration': round(self.exploration_rate, 2),
                'sociability': round(self.sociability, 2),
                'aggression': round(self.aggression, 2)
            },
            'specialization': self.specialization,
            'combat_cooldown': self.combat_cooldown,
            'memory_count': len(self.memory.long_term)
        }
