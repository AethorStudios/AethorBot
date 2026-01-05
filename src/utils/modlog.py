import discord

from src.config import ConfigModel, get_config

CONFIG: ConfigModel = get_config()


async def send_mod_log(bot: discord.Client, title: str, description: str, *, color: int = 0xE67E22):
    if not CONFIG.channels.mod_log_channel_id:
        return
    chan = bot.get_channel(CONFIG.channels.mod_log_channel_id)
    if not isinstance(chan, discord.TextChannel):
        return
    embed = discord.Embed(title=title, description=description, color=color)
    try:
        await chan.send(embed=embed)
    except Exception:
        pass
