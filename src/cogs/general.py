import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping_prefix(self, ctx: commands.Context):
        await ctx.reply(f"Pong! {round(self.bot.latency * 1000)}ms")

    @app_commands.command(name="ping", description="Check bot latency")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def ping_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(name="about")
    async def about_prefix(self, ctx: commands.Context):
        await ctx.reply("Aethor Bot — Minecraft MMORPG companion.")

    @app_commands.command(name="about", description="About Aethor bot")
    async def about_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message("Aethor Bot — Minecraft MMORPG companion.")


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
