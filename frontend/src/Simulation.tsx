import { useEffect, useRef, useState, useCallback } from 'react';
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
  const [showCommunities, setShowCommunities] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(false);
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

  const drawHeatmap = useCallback((ctx: CanvasRenderingContext2D, agents: Agent[]) => {
    const cellSize = 50;
    const gridWidth = Math.ceil(CANVAS_WIDTH / cellSize);
    const gridHeight = Math.ceil(CANVAS_HEIGHT / cellSize);
    const grid: number[][] = Array(gridHeight).fill(0).map(() => Array(gridWidth).fill(0));

    // Count agents in each cell
    agents.forEach(agent => {
      const gx = Math.floor(agent.x / cellSize);
      const gy = Math.floor(agent.y / cellSize);
      if (gx >= 0 && gx < gridWidth && gy >= 0 && gy < gridHeight) {
        grid[gy][gx] += 1;
      }
    });

    // Draw heatmap
    const maxVal = Math.max(...grid.flat(), 1);
    for (let y = 0; y < gridHeight; y++) {
      for (let x = 0; x < gridWidth; x++) {
        const intensity = grid[y][x] / maxVal;
        if (intensity > 0) {
          ctx.fillStyle = `rgba(255, 50, 50, ${intensity * 0.4})`;
          ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
      }
    }
  }, []);

  const drawCommunityLines = useCallback((ctx: CanvasRenderingContext2D, communities: string[][], agents: Agent[]) => {
    const agentMap = new Map(agents.map(a => [a.id, a]));
    const colors = ['#f472b6', '#4ade80', '#60a5fa', '#fbbf24', '#a78bfa', '#f87171'];

    communities.forEach((community, idx) => {
      const color = colors[idx % colors.length];
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.3;

      for (let i = 0; i < community.length; i++) {
        const agent1 = agentMap.get(community[i]);
        if (!agent1) continue;

        for (let j = i + 1; j < community.length; j++) {
          const agent2 = agentMap.get(community[j]);
          if (!agent2) continue;

          const dist = Math.sqrt((agent1.x - agent2.x)**2 + (agent1.y - agent2.y)**2);
          if (dist < 150) {
            ctx.beginPath();
            ctx.moveTo(agent1.x, agent1.y);
            ctx.lineTo(agent2.x, agent2.y);
            ctx.stroke();
          }
        }
      }
    });
    ctx.globalAlpha = 1;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !state) return;

    const ctx = canvas.getContext('2d')!;
    ctx.clearRect(0, 0, CANVAS_WIDTH * SCALE, CANVAS_HEIGHT * SCALE);

    ctx.save();
    ctx.scale(SCALE, SCALE);

    // Draw season background
    const seasonColors: Record<string, string> = {
      spring: 'rgba(100, 255, 100, 0.05)',
      summer: 'rgba(255, 255, 100, 0.05)',
      fall: 'rgba(255, 150, 50, 0.05)',
      winter: 'rgba(200, 230, 255, 0.1)'
    };
    const season = state.environment?.season || 'spring';
    ctx.fillStyle = seasonColors[season] || 'rgba(0,0,0,0)';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Draw heatmap
    if (showHeatmap) {
      drawHeatmap(ctx, state.agents);
    }

    // Draw catastrophe regions
    if (state.catastrophe_regions) {
      state.catastrophe_regions.forEach(region => {
        const gradient = ctx.createRadialGradient(
          region.x, region.y, 0,
          region.x, region.y, region.radius
        );
        if (region.type === 'fire') {
          gradient.addColorStop(0, 'rgba(255, 100, 50, 0.6)');
          gradient.addColorStop(0.5, 'rgba(255, 150, 50, 0.3)');
          gradient.addColorStop(1, 'rgba(255, 200, 100, 0)');
        } else if (region.type === 'flood') {
          gradient.addColorStop(0, 'rgba(50, 100, 255, 0.4)');
          gradient.addColorStop(0.5, 'rgba(100, 150, 255, 0.2)');
          gradient.addColorStop(1, 'rgba(150, 200, 255, 0)');
        }
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(region.x, region.y, region.radius, 0, Math.PI * 2);
        ctx.fill();
      });
    }

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
        gold: '#fbbf24',
        hazard: '#ef4444',
        portal: '#a855f7',
        mystery: '#14b8a6'
      };

      const color = typeColors[node.type] || '#94a3b8';
      const size = 5 + (node.value / 100) * 10;
      const alpha = node.depleted ? 0.3 : 0.8;

      ctx.fillStyle = color;
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, Math.PI * 2);
      ctx.fill();

      // Special effects
      if (node.type === 'hazard' && !node.depleted) {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 5 + Math.sin(Date.now() / 200) * 3, 0, Math.PI * 2);
        ctx.stroke();
      } else if (node.type === 'portal' && !node.depleted) {
        ctx.strokeStyle = '#a855f7';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 8, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      } else if (node.value > 60 && !node.depleted) {
        ctx.shadowBlur = 10;
        ctx.shadowColor = color;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
      ctx.globalAlpha = 1;
    });

    // Draw community lines
    if (showCommunities && state.communities) {
      drawCommunityLines(ctx, state.communities, state.agents);
    }

    // Draw agents
    state.agents.forEach((agent: Agent) => {
      if (agent.health <= 0) return; // Skip "dead" agents

      const isSelected = agent.id === selectedAgent;
      const size = isSelected ? 12 : 8;

      // Color by aggression
      const explorationColor = `hsl(${240 - agent.strategy.exploration * 240}, 70%, 50%)`;
      const aggressionColor = agent.strategy.aggression > 0.5 ? '#ef4444' : explorationColor;

      ctx.fillStyle = isSelected ? '#ef4444' : aggressionColor;
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, size, 0, Math.PI * 2);
      ctx.fill();

      // Specialization indicator
      if (agent.specialization !== 'generalist') {
        const specColors: Record<string, string> = {
          explorer: '#3b82f6',
          harvester: '#22c55e',
          social: '#f59e0b',
          fighter: '#ef4444'
        };
        ctx.strokeStyle = specColors[agent.specialization] || '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(agent.x, agent.y, size + 4, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Velocity vector
      const speed = Math.sqrt(agent.vx ** 2 + agent.vy ** 2);
      if (speed > 0.1) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(agent.x, agent.y);
        ctx.lineTo(agent.x + agent.vx * 5, agent.y + agent.vy * 5);
        ctx.stroke();
      }

      // Energy ring
      ctx.strokeStyle = `hsl(${agent.energy * 1.2}, 70%, 50%)`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, size + 3, 0, (agent.energy / 100) * Math.PI * 2);
      ctx.stroke();

      // Health ring (inner)
      ctx.strokeStyle = `hsl(${agent.health * 1.2}, 70%, 40%)`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, size + 6, 0, (agent.health / 100) * Math.PI * 2);
      ctx.stroke();

      // Combat cooldown indicator
      if (agent.combat_cooldown > 0) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.beginPath();
        ctx.arc(agent.x, agent.y, size, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    ctx.restore();
  }, [state, selectedAgent, showPheromones, showTrails, showCommunities, showHeatmap, drawHeatmap, drawCommunityLines]);

  const handleCanvasClick = (e: React.MouseEvent) => {
    if (!state) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / SCALE;
    const y = (e.clientY - rect.top) / SCALE;

    const clicked = state.agents.find(a => {
      const dist = Math.sqrt((a.x - x) ** 2 + (a.y - y) ** 2);
      return dist < 20 && a.health > 0;
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
    <div className="flex h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 text-white overflow-hidden">
      {/* Connection status indicator */}
      <div className="fixed top-4 left-4 z-50 flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full animate-pulse ${state ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]' : 'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.8)]'}`} />
        <span className="text-xs text-gray-400 font-medium">{state ? 'Live' : 'Disconnected'}</span>
      </div>

      {/* Tick counter */}
      {state && (
        <div className="fixed top-4 left-24 z-50 px-3 py-1 rounded-full bg-gray-800/50 backdrop-blur-md border border-gray-700/50">
          <span className="text-xs text-gray-400">Tick: </span>
          <span className="text-xs font-mono text-cyan-400">{state.tick.toLocaleString()}</span>
        </div>
      )}

      <div className="flex-1 flex items-center justify-center p-4 relative">
        {/* Background grid effect */}
        <div className="absolute inset-0 opacity-5 pointer-events-none"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
            backgroundSize: '50px 50px'
          }}
        />
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH * SCALE}
          height={CANVAS_HEIGHT * SCALE}
          onClick={handleCanvasClick}
          className="border border-gray-700/50 rounded-2xl cursor-crosshair bg-gray-950/80 shadow-2xl shadow-black/50 backdrop-blur-sm"
        />
      </div>

      <div className="w-80 p-4 bg-gray-900/90 backdrop-blur-xl border-l border-gray-700/50 overflow-y-auto shadow-2xl">
        <h1 className="text-2xl font-bold mb-6 bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent tracking-tight">
          SYNTHESIA
        </h1>

        {state?.environment && (
          <div className="mb-5 p-4 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/30 shadow-lg">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Season</h2>
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg shadow-lg ${
                state.environment.season === 'spring' && 'bg-green-500/20 text-green-400 shadow-green-500/20',
                state.environment.season === 'summer' && 'bg-yellow-500/20 text-yellow-400 shadow-yellow-500/20',
                state.environment.season === 'fall' && 'bg-orange-500/20 text-orange-400 shadow-orange-500/20',
                state.environment.season === 'winter' && 'bg-blue-500/20 text-blue-400 shadow-blue-500/20',
              }`}>
                {state.environment.season === 'spring' && '🌱'}
                {state.environment.season === 'summer' && '☀️'}
                {state.environment.season === 'fall' && '🍂'}
                {state.environment.season === 'winter' && '❄️'}
              </div>
              <span className="text-lg capitalize font-semibold text-white">
                {state.environment.season}
              </span>
            </div>
            <div className="w-full bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyan-400 to-blue-400 h-full rounded-full transition-all duration-500 shadow-[0_0_8px_rgba(34,211,238,0.5)]"
                style={{ width: `${(state.environment.season_progress || 0) * 100}%` }}
              />
            </div>
            {state.environment.catastrophe_active && (
              <div className="mt-3 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 font-semibold text-xs animate-pulse flex items-center gap-2">
                <span className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                CATASTROPHE ACTIVE
              </div>
            )}
          </div>
        )}

        <div className="space-y-3 mb-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Events</h2>
          <div className="grid grid-cols-2 gap-2">
            {[
              { cmd: 'gold_rush', label: 'Gold Rush', colors: 'from-yellow-600 to-amber-600 hover:from-yellow-500 hover:to-amber-500', icon: '💰' },
              { cmd: 'hazard_zone', label: 'Hazard Zone', colors: 'from-red-700 to-red-600 hover:from-red-600 hover:to-red-500', icon: '⚠️' },
              { cmd: 'portal_storm', label: 'Portal Storm', colors: 'from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500', icon: '🌀' },
              { cmd: 'wildfire', label: 'Wildfire', colors: 'from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500', icon: '🔥' },
              { cmd: 'flood', label: 'Flood', colors: 'from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500', icon: '🌊' },
              { cmd: 'drought', label: 'Drought', colors: 'from-amber-700 to-orange-700 hover:from-amber-600 hover:to-orange-600', icon: '🏜️' },
            ].map(({ cmd, label, colors, icon }) => (
              <button
                key={cmd}
                onClick={() => sendCommand('inject', cmd)}
                className={`px-3 py-2.5 bg-gradient-to-br ${colors} rounded-lg text-xs font-medium transition-all duration-200 hover:scale-105 hover:shadow-lg active:scale-95 flex items-center justify-center gap-1.5`}
              >
                <span>{icon}</span>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Agents</h2>
          <div className="grid grid-cols-2 gap-2">
            {[
              { cmd: 'add_agent', label: 'Add Agent', colors: 'from-blue-600 to-blue-500', icon: '👤' },
              { cmd: 'add_fighter', label: 'Add Fighter', colors: 'from-red-600 to-red-500', icon: '⚔️' },
              { cmd: 'add_explorer', label: 'Add Explorer', colors: 'from-green-600 to-green-500', icon: '🔍' },
              { cmd: 'remove_agent', label: 'Remove Agent', colors: 'from-gray-600 to-gray-500', icon: '✕' },
            ].map(({ cmd, label, colors, icon }) => (
              <button
                key={cmd}
                onClick={() => sendCommand('inject', cmd)}
                className={`px-3 py-2.5 bg-gradient-to-r ${colors} rounded-lg text-xs font-medium transition-all duration-200 hover:scale-105 hover:shadow-lg active:scale-95 flex items-center justify-center gap-1.5`}
              >
                <span>{icon}</span>
                <span>{label}</span>
              </button>
            ))}
          </div>
          <button
            onClick={() => sendCommand('reset')}
            className="w-full px-4 py-3 bg-gray-700/50 hover:bg-gray-600/50 border border-gray-600/30 rounded-lg text-xs font-medium transition-all duration-200 hover:border-gray-500/50 flex items-center justify-center gap-2 group"
          >
            <span className="group-hover:rotate-180 transition-transform duration-300">🔄</span>
            Reset Simulation
          </button>
        </div>

        <div className="space-y-3 mb-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Visualization</h2>
          <div className="grid grid-cols-2 gap-2">
            {[
              { state: showPheromones, set: setShowPheromones, label: 'Pheromones', color: 'yellow' },
              { state: showTrails, set: setShowTrails, label: 'Trails', color: 'blue' },
              { state: showCommunities, set: setShowCommunities, label: 'Communities', color: 'pink' },
              { state: showHeatmap, set: setShowHeatmap, label: 'Heatmap', color: 'red' },
            ].map(({ state: checked, set, label, color }) => (
              <label key={label} className="flex items-center gap-2 p-2 rounded-lg bg-gray-800/30 border border-gray-700/30 cursor-pointer hover:bg-gray-700/30 transition-colors">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => set(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className={`w-9 h-5 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-${color}-500`}
                  />
                </div>
                <span className="text-xs text-gray-300">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {state?.metrics && (
          <div className="mb-6 p-4 bg-gray-800/30 backdrop-blur-sm rounded-xl border border-gray-700/30">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse" />
              Emergent Metrics
            </h2>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {[
                { label: 'Agents', value: state.metrics.agent_count, color: 'text-white' },
                { label: 'Communities', value: state.metrics.communities, color: 'text-green-400' },
                { label: 'Largest Cluster', value: state.metrics.largest_community, color: 'text-cyan-400' },
                { label: 'Entropy', value: state.metrics.knowledge_entropy.toFixed(2), color: 'text-purple-400' },
                { label: 'Exploration', value: state.metrics.avg_exploration.toFixed(2), color: 'text-blue-400' },
                { label: 'Aggression', value: (state.metrics.avg_aggression || 0).toFixed(2), color: (state.metrics.avg_aggression || 0) > 0.5 ? 'text-red-400' : 'text-green-400' },
                { label: 'Energy', value: (state.metrics.avg_energy || 0).toFixed(1), color: 'text-yellow-400' },
                { label: 'Health', value: (state.metrics.avg_health || 0).toFixed(1), color: 'text-emerald-400' },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex flex-col p-2 bg-gray-700/30 rounded-lg">
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</span>
                  <span className={`font-mono text-sm ${color}`}>{value}</span>
                </div>
              ))}
            </div>

            {state.metrics.specializations && Object.keys(state.metrics.specializations).length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-700/30">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Specializations</div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(state.metrics.specializations).map(([spec, count]) => (
                    <span
                      key={spec}
                      className="px-2.5 py-1 bg-gradient-to-r from-gray-700/50 to-gray-600/30 border border-gray-600/30 rounded-md text-[10px] capitalize font-medium text-gray-300 shadow-sm"
                    >
                      {spec}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {state?.environment && (
          <div className="mb-6 p-4 bg-gray-800/30 backdrop-blur-sm rounded-xl border border-gray-700/30">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Environment</h2>
            <div className="space-y-2">
              {[
                { label: 'Nodes', value: state.environment.node_count, icon: '📍' },
                { label: 'Total Value', value: Math.round(state.environment.total_value), icon: '💎' },
                { label: 'Pheromones', value: state.environment.pheromone_trails, icon: '✨' },
              ].map(({ label, value, icon }) => (
                <div key={label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <span>{icon}</span>
                    <span>{label}</span>
                  </div>
                  <span className="font-mono text-sm text-white">{value}</span>
                </div>
              ))}
              {state.environment.by_type && (
                <div className="mt-3 pt-3 border-t border-gray-700/30 grid grid-cols-2 gap-x-2 gap-y-1">
                  {Object.entries(state.environment.by_type).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-xs">
                      <span className="text-gray-500 capitalize">{type}:</span>
                      <span className="font-mono text-gray-300">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {selectedAgentData && selectedAgentData.health > 0 && (
          <div className="p-4 bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-md rounded-xl border border-cyan-500/30 shadow-lg shadow-cyan-500/10">
            <h2 className="text-sm font-bold text-cyan-400 mb-3 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center text-xs">👤</span>
              Agent {selectedAgentData.id.slice(0, 8)}
            </h2>
            <div className="space-y-3">
              <div className="flex items-center gap-2 p-2 bg-gray-700/30 rounded-lg">
                <span className="text-xs text-gray-400">Action:</span>
                <span className="text-xs font-medium text-cyan-300 px-2 py-0.5 bg-cyan-500/20 rounded">{selectedAgentData.action}</span>
              </div>
              <div className="text-xs text-gray-400 italic truncate" title={selectedAgentData.reason}>
                "{selectedAgentData.reason}"
              </div>

              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Energy', value: Math.round(selectedAgentData.energy), color: 'yellow' },
                  { label: 'Health', value: Math.round(selectedAgentData.health), color: 'red' },
                  { label: 'Curiosity', value: Math.round(selectedAgentData.curiosity), color: 'purple' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="p-2 bg-gray-700/30 rounded-lg text-center">
                    <div className="text-[10px] text-gray-500 uppercase">{label}</div>
                    <div className={`font-mono text-sm text-${color}-400`}>{value}</div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Reputation: <span className="text-white font-mono">{Math.round(selectedAgentData.reputation)}</span></span>
                <span className="text-gray-400">Memories: <span className="text-white font-mono">{selectedAgentData.memory_count}</span></span>
              </div>

              <div className="pt-3 border-t border-gray-700/30 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">Spec:</span>
                  <span className="text-xs font-medium text-purple-300 capitalize px-2 py-0.5 bg-purple-500/20 rounded">
                    {selectedAgentData.specialization}
                  </span>
                </div>

                {[
                  { label: 'Exploration', value: selectedAgentData.strategy.exploration, color: 'blue' },
                  { label: 'Sociability', value: selectedAgentData.strategy.sociability, color: 'green' },
                  { label: 'Aggression', value: selectedAgentData.strategy.aggression, color: 'red' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="space-y-1">
                    <div className="flex justify-between text-[10px] text-gray-500">
                      <span>{label}</span>
                      <span className={`text-${color}-400 font-mono`}>{(value * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`bg-${color}-500 h-full rounded-full transition-all duration-300`}
                        style={{ width: `${value * 100}%` }}
                      />
                    </div>
                  </div>
                ))}

                {selectedAgentData.combat_cooldown > 0 && (
                  <div className="flex items-center gap-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-xs text-red-400">Cooldown: {selectedAgentData.combat_cooldown} ticks</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
