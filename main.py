import discord
from discord.ext import commands, app_commands
from config import BOT_TOKEN
from database import MarketDB
from background_jobs import start_scheduler
import logging
import sys

if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger("markets_bot")

    intents = discord.Intents.default()
    intents.message_content = False  # We only use slash commands & DMs
    
    bot = commands.Bot(
        command_prefix="!",
        intents=intents,
        help_command=None,
        activity=discord.Game(name="/track AAPL | Markets Dashboard")
    )

    db = MarketDB()

    @bot.event
    async def on_ready():
        logger.info(f"✅ Logged in as {bot.user} ({bot.user.id})")
        
        # Sync slash commands globally
        synced = await app_commands.AppCommandTree(bot).sync()
        logger.info(f"Synced {len(synced)} commands globally.")

        # Start background scheduler
        start_scheduler(db, bot)

    @bot.event
    async def on_app_command_error(interaction, error):
        if isinstance(error, app_commands.CommandNotFound):
            return
        if interaction:
            await interaction.response.send_message("⚠️ An error occurred while processing your command. Please try again.", ephemeral=True)
        logger.error(f"Command error: {error}")

    # Load extensions
    import cogs.tracking as tracking_cog
    import cogs.updates as updates_cog
    
    tracking_cog.setup(bot, db)
    updates_cog.setup(bot, db)

    bot.run(BOT_TOKEN)
