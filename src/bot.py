import argparse
import asyncio
import logging
import sys
import time

import discord
from discord.ext import commands
from pretty_help import PrettyHelp

from src.config import (
    APPLICATION_ID,
    DISCORD_TOKEN,
    GUILD_ID,
    HEALTHCHECK_ENABLED,
    HEALTHCHECK_PORT,
    require_token,
)
from src.utils.health import make_status_func, start_health_server
from src.utils.logger import setup_logging


async def load_cogs(bot: commands.Bot) -> None:
    logger = logging.getLogger("Aethor")
    for ext in (
        "src.cogs.general",
        "src.cogs.admin",
        "src.cogs.minecraft",
        "src.cogs.management",
        "src.cogs.onboarding",
        "src.cogs.moderation",
    ):
        try:
            await bot.load_extension(ext)
            logger.info(f"Loaded cog {ext}")
        except Exception as e:
            logger.exception(f"Failed to load {ext}: {e}")


class AethorBot(commands.Bot):
    async def setup_hook(self) -> None:
        await load_cogs(self)
        # Start healthcheck server after cogs load
        if HEALTHCHECK_ENABLED:
            started_at = getattr(self, "_started_at", time.time())
            self._started_at = started_at
            try:
                start_health_server(HEALTHCHECK_PORT, make_status_func(self, started_at))
                logging.getLogger("Aethor").info(f"Healthcheck server listening on :{HEALTHCHECK_PORT}")
            except Exception as e:
                logging.getLogger("Aethor").warning(f"Failed to start healthcheck server: {e}")


def build_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True  # for prefix commands
    bot = AethorBot(command_prefix="!", intents=intents, application_id=APPLICATION_ID, help_command=PrettyHelp())
    return bot


def main() -> None:
    parser = argparse.ArgumentParser(description="Aethor Discord Bot")
    parser.add_argument("--check", action="store_true", help="Validate setup and cogs, then exit.")
    parser.add_argument("--sync", action="store_true", help="Sync slash commands on ready.")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("Aethor")

    bot = build_bot()

    if args.check:
        # Load extensions in an async context to validate without running the bot
        try:
            asyncio.run(bot.setup_hook())
            logger.info("Smoke-check complete: config imported and cogs loaded.")
            sys.exit(0)
        except Exception as e:
            logger.exception(f"Smoke-check failed during extension load: {e}")
            sys.exit(1)

    require_token()

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        if args.sync:
            try:
                if GUILD_ID:
                    bot.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))
                    commands_synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
                    logger.info(f"Synced {len(commands_synced)} slash commands to guild {GUILD_ID}")
                else:
                    commands_synced = await bot.tree.sync()
                    logger.info(f"Synced {len(commands_synced)} global slash commands")
            except Exception as e:
                logger.exception(f"Failed to sync commands: {e}")

    bot.run(DISCORD_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
