"""FastAPI application entry point for Bukhari Sales."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routers import webhook, conversations, products, settings, demo, orders
from app.routers import telegram as telegram_router
from app.services import telegram_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("🚀 Starting Bukhari Sales API...")
    await init_db()
    logger.info("✅ Database initialized")

    # Start Telegram bot (polling in background)
    await telegram_bot.start_bot(_settings.telegram_bot_token)

    yield

    # Graceful shutdown
    await telegram_bot.stop_bot()
    logger.info("🛑 Shutting down Bukhari Sales API...")


app = FastAPI(
    title="Bukhari Sales — AI Sales Assistant",
    description="AI-powered sales bot with Telegram + Instagram support, powered by LangChain + OpenAI",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow Svelte frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(webhook.router)
app.include_router(conversations.router)
app.include_router(products.router)
app.include_router(settings.router)
app.include_router(demo.router)
app.include_router(orders.router)
app.include_router(telegram_router.router)


# WebSocket endpoint for real-time dashboard updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    webhook.ws_clients.add(websocket)
    logger.info("WebSocket client connected (%d total)", len(webhook.ws_clients))
    try:
        while True:
            # Keep connection alive — wait for messages (used for ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        webhook.ws_clients.discard(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(webhook.ws_clients))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "bukhari-sales", "version": "2.0.0"}
