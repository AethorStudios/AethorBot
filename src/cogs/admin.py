import discord
from discord import app_commands
from discord.ext import commands

from src.config import ADMIN_ROLE_IDS, GUILD_ID


def user_is_admin(ctx_or_interaction) -> bool:
    # Works for both Context (prefix) and Interaction (slash)
    if hasattr(ctx_or_interaction, "user"):
        member = ctx_or_interaction.user
    else:
        member = ctx_or_interaction.author

    if isinstance(member, discord.Member):
        if member.guild_permissions.administrator:
            return True
        if ADMIN_ROLE_IDS and any(r.id in ADMIN_ROLE_IDS for r in member.roles):
            return True
    return False


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
        if not user_is_admin(ctx):
            await ctx.reply("You lack permissions to sync commands.")
            return
        try:
            if GUILD_ID:
                await self.bot.tree.sync(guild=discord.Object(id=GUILD_ID))
                await ctx.reply(f"Synced slash commands to guild {GUILD_ID}.")
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
        if not user_is_admin(interaction):
            await interaction.response.send_message("Insufficient permissions.", ephemeral=True)
            return
        try:
            if GUILD_ID:
                await self.bot.tree.sync(guild=discord.Object(id=GUILD_ID))
                await interaction.response.send_message(f"Synced slash commands to guild {GUILD_ID}.", ephemeral=True)
            else:
                await self.bot.tree.sync()
                await interaction.response.send_message("Synced global slash commands.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to sync: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
