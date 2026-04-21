import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or "0")

CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

REQUIRED_CHANNELS = [
    c.strip() for c in os.environ.get("REQUIRED_CHANNELS", "").split(",") if c.strip()
]

NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")

POST_INTERVAL_MINUTES = int(os.environ.get("POST_INTERVAL_MINUTES", "5"))
POSTS_PER_BATCH = int(os.environ.get("POSTS_PER_BATCH", "10"))

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
PORT = int(os.environ.get("PORT", "8080"))


def get_public_url() -> str:
    if WEBHOOK_URL:
        return WEBHOOK_URL.rstrip("/")
    if RENDER_EXTERNAL_URL:
        return RENDER_EXTERNAL_URL.rstrip("/")
    return ""
