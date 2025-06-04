import discord
from discord.ext import commands
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EconomyEvents:
    """Event handlers for economy system features."""
    
    def __init__(self, bot):
        self.bot = bot
        self.setup_events()
    
    def setup_events(self):
        """Set up economy-related event handlers."""
        
        @self.bot.event
        async def on_message(message):
            """Handle passive economy earning on message."""
            if message.author.bot or not message.guild:
                return
            
            # Update passive earnings when user is active
            self.bot.db.update_passive_earning(message.guild.id, message.author.id)
    
    async def process_passive_earnings(self):
        """Process passive earnings for all users."""
        try:
            logger.info("Processing passive earnings...")
            
            total_processed = 0
            total_earned = 0
            
            for guild_id, users in self.bot.db.economy.items():
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                
                for user_id, user_data in users.items():
                    member = guild.get_member(user_id)
                    if not member:
                        continue
                    
                    current_time = datetime.utcnow()
                    last_passive = user_data.get('last_passive', current_time)
                    
                    # Calculate hours passed
                    hours_passed = (current_time - last_passive).total_seconds() / 3600
                    
                    if hours_passed >= 1:
                        # Earn 0.125 tokens per hour
                        tokens_earned = int(hours_passed * 0.125)
                        
                        if tokens_earned > 0:
                            old_balance = user_data['tokens']
                            self.bot.db.add_tokens(guild_id, user_id, tokens_earned)
                            user_data['last_passive'] = current_time
                            
                            total_processed += 1
                            total_earned += tokens_earned
                            
                            logger.debug(f"User {user_id} earned {tokens_earned} passive tokens")
            
            logger.info(f"Passive earnings complete: {total_processed} users processed, {total_earned} total tokens earned")
            
        except Exception as e:
            logger.error(f"Error processing passive earnings: {e}")
    
    async def handle_economy_milestone(self, guild_id, user_id, old_balance, new_balance):
        """Handle economy milestones and achievements."""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            member = guild.get_member(user_id)
            if not member:
                return
            
            # Check for milestone achievements
            milestones = [
                (1000, "🌱 First Thousand", "Reached 1,000 tokens!"),
                (5000, "⭐ Rising Star", "Reached 5,000 tokens!"),
                (10000, "🥉 Bronze Tier", "Reached 10,000 tokens!"),
                (25000, "🥈 Silver Tier", "Reached 25,000 tokens!"),
                (50000, "🥇 Gold Tier", "Reached 50,000 tokens!"),
                (100000, "👑 Platinum Tier", "Reached 100,000 tokens!"),
                (250000, "💎 Diamond Tier", "Reached 250,000 tokens!"),
                (500000, "🌟 Elite Status", "Reached 500,000 tokens!"),
                (1000000, "🏆 Token Millionaire", "Reached 1,000,000 tokens!")
            ]
            
            for threshold, title, description in milestones:
                if old_balance < threshold <= new_balance:
                    # Send milestone achievement
                    embed = discord.Embed(
                        title="🎉 Milestone Achievement!",
                        description=f"**{title}**\n{description}",
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_author(
                        name=member.display_name,
                        icon_url=member.display_avatar.url
                    )
                    
                    # Try to send in economy channel or system channel
                    channel = guild.system_channel
                    if not channel:
                        log_channel_id = self.bot.db.get_guild_config(guild_id, 'log_channel')
                        if log_channel_id:
                            channel = guild.get_channel(log_channel_id)
                    
                    if channel:
                        try:
                            await channel.send(embed=embed)
                        except discord.Forbidden:
                            pass
                    
                    # Give bonus tokens for major milestones
                    if threshold >= 100000:
                        bonus = min(threshold // 10, 10000)  # 10% bonus, max 10k
                        self.bot.db.add_tokens(guild_id, user_id, bonus)
                        
                        # Notify user about bonus
                        try:
                            bonus_embed = discord.Embed(
                                title="💰 Milestone Bonus!",
                                description=(
                                    f"You received {bonus:,} bonus tokens for reaching {threshold:,} tokens!\n"
                                    f"New balance: {self.bot.db.get_balance(guild_id, user_id):,}"
                                ),
                                color=discord.Color.green(),
                                timestamp=datetime.utcnow()
                            )
                            await member.send(embed=bonus_embed)
                        except discord.Forbidden:
                            pass  # User has DMs disabled
                    
                    break  # Only announce one milestone per update
            
        except Exception as e:
            logger.error(f"Error handling economy milestone: {e}")
    
    async def handle_daily_streak(self, guild_id, user_id):
        """Handle daily activity streaks and bonuses."""
        try:
            # This would track daily login streaks and give bonus tokens
            # For MVP, we'll implement a simple version
            
            user_data = self.bot.db.economy[guild_id].get(user_id)
            if not user_data:
                return
            
            current_date = datetime.utcnow().date()
            last_active_date = user_data.get('last_active_date')
            
            if last_active_date != current_date:
                # Update last active date
                user_data['last_active_date'] = current_date
                
                # Check for consecutive days
                streak = user_data.get('daily_streak', 0)
                
                if last_active_date and (current_date - last_active_date).days == 1:
                    # Consecutive day
                    streak += 1
                else:
                    # Reset streak
                    streak = 1
                
                user_data['daily_streak'] = streak
                
                # Give daily bonus based on streak
                daily_bonus = min(10 + (streak * 2), 50)  # 10-50 tokens based on streak
                self.bot.db.add_tokens(guild_id, user_id, daily_bonus)
                
                # Notify user of streak bonus (for significant streaks)
                if streak >= 7 and streak % 7 == 0:  # Weekly streaks
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        member = guild.get_member(user_id)
                        if member:
                            try:
                                streak_embed = discord.Embed(
                                    title="🔥 Daily Streak Bonus!",
                                    description=(
                                        f"**{streak} day streak!**\n"
                                        f"Daily bonus: {daily_bonus} tokens\n"
                                        f"Keep it up!"
                                    ),
                                    color=discord.Color.orange(),
                                    timestamp=datetime.utcnow()
                                )
                                await member.send(embed=streak_embed)
                            except discord.Forbidden:
                                pass
            
        except Exception as e:
            logger.error(f"Error handling daily streak: {e}")
    
    async def handle_economy_leaderboard_update(self, guild_id):
        """Handle periodic leaderboard updates."""
        try:
            # This could send weekly leaderboard updates
            # For MVP, we'll implement a simple version
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            
            # Check if it's time for weekly update (Sundays)
            if datetime.utcnow().weekday() != 6:  # 6 = Sunday
                return
            
            leaderboard = self.bot.db.get_leaderboard(guild_id, 5)
            if not leaderboard:
                return
            
            embed = discord.Embed(
                title="📊 Weekly Economy Leaderboard",
                description="Top 5 richest users this week:",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            
            for i, (user_id, tokens) in enumerate(leaderboard):
                member = guild.get_member(user_id)
                if member:
                    embed.add_field(
                        name=f"{medals[i]} {member.display_name}",
                        value=f"{tokens:,} tokens",
                        inline=False
                    )
            
            # Send to system channel or log channel
            channel = guild.system_channel
            if not channel:
                log_channel_id = self.bot.db.get_guild_config(guild_id, 'log_channel')
                if log_channel_id:
                    channel = guild.get_channel(log_channel_id)
            
            if channel:
                await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error handling leaderboard update: {e}")
    
    async def handle_token_transfer_validation(self, guild_id, from_user_id, to_user_id, amount):
        """Validate and log token transfers."""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return False
            
            from_member = guild.get_member(from_user_id)
            to_member = guild.get_member(to_user_id)
            
            if not from_member or not to_member:
                return False
            
            # Check for suspicious transfers (large amounts to new accounts)
            if to_member.joined_at and (datetime.utcnow() - to_member.joined_at).days < 7:
                if amount > 10000:  # Large transfer to new account
                    # Log suspicious activity
                    log_channel_id = self.bot.db.get_guild_config(guild_id, 'log_channel')
                    if log_channel_id:
                        log_channel = guild.get_channel(log_channel_id)
                        if log_channel:
                            embed = discord.Embed(
                                title="⚠️ Suspicious Token Transfer",
                                description=(
                                    f"**From:** {from_member.mention}\n"
                                    f"**To:** {to_member.mention} (joined <t:{int(to_member.joined_at.timestamp())}:R>)\n"
                                    f"**Amount:** {amount:,} tokens"
                                ),
                                color=discord.Color.orange(),
                                timestamp=datetime.utcnow()
                            )
                            await log_channel.send(embed=embed)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating token transfer: {e}")
            return False
    
    async def process_economy_backups(self):
        """Process periodic economy data backups."""
        try:
            # In a real implementation, this would backup economy data
            # For MVP, we'll just log the current state
            
            total_guilds = len(self.bot.db.economy)
            total_users = sum(len(users) for users in self.bot.db.economy.values())
            total_tokens = sum(
                sum(user_data['tokens'] for user_data in users.values())
                for users in self.bot.db.economy.values()
            )
            
            logger.info(f"Economy backup: {total_guilds} guilds, {total_users} users, {total_tokens:,} total tokens")
            
        except Exception as e:
            logger.error(f"Error processing economy backups: {e}")
