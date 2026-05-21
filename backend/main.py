import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time

from engine import SynthesiaEngine

# Configuration from environment
PORT = int(os.environ.get("PORT", 8000))
NUM_AGENTS = int(os.environ.get("NUM_AGENTS", 30))
MAX_FPS = int(os.environ.get("MAX_FPS", 30))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Logging setup
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("synthesia")

app = FastAPI(title="SYNTHESIA API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
engine = SynthesiaEngine(num_agents=NUM_AGENTS)

@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("  SYNTHESIA Engine Starting")
    logger.info(f"  Port: {PORT}")
    logger.info(f"  Agents: {NUM_AGENTS}")
    logger.info(f"  Target FPS: {MAX_FPS}")
    logger.info("=" * 50)

@app.websocket("/ws/simulation")
async def simulation_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time simulation"""
    global engine
    await websocket.accept()
    logger.info("Client connected to simulation")

    async def send_state(state):
        await websocket.send_json(state)

    # Set callback for engine
    engine.callback = send_state

    # Run engine in background
    task = asyncio.create_task(engine.run(fps=MAX_FPS))

    try:
        while True:
            # Receive commands from frontend
            message = await websocket.receive_text()
            try:
                data = json.loads(message)
                if data.get('action') == 'inject':
                    engine.inject_event(data.get('event'), data.get('data'))
                    logger.info(f"Event injected: {data.get('event')}")
                elif data.get('action') == 'reset':
                    agent_count = data.get('agents', NUM_AGENTS)
                    engine = SynthesiaEngine(num_agents=agent_count)
                    engine.callback = send_state
                    task.cancel()
                    task = asyncio.create_task(engine.run(fps=MAX_FPS))
                    logger.info(f"Simulation reset with {agent_count} agents")
            except json.JSONDecodeError:
                pass
    except Exception as e:
        logger.warning(f"WebSocket disconnected: {e}")
    finally:
        engine.running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.info("Client disconnected")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "simulation_running": engine.running,
        "tick": engine.tick,
        "agents": len(engine.agents),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

