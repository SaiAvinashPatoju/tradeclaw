"""
TradeClaw — FastAPI Application Entry Point
Runs the backend server with all routes, scheduler, FCM, and database initialization.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .fcm import init_fcm
from .scheduler import start_scheduler, stop_scheduler
from .routes.signals import router as signals_router
from .routes.health import router as health_router
from .routes.export import router as export_router

# ── Logging Setup ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tradeclaw")


# ── Lifespan (Startup/Shutdown) ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    # Startup
    logger.info("🦀 TradeClaw starting up...")
    await init_db()
    logger.info("Database initialized")

    init_fcm()

    start_scheduler()
    logger.info("All systems go!")

    yield

    # Shutdown
    logger.info("TradeClaw shutting down...")
    stop_scheduler()
    logger.info("Goodbye 🦀")


# ── App Creation ─────────────────────────────────────────────────────
app = FastAPI(
    title="TradeClaw API",
    description="Crypto momentum signal engine",
    version="1.0.0-beta",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────
app.include_router(signals_router)
app.include_router(health_router)
app.include_router(export_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint — simple welcome message."""
    return {
        "app": "TradeClaw",
        "version": "1.0.0-beta",
        "docs": "/docs",
    }
