import datetime

import discord
from discord import Permissions, app_commands
from discord.ext import commands

from src.config import ConfigModel, get_config
from src.utils.modlog import send_mod_log

CONFIG: ConfigModel = get_config()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Member moderation
    member_moderation = app_commands.Group(name="moderation", description="Member moderation commands")
    member_moderation.default_permissions = Permissions(
        kick_members=True, ban_members=True, moderate_members=True, manage_messages=True
    )

    # Kick
    @member_moderation.command(name="kick", description="Kick a member")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None):
        try:
            await member.kick(reason=reason or f"Kicked by {interaction.user}")
            await interaction.response.send_message(f"Kicked {member.mention}.", ephemeral=True)
            await send_mod_log("Kick", f"{interaction.user.mention} kicked {member.mention}\nReason: {reason or 'n/a'}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick: {e}", ephemeral=True)

    # Ban
    @member_moderation.command(name="ban", description="Ban a member")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        delete_message_days: int = 0,
        reason: str | None = None,
    ):
        try:
            await interaction.guild.ban(
                member, reason=reason or f"Banned by {interaction.user}", delete_message_days=delete_message_days
            )
            await interaction.response.send_message(f"Banned {member.mention}.", ephemeral=True)
            await send_mod_log(
                "Ban",
                f"{interaction.user.mention} banned {member.mention}\nReason: {reason or 'n/a'}\nDelete days: {delete_message_days}",
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban: {e}", ephemeral=True)

    @member_moderation.command(name="unban", description="Unban a user by ID")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        try:
            user = await self.bot.fetch_user(user)
            await interaction.guild.unban(user, reason=reason or f"Unbanned by {interaction.user}")
            await interaction.response.send_message(f"Unbanned {user.mention}.", ephemeral=True)
            await send_mod_log(
                "Unban", f"{interaction.user.mention} unbanned {user.mention}\nReason: {reason or 'n/a'}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to unban: {e}", ephemeral=True)

    # Timeout / Untimeout
    @member_moderation.command(name="timeout", description="Timeout a member (minutes)")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str | None = None
    ):
        try:
            until = discord.utils.utcnow() + datetime.timedelta(minutes=max(1, minutes))
            await member.timeout(until, reason=reason or f"Timeout by {interaction.user}")
            await interaction.response.send_message(f"Timed out {member.mention} for {minutes}m.", ephemeral=True)
            await send_mod_log(
                "Timeout",
                f"{interaction.user.mention} timed out {member.mention} for {minutes}m\nReason: {reason or 'n/a'}",
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout: {e}", ephemeral=True)

    @member_moderation.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None):
        try:
            await member.timeout(None, reason=reason or f"Untimeout by {interaction.user}")
            await interaction.response.send_message(f"Removed timeout for {member.mention}.", ephemeral=True)
            await send_mod_log(
                "Untimeout",
                f"{interaction.user.mention} removed timeout for {member.mention}\nReason: {reason or 'n/a'}",
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to untimeout: {e}", ephemeral=True)

    @member_moderation.command(name="purge", description="Delete last N messages in this channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, count: int):
        try:
            channel = interaction.channel
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message("Not a text channel.", ephemeral=True)
                return
            deleted = await channel.purge(limit=max(1, min(1000, count)))
            await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)
            await send_mod_log(
                "Purge", f"{interaction.user.mention} purged {len(deleted)} messages in {channel.mention}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to purge: {e}", ephemeral=True)

    # Channel moderation
    channel_moderation = app_commands.Group(name="channel", description="Channel moderation commands")
    channel_moderation.default_permissions = Permissions(manage_channels=True)

    # Slowmode
    @channel_moderation.command(name="slowmode", description="Set slowmode seconds for a channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        self, interaction: discord.Interaction, seconds: int, target_channel: discord.TextChannel | None = None
    ):
        channel = target_channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Not a text channel.", ephemeral=True)
            return
        try:
            await channel.edit(slowmode_delay=max(0, min(21600, seconds)))
            await interaction.response.send_message(f"Set slowmode to {seconds}s in {channel.mention}.", ephemeral=True)
            await send_mod_log(
                "Slowmode", f"{interaction.user.mention} set slowmode to {seconds}s in {channel.mention}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to set slowmode: {e}", ephemeral=True)

    # Lock/Unlock
    @channel_moderation.command(name="lock", description="Lock a channel (deny @everyone sending)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, target_channel: discord.TextChannel | None = None):
        channel = target_channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Not a text channel.", ephemeral=True)
            return
        try:
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message(f"Locked {channel.mention}.", ephemeral=True)
            await send_mod_log("Lock", f"{interaction.user.mention} locked {channel.mention}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to lock: {e}", ephemeral=True)

    @channel_moderation.command(name="unlock", description="Unlock a channel (allow @everyone sending)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, target_channel: discord.TextChannel | None = None):
        channel = target_channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Not a text channel.", ephemeral=True)
            return
        try:
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message(f"Unlocked {channel.mention}.", ephemeral=True)
            await send_mod_log("Unlock", f"{interaction.user.mention} unlocked {channel.mention}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to unlock: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
