"""Zectrix plugin configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[5]
DATA_DIR = PROJECT_ROOT / "data" / "zectrix"
TOKEN_PATH = DATA_DIR / "tokens" / "google_token.json"
SYNC_STATE_PATH = DATA_DIR / "synced_events" / "sync_state.json"

# API config
ZECTRIX_BASE_URL = "https://cloud.zectrix.com/open/v1"
ZECTRIX_API_KEY = os.getenv("ZECTRIX_API_KEY", "")
ZECTRIX_DEVICE_ID = os.getenv("ZECTRIX_DEVICE_ID", "")

# Google Calendar OAuth
GOOGLE_CLIENT_ID = os.getenv("ZECTRIX_GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("ZECTRIX_GOOGLE_CLIENT_SECRET", "")
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Sync settings
SYNC_DAYS_AHEAD = 30


def ensure_data_dirs() -> None:
    """Create data directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "tokens").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "synced_events").mkdir(parents=True, exist_ok=True)
