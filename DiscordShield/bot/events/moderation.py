import discord
from discord.ext import commands
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)

class ModerationEvents:
    """Event handlers for automated moderation features."""
    
    def __init__(self, bot):
        self.bot = bot
        self.setup_events()
        
        # Raid detection tracking
        self.recent_joins = {}
        
        # DM spam tracking
        self.dm_tracking = {}
    
    def setup_events(self):
        """Set up event handlers."""
        
        @self.bot.event
        async def on_message(message):
            """Handle message events for spam detection and word filtering."""
            if message.author.bot or not message.guild:
                return
            
            # Check for spam
            is_spam = await self.bot.check_spam(message)
            if is_spam:
                return
            
            # Check word filter
            await self.check_word_filter(message)
            
            # Process commands (this ensures commands still work)
            await self.bot.process_commands(message)
        
        @self.bot.event
        async def on_member_join(member):
            """Handle member join events for raid detection."""
            await self.check_raid_detection(member)
            
            # Auto-role assignment
            auto_role_id = self.bot.db.get_guild_config(member.guild.id, 'auto_role')
            if auto_role_id:
                auto_role = member.guild.get_role(auto_role_id)
                if auto_role and auto_role < member.guild.me.top_role:
                    try:
                        await member.add_roles(auto_role, reason="Auto-role assignment")
                    except discord.Forbidden:
                        logger.warning(f"Failed to assign auto-role in {member.guild.name}")
            
            # Welcome message
            welcome_channel_id = self.bot.db.get_guild_config(member.guild.id, 'welcome_channel')
            if welcome_channel_id:
                welcome_channel = member.guild.get_channel(welcome_channel_id)
                if welcome_channel:
                    embed = discord.Embed(
                        title="👋 Welcome!",
                        description=f"Welcome to **{member.guild.name}**, {member.mention}!",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(
                        name="📋 Getting Started",
                        value=(
                            "• Check out the rules\n"
                            "• Introduce yourself\n"
                            "• Have fun!"
                        ),
                        inline=False
                    )
                    
                    try:
                        await welcome_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
        
        @self.bot.event
        async def on_member_update(before, after):
            """Handle member update events for boost detection."""
            # Check for server boost changes
            if before.premium_since != after.premium_since:
                if after.premium_since:  # User started boosting
                    await self.handle_boost_start(after)
                elif before.premium_since:  # User stopped boosting
                    await self.handle_boost_end(after)
        
        @self.bot.event
        async def on_raw_reaction_add(payload):
            """Handle reaction role assignments."""
            await self.handle_reaction_role(payload, add=True)
        
        @self.bot.event
        async def on_raw_reaction_remove(payload):
            """Handle reaction role removals."""
            await self.handle_reaction_role(payload, add=False)
    
    async def check_word_filter(self, message):
        """Check message against word filter."""
        try:
            banned_words = self.bot.db.word_filters.get(message.guild.id, [])
            if not banned_words:
                return
            
            content_lower = message.content.lower()
            
            # Check for banned words
            for word in banned_words:
                if re.search(r'\b' + re.escape(word.lower()) + r'\b', content_lower):
                    try:
                        await message.delete()
                        
                        # Send warning to user
                        embed = discord.Embed(
                            title="⚠️ Message Filtered",
                            description=f"Your message contained a banned word and was removed.",
                            color=discord.Color.orange(),
                            timestamp=datetime.utcnow()
                        )
                        
                        try:
                            await message.author.send(embed=embed)
                        except discord.Forbidden:
                            pass  # User has DMs disabled
                        
                        # Log the action
                        log_channel_id = self.bot.db.get_guild_config(message.guild.id, 'log_channel')
                        if log_channel_id:
                            log_channel = message.guild.get_channel(log_channel_id)
                            if log_channel:
                                log_embed = discord.Embed(
                                    title="🔍 Word Filter Triggered",
                                    description=(
                                        f"**User:** {message.author.mention}\n"
                                        f"**Channel:** {message.channel.mention}\n"
                                        f"**Triggered Word:** ||{word}||"
                                    ),
                                    color=discord.Color.red(),
                                    timestamp=datetime.utcnow()
                                )
                                await log_channel.send(embed=log_embed)
                        
                        return True
                    
                    except discord.NotFound:
                        pass  # Message already deleted
                    except discord.Forbidden:
                        pass  # No permission to delete
            
            return False
            
        except Exception as e:
            logger.error(f"Error in word filter: {e}")
    
    async def check_raid_detection(self, member):
        """Check for potential raid and trigger lockdown if needed."""
        try:
            guild_id = member.guild.id
            current_time = datetime.utcnow()
            
            # Initialize tracking for guild
            if guild_id not in self.recent_joins:
                self.recent_joins[guild_id] = []
            
            # Add current join
            self.recent_joins[guild_id].append(current_time)
            
            # Clean old joins (older than 60 seconds)
            cutoff_time = current_time - timedelta(seconds=60)
            self.recent_joins[guild_id] = [
                join_time for join_time in self.recent_joins[guild_id]
                if join_time > cutoff_time
            ]
            
            # Check if raid threshold exceeded (10 joins in 60 seconds)
            if len(self.recent_joins[guild_id]) >= 10:
                logger.warning(f"Raid detected in {member.guild.name}! Triggering lockdown.")
                
                # Trigger automatic lockdown
                await self.trigger_raid_lockdown(member.guild)
                
                # Reset counter
                self.recent_joins[guild_id] = []
            
        except Exception as e:
            logger.error(f"Error in raid detection: {e}")
    
    async def trigger_raid_lockdown(self, guild):
        """Trigger automatic server lockdown due to raid detection."""
        try:
            locked_channels = []
            everyone_role = guild.default_role
            
            for channel in guild.text_channels:
                try:
                    if channel.permissions_for(guild.me).manage_channels:
                        overwrites = channel.overwrites
                        
                        if everyone_role in overwrites:
                            overwrites[everyone_role] = overwrites[everyone_role]
                        else:
                            overwrites[everyone_role] = discord.PermissionOverwrite()
                        
                        overwrites[everyone_role].send_messages = False
                        
                        await channel.edit(
                            overwrites=overwrites,
                            reason="Automatic raid detection lockdown"
                        )
                        locked_channels.append(channel.mention)
                        
                        # Store lock info
                        self.bot.db.locked_channels[channel.id] = {
                            'guild_id': guild.id,
                            'locked_by': guild.me.id,
                            'unlock_time': None,  # Manual unlock required
                            'original_overwrites': dict(channel.overwrites),
                            'raid_lockdown': True
                        }
                
                except Exception as e:
                    logger.error(f"Failed to lock channel {channel.name}: {e}")
            
            # Log the raid lockdown
            log_channel_id = self.bot.db.get_guild_config(guild.id, 'log_channel')
            if log_channel_id:
                log_channel = guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="🚨 RAID DETECTED - AUTOMATIC LOCKDOWN",
                        description=(
                            f"**Locked {len(locked_channels)} channels**\n"
                            f"**Trigger:** 10+ members joined within 60 seconds\n"
                            f"**Time:** <t:{int(datetime.utcnow().timestamp())}:F>\n\n"
                            "**Manual unlock required using `/unlock` command.**"
                        ),
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    await log_channel.send(embed=embed)
            
            # Try to notify owner
            if guild.owner:
                try:
                    dm_embed = discord.Embed(
                        title=f"🚨 Raid Detected in {guild.name}",
                        description=(
                            "Automatic server lockdown has been triggered due to raid detection.\n"
                            f"**Locked Channels:** {len(locked_channels)}\n"
                            "Use `/unlock` to manually unlock channels when the raid has stopped."
                        ),
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    await guild.owner.send(embed=dm_embed)
                except discord.Forbidden:
                    pass  # Owner has DMs disabled
            
        except Exception as e:
            logger.error(f"Error in raid lockdown: {e}")
    
    async def handle_boost_start(self, member):
        """Handle when a member starts boosting."""
        try:
            # Give boost role
            boost_role_id = self.bot.db.get_guild_config(member.guild.id, 'boost_role')
            if boost_role_id:
                boost_role = member.guild.get_role(boost_role_id)
                if boost_role and boost_role < member.guild.me.top_role:
                    try:
                        await member.add_roles(boost_role, reason="Server boost reward")
                    except discord.Forbidden:
                        pass
            
            # Give bonus tokens
            boost_tokens = self.bot.db.get_guild_config(member.guild.id, 'boost_tokens') or 0
            if boost_tokens > 0:
                self.bot.db.add_tokens(member.guild.id, member.id, boost_tokens)
            
            # Send thank you message
            embed = discord.Embed(
                title="🚀 Thank You for Boosting!",
                description=(
                    f"Thanks for boosting **{member.guild.name}**, {member.mention}!\n\n"
                    f"**Rewards:**\n"
                    f"• Role: {boost_role.mention if boost_role_id and member.guild.get_role(boost_role_id) else 'None'}\n"
                    f"• Bonus tokens: {boost_tokens:,}"
                ),
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            # Send in system channel or log channel
            channel = member.guild.system_channel
            if not channel:
                log_channel_id = self.bot.db.get_guild_config(member.guild.id, 'log_channel')
                if log_channel_id:
                    channel = member.guild.get_channel(log_channel_id)
            
            if channel:
                await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error handling boost start: {e}")
    
    async def handle_boost_end(self, member):
        """Handle when a member stops boosting."""
        try:
            # Remove boost role
            boost_role_id = self.bot.db.get_guild_config(member.guild.id, 'boost_role')
            if boost_role_id:
                boost_role = member.guild.get_role(boost_role_id)
                if boost_role and boost_role in member.roles:
                    try:
                        await member.remove_roles(boost_role, reason="Server boost ended")
                    except discord.Forbidden:
                        pass
            
        except Exception as e:
            logger.error(f"Error handling boost end: {e}")
    
    async def handle_reaction_role(self, payload, add=True):
        """Handle reaction role assignment/removal."""
        try:
            if payload.user_id == self.bot.user.id:
                return
            
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            member = guild.get_member(payload.user_id)
            if not member:
                return
            
            # Check if this message has reaction roles
            reaction_roles = self.bot.db.reaction_roles.get(guild.id, {})
            message_reactions = reaction_roles.get(payload.message_id, {})
            
            emoji_str = str(payload.emoji)
            if emoji_str not in message_reactions:
                return
            
            role_id = message_reactions[emoji_str]
            role = guild.get_role(role_id)
            
            if not role:
                # Role was deleted, remove from database
                del message_reactions[emoji_str]
                return
            
            # Check bot permissions
            if role >= guild.me.top_role:
                return
            
            try:
                if add and role not in member.roles:
                    await member.add_roles(role, reason="Reaction role assignment")
                elif not add and role in member.roles:
                    await member.remove_roles(role, reason="Reaction role removal")
            
            except discord.Forbidden:
                logger.warning(f"Failed to assign reaction role {role.name} in {guild.name}")
            
        except Exception as e:
            logger.error(f"Error in reaction role handler: {e}")
    
    async def check_dm_spam(self, user_id):
        """Check for DM spam attempts."""
        try:
            current_time = datetime.utcnow()
            
            if user_id not in self.dm_tracking:
                self.dm_tracking[user_id] = []
            
            # Add current attempt
            self.dm_tracking[user_id].append(current_time)
            
            # Clean old attempts (older than 5 minutes)
            cutoff_time = current_time - timedelta(minutes=5)
            self.dm_tracking[user_id] = [
                attempt_time for attempt_time in self.dm_tracking[user_id]
                if attempt_time > cutoff_time
            ]
            
            # Check if spam threshold exceeded (5 DM attempts in 5 minutes)
            if len(self.dm_tracking[user_id]) >= 5:
                # Timeout user in all mutual guilds
                user = self.bot.get_user(user_id)
                if user:
                    for guild in self.bot.guilds:
                        member = guild.get_member(user_id)
                        if member:
                            try:
                                await member.timeout(
                                    timedelta(minutes=10),
                                    reason="Automatic DM spam detection"
                                )
                            except discord.Forbidden:
                                pass
                
                # Reset counter
                self.dm_tracking[user_id] = []
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in DM spam check: {e}")
            return False
