import discord
from discord import Permissions, app_commands
from discord.ext import commands

from src.bot import AethorBot
from src.config import ConfigModel, get_config
from src.utils import rcon
from src.utils.mc_online import is_player_online
from src.utils.mojang import fetch_player_by_username
from src.utils.players import delete_player, get_player, set_player
from src.utils.store import add_to_whitelist, remove_from_whitelist

CONFIG: ConfigModel = get_config()


class Onboarding(commands.Cog):
    def __init__(self, bot: AethorBot):
        self.bot = bot

    @app_commands.command(name="verify", description="Link your Minecraft name and get verified")
    @app_commands.describe(name="Your Minecraft in-game name")
    async def verify_self(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        user = await fetch_player_by_username(name)
        if not user:
            await interaction.followup.send("Could not find that Minecraft name. Check spelling.", ephemeral=True)
            return
        set_player(interaction.user.id, user.username, user.uuid)

        added = add_to_whitelist(user.username)
        msg = f"Linked {user.username} (UUID: {user.uuid}). "
        msg += "Added to whitelist. " if added else "Already on whitelist. "

        if rcon.is_enabled() and added:
            try:
                r = rcon.whitelist_add(user.username)
                msg += f"RCON: {r} "
            except Exception as e:
                msg += f"RCON failed: {e} "

        if CONFIG.roles.verified_role_id:
            try:
                role = CONFIG.roles.verified_role
                if isinstance(role, discord.Role) and isinstance(interaction.user, discord.Member):
                    await interaction.user.add_roles(role, reason="Verification")
                    msg += f"Granted role {role.name}. "
            except Exception:
                pass

        if CONFIG.channels.verify_log_channel_id:
            channel = CONFIG.channels.verify_log_channel
            try:
                await channel.send(f"Verified {interaction.user.mention} as {user.username} (UUID {user.uuid}).")
            except Exception:
                pass

        await interaction.followup.send(msg.strip(), ephemeral=True)

    @app_commands.command(name="unverify", description="Remove your verification, role, and whitelist entry")
    @app_commands.checks.has_role(CONFIG.roles.verified_role_id)
    async def unverify_self(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        record = get_player(interaction.user.id)
        if not record:
            await interaction.followup.send("You have no linked account.", ephemeral=True)
            return
        mc_name = record.get("name") or ""

        if await is_player_online(mc_name):
            await interaction.followup.send(
                f"{mc_name} appears to be online. Disconnect before unverifying.",
                ephemeral=True,
            )
            return

        # Remove whitelist locally and via RCON
        removed_msg = ""
        if mc_name:
            removed = remove_from_whitelist(mc_name)
            removed_msg = "Removed from whitelist. " if removed else "Not found on whitelist. "
            if removed and rcon.is_enabled():
                try:
                    r = rcon.whitelist_remove(mc_name)
                    removed_msg += f"RCON: {r} "
                except Exception as e:
                    removed_msg += f"RCON failed: {e} "

        # Remove verified role
        role_msg = ""
        if CONFIG.roles.verified_role_id and isinstance(interaction.user, discord.Member):
            role = CONFIG.roles.verified_role
            if isinstance(role, discord.Role):
                try:
                    await interaction.user.remove_roles(role, reason="Unverify")
                    role_msg = f"Removed role {role.name}. "
                except Exception:
                    pass

        # Delete mapping
        delete_player(interaction.user.id)

        # Log
        if CONFIG.channels.verify_log_channel_id:
            channel = CONFIG.channels.verify_log_channel
            try:
                await channel.send(f"Unverified {interaction.user.mention} (was {mc_name}).")
            except Exception:
                pass

        await interaction.followup.send((removed_msg + role_msg + "Unverified.").strip(), ephemeral=True)

    verification_management = app_commands.Group(
        name="verification", description="Admin commands for user verification"
    )
    verification_management.default_permissions = Permissions(administrator=True)

    @verification_management.command(name="verify", description="Admin: Verify a user with given Minecraft name")
    @app_commands.describe(user="Discord user to verify", name="Minecraft in-game name")
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_other_user(self, interaction: discord.Interaction, user: discord.User, name: str):
        await interaction.response.defer(ephemeral=True)
        mc_user = await fetch_player_by_username(name)
        if not user:
            await interaction.followup.send("Could not find that Minecraft name. Check spelling.", ephemeral=True)
            return
        set_player(user.id, mc_user.username, mc_user.uuid)

        added = add_to_whitelist(mc_user.username)
        msg = f"Linked {mc_user.username} (UUID: {mc_user.uuid}) to {user.mention}. "
        msg += "Added to whitelist. " if added else "Already on whitelist. "

        if rcon.is_enabled() and added:
            try:
                r = rcon.whitelist_add(mc_user.username)
                msg += f"RCON: {r} "
            except Exception as e:
                msg += f"RCON failed: {e} "

        if CONFIG.roles.verified_role_id:
            try:
                role = CONFIG.roles.verified_role
                member = interaction.guild.get_member(user.id)
                if isinstance(role, discord.Role) and isinstance(member, discord.Member):
                    await member.add_roles(role, reason="Admin verification")
                    msg += f"Granted role {role.name}. "
            except Exception:
                pass

        if CONFIG.channels.verify_log_channel_id:
            channel = CONFIG.channels.verify_log_channel
            try:
                await channel.send(
                    f"Admin {interaction.user.mention} verified {user.mention} as {mc_user.username} (UUID {mc_user.uuid})."
                )
            except Exception:
                pass

        await interaction.followup.send(msg.strip(), ephemeral=True)

    @verification_management.command(name="unverify", description="Admin: Unverify a user, remove role and whitelist")
    @app_commands.checks.has_permissions(administrator=True)
    async def unverify_other_user(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)
        record = get_player(user.id)
        mc_name = record.get("name") if record else None

        if mc_name and await is_player_online(mc_name):
            await interaction.followup.send(
                f"{mc_name} appears to be online. Try again after they disconnect.",
                ephemeral=True,
            )
            return

        removed_msg = ""
        if mc_name:
            removed = remove_from_whitelist(mc_name)
            removed_msg = f"Removed {mc_name} from whitelist. " if removed else f"{mc_name} not on whitelist. "
            if removed and rcon.is_enabled():
                try:
                    r = rcon.whitelist_remove(mc_name)
                    removed_msg += f"RCON: {r} "
                except Exception as e:
                    removed_msg += f"RCON failed: {e} "

        role_msg = ""
        if CONFIG.roles.verified_role_id:
            member = interaction.guild.get_member(user.id)
            role = CONFIG.roles.verified_role
            if isinstance(member, discord.Member) and isinstance(role, discord.Role):
                try:
                    await member.remove_roles(role, reason="Admin unverify")
                    role_msg = f"Removed role {role.name} from {member.mention}. "
                except Exception:
                    pass

        if record:
            delete_player(user.id)

        if CONFIG.channels.verify_log_channel_id:
            channel = CONFIG.channels.verify_log_channel
            try:
                await channel.send(
                    f"Admin {interaction.user.mention} unverifed {user.mention} (was {mc_name or 'unknown'})."
                )
            except Exception:
                pass

        await interaction.followup.send((removed_msg + role_msg + "User unverified.").strip(), ephemeral=True)

    @verification_management.command(name="change", description="Change a user's linked Minecraft account")
    @app_commands.describe(user="Discord user to change", name="New Minecraft in-game name")
    @app_commands.checks.has_permissions(administrator=True)
    async def change_user_mc_account(self, interaction: discord.Interaction, user: discord.User, name: str):
        await interaction.response.defer(ephemeral=True)
        mc_user = await fetch_player_by_username(name)
        if not mc_user:
            await interaction.followup.send("Could not find that Minecraft name. Check spelling.", ephemeral=True)
            return
        set_player(user.id, mc_user.username, mc_user.uuid)

    @verification_management.command(name="whois", description="Look up a user's linked Minecraft account")
    @app_commands.describe(user="Discord user to look up")
    @app_commands.checks.has_permissions(administrator=True)
    async def whois_user(self, interaction: discord.Interaction, user: discord.User | None = None):
        target = user or interaction.user
        record = get_player(target.id)
        if not record:
            await interaction.response.send_message("No linked account.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"{target.mention}: {record.get('name')} (UUID: {record.get('uuid')})", ephemeral=True
        )


async def setup(bot: AethorBot):
    await bot.add_cog(Onboarding(bot))
