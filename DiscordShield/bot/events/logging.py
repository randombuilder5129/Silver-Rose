import discord
from discord.ext import commands
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LoggingEvents:
    """Event handlers for comprehensive server logging."""
    
    def __init__(self, bot):
        self.bot = bot
        self.setup_events()
    
    def setup_events(self):
        """Set up logging event handlers."""
        
        @self.bot.event
        async def on_message_edit(before, after):
            """Log message edits."""
            if before.author.bot or not before.guild or before.content == after.content:
                return
            
            await self.log_action(
                before.guild,
                "Message Edit",
                (
                    f"**User:** {before.author.mention}\n"
                    f"**Channel:** {before.channel.mention}\n"
                    f"**Before:** {before.content[:500]}\n"
                    f"**After:** {after.content[:500]}\n"
                    f"**Message ID:** {before.id}"
                ),
                discord.Color.yellow()
            )
        
        @self.bot.event
        async def on_message_delete(message):
            """Log message deletions."""
            if message.author.bot or not message.guild:
                return
            
            await self.log_action(
                message.guild,
                "Message Delete",
                (
                    f"**User:** {message.author.mention}\n"
                    f"**Channel:** {message.channel.mention}\n"
                    f"**Content:** {message.content[:500] if message.content else '*No content*'}\n"
                    f"**Message ID:** {message.id}"
                ),
                discord.Color.red()
            )
        
        @self.bot.event
        async def on_member_join(member):
            """Log member joins."""
            account_age = (datetime.utcnow() - member.created_at).days
            
            embed_color = discord.Color.green()
            if account_age < 7:
                embed_color = discord.Color.orange()  # New account warning
            
            await self.log_action(
                member.guild,
                "Member Join",
                (
                    f"**User:** {member.mention}\n"
                    f"**Account Created:** <t:{int(member.created_at.timestamp())}:R>\n"
                    f"**Account Age:** {account_age} days\n"
                    f"**User ID:** {member.id}"
                ),
                embed_color
            )
        
        @self.bot.event
        async def on_member_remove(member):
            """Log member leaves/kicks."""
            await self.log_action(
                member.guild,
                "Member Leave",
                (
                    f"**User:** {member} ({member.id})\n"
                    f"**Joined:** <t:{int(member.joined_at.timestamp())}:R>\n"
                    f"**Roles:** {', '.join([role.name for role in member.roles[1:]]) or 'None'}"
                ),
                discord.Color.orange()
            )
        
        @self.bot.event
        async def on_member_ban(guild, user):
            """Log member bans."""
            await self.log_action(
                guild,
                "Member Ban",
                (
                    f"**User:** {user} ({user.id})\n"
                    f"**Account Created:** <t:{int(user.created_at.timestamp())}:R>"
                ),
                discord.Color.red()
            )
        
        @self.bot.event
        async def on_member_unban(guild, user):
            """Log member unbans."""
            await self.log_action(
                guild,
                "Member Unban",
                f"**User:** {user} ({user.id})",
                discord.Color.green()
            )
        
        @self.bot.event
        async def on_member_update(before, after):
            """Log member updates (roles, nickname, etc.)."""
            changes = []
            
            # Check nickname change
            if before.nick != after.nick:
                changes.append(
                    f"**Nickname:** `{before.nick or before.name}` → `{after.nick or after.name}`"
                )
            
            # Check role changes
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            
            if added_roles:
                changes.append(f"**Roles Added:** {', '.join(role.name for role in added_roles)}")
            
            if removed_roles:
                changes.append(f"**Roles Removed:** {', '.join(role.name for role in removed_roles)}")
            
            # Check timeout changes
            if before.timed_out_until != after.timed_out_until:
                if after.timed_out_until:
                    changes.append(f"**Timed out until:** <t:{int(after.timed_out_until.timestamp())}:F>")
                else:
                    changes.append("**Timeout removed**")
            
            if changes:
                await self.log_action(
                    after.guild,
                    "Member Update",
                    f"**User:** {after.mention}\n" + "\n".join(changes),
                    discord.Color.blue()
                )
        
        @self.bot.event
        async def on_guild_channel_create(channel):
            """Log channel creation."""
            await self.log_action(
                channel.guild,
                "Channel Create",
                (
                    f"**Channel:** {channel.mention}\n"
                    f"**Type:** {channel.type.name.title()}\n"
                    f"**Category:** {channel.category.name if channel.category else 'None'}"
                ),
                discord.Color.green()
            )
        
        @self.bot.event
        async def on_guild_channel_delete(channel):
            """Log channel deletion."""
            await self.log_action(
                channel.guild,
                "Channel Delete",
                (
                    f"**Channel:** #{channel.name}\n"
                    f"**Type:** {channel.type.name.title()}\n"
                    f"**Category:** {channel.category.name if channel.category else 'None'}"
                ),
                discord.Color.red()
            )
        
        @self.bot.event
        async def on_guild_channel_update(before, after):
            """Log channel updates."""
            changes = []
            
            if before.name != after.name:
                changes.append(f"**Name:** `{before.name}` → `{after.name}`")
            
            if before.topic != after.topic:
                changes.append(f"**Topic:** `{before.topic or 'None'}` → `{after.topic or 'None'}`")
            
            if hasattr(before, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
                changes.append(f"**Slowmode:** {before.slowmode_delay}s → {after.slowmode_delay}s")
            
            if changes:
                await self.log_action(
                    after.guild,
                    "Channel Update",
                    f"**Channel:** {after.mention}\n" + "\n".join(changes),
                    discord.Color.blue()
                )
        
        @self.bot.event
        async def on_guild_role_create(role):
            """Log role creation."""
            await self.log_action(
                role.guild,
                "Role Create",
                (
                    f"**Role:** {role.mention}\n"
                    f"**Color:** {role.color}\n"
                    f"**Mentionable:** {role.mentionable}\n"
                    f"**Hoisted:** {role.hoist}"
                ),
                discord.Color.green()
            )
        
        @self.bot.event
        async def on_guild_role_delete(role):
            """Log role deletion."""
            await self.log_action(
                role.guild,
                "Role Delete",
                (
                    f"**Role:** @{role.name}\n"
                    f"**Color:** {role.color}\n"
                    f"**Members:** {len(role.members)}"
                ),
                discord.Color.red()
            )
        
        @self.bot.event
        async def on_guild_role_update(before, after):
            """Log role updates."""
            changes = []
            
            if before.name != after.name:
                changes.append(f"**Name:** `{before.name}` → `{after.name}`")
            
            if before.color != after.color:
                changes.append(f"**Color:** {before.color} → {after.color}")
            
            if before.mentionable != after.mentionable:
                changes.append(f"**Mentionable:** {before.mentionable} → {after.mentionable}")
            
            if before.hoist != after.hoist:
                changes.append(f"**Hoisted:** {before.hoist} → {after.hoist}")
            
            if before.permissions != after.permissions:
                changes.append("**Permissions:** Updated")
            
            if changes:
                await self.log_action(
                    after.guild,
                    "Role Update",
                    f"**Role:** {after.mention}\n" + "\n".join(changes),
                    discord.Color.blue()
                )
        
        @self.bot.event
        async def on_voice_state_update(member, before, after):
            """Log voice channel activity."""
            if before.channel != after.channel:
                if before.channel and after.channel:
                    # Channel switch
                    action = "Voice Channel Switch"
                    description = (
                        f"**User:** {member.mention}\n"
                        f"**From:** {before.channel.name}\n"
                        f"**To:** {after.channel.name}"
                    )
                    color = discord.Color.blue()
                elif after.channel:
                    # Join
                    action = "Voice Channel Join"
                    description = (
                        f"**User:** {member.mention}\n"
                        f"**Channel:** {after.channel.name}"
                    )
                    color = discord.Color.green()
                elif before.channel:
                    # Leave
                    action = "Voice Channel Leave"
                    description = (
                        f"**User:** {member.mention}\n"
                        f"**Channel:** {before.channel.name}"
                    )
                    color = discord.Color.orange()
                else:
                    return
                
                await self.log_action(member.guild, action, description, color)
        
        @self.bot.event
        async def on_guild_update(before, after):
            """Log server updates."""
            changes = []
            
            if before.name != after.name:
                changes.append(f"**Name:** `{before.name}` → `{after.name}`")
            
            if before.description != after.description:
                changes.append(f"**Description:** Updated")
            
            if before.verification_level != after.verification_level:
                changes.append(f"**Verification Level:** {before.verification_level.name} → {after.verification_level.name}")
            
            if before.explicit_content_filter != after.explicit_content_filter:
                changes.append(f"**Content Filter:** {before.explicit_content_filter.name} → {after.explicit_content_filter.name}")
            
            if changes:
                await self.log_action(
                    after,
                    "Server Update",
                    "\n".join(changes),
                    discord.Color.purple()
                )
        
        @self.bot.event
        async def on_invite_create(invite):
            """Log invite creation."""
            await self.log_action(
                invite.guild,
                "Invite Create",
                (
                    f"**Invite:** {invite.url}\n"
                    f"**Channel:** {invite.channel.mention}\n"
                    f"**Creator:** {invite.inviter.mention if invite.inviter else 'Unknown'}\n"
                    f"**Max Uses:** {invite.max_uses or 'Unlimited'}\n"
                    f"**Expires:** <t:{int((invite.created_at + invite.max_age).timestamp())}:R>" if invite.max_age else "Never"
                ),
                discord.Color.green()
            )
        
        @self.bot.event
        async def on_invite_delete(invite):
            """Log invite deletion."""
            await self.log_action(
                invite.guild,
                "Invite Delete",
                (
                    f"**Invite:** {invite.url}\n"
                    f"**Channel:** {invite.channel.mention}\n"
                    f"**Uses:** {invite.uses}"
                ),
                discord.Color.red()
            )
    
    async def log_action(self, guild, action, description, color):
        """Log an action to the guild's log channel."""
        try:
            log_channel_id = self.bot.db.get_guild_config(guild.id, 'log_channel')
            if not log_channel_id:
                return
            
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return
            
            embed = discord.Embed(
                title=f"📋 {action}",
                description=description,
                color=color,
                timestamp=datetime.utcnow()
            )
            
            # Add server info in footer
            embed.set_footer(
                text=f"{guild.name}",
                icon_url=guild.icon.url if guild.icon else None
            )
            
            await log_channel.send(embed=embed)
            
        except discord.Forbidden:
            logger.warning(f"No permission to send logs in {guild.name}")
        except Exception as e:
            logger.error(f"Error logging action in {guild.name}: {e}")
    
    async def log_command_usage(self, guild, user, command_name, success):
        """Log command usage."""
        try:
            # Store in database
            self.bot.db.log_command(guild.id, user.id, command_name, success)
            
            # Only log failed commands to reduce spam
            if not success:
                await self.log_action(
                    guild,
                    "Command Failed",
                    (
                        f"**User:** {user.mention}\n"
                        f"**Command:** /{command_name}\n"
                        f"**Status:** Failed"
                    ),
                    discord.Color.red()
                )
            
        except Exception as e:
            logger.error(f"Error logging command usage: {e}")
    
    async def log_moderation_action(self, guild, moderator, target, action, reason):
        """Log moderation actions."""
        try:
            await self.log_action(
                guild,
                f"Moderation: {action}",
                (
                    f"**Moderator:** {moderator.mention}\n"
                    f"**Target:** {target.mention if hasattr(target, 'mention') else str(target)}\n"
                    f"**Action:** {action}\n"
                    f"**Reason:** {reason}"
                ),
                discord.Color.orange()
            )
            
        except Exception as e:
            logger.error(f"Error logging moderation action: {e}")
    
    async def log_economy_transaction(self, guild, user, transaction_type, amount, details=""):
        """Log economy transactions."""
        try:
            # Only log significant transactions to reduce spam
            if amount >= 1000:
                await self.log_action(
                    guild,
                    f"Economy: {transaction_type}",
                    (
                        f"**User:** {user.mention}\n"
                        f"**Type:** {transaction_type}\n"
                        f"**Amount:** {amount:,} tokens\n"
                        f"**Details:** {details}"
                    ),
                    discord.Color.gold()
                )
            
        except Exception as e:
            logger.error(f"Error logging economy transaction: {e}")
    
    async def generate_activity_report(self, guild):
        """Generate a daily activity report."""
        try:
            current_date = datetime.utcnow().date()
            
            # Get command usage for today
            command_logs = self.bot.db.command_logs.get(guild.id, [])
            today_commands = [
                log for log in command_logs
                if log['timestamp'].date() == current_date
            ]
            
            if not today_commands:
                return
            
            # Count command usage
            command_counts = {}
            user_counts = {}
            success_count = 0
            
            for log in today_commands:
                command = log['command']
                user_id = log['user_id']
                success = log['success']
                
                command_counts[command] = command_counts.get(command, 0) + 1
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
                
                if success:
                    success_count += 1
            
            # Create report
            embed = discord.Embed(
                title="📊 Daily Activity Report",
                description=f"Activity summary for {current_date}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📈 Command Usage",
                value=(
                    f"**Total Commands:** {len(today_commands)}\n"
                    f"**Successful:** {success_count}\n"
                    f"**Success Rate:** {(success_count/len(today_commands)*100):.1f}%"
                ),
                inline=True
            )
            
            # Top commands
            top_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            if top_commands:
                embed.add_field(
                    name="🔥 Top Commands",
                    value="\n".join(f"**/{cmd}:** {count}" for cmd, count in top_commands),
                    inline=True
                )
            
            # Active users
            embed.add_field(
                name="👥 Active Users",
                value=f"{len(user_counts)} unique users",
                inline=True
            )
            
            await self.log_action(guild, "Daily Report", "", discord.Color.blue())
            
        except Exception as e:
            logger.error(f"Error generating activity report: {e}")
