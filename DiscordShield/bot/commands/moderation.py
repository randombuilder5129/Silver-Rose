import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import logging
from ..utils.permissions import moderator_only, admin_only, Permissions

logger = logging.getLogger(__name__)

class ModerationCommands(commands.Cog):
    """Moderation commands for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(
        user="The user to warn",
        reason="Reason for the warning"
    )
    @moderator_only()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        """Warn a user."""
        try:
            # Check if user can be warned
            if user.id == interaction.user.id:
                await interaction.response.send_message(
                    "❌ You cannot warn yourself!",
                    ephemeral=True
                )
                return
            
            if user.bot:
                await interaction.response.send_message(
                    "❌ You cannot warn bots!",
                    ephemeral=True
                )
                return
            
            if not Permissions.has_higher_role(interaction.user, user):
                await interaction.response.send_message(
                    "❌ You cannot warn someone with a higher or equal role!",
                    ephemeral=True
                )
                return
            
            # Add warning
            warning_id = self.bot.db.add_warning(
                interaction.guild.id,
                user.id,
                reason,
                interaction.user.id
            )
            
            # Get current warnings count
            warnings = self.bot.db.get_warnings(interaction.guild.id, user.id)
            warnings_count = len(warnings)
            
            embed = discord.Embed(
                title="⚠️ User Warned",
                description=(
                    f"**User:** {user.mention}\n"
                    f"**Reason:** {reason}\n"
                    f"**Warning ID:** {warning_id}\n"
                    f"**Total Active Warnings:** {warnings_count}/3\n"
                    f"**Moderator:** {interaction.user.mention}"
                ),
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # DM user about warning
            try:
                dm_embed = discord.Embed(
                    title=f"⚠️ Warning in {interaction.guild.name}",
                    description=(
                        f"**Reason:** {reason}\n"
                        f"**Active Warnings:** {warnings_count}/3\n"
                        f"**Moderator:** {interaction.user}\n\n"
                        "Please follow the server rules to avoid further warnings."
                    ),
                    color=discord.Color.yellow(),
                    timestamp=datetime.utcnow()
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Auto-kick on 3 warnings
            if warnings_count >= 3:
                try:
                    await user.kick(reason="Auto-kick: 3 active warnings")
                    
                    kick_embed = discord.Embed(
                        title="🦶 Auto-Kick Executed",
                        description=(
                            f"**User:** {user} ({user.id})\n"
                            f"**Reason:** 3 active warnings\n"
                            f"**Moderator:** System"
                        ),
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    
                    await interaction.followup.send(embed=kick_embed)
                    
                except discord.Forbidden:
                    await interaction.followup.send(
                        f"⚠️ {user.mention} has 3 active warnings but I couldn't kick them due to insufficient permissions!",
                        ephemeral=True
                    )
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "warn", True)
            
        except Exception as e:
            logger.error(f"Error in warn command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while warning the user.",
                ephemeral=True
            )
    
    @app_commands.command(name="warnings", description="View active warnings for a user")
    @app_commands.describe(user="The user to check warnings for")
    @moderator_only()
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        """View user's warnings."""
        try:
            warnings = self.bot.db.get_warnings(interaction.guild.id, user.id)
            
            if not warnings:
                embed = discord.Embed(
                    title="✅ No Active Warnings",
                    description=f"{user.mention} has no active warnings.",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"⚠️ Active Warnings for {user.display_name}",
                description=f"**Total:** {len(warnings)}/3",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            
            for i, warning in enumerate(warnings, 1):
                moderator = interaction.guild.get_member(warning['moderator'])
                moderator_name = moderator.display_name if moderator else "Unknown"
                
                embed.add_field(
                    name=f"Warning #{i}",
                    value=(
                        f"**ID:** {warning['id']}\n"
                        f"**Reason:** {warning['reason']}\n"
                        f"**Moderator:** {moderator_name}\n"
                        f"**Date:** <t:{int(warning['timestamp'].timestamp())}:R>"
                    ),
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "warnings", True)
            
        except Exception as e:
            logger.error(f"Error in warnings command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching warnings.",
                ephemeral=True
            )
    
    @app_commands.command(name="removewarning", description="Remove a specific warning from a user")
    @app_commands.describe(
        user="The user to remove warning from",
        warning_id="The warning ID to remove"
    )
    @moderator_only()
    async def removewarning(self, interaction: discord.Interaction, user: discord.Member, warning_id: str):
        """Remove a specific warning."""
        try:
            success = self.bot.db.remove_warning(interaction.guild.id, user.id, warning_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Warning Removed",
                    description=(
                        f"**User:** {user.mention}\n"
                        f"**Warning ID:** {warning_id}\n"
                        f"**Removed by:** {interaction.user.mention}"
                    ),
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f"❌ Warning ID `{warning_id}` not found for {user.mention}!",
                    ephemeral=True
                )
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "removewarning", success)
            
        except Exception as e:
            logger.error(f"Error in removewarning command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while removing the warning.",
                ephemeral=True
            )
    
    @app_commands.command(name="clear", description="Delete messages from a channel")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        user="Optional: Only delete messages from this user"
    )
    @moderator_only()
    async def clear(self, interaction: discord.Interaction, amount: int, user: discord.Member = None):
        """Clear messages from a channel."""
        try:
            if amount < 1 or amount > 100:
                await interaction.response.send_message(
                    "❌ Amount must be between 1 and 100!",
                    ephemeral=True
                )
                return
            
            # Check bot permissions
            if not Permissions.check_bot_permissions(interaction.channel, "manage_messages"):
                await interaction.response.send_message(
                    "❌ I don't have permission to manage messages in this channel!",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer(ephemeral=True)
            
            def check(message):
                if user:
                    return message.author == user
                return True
            
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            embed = discord.Embed(
                title="🧹 Messages Cleared",
                description=(
                    f"**Deleted:** {len(deleted)} messages\n"
                    f"**Channel:** {interaction.channel.mention}\n"
                    f"**User filter:** {user.mention if user else 'None'}\n"
                    f"**Moderator:** {interaction.user.mention}"
                ),
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.followup.send(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "clear", True)
            
        except Exception as e:
            logger.error(f"Error in clear command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while clearing messages.",
                ephemeral=True
            )
    
    @app_commands.command(name="slowmode", description="Set slowmode for a channel")
    @app_commands.describe(
        channel="The channel to set slowmode for",
        duration="Slowmode duration in seconds (0-21600)"
    )
    @moderator_only()
    async def slowmode(self, interaction: discord.Interaction, channel: discord.TextChannel, duration: int):
        """Set slowmode for a channel."""
        try:
            if duration < 0 or duration > 21600:  # 6 hours max
                await interaction.response.send_message(
                    "❌ Duration must be between 0 and 21600 seconds (6 hours)!",
                    ephemeral=True
                )
                return
            
            # Check bot permissions
            if not Permissions.check_bot_permissions(channel, "manage_channels"):
                await interaction.response.send_message(
                    f"❌ I don't have permission to manage {channel.mention}!",
                    ephemeral=True
                )
                return
            
            await channel.edit(slowmode_delay=duration)
            
            if duration == 0:
                description = f"Slowmode disabled for {channel.mention}"
                color = discord.Color.green()
            else:
                description = f"Slowmode set to {duration} seconds for {channel.mention}"
                color = discord.Color.orange()
            
            embed = discord.Embed(
                title="⏱️ Slowmode Updated",
                description=description,
                color=color,
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "slowmode", True)
            
        except Exception as e:
            logger.error(f"Error in slowmode command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting slowmode.",
                ephemeral=True
            )
    
    @app_commands.command(name="nick", description="Change a user's nickname")
    @app_commands.describe(
        user="The user to change nickname for",
        nickname="The new nickname (leave empty to remove)"
    )
    @moderator_only()
    async def nick(self, interaction: discord.Interaction, user: discord.Member, nickname: str = None):
        """Change a user's nickname."""
        try:
            # Check permissions
            if not Permissions.has_higher_role(interaction.user, user):
                await interaction.response.send_message(
                    "❌ You cannot change the nickname of someone with a higher or equal role!",
                    ephemeral=True
                )
                return
            
            old_nick = user.display_name
            
            try:
                await user.edit(nick=nickname)
                
                if nickname:
                    description = f"Changed {user.mention}'s nickname from `{old_nick}` to `{nickname}`"
                else:
                    description = f"Removed {user.mention}'s nickname (was `{old_nick}`)"
                
                embed = discord.Embed(
                    title="✏️ Nickname Changed",
                    description=description,
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                await interaction.response.send_message(embed=embed)
                
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ I don't have permission to change that user's nickname!",
                    ephemeral=True
                )
                return
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "nick", True)
            
        except Exception as e:
            logger.error(f"Error in nick command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while changing the nickname.",
                ephemeral=True
            )
    
    @app_commands.command(name="unlock", description="Manually unlock a specific or all channels")
    @app_commands.describe(channel="Optional: Specific channel to unlock (leave empty to unlock all)")
    @moderator_only()
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Unlock channels."""
        try:
            await interaction.response.defer()
            
            unlocked_channels = []
            
            if channel:
                # Unlock specific channel
                if channel.id in self.bot.db.locked_channels:
                    await self._unlock_channel(channel)
                    unlocked_channels.append(channel.mention)
                else:
                    await interaction.followup.send(
                        f"❌ {channel.mention} is not locked!",
                        ephemeral=True
                    )
                    return
            else:
                # Unlock all locked channels in the guild
                channels_to_unlock = []
                for channel_id, lock_info in self.bot.db.locked_channels.items():
                    if lock_info['guild_id'] == interaction.guild.id:
                        guild_channel = interaction.guild.get_channel(channel_id)
                        if guild_channel:
                            channels_to_unlock.append(guild_channel)
                
                for guild_channel in channels_to_unlock:
                    await self._unlock_channel(guild_channel)
                    unlocked_channels.append(guild_channel.mention)
            
            if unlocked_channels:
                embed = discord.Embed(
                    title="🔓 Channels Unlocked",
                    description=(
                        f"**Unlocked {len(unlocked_channels)} channel(s):**\n"
                        f"{', '.join(unlocked_channels[:10])}"
                        f"{'...' if len(unlocked_channels) > 10 else ''}\n\n"
                        f"**Unlocked by:** {interaction.user.mention}"
                    ),
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    "❌ No locked channels found!",
                    ephemeral=True
                )
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "unlock", len(unlocked_channels) > 0)
            
        except Exception as e:
            logger.error(f"Error in unlock command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while unlocking channels.",
                ephemeral=True
            )
    
    async def _unlock_channel(self, channel: discord.TextChannel):
        """Unlock a specific channel."""
        try:
            everyone_role = channel.guild.default_role
            overwrites = channel.overwrites
            
            if everyone_role in overwrites:
                overwrites[everyone_role].send_messages = None
                
                await channel.edit(
                    overwrites=overwrites,
                    reason="Manual unlock"
                )
                
                # Send unlock notification
                unlock_embed = discord.Embed(
                    title="🔓 Channel Unlocked",
                    description="This channel has been unlocked",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                await channel.send(embed=unlock_embed)
        
        except Exception as e:
            logger.error(f"Failed to unlock channel {channel.id}: {e}")
        
        # Remove lock info
        if channel.id in self.bot.db.locked_channels:
            del self.bot.db.locked_channels[channel.id]
