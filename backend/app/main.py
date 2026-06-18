import asyncio
import os
import json
import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.core.config import settings
from app.api import api_router
from contextlib import asynccontextmanager

from app.database import engine, Base
import app.models  # noqa: F401 – registers all ORM models onto Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup (no-op if they already exist)
    Base.metadata.create_all(bind=engine)
    # Ensure evidence directory exists
    Path("/app/evidence").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="BugHunterLab API",
    version="2.0.0",
    description="Professional Bug Bounty & VAPT Platform — Scope → Recon → Testing → PoC → Report",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
# Allow the frontend dev server and Docker service name
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",
]
extra = os.getenv("ALLOWED_ORIGINS", "")
if extra:
    allowed_origins += [o.strip() for o in extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api")

# ─── Static evidence files ─────────────────────────────────────────────────────
evidence_dir = Path("/app/evidence")
evidence_dir.mkdir(parents=True, exist_ok=True)

# ─── Root health check ─────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {"name": "BugHunterLab API", "version": "2.0.0", "status": "ok"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


# ─── WebSocket: live scan log stream ───────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, target_id: int):
        await ws.accept()
        self.active.setdefault(target_id, []).append(ws)

    def disconnect(self, ws: WebSocket, target_id: int):
        if target_id in self.active:
            self.active[target_id] = [c for c in self.active[target_id] if c != ws]


manager = ConnectionManager()


@app.websocket("/ws/logs/{target_id}")
async def websocket_logs(websocket: WebSocket, target_id: int):
    await manager.connect(websocket, target_id)
    redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"target_{target_id}_updates")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                data = message["data"]
                text = data.decode("utf-8") if isinstance(data, bytes) else data
                await websocket.send_text(text)
            else:
                await asyncio.sleep(0.1)
            # Handle pings from client
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, target_id)
    except Exception:
        manager.disconnect(websocket, target_id)
    finally:
        await pubsub.unsubscribe(f"target_{target_id}_updates")
        await redis.aclose()