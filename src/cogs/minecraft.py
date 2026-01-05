import discord
from discord import app_commands
from discord.ext import commands
from mcstatus import JavaServer

from src.config import ConfigModel, get_config

CONFIG: ConfigModel = get_config()


async def query_status(address: str):
    server = JavaServer.lookup(address)
    status = await server.async_status()
    return status


class Minecraft(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="mcstatus")
    async def mcstatus_prefix(self, ctx: commands.Context, address: str = ""):
        addr = address or CONFIG.minecraft.address
        if not addr:
            await ctx.reply("No server provided. Set `MC_SERVER` or pass an address.")
            return
        try:
            status = await query_status(addr)
            embed = discord.Embed(title="Minecraft Server Status", color=0x00AAFF)
            embed.add_field(name="Address", value=addr, inline=True)
            embed.add_field(name="Players", value=f"{status.players.online}", inline=True)
            embed.add_field(name="Latency", value=f"{round(status.latency)}ms", inline=True)
            await ctx.reply(embed=embed)
        except Exception as e:
            await ctx.reply(f"Failed to query status: {e}")

    @app_commands.command(name="mcstatus", description="Check Minecraft server status")
    @app_commands.describe(address="Server address (host[:port])")
    async def mcstatus_slash(self, interaction: discord.Interaction, address: str | None = None):
        addr = address or CONFIG.minecraft.address
        if not addr:
            await interaction.response.send_message(
                "No server provided. Set `MC_SERVER` or pass an address.", ephemeral=True
            )
            return
        try:
            status = await query_status(addr)
            embed = discord.Embed(title="Minecraft Server Status", color=0x00AAFF)
            embed.add_field(name="Address", value=addr, inline=True)
            embed.add_field(name="Players", value=f"{status.players.online}", inline=True)
            embed.add_field(name="Latency", value=f"{round(status.latency)}ms", inline=True)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Failed to query status: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Minecraft(bot))
