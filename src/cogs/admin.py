from pathlib import Path

import discord
from discord import Permissions, app_commands
from discord.ext import commands

from src.bot import AethorBot
from src.utils.config import ConfigModel, get_config

CONFIG: ConfigModel = get_config()


class Admin(commands.Cog):
    def __init__(self, bot: AethorBot):
        self.bot = bot

    # ============== COG FUNCTIONS ==============

    def get_loaded_extensions(self) -> set[str]:
        return {ext.split(".")[-1] for ext in self.bot.extensions.keys()}

    def get_all_extensions(self) -> set[str]:
        return {ext.stem for ext in Path("src/cogs").glob("*.py")}

    def get_unloaded_extensions(self) -> set[str]:
        return self.get_all_extensions() - self.get_loaded_extensions()

    async def autocomplete_cogs(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        loaded: bool | None = {"reload": True, "unload": True, "load": False}.get(
            interaction.command.name, None
        )  # Select what to show based on command
        extensions = ["ALL"] if not current or "ALL".startswith(current.upper()) else []

        if loaded is True:
            extensions += sorted(self.get_loaded_extensions())
        elif loaded is False:
            extensions += sorted(self.get_unloaded_extensions())
        else:
            extensions += sorted(self.get_all_extensions())

        if interaction.command.name == "unload" and "admin" in extensions:
            extensions.remove("admin")  # Prevent unloading self

        choices = [app_commands.Choice(name=ext, value=ext) for ext in extensions if current.lower() in ext.lower()]
        return choices

    # ============== COMMANDS ==============

    # Cog Management
    extension_management = app_commands.Group(name="cog", description="Cog management commands")
    extension_management.default_permissions = Permissions(administrator=True)

    @extension_management.command(name="load", description="Load bot cogs")
    @app_commands.describe(extension="The cog to load")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(extension=autocomplete_cogs)
    async def load_extension(self, interaction: discord.Interaction, extension: str):
        if not extension:
            await interaction.response.send_message("Please specify an extension to load.", ephemeral=True)
            return

        if extension.upper() == "ALL":
            unloaded_extensions = self.get_unloaded_extensions()
            for ext_name in unloaded_extensions:
                try:
                    await self.bot.load_extension(f"src.cogs.{ext_name}")
                except Exception as e:
                    await interaction.response.send_message(f"Failed to load `{ext_name}`: {e}", ephemeral=True)
                    return
            await interaction.response.send_message("Loaded all cogs that weren't previously loaded.", ephemeral=True)
            return
        if extension and extension not in self.get_unloaded_extensions():
            extension = f"src.cogs.{extension}"
            try:
                await self.bot.load_extension(extension)
                await interaction.response.send_message(f"Loaded `{extension}`.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Failed to load `{extension}`: {e}", ephemeral=True)

    @extension_management.command(name="unload", description="Unload bot cog")
    @app_commands.describe(extension="The cog to unload")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(extension=autocomplete_cogs)
    async def unload_extension(self, interaction: discord.Interaction, extension: str):
        if extension.lower() == "admin":
            await interaction.response.send_message(
                "Cannot unload the admin cog. It must be reloaded instead.", ephemeral=True
            )
            return
        if not extension:
            await interaction.response.send_message("Please specify an extension to unload.", ephemeral=True)
            return

        if extension.upper() == "ALL":
            loaded_extensions = self.get_loaded_extensions()
            loaded_extensions.discard("admin")  # Prevent unloading self
            for ext_name in loaded_extensions:
                try:
                    await self.bot.unload_extension(f"src.cogs.{ext_name}")
                except Exception as e:
                    await interaction.response.send_message(f"Failed to unload `{ext_name}`: {e}", ephemeral=True)
                    return
            await interaction.response.send_message("Unloaded all cogs.", ephemeral=True)
            return
        if extension and extension in self.get_loaded_extensions():
            extension = f"src.cogs.{extension}"
            try:
                await self.bot.unload_extension(extension)
                await interaction.response.send_message(f"Unloaded `{extension}`.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Failed to unload `{extension}`: {e}", ephemeral=True)

    @extension_management.command(name="reload", description="Reload bot cogs")
    @app_commands.describe(extension="The cog to reload")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(extension=autocomplete_cogs)
    async def reload_extension(self, interaction: discord.Interaction, extension: str):
        if not extension:
            await interaction.response.send_message("Please specify an extension to reload.", ephemeral=True)
            return

        if extension.upper() == "ALL":
            loaded_extensions = self.get_loaded_extensions()
            for ext_name in loaded_extensions:
                try:
                    await self.bot.reload_extension(f"src.cogs.{ext_name}")
                except Exception as e:
                    await interaction.response.send_message(f"Failed to reload `{ext_name}`: {e}", ephemeral=True)
                    return
            await interaction.response.send_message("Reloaded all cogs.", ephemeral=True)
            return
        if extension and extension in self.get_loaded_extensions():
            extension = f"src.cogs.{extension}"
            try:
                await self.bot.reload_extension(extension)
                await interaction.response.send_message(f"Reloaded `{extension}`.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Failed to reload `{extension}`: {e}", ephemeral=True)

    @app_commands.command(name="sync", description="Sync application commands")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        try:
            if CONFIG.bot.guild_id:
                self.bot.tree.copy_global_to(guild=discord.Object(id=CONFIG.bot.guild_id))
                commands_synced = await self.bot.tree.sync(guild=discord.Object(id=CONFIG.bot.guild_id))
                await interaction.response.send_message(
                    f"Synced {len(commands_synced)} slash commands to guild {CONFIG.bot.guild_id}.", ephemeral=True
                )
            else:
                commands_synced = await self.bot.tree.sync()
                await interaction.response.send_message(
                    f"Synced {len(commands_synced)} slash commands globally.", ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(f"Failed to sync: {e}", ephemeral=True)

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_commands_prefix(self, ctx: commands.Context):
        try:
            if CONFIG.bot.guild_id:
                self.bot.tree.copy_global_to(guild=discord.Object(id=CONFIG.bot.guild_id))
                commands_synced = await self.bot.tree.sync(guild=discord.Object(id=CONFIG.bot.guild_id))
                await ctx.reply(
                    f"Synced {len(commands_synced)} slash commands to guild {CONFIG.bot.guild_id}.", delete_after=10
                )
            else:
                commands_synced = await self.bot.tree.sync()
                await ctx.reply(f"Synced {len(commands_synced)} slash commands globally.", delete_after=10)
        except Exception as e:
            await ctx.reply(f"Failed to sync commands: {e}", delete_after=10)


async def setup(bot: AethorBot):
    await bot.add_cog(Admin(bot))
