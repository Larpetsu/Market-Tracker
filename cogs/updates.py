import discord
from discord import app_commands
from discord.ext import commands
import logging

from database import MarketDB
from config import UPDATE_INTERVAL_HOURS, MAX_TICKERS_PER_USER, COLOR_NEUTRAL, BRAND_NAME

logger = logging.getLogger("markets_bot")


class UpdatesCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: MarketDB):
        self.bot = bot
        self.db = db

    @app_commands.command(name="subscribe", description="Enable automatic market updates via DM")
    async def subscribe(self, interaction: discord.Interaction):
        if self.db.is_subscribed(interaction.user.id):
            return await interaction.response.send_message("🔔 You're already subscribed.", ephemeral=True)

        self.db.toggle_subscription(interaction.user.id, True)
        await interaction.response.send_message(
            f"✅ Subscribed! You'll get a DM update every {UPDATE_INTERVAL_HOURS} hours for stocks on your watchlist.\n"
            f"Make sure your DMs are open, and add stocks with `/track` if you haven't yet."
        )
        logger.info(f"User {interaction.user.id} enabled updates")

    @app_commands.command(name="unsubscribe", description="Disable automatic market updates")
    async def unsubscribe(self, interaction: discord.Interaction):
        if not self.db.is_subscribed(interaction.user.id):
            return await interaction.response.send_message("🔕 You're not subscribed.", ephemeral=True)

        self.db.toggle_subscription(interaction.user.id, False)
        await interaction.response.send_message("🔇 Updates paused. Use `/subscribe` to opt back in.")
        logger.info(f"User {interaction.user.id} disabled updates")

    @app_commands.command(name="status", description="Check your subscription and watchlist status")
    async def check_status(self, interaction: discord.Interaction):
        sub_status = "🔔 Active" if self.db.is_subscribed(interaction.user.id) else "🔕 Paused"
        watchlist_count = self.db.count_tracked(interaction.user.id)

        embed = discord.Embed(title="Your Status", color=COLOR_NEUTRAL)
        embed.add_field(name="Updates", value=sub_status, inline=True)
        embed.add_field(name="Tracked Stocks", value=f"{watchlist_count}/{MAX_TICKERS_PER_USER}", inline=True)
        embed.set_footer(text=BRAND_NAME)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="See everything Markets Bot can do")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"📈 {BRAND_NAME}",
            description="Track stocks, check prices, and get periodic DM updates.",
            color=COLOR_NEUTRAL,
        )
        embed.add_field(
            name="Watchlist",
            value=(
                "`/track <ticker> [exchange]` — add a stock\n"
                "`/untrack <ticker>` — remove a stock\n"
                "`/watchlist` — view live prices for everything you track"
            ),
            inline=False,
        )
        embed.add_field(
            name="Quick lookup",
            value="`/price <ticker> [exchange]` — check a price without saving it",
            inline=False,
        )
        embed.add_field(
            name="DM updates",
            value=(
                "`/subscribe` — get a DM every "
                f"{UPDATE_INTERVAL_HOURS}h with prices for your watchlist\n"
                "`/unsubscribe` — turn that off\n"
                "`/status` — check your current settings"
            ),
            inline=False,
        )
        embed.set_footer(text="Tip: leave [exchange] blank for US tickers like AAPL or TSLA.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UpdatesCog(bot, bot.db))
