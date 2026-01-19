import discord
from discord import app_commands
from discord.ext import commands
from mcstatus import JavaServer

from src.bot import AethorBot
from src.config import ConfigModel, get_config

CONFIG: ConfigModel = get_config()


async def query_status(address: str):
    server = JavaServer.lookup(address)
    status = await server.async_status()
    return status


class Minecraft(commands.Cog):
    def __init__(self, bot: AethorBot):
        self.bot = bot

    @app_commands.command(name="mcstatus", description="Check Minecraft server status")
    @app_commands.describe(address="Server address (host[:port])")
    async def mcstatus(self, interaction: discord.Interaction, address: str | None = None):
        server_address = address or CONFIG.minecraft.address
        if not server_address:
            await interaction.response.send_message("No server provided.", ephemeral=True)
            return
        try:
            status = await query_status(server_address)
            embed = discord.Embed(title="Minecraft Server Status", color=0x00AAFF)
            embed.add_field(name="Address", value=server_address, inline=True)
            embed.add_field(name="Players", value=f"{status.players.online}", inline=True)
            embed.add_field(name="Latency", value=f"{round(status.latency)}ms", inline=True)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to query status: {e}", ephemeral=True)


async def setup(bot: AethorBot):
    await bot.add_cog(Minecraft(bot))
