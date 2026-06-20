import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import logging
import re

from database import MarketDB
from stock_fetcher import fetch_market_data
from config import MAX_TICKERS_PER_USER, COLOR_UP, COLOR_DOWN, COLOR_NEUTRAL, BRAND_NAME

logger = logging.getLogger("markets_bot")

TICKER_PATTERN = re.compile(r"^[A-Z0-9.\-]{1,10}$")

EXCHANGE_CHOICES = [
    app_commands.Choice(name="US – NYSE / NASDAQ (default)", value=""),
    app_commands.Choice(name="London Stock Exchange (LSE)", value="LSE"),
    app_commands.Choice(name="Euronext Paris (PAR)", value="PAR"),
    app_commands.Choice(name="Deutsche Börse Xetra (XETRA)", value="XETRA"),
    app_commands.Choice(name="Tokyo Stock Exchange (TOK)", value="TOK"),
    app_commands.Choice(name="Hong Kong Exchange (HKEX)", value="HKEX"),
    app_commands.Choice(name="Toronto Stock Exchange (TSX)", value="TSX"),
    app_commands.Choice(name="Australian Securities Exchange (ASX)", value="ASX"),
]


def _price_embed(data: dict, *, title_prefix: str = "") -> discord.Embed:
    is_up = data["change"] >= 0
    embed = discord.Embed(
        title=f"{title_prefix}{data['name']} ({data['ticker']})",
        color=COLOR_UP if is_up else COLOR_DOWN,
        timestamp=discord.utils.utcnow(),
    )
    arrow = "▲" if is_up else "▼"
    embed.add_field(name="Price", value=f"{data['currency']} {data['price']:,.2f}", inline=True)
    embed.add_field(
        name="Change",
        value=f"{arrow} {data['change']:+.2f} ({data['percent']:+.2%})",
        inline=True,
    )
    embed.add_field(name="Market", value=data["market_status"], inline=True)
    embed.set_footer(text=BRAND_NAME)
    return embed


class TrackingCog(commands.Cog):
    """Lets users build and check a personal stock watchlist."""

    def __init__(self, bot: commands.Bot, db: MarketDB):
        self.bot = bot
        self.db = db

    @app_commands.command(name="track", description="Add a stock to your watchlist")
    @app_commands.describe(ticker="Stock symbol, e.g. AAPL", exchange="Exchange the ticker trades on")
    @app_commands.choices(exchange=EXCHANGE_CHOICES)
    @app_commands.checks.cooldown(1, 3.0)
    async def track(
        self,
        interaction: discord.Interaction,
        ticker: str,
        exchange: app_commands.Choice[str] = None,
    ):
        ticker = ticker.strip().upper()
        exch_value = exchange.value if exchange else ""

        if not TICKER_PATTERN.match(ticker):
            return await interaction.response.send_message(
                "That doesn't look like a valid ticker symbol (letters/numbers only, max 10 characters).",
                ephemeral=True,
            )

        existing = {sym for sym, _ in self.db.get_user_tracking(interaction.user.id)}
        if ticker not in existing and len(existing) >= MAX_TICKERS_PER_USER:
            return await interaction.response.send_message(
                f"You're already tracking the max of **{MAX_TICKERS_PER_USER}** stocks. "
                f"Use `/untrack` to remove one first.",
                ephemeral=True,
            )

        await interaction.response.defer(thinking=True)
        data = await fetch_market_data(ticker, exch_value)

        if not data:
            return await interaction.followup.send(
                f"Couldn't find **{ticker}**{f' on {exch_value}' if exch_value else ''}. "
                f"Double check the symbol and exchange.",
                ephemeral=True,
            )

        added = self.db.add_ticker(interaction.user.id, ticker, exch_value)
        if not added:
            return await interaction.followup.send(f"You're already tracking **{ticker}**.", ephemeral=True)

        embed = _price_embed(data, title_prefix="✅ Tracking ")
        await interaction.followup.send(embed=embed)
        logger.info(f"User {interaction.user.id} started tracking {ticker} ({exch_value or 'US'})")

    @app_commands.command(name="untrack", description="Remove a stock from your watchlist")
    @app_commands.describe(ticker="Stock symbol to remove")
    async def untrack(self, interaction: discord.Interaction, ticker: str):
        ticker = ticker.strip().upper()
        removed = self.db.remove_ticker(interaction.user.id, ticker)
        if removed:
            await interaction.response.send_message(f"🗑️ Removed **{ticker}** from your watchlist.")
        else:
            await interaction.response.send_message(f"**{ticker}** wasn't on your watchlist.", ephemeral=True)

    @untrack.autocomplete("ticker")
    async def untrack_autocomplete(self, interaction: discord.Interaction, current: str):
        tickers = [sym for sym, _ in self.db.get_user_tracking(interaction.user.id)]
        current = current.upper()
        return [
            app_commands.Choice(name=t, value=t)
            for t in tickers if current in t
        ][:25]

    @app_commands.command(name="watchlist", description="View live prices for everything on your watchlist")
    @app_commands.checks.cooldown(1, 5.0)
    async def watchlist(self, interaction: discord.Interaction):
        tracked = self.db.get_user_tracking(interaction.user.id)
        if not tracked:
            return await interaction.response.send_message(
                "Your watchlist is empty. Add one with `/track`.", ephemeral=True
            )

        await interaction.response.defer(thinking=True)
        results = await asyncio.gather(*(fetch_market_data(t, ex) for t, ex in tracked))

        rows = []
        for (ticker, _), data in zip(tracked, results):
            if data is None:
                rows.append(f"{ticker:<8} unavailable right now")
                continue
            arrow = "▲" if data["change"] >= 0 else "▼"
            rows.append(
                f"{data['ticker']:<8} {data['currency']} {data['price']:>10,.2f}  "
                f"{arrow} {data['percent']:+.2%}"
            )

        embed = discord.Embed(
            title=f"📋 {interaction.user.display_name}'s Watchlist",
            description="```\n" + "\n".join(rows) + "\n```",
            color=COLOR_NEUTRAL,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"{BRAND_NAME} • {len(tracked)}/{MAX_TICKERS_PER_USER} tracked")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="price", description="Look up a stock's price without saving it")
    @app_commands.describe(ticker="Stock symbol, e.g. AAPL", exchange="Exchange the ticker trades on")
    @app_commands.choices(exchange=EXCHANGE_CHOICES)
    @app_commands.checks.cooldown(1, 3.0)
    async def price(
        self,
        interaction: discord.Interaction,
        ticker: str,
        exchange: app_commands.Choice[str] = None,
    ):
        ticker = ticker.strip().upper()
        exch_value = exchange.value if exchange else ""

        await interaction.response.defer(thinking=True)
        data = await fetch_market_data(ticker, exch_value)

        if not data:
            return await interaction.followup.send(
                f"Couldn't find **{ticker}**{f' on {exch_value}' if exch_value else ''}.",
                ephemeral=True,
            )

        await interaction.followup.send(embed=_price_embed(data))

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Slow down a bit — try again in {error.retry_after:.1f}s.", ephemeral=True
            )
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(TrackingCog(bot, bot.db))
