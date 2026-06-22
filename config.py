import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    print("❌ FATAL: BOT_TOKEN environment variable is not set.")
    print("   Set it in .env or via Railway dashboard.")
    sys.exit(1)

# ── PostgreSQL ────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    print("❌ FATAL: DATABASE_URL environment variable is not set.")
    print("   Railway PostgreSQL plugin must be linked and DATABASE_URL injected.")
    print("   If using Railway: ensure the PostgreSQL plugin is attached to this service.")
    sys.exit(1)

# ── Broadcast ──────────────────────────────────────────────────────────────────
_raw_ids = os.getenv("BROADCAST_ADMIN_IDS", "")
BROADCAST_ADMIN_IDS: set[int] = {
    int(x.strip()) for x in _raw_ids.split(",") if x.strip().lstrip("-").isdigit()
}

# ── Application ────────────────────────────────────────────────────────────────
LOG_LEVEL: str            = os.getenv("LOG_LEVEL", "INFO").upper()
TZ: str                   = os.getenv("TZ", "UTC")
MAX_CONCURRENT_TASKS: int = int(os.getenv("MAX_CONCURRENT_TASKS", "2"))
START_FROM_LATEST: bool   = os.getenv("START_FROM_LATEST", "true").lower() == "true"

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.info(
    "Configuration loaded | LOG_LEVEL=%s TZ=%s MAX_CONCURRENT_TASKS=%d START_FROM_LATEST=%s",
    LOG_LEVEL, TZ, MAX_CONCURRENT_TASKS, START_FROM_LATEST,
)
