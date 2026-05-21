# SYNTHESIA

Emergent Knowledge Ecosystem — A living AI system where autonomous agents forage for insights, form communities, and evolve strategies through local interactions.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)

## Quick Start

### Backend
```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

---

## Deployment

### Option 1: Docker Compose (Local / VPS)

```bash
cp .env.example .env   # edit as needed
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws/simulation

### Option 2: Render (Free Tier)

1. Push your repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New > Blueprint** and connect your repo
4. Render auto-detects `render.yaml` and deploys

> The free tier supports WebSockets and is sufficient for this app.

### Option 3: Fly.io

```bash
# Install flyctl: https://fly.io/docs/getting-started/installing-flyctl/
fly auth login
fly launch --config fly.toml
fly deploy
```

### Option 4: Railway

1. Push your repo to GitHub
2. Go to [Railway](https://railway.app) and create a new project
3. Connect your repo — Railway auto-detects the `Dockerfile`
4. Set the port to `80` in the service settings

### Option 5: Any VPS (DigitalOcean, AWS EC2, etc.)

```bash
# On your server
git clone <your-repo-url>
cd synthesia
docker build -t synthesia .
docker run -d -p 80:80 --name synthesia synthesia
```

### Individual Docker Images

```bash
# Backend only
docker build -f Dockerfile.backend -t synthesia-backend .
docker run -p 8000:8000 synthesia-backend

# Frontend only
docker build -f Dockerfile.frontend -t synthesia-frontend .
docker run -p 3000:80 synthesia-frontend
```

---

## Configuration

All settings can be configured via environment variables:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Backend server port |
| `NUM_AGENTS` | `30` | Number of simulation agents |
| `MAX_FPS` | `30` | Simulation update rate |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING) |
| `VITE_WS_URL` | *(auto)* | WebSocket URL override (build-time) |

Copy `.env.example` to `.env` to customize.

---

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
- **Deployment**: Docker + Nginx + Supervisor

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
