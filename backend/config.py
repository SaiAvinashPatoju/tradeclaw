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
