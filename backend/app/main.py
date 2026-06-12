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
import app.models

Base.metadata.create_all(bind=engine)

# Mock import for fastapi_limiter (must be in requirements)
# from fastapi_limiter import FastAPILimiter
# from fastapi_limiter.depends import RateLimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # redis_conn = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
    # await FastAPILimiter.init(redis_conn)
    yield
    # await redis_conn.close()

app = FastAPI(title="BugHunterLab V2 API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
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