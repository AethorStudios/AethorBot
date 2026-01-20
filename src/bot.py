import asyncio
import logging
import sys
import time

import discord
from discord.ext import commands
from pretty_help import PrettyHelp

from src.utils.args import RuntimeArgs, get_runtime_args
from src.utils.config import ConfigModel, load_config, resolve_config_values
from src.utils.database.sql_database import close_local_database, initialize_local_database
from src.utils.health import make_status_func, start_health_server
from src.utils.logger import setup_logging

args: RuntimeArgs = None
config: ConfigModel = None


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
    def __init__(self, *, config: ConfigModel, args: RuntimeArgs, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.runtime_args = args

    async def setup_hook(self) -> None:
        await load_cogs(self)

        # Start healthcheck server after cogs load
        if self.config.minecraft.healthcheck.enabled:
            started_at = getattr(self, "_started_at", time.time())
            self._started_at = started_at
            try:
                start_health_server(self.config.minecraft.healthcheck.port, make_status_func(self, started_at))
                logging.getLogger("Aethor").info(
                    f"Healthcheck server listening on :{self.config.minecraft.healthcheck.port}"
                )
            except Exception as e:
                logging.getLogger("Aethor").warning(f"Failed to start healthcheck server: {e}")

    async def close(self) -> None:
        await close_local_database()
        await super().close()


def build_bot(config: ConfigModel, args: RuntimeArgs) -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True  # for prefix commands
    bot = AethorBot(
        config=config,
        args=args,
        command_prefix="!",
        intents=intents,
        application_id=config.bot.application_id,
        help_command=PrettyHelp(),
    )
    return bot


def main() -> None:
    global args, config
    args = get_runtime_args()
    config = load_config(args.config_path, update_if_has_string="token: CHANGE_ME")

    if not args.check:
        config.validate_required_runtime()

    setup_logging(config)
    logger = logging.getLogger("Aethor")

    bot = build_bot(config, args)

    if args.check:
        # Load extensions in an async context to validate without running the bot
        try:
            asyncio.run(initialize_local_database())
            asyncio.run(bot.setup_hook())
            asyncio.run(close_local_database())
            logger.info("Smoke-check complete: config imported and cogs loaded.")
            sys.exit(0)
        except Exception as e:
            logger.exception(f"Smoke-check failed during extension load: {e}")
            sys.exit(1)

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        resolve_config_values(bot)
        await initialize_local_database()
        if args.sync:
            try:
                if config.bot.guild_id:
                    bot.tree.copy_global_to(guild=discord.Object(id=config.bot.guild_id))
                    commands_synced = await bot.tree.sync(guild=discord.Object(id=config.bot.guild_id))
                    logger.info(f"Synced {len(commands_synced)} slash commands to guild {config.bot.guild_id}")
                else:
                    commands_synced = await bot.tree.sync()
                    logger.info(f"Synced {len(commands_synced)} global slash commands")
            except Exception as e:
                logger.exception(f"Failed to sync commands: {e}")

    bot.run(config.bot.token.get_secret_value(), log_handler=None)


if __name__ == "__main__":
    main()
