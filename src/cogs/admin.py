import discord
from discord import app_commands
from discord.ext import commands

from src.config import ConfigModel, get_config

CONFIG: ConfigModel = get_config()


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="reload")
    @commands.has_permissions(administrator=True)
    async def reload_prefix(self, ctx: commands.Context, extension: str = ""):
        if not extension:
            for ext in list(self.bot.extensions.keys()):
                try:
                    await self.bot.reload_extension(ext)
                except Exception as e:
                    await ctx.reply(f"Failed to reload `{ext}`: {e}")
                    return
            await ctx.reply("Reloaded all cogs.")
            return
        try:
            await self.bot.reload_extension(extension)
            await ctx.reply(f"Reloaded `{extension}`.")
        except Exception as e:
            await ctx.reply(f"Failed to reload `{extension}`: {e}")

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_prefix(self, ctx: commands.Context):
        try:
            if CONFIG.discord.guild_id:
                await self.bot.tree.sync(guild=discord.Object(id=CONFIG.discord.guild_id))
                await ctx.reply(f"Synced slash commands to guild {CONFIG.discord.guild_id}.")
            else:
                await self.bot.tree.sync()
                await ctx.reply("Synced global slash commands.")
        except Exception as e:
            await ctx.reply(f"Failed to sync commands: {e}")

    @commands.command(name="say")
    @commands.has_permissions(administrator=True)
    async def say_prefix(self, ctx: commands.Context, *, message: str):
        await ctx.message.delete()
        await ctx.send(message)

    @app_commands.command(name="sync", description="Sync application commands")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_slash(self, interaction: discord.Interaction):
        try:
            if CONFIG.discord.guild_id:
                await self.bot.tree.sync(guild=discord.Object(id=CONFIG.discord.guild_id))
                await interaction.response.send_message(
                    f"Synced slash commands to guild {CONFIG.discord.guild_id}.", ephemeral=True
                )
            else:
                await self.bot.tree.sync()
                await interaction.response.send_message("Synced global slash commands.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to sync: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
