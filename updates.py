import discord
from discord.app_commands import CommandInteraction
from discord.ext import commands, app_commands
from database import MarketDB
import logging

logger = logging.getLogger("markets_bot")

class UpdatesCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: MarketDB):
        self.bot = bot
        self.db = db

    @app_commands.command(name="subscribe", description="Enable 3-hour market updates via DM")
    async def subscribe(self, interaction: CommandInteraction):
        if self.db.is_subscribed(interaction.user.id):
            return await interaction.response.send_message("🔔 You are already subscribed to updates.", ephemeral=True)
        
        self.db.toggle_subscription(interaction.user.id, True)
        await interaction.response.send_message("✅ Subscribed! You will now receive market updates every 3 hours.")
        logger.info(f"User {interaction.user.id} enabled updates")

    @app_commands.command(name="unsubscribe", description="Disable automatic market updates")
    async def unsubscribe(self, interaction: CommandInteraction):
        if not self.db.is_subscribed(interaction.user.id):
            return await interaction.response.send_message("🔕 You are not subscribed to updates.", ephemeral=True)
        
        self.db.toggle_subscription(interaction.user.id, False)
        await interaction.response.send_message("🔇 Updates have been paused. Use `/subscribe` to opt back in.")
        logger.info(f"User {interaction.user.id} disabled updates")

    @app_commands.command(name="status", description="Check your subscription & tracking status")
    async def check_status(self, interaction: CommandInteraction):
        sub_status = "🔔 Active" if self.db.is_subscribed(interaction.user.id) else "🔕 Paused"
        tickers = self.db.get_user_tracking(interaction.user.id)
        watchlist_count = len(tickers)
        
        await interaction.response.send_message(
            f"📈 **Update Status:** {sub_status}\n"
            f"📋 **Tracked Stocks:** {watchlist_count}\n"
            f"💡 Use `/subscribe` or `/unsubscribe` to change updates."
        )

def setup(bot: commands.Bot, db: MarketDB):
    bot.add_cog(UpdatesCog(bot, db))
