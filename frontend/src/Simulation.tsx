import { useEffect, useRef, useState } from 'react';
import { useSimStore } from './store';
import { SimulationState, Agent, Node } from './types';

const CANVAS_WIDTH = 1000;
const CANVAS_HEIGHT = 1000;
const SCALE = 0.8;

export function Simulation() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const { state, setState, setConnected, selectedAgent, setSelectedAgent } = useSimStore();
  const [showPheromones, setShowPheromones] = useState(true);
  const [showTrails, setShowTrails] = useState(true);
  const trailsRef = useRef<Map<string, {x: number, y: number}[]>>(new Map());

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/simulation');
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      const data: SimulationState = JSON.parse(e.data);
      setState(data);

      // Update trails
      data.agents.forEach(agent => {
        if (!trailsRef.current.has(agent.id)) {
          trailsRef.current.set(agent.id, []);
        }
        const trail = trailsRef.current.get(agent.id)!;
        trail.push({x: agent.x, y: agent.y});
        if (trail.length > 50) trail.shift();
      });
    };

    return () => ws.close();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !state) return;

    const ctx = canvas.getContext('2d')!;
    ctx.clearRect(0, 0, CANVAS_WIDTH * SCALE, CANVAS_HEIGHT * SCALE);

    ctx.save();
    ctx.scale(SCALE, SCALE);

    // Draw pheromones
    if (showPheromones) {
      state.pheromones.forEach(p => {
        const alpha = Math.min(p.strength, 0.3);
        ctx.fillStyle = `rgba(255, 200, 100, ${alpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 15, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // Draw trails
    if (showTrails) {
      trailsRef.current.forEach((trail, agentId) => {
        if (trail.length < 2) return;
        ctx.strokeStyle = 'rgba(100, 150, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(trail[0].x, trail[0].y);
        for (let i = 1; i < trail.length; i++) {
          ctx.lineTo(trail[i].x, trail[i].y);
        }
        ctx.stroke();
      });
    }

    // Draw nodes
    state.nodes.forEach((node: Node) => {
      const typeColors: Record<string, string> = {
        science: '#4ade80',
        art: '#f472b6',
        history: '#fbbf24',
        technology: '#60a5fa',
        gold: '#fbbf24'
      };

      const color = typeColors[node.type] || '#94a3b8';
      const size = 5 + (node.value / 100) * 10;
      const alpha = node.depleted ? 0.3 : 0.8;

      ctx.fillStyle = color;
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, Math.PI * 2);
      ctx.fill();

      if (node.value > 60 && !node.depleted) {
        ctx.shadowBlur = 10;
        ctx.shadowColor = color;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
      ctx.globalAlpha = 1;
    });

    // Draw agents
    state.agents.forEach((agent: Agent) => {
      const isSelected = agent.id === selectedAgent;
      const size = isSelected ? 12 : 8;

      const explorationColor = `hsl(${240 - agent.strategy.exploration * 240}, 70%, 50%)`;

      ctx.fillStyle = isSelected ? '#ef4444' : explorationColor;
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, size, 0, Math.PI * 2);
      ctx.fill();

      const speed = Math.sqrt(agent.vx ** 2 + agent.vy ** 2);
      if (speed > 0.1) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(agent.x, agent.y);
        ctx.lineTo(agent.x + agent.vx * 5, agent.y + agent.vy * 5);
        ctx.stroke();
      }

      ctx.strokeStyle = `hsl(${agent.energy * 1.2}, 70%, 50%)`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, size + 3, 0, (agent.energy / 100) * Math.PI * 2);
      ctx.stroke();
    });

    ctx.restore();
  }, [state, selectedAgent, showPheromones, showTrails]);

  const handleCanvasClick = (e: React.MouseEvent) => {
    if (!state) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / SCALE;
    const y = (e.clientY - rect.top) / SCALE;

    const clicked = state.agents.find(a => {
      const dist = Math.sqrt((a.x - x) ** 2 + (a.y - y) ** 2);
      return dist < 20;
    });

    setSelectedAgent(clicked ? clicked.id : null);
  };

  const sendCommand = (action: string, event?: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, event }));
    }
  };

  const selectedAgentData = selectedAgent
    ? state?.agents.find(a => a.id === selectedAgent)
    : null;

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <div className="flex-1 flex items-center justify-center p-4">
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH * SCALE}
          height={CANVAS_HEIGHT * SCALE}
          onClick={handleCanvasClick}
          className="border border-gray-700 rounded-lg cursor-crosshair bg-gray-950"
        />
      </div>

      <div className="w-80 p-4 bg-gray-800 border-l border-gray-700 overflow-y-auto">
        <h1 className="text-2xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          SYNTHESIA
        </h1>

        <div className="space-y-2 mb-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase">Controls</h2>
          <button
            onClick={() => sendCommand('inject', 'gold_rush')}
            className="w-full px-3 py-2 bg-yellow-600 hover:bg-yellow-500 rounded text-sm transition"
          >
            Inject Gold Rush
          </button>
          <button
            onClick={() => sendCommand('inject', 'add_agent')}
            className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded text-sm transition"
          >
            Add Agent
          </button>
          <button
            onClick={() => sendCommand('inject', 'remove_agent')}
            className="w-full px-3 py-2 bg-red-600 hover:bg-red-500 rounded text-sm transition"
          >
            Remove Random Agent
          </button>
          <button
            onClick={() => sendCommand('reset')}
            className="w-full px-3 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm transition"
          >
            Reset Simulation
          </button>
        </div>

        <div className="space-y-2 mb-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase">Visualization</h2>
          <label className="flex items-center space-x-2">
            <input type="checkbox" checked={showPheromones} onChange={(e) => setShowPheromones(e.target.checked)} />
            <span>Show Pheromones</span>
          </label>
          <label className="flex items-center space-x-2">
            <input type="checkbox" checked={showTrails} onChange={(e) => setShowTrails(e.target.checked)} />
            <span>Show Agent Trails</span>
          </label>
        </div>

        {state?.metrics && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase mb-2">Emergent Metrics</h2>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Communities:</span>
                <span className="font-mono text-green-400">{state.metrics.communities}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Largest Cluster:</span>
                <span className="font-mono">{state.metrics.largest_community} agents</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Knowledge Entropy:</span>
                <span className="font-mono text-blue-400">{state.metrics.knowledge_entropy}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Total Memories:</span>
                <span className="font-mono">{state.metrics.total_memories}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Avg Exploration:</span>
                <span className="font-mono">{state.metrics.avg_exploration}</span>
              </div>
            </div>
          </div>
        )}

        {state?.environment && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase mb-2">Environment</h2>
            <div className="space-y-1 text-sm text-gray-300">
              <div>Nodes: {state.environment.node_count}</div>
              <div>Total Value: {Math.round(state.environment.total_value)}</div>
              <div>Pheromone Trails: {state.environment.pheromone_trails}</div>
            </div>
          </div>
        )}

        {selectedAgentData && (
          <div className="p-3 bg-gray-700 rounded-lg">
            <h2 className="text-sm font-semibold text-yellow-400 mb-2">
              Agent {selectedAgentData.id}
            </h2>
            <div className="space-y-1 text-xs">
              <div>Action: <span className="text-blue-300">{selectedAgentData.action}</span></div>
              <div>Reason: <span className="text-gray-300 italic">{selectedAgentData.reason}</span></div>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <div>Energy: {Math.round(selectedAgentData.energy)}</div>
                <div>Curiosity: {Math.round(selectedAgentData.curiosity)}</div>
                <div>Reputation: {Math.round(selectedAgentData.reputation)}</div>
                <div>Memories: {selectedAgentData.memory_count}</div>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-600">
                <div>Exploration: {selectedAgentData.strategy.exploration}</div>
                <div>Sociability: {selectedAgentData.strategy.sociability}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
