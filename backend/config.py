import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

BINANCE_API_KEY = (os.getenv("BINANCE_API_KEY") or "").strip()
BINANCE_API_SECRET = (os.getenv("BINANCE_API_SECRET") or "").strip()
DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
FCM_PROJECT_ID = (os.getenv("FCM_PROJECT_ID") or "").strip()

if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    raise ValueError("Missing Binance API keys in environment.")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in environment.")

if not FCM_PROJECT_ID:
    raise ValueError("Missing FCM_PROJECT_ID in environment.")

# ── Optional / security-related settings ──────────────────────────────
# Comma-separated list of allowed CORS origins (defaults to localhost dev ports).
ALLOWED_ORIGINS_RAW = (os.getenv("ALLOWED_ORIGINS") or "http://localhost:3000,http://localhost:8081").strip()
ALLOWED_ORIGINS: list[str] = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()]

# Admin API key — when set, required as X-API-Key header on write/admin endpoints.
# Leave empty to disable enforcement (development only).
TRADECLAW_API_KEY = (os.getenv("TRADECLAW_API_KEY") or "").strip()

# Path to Firebase service account JSON. Can be absolute or relative to project root.
_default_sa_path = str(Path(__file__).resolve().parent.parent / "firebase-service-account.json")
FIREBASE_SERVICE_ACCOUNT_PATH = (os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH") or _default_sa_path).strip()
