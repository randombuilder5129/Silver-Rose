import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import logging
from ..utils.permissions import admin_only, moderator_only, owner_only, Permissions

logger = logging.getLogger(__name__)

class CoreCommands(commands.Cog):
    """Core commands for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="announce", description="Schedule a message in a specified channel")
    @app_commands.describe(
        message="The message to announce",
        channel="The channel to send the announcement to",
        time="Time in format: YYYY-MM-DD HH:MM or in X minutes/hours/days",
        repeat="Repeat frequency (once, daily, weekly)"
    )
    @moderator_only()
    async def announce(
        self, 
        interaction: discord.Interaction,
        message: str,
        channel: discord.TextChannel,
        time: str,
        repeat: str = "once"
    ):
        """Schedule an announcement."""
        try:
            # Parse time
            scheduled_time = None
            
            # Check if it's a relative time (e.g., "30 minutes", "2 hours", "1 day")
            if any(unit in time.lower() for unit in ["minute", "hour", "day"]):
                parts = time.lower().split()
                if len(parts) >= 2:
                    try:
                        amount = int(parts[0])
                        unit = parts[1]
                        
                        if "minute" in unit:
                            scheduled_time = datetime.utcnow() + timedelta(minutes=amount)
                        elif "hour" in unit:
                            scheduled_time = datetime.utcnow() + timedelta(hours=amount)
                        elif "day" in unit:
                            scheduled_time = datetime.utcnow() + timedelta(days=amount)
                    except ValueError:
                        pass
            else:
                # Try to parse absolute time
                try:
                    scheduled_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
                except ValueError:
                    try:
                        scheduled_time = datetime.strptime(time, "%m-%d %H:%M")
                        # Assume current year
                        scheduled_time = scheduled_time.replace(year=datetime.utcnow().year)
                    except ValueError:
                        pass
            
            if not scheduled_time:
                await interaction.response.send_message(
                    "❌ Invalid time format. Use formats like:\n"
                    "• `30 minutes`\n"
                    "• `2 hours`\n"
                    "• `1 day`\n"
                    "• `2024-12-25 14:30`\n"
                    "• `12-25 14:30`",
                    ephemeral=True
                )
                return
            
            if scheduled_time <= datetime.utcnow():
                await interaction.response.send_message(
                    "❌ Scheduled time must be in the future!",
                    ephemeral=True
                )
                return
            
            if repeat not in ["once", "daily", "weekly"]:
                await interaction.response.send_message(
                    "❌ Repeat must be one of: once, daily, weekly",
                    ephemeral=True
                )
                return
            
            # Check bot permissions in target channel
            if not Permissions.check_bot_permissions(channel, "send_messages"):
                await interaction.response.send_message(
                    f"❌ I don't have permission to send messages in {channel.mention}!",
                    ephemeral=True
                )
                return
            
            # Schedule the announcement
            task_id = await self.bot.scheduler.schedule_announcement(
                interaction.guild.id,
                channel.id,
                message,
                scheduled_time,
                repeat
            )
            
            embed = discord.Embed(
                title="✅ Announcement Scheduled",
                description=(
                    f"**Message:** {message[:100]}{'...' if len(message) > 100 else ''}\n"
                    f"**Channel:** {channel.mention}\n"
                    f"**Time:** <t:{int(scheduled_time.timestamp())}:F>\n"
                    f"**Repeat:** {repeat.title()}"
                ),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "announce", True)
            
        except Exception as e:
            logger.error(f"Error in announce command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while scheduling the announcement.",
                ephemeral=True
            )
    
    @app_commands.command(name="logset", description="Set the channel where logs will be sent")
    @app_commands.describe(channel="The channel to send logs to")
    @admin_only()
    async def logset(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the log channel."""
        try:
            # Check bot permissions in target channel
            if not Permissions.check_bot_permissions(channel, "send_messages", "embed_links"):
                await interaction.response.send_message(
                    f"❌ I need Send Messages and Embed Links permissions in {channel.mention}!",
                    ephemeral=True
                )
                return
            
            # Set log channel
            self.bot.db.set_guild_config(interaction.guild.id, 'log_channel', channel.id)
            
            embed = discord.Embed(
                title="✅ Log Channel Set",
                description=f"Server logs will now be sent to {channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Send test log
            test_embed = discord.Embed(
                title="📋 Log Channel Configured",
                description=f"This channel has been set as the log channel by {interaction.user.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            await channel.send(embed=test_embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "logset", True)
            
        except Exception as e:
            logger.error(f"Error in logset command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting the log channel.",
                ephemeral=True
            )
    
    @app_commands.command(name="lock", description="Lock a single channel for a set duration")
    @app_commands.describe(
        channel="The channel to lock",
        duration="Duration in format: Xm (minutes), Xh (hours), Xd (days)"
    )
    @moderator_only()
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel, duration: str):
        """Lock a channel for a specified duration."""
        try:
            # Parse duration
            duration_seconds = None
            
            if duration.endswith('m'):
                try:
                    minutes = int(duration[:-1])
                    duration_seconds = minutes * 60
                except ValueError:
                    pass
            elif duration.endswith('h'):
                try:
                    hours = int(duration[:-1])
                    duration_seconds = hours * 3600
                except ValueError:
                    pass
            elif duration.endswith('d'):
                try:
                    days = int(duration[:-1])
                    duration_seconds = days * 86400
                except ValueError:
                    pass
            
            if not duration_seconds or duration_seconds <= 0:
                await interaction.response.send_message(
                    "❌ Invalid duration format. Use formats like: `30m`, `2h`, `1d`",
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
            
            # Lock the channel
            overwrites = channel.overwrites
            everyone_role = interaction.guild.default_role
            
            if everyone_role in overwrites:
                overwrites[everyone_role] = overwrites[everyone_role]
            else:
                overwrites[everyone_role] = discord.PermissionOverwrite()
            
            overwrites[everyone_role].send_messages = False
            
            await channel.edit(overwrites=overwrites, reason=f"Channel locked by {interaction.user}")
            
            # Store lock info
            unlock_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
            self.bot.db.locked_channels[channel.id] = {
                'guild_id': interaction.guild.id,
                'locked_by': interaction.user.id,
                'unlock_time': unlock_time,
                'original_overwrites': dict(channel.overwrites)
            }
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=(
                    f"**Channel:** {channel.mention}\n"
                    f"**Duration:** {duration}\n"
                    f"**Unlock Time:** <t:{int(unlock_time.timestamp())}:F>\n"
                    f"**Locked by:** {interaction.user.mention}"
                ),
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Send notification in locked channel
            lock_embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"This channel has been locked for {duration}",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            await channel.send(embed=lock_embed)
            
            # Schedule unlock
            await self._schedule_unlock(channel.id, duration_seconds)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "lock", True)
            
        except Exception as e:
            logger.error(f"Error in lock command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while locking the channel.",
                ephemeral=True
            )
    
    @app_commands.command(name="lockall", description="Locks all public channels server-wide")
    @owner_only()
    async def lockall(self, interaction: discord.Interaction):
        """Lock all channels in the server."""
        try:
            await interaction.response.defer()
            
            locked_channels = []
            everyone_role = interaction.guild.default_role
            
            for channel in interaction.guild.text_channels:
                try:
                    if Permissions.check_bot_permissions(channel, "manage_channels"):
                        overwrites = channel.overwrites
                        
                        if everyone_role in overwrites:
                            overwrites[everyone_role] = overwrites[everyone_role]
                        else:
                            overwrites[everyone_role] = discord.PermissionOverwrite()
                        
                        overwrites[everyone_role].send_messages = False
                        
                        await channel.edit(
                            overwrites=overwrites, 
                            reason=f"Server lockdown by {interaction.user}"
                        )
                        locked_channels.append(channel.mention)
                        
                        # Store lock info (no auto-unlock for lockall)
                        self.bot.db.locked_channels[channel.id] = {
                            'guild_id': interaction.guild.id,
                            'locked_by': interaction.user.id,
                            'unlock_time': None,  # Manual unlock required
                            'original_overwrites': dict(channel.overwrites)
                        }
                
                except Exception as e:
                    logger.error(f"Failed to lock channel {channel.name}: {e}")
            
            embed = discord.Embed(
                title="🔒 Server Lockdown Activated",
                description=(
                    f"**Locked {len(locked_channels)} channels**\n"
                    f"**Triggered by:** {interaction.user.mention}\n"
                    f"**Time:** <t:{int(datetime.utcnow().timestamp())}:F>\n\n"
                    "Use `/unlock` to unlock channels manually."
                ),
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.followup.send(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "lockall", True)
            
        except Exception as e:
            logger.error(f"Error in lockall command: {e}")
            await interaction.followup.send(
                "❌ An error occurred during server lockdown.",
                ephemeral=True
            )
    
    async def _schedule_unlock(self, channel_id: int, duration_seconds: int):
        """Schedule automatic channel unlock."""
        await asyncio.sleep(duration_seconds)
        
        if channel_id in self.bot.db.locked_channels:
            lock_info = self.bot.db.locked_channels[channel_id]
            guild = self.bot.get_guild(lock_info['guild_id'])
            
            if guild:
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        # Restore original permissions
                        everyone_role = guild.default_role
                        overwrites = channel.overwrites
                        
                        if everyone_role in overwrites:
                            overwrites[everyone_role].send_messages = None
                            
                            await channel.edit(
                                overwrites=overwrites,
                                reason="Automatic unlock after duration expired"
                            )
                            
                            # Send unlock notification
                            unlock_embed = discord.Embed(
                                title="🔓 Channel Unlocked",
                                description="Channel has been automatically unlocked",
                                color=discord.Color.green(),
                                timestamp=datetime.utcnow()
                            )
                            await channel.send(embed=unlock_embed)
                            
                    except Exception as e:
                        logger.error(f"Failed to auto-unlock channel {channel_id}: {e}")
            
            # Remove lock info
            del self.bot.db.locked_channels[channel_id]
