import asyncio
import os
import json
import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router
from contextlib import asynccontextmanager

from app.database import engine, Base
import app.models  # noqa: F401 – registers all ORM models onto Base.metadata

# NOTE: create_all is called in lifespan so it runs after CORS middleware is registered,
# ensuring error responses still include CORS headers.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (no-op if they already exist)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="BugHunterLab V2 API", version="2.0.0", lifespan=lifespan)

# CORS must be added BEFORE including routers so it wraps all responses,
# including 4xx/5xx error responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api") # Add dependencies=[Depends(RateLimiter(times=10, seconds=60))] for global rate limit

@app.get("/")
def root():
    return {"name": "BugHunterLab V2 API", "status": "ok"}

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/logs/{target_id}")
async def websocket_endpoint(websocket: WebSocket, target_id: int):
    await manager.connect(websocket)
    
    # Connect to Redis
    redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"target_{target_id}_updates")
    
    try:
        while True:
            # Poll redis for new messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                await websocket.send_text(message["data"].decode("utf-8"))
            else:
                # Need to give control back to the event loop
                await asyncio.sleep(0.1)
                
            # Check if client sent any message (e.g. ping)
            # This is optional but good for keeping connection alive
            try:
                # use a very small timeout for receive
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
            except asyncio.TimeoutError:
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await pubsub.unsubscribe(f"target_{target_id}_updates")
        await redis.close()
    except Exception as e:
        manager.disconnect(websocket)
        await pubsub.unsubscribe(f"target_{target_id}_updates")
        await redis.close()