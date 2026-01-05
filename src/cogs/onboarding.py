import discord
from discord import app_commands
from discord.ext import commands

from src.config import VERIFIED_ROLE_ID, VERIFY_LOG_CHANNEL_ID
from src.utils import rcon
from src.utils.mc_online import is_player_online
from src.utils.mojang import fetch_uuid
from src.utils.players import delete_player, get_player, set_player
from src.utils.store import add_to_whitelist, remove_from_whitelist


class Onboarding(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Link your Minecraft name and get verified")
    @app_commands.describe(name="Your Minecraft in-game name")
    async def verify_slash(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        uuid, exact = await fetch_uuid(name)
        if not uuid:
            await interaction.followup.send("Could not find that Minecraft name. Check spelling.", ephemeral=True)
            return
        mc_name = exact or name
        set_player(interaction.user.id, mc_name, uuid)

        added = add_to_whitelist(mc_name)
        msg = f"Linked {mc_name} (UUID: {uuid}). "
        msg += "Added to whitelist. " if added else "Already on whitelist. "

        if rcon.is_enabled() and added:
            try:
                r = rcon.whitelist_add(mc_name)
                msg += f"RCON: {r} "
            except Exception as e:
                msg += f"RCON failed: {e} "

        if VERIFIED_ROLE_ID:
            try:
                role = interaction.guild.get_role(VERIFIED_ROLE_ID) if interaction.guild else None
                if isinstance(role, discord.Role) and isinstance(interaction.user, discord.Member):
                    await interaction.user.add_roles(role, reason="Verification")
                    msg += f"Granted role {role.name}. "
            except Exception:
                pass

        if VERIFY_LOG_CHANNEL_ID:
            chan = self.bot.get_channel(VERIFY_LOG_CHANNEL_ID)
            if isinstance(chan, discord.TextChannel):
                try:
                    await chan.send(f"[Aethor] Verified {interaction.user.mention} as {mc_name} (UUID {uuid}).")
                except Exception:
                    pass

        await interaction.followup.send(msg.strip(), ephemeral=True)

    @app_commands.command(name="verify_user", description="Admin: Verify a user with given Minecraft name")
    @app_commands.describe(user="Discord user to verify", name="Minecraft in-game name")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_user_slash(self, interaction: discord.Interaction, user: discord.User, name: str):
        await interaction.response.defer(ephemeral=True)
        uuid, exact = await fetch_uuid(name)
        if not uuid:
            await interaction.followup.send("Could not find that Minecraft name. Check spelling.", ephemeral=True)
            return
        mc_name = exact or name
        set_player(user.id, mc_name, uuid)

        added = add_to_whitelist(mc_name)
        msg = f"Linked {mc_name} (UUID: {uuid}) to {user.mention}. "
        msg += "Added to whitelist. " if added else "Already on whitelist. "

        if rcon.is_enabled() and added:
            try:
                r = rcon.whitelist_add(mc_name)
                msg += f"RCON: {r} "
            except Exception as e:
                msg += f"RCON failed: {e} "

        if VERIFIED_ROLE_ID:
            try:
                role = interaction.guild.get_role(VERIFIED_ROLE_ID) if interaction.guild else None
                member = interaction.guild.get_member(user.id) if interaction.guild else None
                if isinstance(role, discord.Role) and isinstance(member, discord.Member):
                    await member.add_roles(role, reason="Admin verification")
                    msg += f"Granted role {role.name}. "
            except Exception:
                pass

        if VERIFY_LOG_CHANNEL_ID:
            chan = self.bot.get_channel(VERIFY_LOG_CHANNEL_ID)
            if isinstance(chan, discord.TextChannel):
                try:
                    await chan.send(f"[Aethor] Admin {interaction.user.mention} verified {user.mention} as {mc_name} (UUID {uuid}).")
                except Exception:
                    pass

        await interaction.followup.send(msg.strip(), ephemeral=True)

    @app_commands.command(name="whois", description="Look up a user's linked Minecraft account")
    @app_commands.describe(user="Discord user to look up")
    @app_commands.checks.has_role(VERIFIED_ROLE_ID)
    async def whois_slash(self, interaction: discord.Interaction, user: discord.User | None = None):
        target = user or interaction.user
        record = get_player(target.id)
        if not record:
            await interaction.response.send_message("No linked account.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"{target.mention}: {record.get('name')} (UUID: {record.get('uuid')})", ephemeral=True
        )

    @app_commands.command(name="unverify", description="Remove your verification, role, and whitelist entry")
    @app_commands.checks.has_role(VERIFIED_ROLE_ID)
    async def unverify_slash(self, interaction: discord.Interaction):
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
        if VERIFIED_ROLE_ID and isinstance(interaction.user, discord.Member):
            role = interaction.guild.get_role(VERIFIED_ROLE_ID) if interaction.guild else None
            if isinstance(role, discord.Role):
                try:
                    await interaction.user.remove_roles(role, reason="Unverify")
                    role_msg = f"Removed role {role.name}. "
                except Exception:
                    pass

        # Delete mapping
        delete_player(interaction.user.id)

        # Log
        if VERIFY_LOG_CHANNEL_ID:
            chan = self.bot.get_channel(VERIFY_LOG_CHANNEL_ID)
            if isinstance(chan, discord.TextChannel):
                try:
                    await chan.send(f"[Aethor] Unverified {interaction.user.mention} (was {mc_name}).")
                except Exception:
                    pass

        await interaction.followup.send((removed_msg + role_msg + "Unverified.").strip(), ephemeral=True)

    @app_commands.command(name="unverify_user", description="Admin: Unverify a user, remove role and whitelist")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def unverify_user_slash(self, interaction: discord.Interaction, user: discord.User):
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
        if VERIFIED_ROLE_ID:
            member = interaction.guild.get_member(user.id) if interaction.guild else None
            role = interaction.guild.get_role(VERIFIED_ROLE_ID) if interaction.guild else None
            if isinstance(member, discord.Member) and isinstance(role, discord.Role):
                try:
                    await member.remove_roles(role, reason="Admin unverify")
                    role_msg = f"Removed role {role.name} from {member.mention}. "
                except Exception:
                    pass

        if record:
            delete_player(user.id)

        if VERIFY_LOG_CHANNEL_ID:
            chan = self.bot.get_channel(VERIFY_LOG_CHANNEL_ID)
            if isinstance(chan, discord.TextChannel):
                try:
                    await chan.send(
                        f"[Aethor] Admin {interaction.user.mention} unverifed {user.mention} (was {mc_name or 'unknown'})."
                    )
                except Exception:
                    pass

        await interaction.followup.send((removed_msg + role_msg + "User unverified.").strip(), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot))
