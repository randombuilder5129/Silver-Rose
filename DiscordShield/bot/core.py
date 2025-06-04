import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
import asyncio

from .utils.database import Database
from .utils.scheduler import Scheduler
from .commands.core import CoreCommands
from .commands.moderation import ModerationCommands
from .commands.economy import EconomyCommands
from .commands.utility import UtilityCommands
from .commands.community import CommunityCommands
from .events.moderation import ModerationEvents
from .events.economy import EconomyEvents
from .events.logging import LoggingEvents

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    """Main Discord bot class with comprehensive features."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="Comprehensive Discord bot with 35+ commands"
        )
        
        # Initialize database and scheduler
        self.db = Database()
        self.scheduler = Scheduler(self)
        
        # Rate limiting
        self.command_usage = {}
        
        # Anti-spam tracking
        self.message_tracking = {}
        
        # Start time for uptime tracking
        self.start_time = datetime.utcnow()
        
        # Setup event handlers
        self.setup_events()
        
    async def setup_hook(self):
        """Called when the bot is starting up."""
        logger.info("Setting up bot...")
        
        # Load command cogs
        await self.add_cog(CoreCommands(self))
        await self.add_cog(ModerationCommands(self))
        await self.add_cog(EconomyCommands(self))
        await self.add_cog(UtilityCommands(self))
        await self.add_cog(CommunityCommands(self))
        
        # Start background tasks
        self.passive_economy.start()
        self.cleanup_tasks.start()
        self.birthday_checker.start()
        self.qotd_scheduler.start()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    def setup_events(self):
        """Setup event handlers for moderation, economy, and logging."""
        self.moderation_events = ModerationEvents(self)
        self.economy_events = EconomyEvents(self)
        self.logging_events = LoggingEvents(self)
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Connected to {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /help | 35+ commands available"
            )
        )
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild."""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Initialize guild data
        self.db.init_guild(guild.id)
        
        # Send welcome message to system channel if available
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="Thanks for adding me!",
                description=(
                    "I'm a comprehensive Discord bot with 35+ commands!\n\n"
                    "**Get started:**\n"
                    "• Use `/help` to see all available commands\n"
                    "• Set up logging with `/logset`\n"
                    "• Configure server settings with `/serverconfig`\n\n"
                    "**Categories:**\n"
                    "• Core & Moderation\n"
                    "• Economy System\n"
                    "• Utilities\n"
                    "• Community Features"
                ),
                color=discord.Color.blue()
            )
            await guild.system_channel.send(embed=embed)
    
    @tasks.loop(hours=1)
    async def passive_economy(self):
        """Passive economy earning task."""
        try:
            await self.economy_events.process_passive_earnings()
        except Exception as e:
            logger.error(f"Error in passive economy task: {e}")
    
    @tasks.loop(hours=6)
    async def cleanup_tasks(self):
        """Cleanup expired data."""
        try:
            # Clean up expired warnings
            current_time = datetime.utcnow()
            for guild_id in self.db.warnings:
                guild_warnings = self.db.warnings[guild_id]
                for user_id in list(guild_warnings.keys()):
                    user_warnings = guild_warnings[user_id]
                    # Remove warnings older than 7 days
                    guild_warnings[user_id] = [
                        w for w in user_warnings 
                        if (current_time - w['timestamp']).days < 7
                    ]
                    if not guild_warnings[user_id]:
                        del guild_warnings[user_id]
            
            # Clean up message tracking
            cutoff_time = current_time - timedelta(minutes=5)
            for user_id in list(self.message_tracking.keys()):
                self.message_tracking[user_id] = [
                    msg_time for msg_time in self.message_tracking[user_id]
                    if msg_time > cutoff_time
                ]
                if not self.message_tracking[user_id]:
                    del self.message_tracking[user_id]
            
            logger.info("Completed cleanup tasks")
        except Exception as e:
            logger.error(f"Error in cleanup tasks: {e}")
    
    @tasks.loop(hours=1)
    async def birthday_checker(self):
        """Check for birthdays and send announcements."""
        try:
            current_date = datetime.utcnow().strftime("%m-%d")
            
            for guild_id, birthdays in self.db.birthdays.items():
                guild = self.get_guild(guild_id)
                if not guild:
                    continue
                
                for user_id, birthday_data in birthdays.items():
                    if birthday_data['date'] == current_date:
                        user = guild.get_member(user_id)
                        if user:
                            # Send birthday message
                            channel_id = self.db.get_guild_config(guild_id, 'birthday_channel')
                            if channel_id:
                                channel = guild.get_channel(channel_id)
                                if channel:
                                    embed = discord.Embed(
                                        title="🎉 Happy Birthday! 🎉",
                                        description=f"Wishing {user.mention} a very happy birthday!",
                                        color=discord.Color.gold()
                                    )
                                    await channel.send(embed=embed)
                                    
                                    # Give birthday tokens
                                    self.db.add_tokens(guild_id, user_id, 100)
        except Exception as e:
            logger.error(f"Error in birthday checker: {e}")
    
    @tasks.loop(hours=1)
    async def qotd_scheduler(self):
        """Schedule question of the day."""
        try:
            current_hour = datetime.utcnow().hour
            
            for guild_id in self.db.guild_configs:
                config = self.db.guild_configs[guild_id]
                qotd_hour = config.get('qotd_hour', 9)
                
                if current_hour == qotd_hour:
                    qotd_channel_id = config.get('qotd_channel')
                    if qotd_channel_id:
                        guild = self.get_guild(guild_id)
                        if guild:
                            channel = guild.get_channel(qotd_channel_id)
                            if channel:
                                # Get random question or use default
                                questions = [
                                    "What's your favorite hobby and why?",
                                    "If you could travel anywhere, where would you go?",
                                    "What's the best advice you've ever received?",
                                    "What's your favorite season and why?",
                                    "If you could have dinner with anyone, who would it be?"
                                ]
                                import random
                                question = random.choice(questions)
                                
                                embed = discord.Embed(
                                    title="📝 Question of the Day",
                                    description=question,
                                    color=discord.Color.purple(),
                                    timestamp=datetime.utcnow()
                                )
                                message = await channel.send(embed=embed)
                                await message.add_reaction("💭")
        except Exception as e:
            logger.error(f"Error in QOTD scheduler: {e}")
    
    async def is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited."""
        current_time = datetime.utcnow()
        
        if user_id in self.command_usage:
            last_used = self.command_usage[user_id]
            if (current_time - last_used).total_seconds() < 5:
                return True
        
        self.command_usage[user_id] = current_time
        return False
    
    async def check_spam(self, message):
        """Check for spam and take action if necessary."""
        user_id = message.author.id
        current_time = datetime.utcnow()
        
        # Initialize tracking for user
        if user_id not in self.message_tracking:
            self.message_tracking[user_id] = []
        
        # Add current message time
        self.message_tracking[user_id].append(current_time)
        
        # Clean old messages (older than 1 minute)
        cutoff_time = current_time - timedelta(minutes=1)
        self.message_tracking[user_id] = [
            msg_time for msg_time in self.message_tracking[user_id]
            if msg_time > cutoff_time
        ]
        
        # Check if spam threshold exceeded
        if len(self.message_tracking[user_id]) > 10:  # 10 messages per minute
            try:
                # Timeout user for 5 minutes
                await message.author.timeout(
                    timedelta(minutes=5),
                    reason="Automatic spam detection"
                )
                
                # Log the action
                await self.logging_events.log_action(
                    message.guild,
                    "Auto-Timeout",
                    f"{message.author.mention} was automatically timed out for spam",
                    discord.Color.orange()
                )
                
                return True
            except discord.Forbidden:
                pass
        
        return False
