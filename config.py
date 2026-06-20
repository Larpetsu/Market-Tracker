import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN: str = os.getenv("DISCORD_TOKEN")
if not BOT_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")

DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./markets.db")

# Scheduler & Update Settings
UPDATE_INTERVAL_HOURS: int = 3
MAX_RETRIES: int = 3
REQUEST_TIMEOUT: int = 15

# Feature Flags
ENABLE_LOGGING: bool = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
