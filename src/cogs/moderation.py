import datetime

import discord
from discord import app_commands
from discord.ext import commands

from src.config import ConfigModel, get_config
from src.utils.modlog import send_mod_log

CONFIG: ConfigModel = get_config()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Kick
    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None):
        try:
            await member.kick(reason=reason or f"Kicked by {interaction.user}")
            await interaction.response.send_message(f"Kicked {member.mention}.", ephemeral=True)
            await send_mod_log(
                self.bot, "Kick", f"{interaction.user.mention} kicked {member.mention}\nReason: {reason or 'n/a'}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to kick: {e}", ephemeral=True)

    # Ban
    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_slash(
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
                self.bot,
                "Ban",
                f"{interaction.user.mention} banned {member.mention}\nReason: {reason or 'n/a'}\nDelete days: {delete_message_days}",
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to ban: {e}", ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user by ID")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_slash(self, interaction: discord.Interaction, user_id: int, reason: str | None = None):
        try:
            user = await self.bot.fetch_user(user_id)
            await interaction.guild.unban(user, reason=reason or f"Unbanned by {interaction.user}")
            await interaction.response.send_message(f"Unbanned {user.mention}.", ephemeral=True)
            await send_mod_log(
                self.bot, "Unban", f"{interaction.user.mention} unbanned {user.mention}\nReason: {reason or 'n/a'}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to unban: {e}", ephemeral=True)

    # Timeout / Untimeout
    @app_commands.command(name="timeout", description="Timeout a member (minutes)")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_slash(
        self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str | None = None
    ):
        try:
            until = discord.utils.utcnow() + datetime.timedelta(minutes=max(1, minutes))
            await member.timeout(until, reason=reason or f"Timeout by {interaction.user}")
            await interaction.response.send_message(f"Timed out {member.mention} for {minutes}m.", ephemeral=True)
            await send_mod_log(
                self.bot,
                "Timeout",
                f"{interaction.user.mention} timed out {member.mention} for {minutes}m\nReason: {reason or 'n/a'}",
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout: {e}", ephemeral=True)

    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout_slash(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ):
        try:
            await member.timeout(None, reason=reason or f"Untimeout by {interaction.user}")
            await interaction.response.send_message(f"Removed timeout for {member.mention}.", ephemeral=True)
            await send_mod_log(
                self.bot,
                "Untimeout",
                f"{interaction.user.mention} removed timeout for {member.mention}\nReason: {reason or 'n/a'}",
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to untimeout: {e}", ephemeral=True)

    # Mute / Unmute via role (optional)
    @app_commands.command(name="mute", description="Mute a user by adding the muted role")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None):
        role = interaction.guild.get_role(CONFIG.roles.mute_role_id)
        if not isinstance(role, discord.Role):
            await interaction.response.send_message("Mute role not found.", ephemeral=True)
            return
        try:
            await member.add_roles(role, reason=reason or f"Mute by {interaction.user}")
            await interaction.response.send_message(f"Muted {member.mention}.", ephemeral=True)
            await send_mod_log(
                self.bot, "Mute", f"{interaction.user.mention} muted {member.mention}\nReason: {reason or 'n/a'}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to mute: {e}", ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute a user by removing the muted role")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None):
        role = interaction.guild.get_role(CONFIG.roles.mute_role_id)
        if not isinstance(role, discord.Role):
            await interaction.response.send_message("Mute role not found.", ephemeral=True)
            return
        try:
            await member.remove_roles(role, reason=reason or f"Unmute by {interaction.user}")
            await interaction.response.send_message(f"Unmuted {member.mention}.", ephemeral=True)
            await send_mod_log(
                self.bot, "Unmute", f"{interaction.user.mention} unmuted {member.mention}\nReason: {reason or 'n/a'}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to unmute: {e}", ephemeral=True)

    # Purge messages
    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge_prefix(self, ctx: commands.Context, count: int):
        try:
            deleted = await ctx.channel.purge(limit=max(1, min(1000, count)))
            await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
            await send_mod_log(
                self.bot, "Purge", f"{ctx.author.mention} purged {len(deleted)} messages in {ctx.channel.mention}"
            )
        except Exception as e:
            await ctx.reply(f"Failed to purge: {e}")

    @app_commands.command(name="purge", description="Delete last N messages in this channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_slash(self, interaction: discord.Interaction, count: int):
        try:
            channel = interaction.channel
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message("Not a text channel.", ephemeral=True)
                return
            deleted = await channel.purge(limit=max(1, min(1000, count)))
            await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)
            await send_mod_log(
                self.bot, "Purge", f"{interaction.user.mention} purged {len(deleted)} messages in {channel.mention}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to purge: {e}", ephemeral=True)

    # Slowmode
    @app_commands.command(name="slowmode", description="Set slowmode seconds for a channel")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode_slash(
        self, interaction: discord.Interaction, seconds: int, channel: discord.TextChannel | None = None
    ):
        ch = channel or interaction.channel
        if not isinstance(ch, discord.TextChannel):
            await interaction.response.send_message("Not a text channel.", ephemeral=True)
            return
        try:
            await ch.edit(slowmode_delay=max(0, min(21600, seconds)))
            await interaction.response.send_message(f"Set slowmode to {seconds}s in {ch.mention}.", ephemeral=True)
            await send_mod_log(
                self.bot, "Slowmode", f"{interaction.user.mention} set slowmode to {seconds}s in {ch.mention}"
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to set slowmode: {e}", ephemeral=True)

    # Lock/Unlock
    @app_commands.command(name="lock", description="Lock a channel (deny @everyone sending)")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock_slash(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        ch = channel or interaction.channel
        if not isinstance(ch, discord.TextChannel):
            await interaction.response.send_message("Not a text channel.", ephemeral=True)
            return
        try:
            overwrite = ch.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await ch.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message(f"Locked {ch.mention}.", ephemeral=True)
            await send_mod_log(self.bot, "Lock", f"{interaction.user.mention} locked {ch.mention}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to lock: {e}", ephemeral=True)

    @app_commands.command(name="unlock", description="Unlock a channel (allow @everyone sending)")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock_slash(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        ch = channel or interaction.channel
        if not isinstance(ch, discord.TextChannel):
            await interaction.response.send_message("Not a text channel.", ephemeral=True)
            return
        try:
            overwrite = ch.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = None
            await ch.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message(f"Unlocked {ch.mention}.", ephemeral=True)
            await send_mod_log(self.bot, "Unlock", f"{interaction.user.mention} unlocked {ch.mention}")
        except Exception as e:
            await interaction.response.send_message(f"Failed to unlock: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
