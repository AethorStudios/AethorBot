import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms")

    @app_commands.command(name="about", description="About Aethor bot")
    async def about(self, interaction: discord.Interaction):
        await interaction.response.send_message("Aethor Bot — Minecraft MMORPG companion.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
