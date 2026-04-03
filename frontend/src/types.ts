export interface Agent {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  energy: number;
  health: number;
  curiosity: number;
  reputation: number;
  action: string;
  reason: string;
  strategy: {
    exploration: number;
    sociability: number;
    aggression: number;
  };
  specialization: string;
  combat_cooldown: number;
  memory_count: number;
}

export interface Node {
  id: string;
  x: number;
  y: number;
  type: string;
  value: number;
  depleted: boolean;
}

export interface Pheromone {
  x: number;
  y: number;
  strength: number;
}

export interface Metrics {
  agent_count: number;
  communities: number;
  largest_community: number;
  knowledge_entropy: number;
  total_memories: number;
  avg_exploration: number;
  avg_aggression: number;
  avg_energy: number;
  avg_health: number;
  avg_reputation: number;
  specializations: Record<string, number>;
}

export interface CatastropheRegion {
  type: string;
  x: number;
  y: number;
  radius: number;
}

export interface SimulationState {
  tick: number;
  agents: Agent[];
  nodes: Node[];
  pheromones: Pheromone[];
  catastrophe_regions: CatastropheRegion[];
  environment: {
    node_count: number;
    total_value: number;
    pheromone_trails: number;
    by_type: Record<string, number>;
    season: string;
    season_progress: number;
    catastrophe_active: boolean;
    affected_regions: number;
  };
  metrics: Metrics;
  communities: string[][];
}
