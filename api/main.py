"""
FastAPI Main Application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import logging

from api.investigations import router as investigations_router
from api.config_api import router as config_router
from api.demo import router as demo_router
from api.ai import router as ai_router
from api.websocket import ConnectionManager
from agent.main import PROCSeeAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
agent: PROCSeeAgent = None

# WebSocket manager
ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global agent
    
    # Startup
    logger.info("🚀 Starting SentinelX API...")
    try:
        agent = PROCSeeAgent()
        await agent.initialize()
        await agent.start()
        logger.info("✅ SentinelX API ready")
    except Exception as e:
        # Do not crash: demo endpoints and the dashboard must still work
        logger.error(f"Agent failed to start - running in degraded/demo mode: {e}", exc_info=True)
        agent = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down SentinelX API...")
    if agent:
        try:
            await agent.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="SentinelX API",
    description="SentinelX - AI-assisted endpoint investigation (prototype, built on PROCSee)",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root"""
    return {
        "name": "SentinelX API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if agent:
        health = await agent.health_check()
        return {
            "status": "healthy",
            "agent": health
        }
    return {"status": "degraded", "mode": "demo"}


# WebSocket endpoint
@app.websocket("/ws/investigations")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time investigation updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# Include routers
app.include_router(investigations_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(ai_router, prefix="/api")


def main():
    """Run API server"""
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to prevent hanging
        log_level="info"
    )


if __name__ == "__main__":
    main()
