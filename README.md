# SYNTHESIA

Emergent Knowledge Ecosystem - A living AI system where autonomous agents forage for insights, form communities, and evolve strategies through local interactions.

## Quick Start

### Backend
```bash
cd synthesia/backend
pip install -r ../requirements.txt
python main.py
```

### Frontend
```bash
cd synthesia/frontend
npm install
npm run dev
```

Open http://localhost:3000

## Features

- **Multi-agent decentralized intelligence**: 30+ autonomous agents with unique strategies
- **Dual-memory architecture**: Short-term + long-term memory per agent
- **Emergent communities**: Agents naturally cluster without explicit grouping
- **Adaptive evolution**: Successful strategies propagate through the population
- **Real-time visualization**: Interactive canvas with trails, pheromones, and metrics

## Architecture

- **Backend**: Python + FastAPI + WebSocket
- **Engine**: Custom simulation with KD-tree spatial indexing
- **Frontend**: React + TypeScript + HTML5 Canvas
- **State**: Zustand for real-time synchronization

## Demo

1. Watch agents explore and form clusters naturally
2. Click "Inject Gold Rush" to see information cascades
3. Click any agent to see its decision trace and memory
4. Observe emergent metrics: communities, entropy, evolution

## License

MIT
