import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import time
import logging
from ..utils.permissions import moderator_only, admin_only

logger = logging.getLogger(__name__)

class UtilityCommands(commands.Cog):
    """Utility commands for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Check bot latency and response time")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency and response time."""
        try:
            # Record start time
            start_time = time.time()
            
            # Get API latency
            api_latency = round(self.bot.latency * 1000, 2)
            
            # Create initial embed
            embed = discord.Embed(
                title="🏓 Pong!",
                description="Calculating response time...",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Send initial response
            await interaction.response.send_message(embed=embed)
            
            # Calculate response time
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            # Update embed with actual times
            embed.description = (
                f"**API Latency:** {api_latency}ms\n"
                f"**Response Time:** {response_time}ms\n"
                f"**Status:** {'🟢 Excellent' if api_latency < 100 else '🟡 Good' if api_latency < 300 else '🔴 Poor'}"
            )
            
            # Add bot info
            embed.add_field(
                name="📊 Bot Info",
                value=(
                    f"**Guilds:** {len(self.bot.guilds)}\n"
                    f"**Users:** {len(set(self.bot.get_all_members()))}\n"
                    f"**Commands:** 35+"
                ),
                inline=True
            )
            
            # Add uptime info
            uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
            if uptime:
                hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{hours}h {minutes}m {seconds}s"
            else:
                uptime_str = "Unknown"
            
            embed.add_field(
                name="⏱️ Uptime",
                value=uptime_str,
                inline=True
            )
            
            await interaction.edit_original_response(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "ping", True)
            
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while checking ping.",
                ephemeral=True
            )

    @app_commands.command(name="commands", description="View all available bot commands")
    async def commands(self, interaction: discord.Interaction):
        """Display all available bot commands organized by category."""
        try:
            embed = discord.Embed(
                title="📚 Bot Commands",
                description="Here are all available commands organized by category:",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            # Core Commands
            embed.add_field(
                name="🔧 Core Commands (4)",
                value=(
                    "`/announce` - Schedule messages\n"
                    "`/logset` - Set logging channel\n"
                    "`/lock` - Lock channel temporarily\n"
                    "`/lockall` - Emergency server lockdown"
                ),
                inline=False
            )
            
            # Moderation Commands
            embed.add_field(
                name="🛡️ Moderation Commands (7)",
                value=(
                    "`/warn` - Warn a user\n"
                    "`/warnings` - View user warnings\n"
                    "`/removewarning` - Remove specific warning\n"
                    "`/clear` - Delete messages\n"
                    "`/slowmode` - Set channel slowmode\n"
                    "`/nick` - Change user nickname\n"
                    "`/unlock` - Unlock channels"
                ),
                inline=False
            )
            
            # Economy Commands
            embed.add_field(
                name="💰 Economy Commands (9)",
                value=(
                    "`/balance` - Check token balance\n"
                    "`/gamble` - Risk tokens for rewards\n"
                    "`/steal` - Attempt to steal tokens\n"
                    "`/give` - Transfer tokens\n"
                    "`/leaderboard` - View top users\n"
                    "`/shop` - Browse shop items\n"
                    "`/buy` - Purchase items\n"
                    "`/sell` - Sell items back\n"
                    "`/economy` - Toggle economy system"
                ),
                inline=False
            )
            
            # Utility Commands
            embed.add_field(
                name="🔧 Utility Commands (8)",
                value=(
                    "`/ping` - Check bot latency\n"
                    "`/commands` - Show this list\n"
                    "`/remindme` - Set reminders\n"
                    "`/poll` - Create polls\n"
                    "`/suggest` - Make suggestions\n"
                    "`/serverstats` - Server statistics\n"
                    "`/userinfo` - User information\n"
                    "`/serverconfig` - Configure settings"
                ),
                inline=False
            )
            
            # Community Commands
            embed.add_field(
                name="👥 Community Commands (9)",
                value=(
                    "`/reactionroles` - Set up reaction roles\n"
                    "`/birthday` - Set your birthday\n"
                    "`/qotd` - Question of the day\n"
                    "`/ticket` - Create support ticket\n"
                    "`/giveaway` - Host giveaways\n"
                    "`/boostconfig` - Configure boost rewards"
                ),
                inline=False
            )
            
            # Automated Features
            embed.add_field(
                name="🤖 Automated Features",
                value=(
                    "• Anti-spam detection & timeouts\n"
                    "• Raid detection & auto-lockdown\n"
                    "• Word filtering system\n"
                    "• Passive economy earnings\n"
                    "• Birthday celebrations\n"
                    "• Server boost rewards\n"
                    "• Comprehensive logging\n"
                    "• Reaction role management"
                ),
                inline=False
            )
            
            embed.set_footer(
                text=f"Total: 37 commands | Requested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "commands", True)
            
        except Exception as e:
            logger.error(f"Error in commands command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while displaying commands.",
                ephemeral=True
            )

    @app_commands.command(name="remindme", description="Set a reminder")
    @app_commands.describe(
        time="Time format: Xm (minutes), Xh (hours), Xd (days)",
        message="What to remind you about"
    )
    async def remindme(self, interaction: discord.Interaction, time: str, message: str):
        """Set a reminder."""
        try:
            # Parse time
            reminder_time = None
            
            if time.endswith('m'):
                try:
                    minutes = int(time[:-1])
                    reminder_time = datetime.utcnow() + timedelta(minutes=minutes)
                except ValueError:
                    pass
            elif time.endswith('h'):
                try:
                    hours = int(time[:-1])
                    reminder_time = datetime.utcnow() + timedelta(hours=hours)
                except ValueError:
                    pass
            elif time.endswith('d'):
                try:
                    days = int(time[:-1])
                    reminder_time = datetime.utcnow() + timedelta(days=days)
                except ValueError:
                    pass
            
            if not reminder_time:
                await interaction.response.send_message(
                    "❌ Invalid time format! Use formats like: `30m`, `2h`, `1d`",
                    ephemeral=True
                )
                return
            
            if len(message) > 500:
                await interaction.response.send_message(
                    "❌ Reminder message is too long! Maximum 500 characters.",
                    ephemeral=True
                )
                return
            
            # Schedule reminder
            task_id = await self.bot.scheduler.schedule_reminder(
                interaction.user.id,
                interaction.channel.id,
                message,
                reminder_time
            )
            
            embed = discord.Embed(
                title="⏰ Reminder Set",
                description=(
                    f"**Message:** {message}\n"
                    f"**Time:** <t:{int(reminder_time.timestamp())}:F>\n"
                    f"**In:** <t:{int(reminder_time.timestamp())}:R>"
                ),
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "remindme", True)
            
        except Exception as e:
            logger.error(f"Error in remindme command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting the reminder.",
                ephemeral=True
            )
    
    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)"
    )
    async def poll(
        self, 
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None
    ):
        """Create a poll."""
        try:
            options = [option1, option2]
            if option3:
                options.append(option3)
            if option4:
                options.append(option4)
            if option5:
                options.append(option5)
            
            # Reaction emojis
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            
            embed = discord.Embed(
                title="📊 Poll",
                description=f"**{question}**",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            poll_text = ""
            for i, option in enumerate(options):
                poll_text += f"{emojis[i]} {option}\n"
            
            embed.add_field(name="Options", value=poll_text, inline=False)
            embed.set_footer(text=f"Poll created by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
            # Get the message to add reactions
            message = await interaction.original_response()
            
            # Add reactions
            for i in range(len(options)):
                await message.add_reaction(emojis[i])
            
            # Store poll data
            poll_id = f"{interaction.guild.id}-{message.id}"
            self.bot.db.polls[poll_id] = {
                'question': question,
                'options': options,
                'creator': interaction.user.id,
                'channel': interaction.channel.id,
                'created_at': datetime.utcnow()
            }
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "poll", True)
            
        except Exception as e:
            logger.error(f"Error in poll command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while creating the poll.",
                ephemeral=True
            )
    
    @app_commands.command(name="suggest", description="Make a suggestion")
    @app_commands.describe(suggestion="Your suggestion for the server")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        """Make a suggestion."""
        try:
            if len(suggestion) > 1000:
                await interaction.response.send_message(
                    "❌ Suggestion is too long! Maximum 1000 characters.",
                    ephemeral=True
                )
                return
            
            # Check if suggestion channel is set
            suggestion_channel_id = self.bot.db.get_guild_config(interaction.guild.id, 'suggestion_channel')
            suggestion_channel = None
            
            if suggestion_channel_id:
                suggestion_channel = interaction.guild.get_channel(suggestion_channel_id)
            
            if not suggestion_channel:
                suggestion_channel = interaction.channel
            
            # Create suggestion embed
            embed = discord.Embed(
                title="💡 New Suggestion",
                description=suggestion,
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(
                name=interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            embed.set_footer(text=f"Suggestion #{len(self.bot.db.suggestions.get(interaction.guild.id, [])) + 1}")
            
            # Send suggestion
            if suggestion_channel == interaction.channel:
                await interaction.response.send_message(embed=embed)
                message = await interaction.original_response()
            else:
                message = await suggestion_channel.send(embed=embed)
                await interaction.response.send_message(
                    f"✅ Your suggestion has been posted in {suggestion_channel.mention}!",
                    ephemeral=True
                )
            
            # Add voting reactions
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            
            # Store suggestion
            if interaction.guild.id not in self.bot.db.suggestions:
                self.bot.db.suggestions[interaction.guild.id] = []
            
            self.bot.db.suggestions[interaction.guild.id].append({
                'id': len(self.bot.db.suggestions[interaction.guild.id]) + 1,
                'user_id': interaction.user.id,
                'suggestion': suggestion,
                'message_id': message.id,
                'channel_id': suggestion_channel.id,
                'created_at': datetime.utcnow()
            })
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "suggest", True)
            
        except Exception as e:
            logger.error(f"Error in suggest command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while submitting your suggestion.",
                ephemeral=True
            )
    
    @app_commands.command(name="serverstats", description="View server statistics")
    async def serverstats(self, interaction: discord.Interaction):
        """View server statistics."""
        try:
            guild = interaction.guild
            
            # Count members by status
            online = sum(1 for member in guild.members if member.status == discord.Status.online)
            idle = sum(1 for member in guild.members if member.status == discord.Status.idle)
            dnd = sum(1 for member in guild.members if member.status == discord.Status.dnd)
            offline = sum(1 for member in guild.members if member.status == discord.Status.offline)
            
            # Count bots
            bots = sum(1 for member in guild.members if member.bot)
            humans = guild.member_count - bots
            
            # Channel counts
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            
            # Role count
            roles = len(guild.roles) - 1  # Exclude @everyone
            
            embed = discord.Embed(
                title=f"📊 {guild.name} Statistics",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            # Member stats
            embed.add_field(
                name="👥 Members",
                value=(
                    f"**Total:** {guild.member_count:,}\n"
                    f"**Humans:** {humans:,}\n"
                    f"**Bots:** {bots:,}"
                ),
                inline=True
            )
            
            # Status stats
            embed.add_field(
                name="🟢 Status",
                value=(
                    f"**Online:** {online:,}\n"
                    f"**Idle:** {idle:,}\n"
                    f"**DND:** {dnd:,}\n"
                    f"**Offline:** {offline:,}"
                ),
                inline=True
            )
            
            # Channel stats
            embed.add_field(
                name="📝 Channels",
                value=(
                    f"**Text:** {text_channels:,}\n"
                    f"**Voice:** {voice_channels:,}\n"
                    f"**Categories:** {categories:,}"
                ),
                inline=True
            )
            
            # Server info
            embed.add_field(
                name="ℹ️ Server Info",
                value=(
                    f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
                    f"**Created:** <t:{int(guild.created_at.timestamp())}:D>\n"
                    f"**Roles:** {roles:,}\n"
                    f"**Boost Level:** {guild.premium_tier}\n"
                    f"**Boosts:** {guild.premium_subscription_count}"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "serverstats", True)
            
        except Exception as e:
            logger.error(f"Error in serverstats command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching server statistics.",
                ephemeral=True
            )
    
    @app_commands.command(name="userinfo", description="View information about a user")
    @app_commands.describe(user="The user to get information about")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """View user information."""
        try:
            target_user = user or interaction.user
            
            embed = discord.Embed(
                title=f"👤 {target_user.display_name}",
                color=target_user.color if target_user.color != discord.Color.default() else discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Basic info
            embed.add_field(
                name="📋 Basic Info",
                value=(
                    f"**Username:** {target_user.name}\n"
                    f"**Display Name:** {target_user.display_name}\n"
                    f"**ID:** {target_user.id}\n"
                    f"**Bot:** {'Yes' if target_user.bot else 'No'}"
                ),
                inline=True
            )
            
            # Status info
            status_emoji = {
                discord.Status.online: "🟢",
                discord.Status.idle: "🟡",
                discord.Status.dnd: "🔴",
                discord.Status.offline: "⚫"
            }
            
            embed.add_field(
                name="📱 Status",
                value=(
                    f"**Status:** {status_emoji.get(target_user.status, '❓')} {target_user.status.name.title()}\n"
                    f"**Activity:** {target_user.activity.name if target_user.activity else 'None'}"
                ),
                inline=True
            )
            
            # Server info
            embed.add_field(
                name="🏠 Server Info",
                value=(
                    f"**Joined:** <t:{int(target_user.joined_at.timestamp())}:D>\n"
                    f"**Account Created:** <t:{int(target_user.created_at.timestamp())}:D>\n"
                    f"**Roles:** {len(target_user.roles) - 1}"  # Exclude @everyone
                ),
                inline=True
            )
            
            # Permissions (if user has notable perms)
            key_perms = []
            if target_user.guild_permissions.administrator:
                key_perms.append("Administrator")
            elif target_user.guild_permissions.manage_guild:
                key_perms.append("Manage Server")
            elif target_user.guild_permissions.manage_channels:
                key_perms.append("Manage Channels")
            elif target_user.guild_permissions.manage_messages:
                key_perms.append("Manage Messages")
            elif target_user.guild_permissions.kick_members:
                key_perms.append("Kick Members")
            elif target_user.guild_permissions.ban_members:
                key_perms.append("Ban Members")
            
            if key_perms:
                embed.add_field(
                    name="🔑 Key Permissions",
                    value="\n".join(f"• {perm}" for perm in key_perms[:5]),
                    inline=False
                )
            
            # Top roles (max 5)
            top_roles = sorted(target_user.roles[1:], key=lambda r: r.position, reverse=True)[:5]
            if top_roles:
                embed.add_field(
                    name="🏷️ Top Roles",
                    value=" ".join(role.mention for role in top_roles),
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "userinfo", True)
            
        except Exception as e:
            logger.error(f"Error in userinfo command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching user information.",
                ephemeral=True
            )
    
    @app_commands.command(name="serverconfig", description="Configure server settings")
    @app_commands.describe(
        setting="The setting to configure",
        value="The new value for the setting"
    )
    @admin_only()
    async def serverconfig(self, interaction: discord.Interaction, setting: str, value: str = None):
        """Configure server settings."""
        try:
            valid_settings = {
                'welcome_channel': 'Welcome channel for new members',
                'birthday_channel': 'Channel for birthday announcements',
                'qotd_channel': 'Channel for question of the day',
                'suggestion_channel': 'Channel for suggestions',
                'qotd_hour': 'Hour to post question of the day (0-23)',
                'prefix': 'Bot command prefix'
            }
            
            if not value:
                # Show current configuration
                embed = discord.Embed(
                    title="⚙️ Server Configuration",
                    description="Current server settings:",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                for config_key, description in valid_settings.items():
                    current_value = self.bot.db.get_guild_config(interaction.guild.id, config_key)
                    
                    if config_key.endswith('_channel') and current_value:
                        channel = interaction.guild.get_channel(current_value)
                        display_value = channel.mention if channel else f"#{current_value} (deleted)"
                    else:
                        display_value = str(current_value) if current_value is not None else "Not set"
                    
                    embed.add_field(
                        name=f"**{config_key}**",
                        value=f"{description}\n*Current:* {display_value}",
                        inline=False
                    )
                
                embed.add_field(
                    name="📝 Usage",
                    value="Use `/serverconfig <setting> <value>` to change a setting",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
                return
            
            if setting not in valid_settings:
                await interaction.response.send_message(
                    f"❌ Invalid setting! Valid settings are:\n" +
                    "\n".join(f"• **{k}**: {v}" for k, v in valid_settings.items()),
                    ephemeral=True
                )
                return
            
            # Handle different setting types
            if setting.endswith('_channel'):
                # Channel setting
                try:
                    if value.lower() in ['none', 'null', 'disable']:
                        new_value = None
                        display_value = "Disabled"
                    else:
                        # Try to parse channel mention or ID
                        if value.startswith('<#') and value.endswith('>'):
                            channel_id = int(value[2:-1])
                        else:
                            channel_id = int(value)
                        
                        channel = interaction.guild.get_channel(channel_id)
                        if not channel:
                            await interaction.response.send_message(
                                f"❌ Channel with ID {channel_id} not found!",
                                ephemeral=True
                            )
                            return
                        
                        new_value = channel_id
                        display_value = channel.mention
                
                except ValueError:
                    # Try to find channel by name
                    channel = discord.utils.get(interaction.guild.channels, name=value)
                    if not channel:
                        await interaction.response.send_message(
                            f"❌ Channel '{value}' not found!",
                            ephemeral=True
                        )
                        return
                    
                    new_value = channel.id
                    display_value = channel.mention
            
            elif setting == 'qotd_hour':
                # Hour setting
                try:
                    hour = int(value)
                    if hour < 0 or hour > 23:
                        await interaction.response.send_message(
                            "❌ Hour must be between 0 and 23!",
                            ephemeral=True
                        )
                        return
                    new_value = hour
                    display_value = f"{hour:02d}:00"
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Hour must be a number between 0 and 23!",
                        ephemeral=True
                    )
                    return
            
            else:
                # String setting
                new_value = value
                display_value = value
            
            # Update configuration
            self.bot.db.set_guild_config(interaction.guild.id, setting, new_value)
            
            embed = discord.Embed(
                title="✅ Configuration Updated",
                description=(
                    f"**Setting:** {setting}\n"
                    f"**New Value:** {display_value}"
                ),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "serverconfig", True)
            
        except Exception as e:
            logger.error(f"Error in serverconfig command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while updating server configuration.",
                ephemeral=True
            )
