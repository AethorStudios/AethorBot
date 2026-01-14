import discord

from src.config import ConfigModel, get_config

CONFIG: ConfigModel = get_config()


async def send_mod_log(title: str, description: str, *, color: int = 0xE67E22):
    if not CONFIG.channels.mod_log_channel_id:
        return
    channel = CONFIG.channels.mod_log_channel
    embed = discord.Embed(title=title, description=description, color=color)
    try:
        await channel.send(embed=embed)
    except Exception:
        pass
