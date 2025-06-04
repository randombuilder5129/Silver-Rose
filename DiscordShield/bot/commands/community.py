import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
import logging
from ..utils.permissions import moderator_only, admin_only, Permissions

logger = logging.getLogger(__name__)

class CommunityCommands(commands.Cog):
    """Community and social commands for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="reactionroles", description="Set up reaction roles")
    @app_commands.describe(
        message_id="ID of the message to add reactions to",
        emoji="The emoji to react with",
        role="The role to assign when reacted"
    )
    @admin_only()
    async def reactionroles(
        self, 
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        """Set up reaction roles."""
        try:
            # Get the message
            try:
                message_id_int = int(message_id)
                message = await interaction.channel.fetch_message(message_id_int)
            except (ValueError, discord.NotFound):
                await interaction.response.send_message(
                    "❌ Invalid message ID or message not found in this channel!",
                    ephemeral=True
                )
                return
            
            # Check if role can be assigned
            if role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    f"❌ I cannot assign {role.mention} as it's higher than my highest role!",
                    ephemeral=True
                )
                return
            
            if role.managed:
                await interaction.response.send_message(
                    f"❌ {role.mention} is a managed role and cannot be assigned manually!",
                    ephemeral=True
                )
                return
            
            # Add reaction to message
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                await interaction.response.send_message(
                    f"❌ Failed to add reaction {emoji}! Make sure it's a valid emoji.",
                    ephemeral=True
                )
                return
            
            # Store reaction role
            if message_id_int not in self.bot.db.reaction_roles[interaction.guild.id]:
                self.bot.db.reaction_roles[interaction.guild.id][message_id_int] = {}
            
            self.bot.db.reaction_roles[interaction.guild.id][message_id_int][emoji] = role.id
            
            embed = discord.Embed(
                title="✅ Reaction Role Set",
                description=(
                    f"**Message:** [Jump to message]({message.jump_url})\n"
                    f"**Emoji:** {emoji}\n"
                    f"**Role:** {role.mention}\n\n"
                    f"Users can now react with {emoji} to get {role.mention}!"
                ),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "reactionroles", True)
            
        except Exception as e:
            logger.error(f"Error in reactionroles command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting up reaction roles.",
                ephemeral=True
            )
    
    @app_commands.command(name="birthday", description="Set your birthday")
    @app_commands.describe(date="Your birthday in MM-DD format (e.g., 03-15)")
    async def birthday(self, interaction: discord.Interaction, date: str):
        """Set user's birthday."""
        try:
            # Validate date format
            try:
                datetime.strptime(date, "%m-%d")
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid date format! Use MM-DD format (e.g., 03-15 for March 15th).",
                    ephemeral=True
                )
                return
            
            # Store birthday
            self.bot.db.birthdays[interaction.guild.id][interaction.user.id] = {
                'date': date,
                'year': None,  # Don't store year for privacy
                'set_at': datetime.utcnow()
            }
            
            embed = discord.Embed(
                title="🎂 Birthday Set",
                description=(
                    f"Your birthday has been set to **{date}**!\n\n"
                    "You'll receive a special birthday message and bonus tokens on your birthday."
                ),
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "birthday", True)
            
        except Exception as e:
            logger.error(f"Error in birthday command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting your birthday.",
                ephemeral=True
            )
    
    @app_commands.command(name="qotd", description="Manage question of the day")
    @app_commands.describe(
        action="Action to perform",
        question="Question for manual QOTD"
    )
    @moderator_only()
    async def qotd(
        self, 
        interaction: discord.Interaction,
        action: str,
        question: str = None
    ):
        """Manage question of the day."""
        try:
            if action.lower() not in ['post', 'schedule', 'status']:
                await interaction.response.send_message(
                    "❌ Invalid action! Use: `post`, `schedule`, or `status`",
                    ephemeral=True
                )
                return
            
            qotd_channel_id = self.bot.db.get_guild_config(interaction.guild.id, 'qotd_channel')
            
            if action.lower() == 'status':
                # Show QOTD status
                if qotd_channel_id:
                    channel = interaction.guild.get_channel(qotd_channel_id)
                    channel_text = channel.mention if channel else f"#{qotd_channel_id} (deleted)"
                else:
                    channel_text = "Not set"
                
                qotd_hour = self.bot.db.get_guild_config(interaction.guild.id, 'qotd_hour') or 9
                
                embed = discord.Embed(
                    title="📝 Question of the Day Status",
                    description=(
                        f"**Channel:** {channel_text}\n"
                        f"**Scheduled Time:** {qotd_hour:02d}:00 UTC daily\n"
                        f"**Status:** {'Enabled' if qotd_channel_id else 'Disabled'}"
                    ),
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                await interaction.response.send_message(embed=embed)
                return
            
            if not qotd_channel_id:
                await interaction.response.send_message(
                    "❌ QOTD channel not set! Use `/serverconfig qotd_channel #channel` first.",
                    ephemeral=True
                )
                return
            
            channel = interaction.guild.get_channel(qotd_channel_id)
            if not channel:
                await interaction.response.send_message(
                    "❌ QOTD channel not found! Please update the configuration.",
                    ephemeral=True
                )
                return
            
            if action.lower() == 'post':
                # Post question now
                if not question:
                    # Use random question
                    questions = [
                        "What's your favorite hobby and why?",
                        "If you could travel anywhere, where would you go?",
                        "What's the best advice you've ever received?",
                        "What's your favorite season and why?",
                        "If you could have dinner with anyone, who would it be?",
                        "What's a skill you'd like to learn?",
                        "What's your favorite book or movie?",
                        "If you could change one thing about the world, what would it be?",
                        "What's the most interesting place you've visited?",
                        "What's your dream job?"
                    ]
                    question = random.choice(questions)
                
                qotd_embed = discord.Embed(
                    title="📝 Question of the Day",
                    description=question,
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )
                qotd_embed.set_footer(text=f"Posted by {interaction.user.display_name}")
                
                message = await channel.send(embed=qotd_embed)
                await message.add_reaction("💭")
                
                await interaction.response.send_message(
                    f"✅ QOTD posted in {channel.mention}!",
                    ephemeral=True
                )
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "qotd", True)
            
        except Exception as e:
            logger.error(f"Error in qotd command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while managing QOTD.",
                ephemeral=True
            )
    
    @app_commands.command(name="ticket", description="Create a support ticket")
    @app_commands.describe(topic="Brief description of your issue")
    async def ticket(self, interaction: discord.Interaction, topic: str):
        """Create a support ticket."""
        try:
            # Check if user already has an open ticket
            user_tickets = self.bot.db.tickets[interaction.guild.id].get(interaction.user.id, [])
            open_tickets = [t for t in user_tickets if not t.get('closed', False)]
            
            if open_tickets:
                await interaction.response.send_message(
                    "❌ You already have an open ticket! Please close your current ticket before creating a new one.",
                    ephemeral=True
                )
                return
            
            if len(topic) > 100:
                await interaction.response.send_message(
                    "❌ Topic is too long! Maximum 100 characters.",
                    ephemeral=True
                )
                return
            
            # Create ticket channel
            category = None
            for cat in interaction.guild.categories:
                if 'ticket' in cat.name.lower():
                    category = cat
                    break
            
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add moderators to ticket
            for role in interaction.guild.roles:
                if (role.permissions.administrator or 
                    role.permissions.manage_channels or 
                    role.permissions.manage_messages):
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            ticket_channel = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=category,
                overwrites=overwrites,
                topic=f"Support ticket by {interaction.user} - {topic}"
            )
            
            # Store ticket info
            ticket_id = len(self.bot.db.tickets[interaction.guild.id].get(interaction.user.id, [])) + 1
            
            if interaction.user.id not in self.bot.db.tickets[interaction.guild.id]:
                self.bot.db.tickets[interaction.guild.id][interaction.user.id] = []
            
            self.bot.db.tickets[interaction.guild.id][interaction.user.id].append({
                'id': ticket_id,
                'channel_id': ticket_channel.id,
                'topic': topic,
                'created_at': datetime.utcnow(),
                'closed': False
            })
            
            # Send ticket info
            ticket_embed = discord.Embed(
                title="🎫 Support Ticket Created",
                description=(
                    f"**User:** {interaction.user.mention}\n"
                    f"**Topic:** {topic}\n"
                    f"**Ticket ID:** #{ticket_id}\n"
                    f"**Created:** <t:{int(datetime.utcnow().timestamp())}:F>"
                ),
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            ticket_embed.add_field(
                name="📋 Instructions",
                value=(
                    "• Please describe your issue in detail\n"
                    "• A staff member will assist you shortly\n"
                    "• React with 🔒 to close this ticket"
                ),
                inline=False
            )
            
            message = await ticket_channel.send(
                f"{interaction.user.mention} Welcome to your support ticket!",
                embed=ticket_embed
            )
            await message.add_reaction("🔒")
            
            await interaction.response.send_message(
                f"✅ Ticket created! Please check {ticket_channel.mention}",
                ephemeral=True
            )
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "ticket", True)
            
        except Exception as e:
            logger.error(f"Error in ticket command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while creating your ticket.",
                ephemeral=True
            )
    
    @app_commands.command(name="giveaway", description="Create a giveaway")
    @app_commands.describe(
        duration="Duration (e.g., 1h, 30m, 2d)",
        winners="Number of winners",
        prize="What you're giving away"
    )
    @moderator_only()
    async def giveaway(
        self, 
        interaction: discord.Interaction,
        duration: str,
        winners: int,
        prize: str
    ):
        """Create a giveaway."""
        try:
            # Parse duration
            end_time = None
            
            if duration.endswith('m'):
                try:
                    minutes = int(duration[:-1])
                    end_time = datetime.utcnow() + timedelta(minutes=minutes)
                except ValueError:
                    pass
            elif duration.endswith('h'):
                try:
                    hours = int(duration[:-1])
                    end_time = datetime.utcnow() + timedelta(hours=hours)
                except ValueError:
                    pass
            elif duration.endswith('d'):
                try:
                    days = int(duration[:-1])
                    end_time = datetime.utcnow() + timedelta(days=days)
                except ValueError:
                    pass
            
            if not end_time:
                await interaction.response.send_message(
                    "❌ Invalid duration format! Use formats like: `30m`, `2h`, `1d`",
                    ephemeral=True
                )
                return
            
            # Validate duration (minimum 1 minute, maximum 1 week)
            duration_seconds = (end_time - datetime.utcnow()).total_seconds()
            if duration_seconds < 60:
                await interaction.response.send_message(
                    "❌ Giveaway duration must be at least 1 minute!",
                    ephemeral=True
                )
                return
            
            if duration_seconds > 604800:  # 1 week
                await interaction.response.send_message(
                    "❌ Giveaway duration cannot exceed 1 week!",
                    ephemeral=True
                )
                return
            
            if winners < 1 or winners > 20:
                await interaction.response.send_message(
                    "❌ Number of winners must be between 1 and 20!",
                    ephemeral=True
                )
                return
            
            if len(prize) > 200:
                await interaction.response.send_message(
                    "❌ Prize description is too long! Maximum 200 characters.",
                    ephemeral=True
                )
                return
            
            # Create giveaway embed
            embed = discord.Embed(
                title="🎉 GIVEAWAY 🎉",
                description=(
                    f"**Prize:** {prize}\n"
                    f"**Winners:** {winners}\n"
                    f"**Ends:** <t:{int(end_time.timestamp())}:F>\n"
                    f"**Time Left:** <t:{int(end_time.timestamp())}:R>\n\n"
                    "React with 🎉 to enter!"
                ),
                color=discord.Color.gold(),
                timestamp=end_time
            )
            embed.set_footer(text=f"Hosted by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            await message.add_reaction("🎉")
            
            # Store giveaway
            giveaway_id = f"{interaction.guild.id}-{message.id}"
            self.bot.db.giveaways[giveaway_id] = {
                'guild_id': interaction.guild.id,
                'channel_id': interaction.channel.id,
                'message_id': message.id,
                'host_id': interaction.user.id,
                'prize': prize,
                'winners': winners,
                'end_time': end_time,
                'created_at': datetime.utcnow()
            }
            
            # Schedule giveaway end
            await self.bot.scheduler.schedule_giveaway_end(
                interaction.guild.id,
                interaction.channel.id,
                message.id,
                end_time,
                winners,
                prize
            )
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "giveaway", True)
            
        except Exception as e:
            logger.error(f"Error in giveaway command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while creating the giveaway.",
                ephemeral=True
            )
    
    @app_commands.command(name="boostconfig", description="Configure server boost rewards")
    @app_commands.describe(
        action="Action to perform (set, remove, view)",
        role="Role to assign to boosters",
        tokens="Bonus tokens for boosting"
    )
    @admin_only()
    async def boostconfig(
        self, 
        interaction: discord.Interaction,
        action: str,
        role: discord.Role = None,
        tokens: int = None
    ):
        """Configure server boost rewards."""
        try:
            if action.lower() not in ['set', 'remove', 'view']:
                await interaction.response.send_message(
                    "❌ Invalid action! Use: `set`, `remove`, or `view`",
                    ephemeral=True
                )
                return
            
            if action.lower() == 'view':
                # Show current boost configuration
                boost_role_id = self.bot.db.get_guild_config(interaction.guild.id, 'boost_role')
                boost_tokens = self.bot.db.get_guild_config(interaction.guild.id, 'boost_tokens') or 0
                
                if boost_role_id:
                    boost_role = interaction.guild.get_role(boost_role_id)
                    role_text = boost_role.mention if boost_role else f"@{boost_role_id} (deleted)"
                else:
                    role_text = "Not set"
                
                embed = discord.Embed(
                    title="🚀 Server Boost Configuration",
                    description=(
                        f"**Boost Role:** {role_text}\n"
                        f"**Bonus Tokens:** {boost_tokens:,}\n\n"
                        f"**Current Boosters:** {interaction.guild.premium_subscription_count}\n"
                        f"**Boost Level:** {interaction.guild.premium_tier}"
                    ),
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow()
                )
                
                await interaction.response.send_message(embed=embed)
                return
            
            if action.lower() == 'remove':
                # Remove boost configuration
                self.bot.db.set_guild_config(interaction.guild.id, 'boost_role', None)
                self.bot.db.set_guild_config(interaction.guild.id, 'boost_tokens', 0)
                
                embed = discord.Embed(
                    title="✅ Boost Rewards Removed",
                    description="Server boost rewards have been disabled.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                await interaction.response.send_message(embed=embed)
                return
            
            if action.lower() == 'set':
                # Set boost configuration
                changes = []
                
                if role:
                    if role >= interaction.guild.me.top_role:
                        await interaction.response.send_message(
                            f"❌ I cannot assign {role.mention} as it's higher than my highest role!",
                            ephemeral=True
                        )
                        return
                    
                    if role.managed:
                        await interaction.response.send_message(
                            f"❌ {role.mention} is a managed role and cannot be assigned manually!",
                            ephemeral=True
                        )
                        return
                    
                    self.bot.db.set_guild_config(interaction.guild.id, 'boost_role', role.id)
                    changes.append(f"**Boost Role:** {role.mention}")
                
                if tokens is not None:
                    if tokens < 0 or tokens > 10000:
                        await interaction.response.send_message(
                            "❌ Bonus tokens must be between 0 and 10,000!",
                            ephemeral=True
                        )
                        return
                    
                    self.bot.db.set_guild_config(interaction.guild.id, 'boost_tokens', tokens)
                    changes.append(f"**Bonus Tokens:** {tokens:,}")
                
                if not changes:
                    await interaction.response.send_message(
                        "❌ Please specify a role and/or tokens to set!",
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="✅ Boost Rewards Updated",
                    description="\n".join(changes),
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "boostconfig", True)
            
        except Exception as e:
            logger.error(f"Error in boostconfig command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while configuring boost rewards.",
                ephemeral=True
            )
