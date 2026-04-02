from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time

from engine import SynthesiaEngine

app = FastAPI(title="SYNTHESIA API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
engine = SynthesiaEngine(num_agents=30)

@app.websocket("/ws/simulation")
async def simulation_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time simulation"""
    await websocket.accept()
    print("Client connected to simulation")

    async def send_state(state):
        await websocket.send_json(state)

    # Set callback for engine
    engine.callback = send_state

    # Run engine in background
    task = asyncio.create_task(engine.run(fps=30))

    try:
        while True:
            # Receive commands from frontend
            message = await websocket.receive_text()
            try:
                data = json.loads(message)
                if data.get('action') == 'inject':
                    engine.inject_event(data.get('event'), data.get('data'))
                elif data.get('action') == 'reset':
                    global engine
                    engine = SynthesiaEngine(num_agents=data.get('agents', 30))
                    engine.callback = send_state
                    task.cancel()
                    task = asyncio.create_task(engine.run(fps=30))
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        engine.running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        print("Client disconnected")

@app.get("/health")
def health():
    return {"status": "ok", "simulation_running": engine.running}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
