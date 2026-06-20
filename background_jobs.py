import discord
from database import MarketDB
from stock_fetcher import fetch_market_data
from config import UPDATE_INTERVAL_HOURS
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("markets_bot")
scheduler = AsyncIOScheduler()

async def check_and_notify(db: MarketDB):
    subscribers = db.get_subscribers()
    if not subscribers:
        return

    logger.info(f"Running market check for {len(subscribers)} subscribers...")
    
    for user_id, ticker, exchange in subscribers:
        try:
            data = await fetch_market_data(ticker, exchange)
            if not data:
                continue

            embed = discord.Embed(
                title=f"📈 {data['name']} ({data['ticker']})",
                color=0x27ae60 if data['change'] >= 0 else 0xc0392b,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Price", value=f"{data['currency']} {data['price']:,.2f}", inline=True)
            embed.add_field(name="Change", value=f"{data['change']:+.2f} ({data['percent']:+.1%})", inline=True)
            embed.add_field(name="Market", value=data['market_status'], inline=True)
            embed.set_footer(text="Markets Bot • Updates every 3 hours")

            user = await db.bot.fetch_user(user_id)
            if user:
                await user.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"User {user_id} has DMs disabled. Skipping.")
            db.toggle_subscription(user_id, False)  # Auto-opt out if DMs fail
        except Exception as e:
            logger.error(f"Failed to process update for user {user_id}: {e}")

def start_scheduler(db: MarketDB, bot: discord.Bot):
    db.bot = bot  # Pass bot reference for fetch_user
    scheduler.add_job(check_and_notify, 'interval', hours=UPDATE_INTERVAL_HOURS, id="market_updates")
    scheduler.start()
    logger.info(f"Scheduler started. Updates will run every {UPDATE_INTERVAL_HOURS} hour(s).")
