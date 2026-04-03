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

## Deployment

### Docker Compose (Recommended)
```bash
cd synthesia
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws/simulation

### Individual Docker Images
```bash
# Build and run backend
docker build -f Dockerfile.backend -t synthesia-backend .
docker run -p 8000:8000 synthesia-backend

# Build and run frontend
docker build -f Dockerfile.frontend -t synthesia-frontend .
docker run -p 3000:80 synthesia-frontend
```

### Production Deployment

For production deployment, set these environment variables:

```bash
# Backend
export PORT=8000
export NUM_AGENTS=50
export MAX_FPS=60

# Frontend
export VITE_API_URL=ws://your-server:8000
```

## Features

- **Multi-agent decentralized intelligence**: 30+ autonomous agents with unique strategies
- **Dual-memory architecture**: Short-term + long-term memory per agent
- **Emergent communities**: Agents naturally cluster without explicit grouping
- **Adaptive evolution**: Successful strategies propagate through the population
- **Seasonal system**: Dynamic environment with spring, summer, fall, winter cycles
- **Catastrophes**: Wildfires, floods, droughts that affect the ecosystem
- **Combat system**: Aggressive agents can attack others for resources
- **Specialization**: Agents evolve into explorers, harvesters, fighters, or social agents
- **Special nodes**: Hazards, portals, and mystery nodes
- **Real-time visualization**: Interactive canvas with trails, pheromones, and metrics

## Architecture

- **Backend**: Python + FastAPI + WebSocket
- **Engine**: Custom simulation with spatial hash indexing
- **Frontend**: React + TypeScript + HTML5 Canvas
- **State**: Zustand for real-time synchronization
- **Deployment**: Docker + Docker Compose

## Events

### Available Events
- **Gold Rush**: Spawn high-value nodes
- **Hazard Zone**: Spawn dangerous areas
- **Portal Storm**: Create teleportation portals
- **Wildfire**: Spreading fire catastrophe
- **Flood**: Large area flooding
- **Drought**: Reduces all node values

### Agent Types
- **Regular Agent**: Balanced exploration/sociability
- **Fighter**: High aggression, seeks combat
- **Explorer**: High exploration, wanders more

## Demo

1. Watch agents explore and form clusters naturally
2. Click "Inject Gold Rush" to see information cascades
3. Trigger "Wildfire" to observe ecosystem response
4. Click any agent to see its specialization, health, energy
5. Observe emergent metrics: communities, entropy, specializations

## Performance Optimizations

- **Spatial Hashing**: O(1) neighbor queries vs O(n) linear search
- **Batch Processing**: Agents processed in batches for smoother FPS
- **Metric Caching**: Expensive calculations cached every 10 ticks
- **Memory Sampling**: Metrics use agent sampling for large populations

## License

MIT
