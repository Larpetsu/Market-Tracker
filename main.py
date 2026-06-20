import discord
from discord.ext import commands
from discord import app_commands
import logging
import sys

from config import BOT_TOKEN
from database import MarketDB
from background_jobs import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("markets_bot")

EXTENSIONS = ("cogs.tracking", "cogs.updates")


class MarketsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False  # we only use slash commands & DMs, no privileged intents needed
        super().__init__(
            command_prefix="!",  # unused, slash commands only, but discord.py requires a value
            intents=intents,
            help_command=None,
            activity=discord.Game(name="/track AAPL | Markets Dashboard"),
        )
        self.db = MarketDB()

    async def setup_hook(self):
        # Cogs are loaded here (the recommended discord.py 2.x lifecycle hook)
        # rather than before bot.run(), so add_cog can be awaited properly.
        for ext in EXTENSIONS:
            await self.load_extension(ext)
            logger.info(f"Loaded extension: {ext}")

        # Re-syncing on every boot is fine for a small personal bot. For a bot
        # in many servers you'd only call this when commands actually change,
        # to avoid Discord's global command rate limit.
        synced = await self.tree.sync()
        logger.info(f"Synced {len(synced)} commands globally.")

        start_scheduler(self.db, self)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} ({self.user.id})")

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandNotFound):
            return
        if isinstance(error, app_commands.CommandOnCooldown):
            return  # handled per-cog; this is a fallback for commands without their own handler
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "⚠️ Something went wrong running that command. Try again in a moment.", ephemeral=True
            )
        logger.error(f"Command error in /{interaction.command.name if interaction.command else '?'}: {error}")


if __name__ == "__main__":
    bot = MarketsBot()
    bot.run(BOT_TOKEN)
