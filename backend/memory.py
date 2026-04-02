from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import deque
import time
import numpy as np

@dataclass
class Observation:
    position: tuple[float, float]
    node_type: str
    value: float
    timestamp: float
    source: str  # 'direct', 'shared', 'inferred'

@dataclass
class Memory:
    observation: Observation
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    importance: float = 0.0  # Calculated from value and recency

class DualMemorySystem:
    def __init__(self, stm_size: int = 20, ltm_size: int = 50):
        self.short_term: deque[Observation] = deque(maxlen=stm_size)
        self.long_term: Dict[str, Memory] = {}
        self.max_ltm = ltm_size

    def observe(self, observation: Observation):
        """Add to short-term memory"""
        self.short_term.append(observation)
        self._maybe_consolidate()

    def _maybe_consolidate(self):
        """Move important observations to long-term"""
        current_time = time.time()
        for obs in list(self.short_term):
            # Importance based on value and novelty
            importance = obs.value * (1 + 0.5 * (obs.source != 'direct'))

            if importance > 30:  # Threshold for consolidation
                key = f"{obs.node_type}_{int(obs.position[0])}_{int(obs.position[1])}"

                if key not in self.long_term:
                    if len(self.long_term) >= self.max_ltm:
                        # Forget least important
                        self._forget_least_important()

                    self.long_term[key] = Memory(observation=obs, importance=importance)

    def _forget_least_important(self):
        """Remove least accessed/oldest memory"""
        if not self.long_term:
            return
        min_key = min(self.long_term.keys(),
                     key=lambda k: self.long_term[k].importance)
        del self.long_term[min_key]

    def query_relevant(self, position: tuple[float, float], radius: float = 200) -> List[Memory]:
        """Retrieve memories near position"""
        relevant = []
        for mem in self.long_term.values():
            dist = np.sqrt((mem.observation.position[0] - position[0])**2 +
                          (mem.observation.position[1] - position[1])**2)
            if dist < radius:
                mem.access_count += 1
                mem.last_accessed = time.time()
                mem.importance *= 1.1  # Reinforce
                relevant.append(mem)
        return sorted(relevant, key=lambda m: m.importance, reverse=True)

    def get_all_memories(self) -> List[Memory]:
        return list(self.long_term.values())
