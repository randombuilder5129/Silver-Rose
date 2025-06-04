import discord
from discord.ext import commands
from typing import Union, List
import logging

logger = logging.getLogger(__name__)

class Permissions:
    """Permission checking utilities for the bot."""
    
    @staticmethod
    def is_owner(user: discord.Member, guild: discord.Guild) -> bool:
        """Check if user is the server owner."""
        return user.id == guild.owner_id
    
    @staticmethod
    def is_admin(user: discord.Member) -> bool:
        """Check if user has administrator permissions."""
        return user.guild_permissions.administrator
    
    @staticmethod
    def is_moderator(user: discord.Member) -> bool:
        """Check if user has moderation permissions."""
        return (
            user.guild_permissions.administrator or
            user.guild_permissions.manage_messages or
            user.guild_permissions.manage_channels or
            user.guild_permissions.kick_members or
            user.guild_permissions.ban_members
        )
    
    @staticmethod
    def can_manage_roles(user: discord.Member) -> bool:
        """Check if user can manage roles."""
        return (
            user.guild_permissions.administrator or
            user.guild_permissions.manage_roles
        )
    
    @staticmethod
    def can_manage_channels(user: discord.Member) -> bool:
        """Check if user can manage channels."""
        return (
            user.guild_permissions.administrator or
            user.guild_permissions.manage_channels
        )
    
    @staticmethod
    def can_kick_members(user: discord.Member) -> bool:
        """Check if user can kick members."""
        return (
            user.guild_permissions.administrator or
            user.guild_permissions.kick_members
        )
    
    @staticmethod
    def can_ban_members(user: discord.Member) -> bool:
        """Check if user can ban members."""
        return (
            user.guild_permissions.administrator or
            user.guild_permissions.ban_members
        )
    
    @staticmethod
    def can_manage_messages(user: discord.Member) -> bool:
        """Check if user can manage messages."""
        return (
            user.guild_permissions.administrator or
            user.guild_permissions.manage_messages
        )
    
    @staticmethod
    def has_higher_role(user: discord.Member, target: discord.Member) -> bool:
        """Check if user has a higher role than target."""
        if user.guild_permissions.administrator:
            return True
        
        if target.guild_permissions.administrator:
            return False
        
        return user.top_role > target.top_role
    
    @staticmethod
    def check_bot_permissions(channel: discord.TextChannel, *permissions) -> bool:
        """Check if bot has required permissions in a channel."""
        bot_perms = channel.permissions_for(channel.guild.me)
        
        for perm in permissions:
            if not getattr(bot_perms, perm, False):
                return False
        
        return True

def admin_only():
    """Decorator for admin-only commands."""
    async def predicate(interaction: discord.Interaction):
        if not Permissions.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ This command requires administrator permissions.",
                ephemeral=True
            )
            return False
        return True
    
    return discord.app_commands.check(predicate)

def moderator_only():
    """Decorator for moderator-only commands."""
    async def predicate(interaction: discord.Interaction):
        if not Permissions.is_moderator(interaction.user):
            await interaction.response.send_message(
                "❌ This command requires moderation permissions.",
                ephemeral=True
            )
            return False
        return True
    
    return discord.app_commands.check(predicate)

def owner_only():
    """Decorator for owner-only commands."""
    async def predicate(interaction: discord.Interaction):
        if not Permissions.is_owner(interaction.user, interaction.guild):
            await interaction.response.send_message(
                "❌ This command can only be used by the server owner.",
                ephemeral=True
            )
            return False
        return True
    
    return discord.app_commands.check(predicate)
