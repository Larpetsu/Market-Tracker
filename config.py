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

# Usage limits
MAX_TICKERS_PER_USER: int = 15  # keeps watchlist commands fast and yfinance happy

# Feature Flags
ENABLE_LOGGING: bool = os.getenv("ENABLE_LOGGING", "true").lower() == "true"

# Branding (used for embeds across cogs)
BRAND_NAME: str = "Markets Bot"
COLOR_UP: int = 0x2ECC71
COLOR_DOWN: int = 0xE74C3C
COLOR_NEUTRAL: int = 0x5865F2  # Discord blurple, used for non price embeds
