import discord
from discord.ext import commands
from database import MarketDB
from stock_fetcher import fetch_market_data
from config import UPDATE_INTERVAL_HOURS, COLOR_UP, COLOR_DOWN, BRAND_NAME
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("markets_bot")
scheduler = AsyncIOScheduler()


async def check_and_notify(db: MarketDB):
    subscribers = db.get_subscribers()
    if not subscribers:
        return

    logger.info(f"Running market check for {len(subscribers)} subscriber/ticker pairs...")

    for user_id, ticker, exchange in subscribers:
        try:
            data = await fetch_market_data(ticker, exchange)
            if not data:
                continue

            is_up = data["change"] >= 0
            embed = discord.Embed(
                title=f"{data['name']} ({data['ticker']})",
                color=COLOR_UP if is_up else COLOR_DOWN,
                timestamp=discord.utils.utcnow(),
            )
            arrow = "▲" if is_up else "▼"
            embed.add_field(name="Price", value=f"{data['currency']} {data['price']:,.2f}", inline=True)
            embed.add_field(name="Change", value=f"{arrow} {data['change']:+.2f} ({data['percent']:+.2%})", inline=True)
            embed.add_field(name="Market", value=data["market_status"], inline=True)
            embed.set_footer(text=f"{BRAND_NAME} • Updates every {UPDATE_INTERVAL_HOURS}h")

            user = await db.bot.fetch_user(user_id)
            if user:
                await user.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"User {user_id} has DMs disabled. Auto-unsubscribing.")
            db.toggle_subscription(user_id, False)
        except Exception as e:
            logger.error(f"Failed to process update for user {user_id}/{ticker}: {e}")


def start_scheduler(db: MarketDB, bot: commands.Bot):
    db.bot = bot  # so check_and_notify can fetch_user
    scheduler.add_job(
        check_and_notify,
        "interval",
        hours=UPDATE_INTERVAL_HOURS,
        id="market_updates",
        args=[db],          # <-- this was missing: without it, check_and_notify(db) never gets its argument
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started. Updates will run every {UPDATE_INTERVAL_HOURS} hour(s).")
