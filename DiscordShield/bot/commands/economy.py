import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import random
import logging
from ..utils.economy import EconomyUtils

logger = logging.getLogger(__name__)

class EconomyCommands(commands.Cog):
    """Economy commands for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="balance", description="Check your token balance")
    @app_commands.describe(user="Optional: Check another user's balance")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check token balance."""
        try:
            target_user = user or interaction.user
            
            # Update passive earnings
            self.bot.db.update_passive_earning(interaction.guild.id, target_user.id)
            
            balance = self.bot.db.get_balance(interaction.guild.id, target_user.id)
            rank_name, rank_emoji = EconomyUtils.get_balance_rank(balance)
            
            embed = discord.Embed(
                title=f"{rank_emoji} {target_user.display_name}'s Balance",
                description=(
                    f"**Tokens:** {EconomyUtils.format_balance(balance)}\n"
                    f"**Rank:** {rank_name}"
                ),
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "balance", True)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while checking balance.",
                ephemeral=True
            )
    
    @app_commands.command(name="gamble", description="Gamble your tokens")
    @app_commands.describe(amount="Amount of tokens to gamble")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        """Gamble tokens."""
        try:
            # Check rate limiting
            if await self.bot.is_rate_limited(interaction.user.id):
                await interaction.response.send_message(
                    "⏱️ You're using commands too quickly! Please wait a moment.",
                    ephemeral=True
                )
                return
            
            # Update passive earnings
            self.bot.db.update_passive_earning(interaction.guild.id, interaction.user.id)
            
            balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            
            # Validate amount
            valid, error_msg = EconomyUtils.validate_transaction_amount(amount, balance)
            if not valid:
                await interaction.response.send_message(f"❌ {error_msg}", ephemeral=True)
                return
            
            # Calculate result
            won, amount_change, result_msg = EconomyUtils.calculate_gamble_result(amount, balance)
            
            # Update balance
            if won:
                self.bot.db.add_tokens(interaction.guild.id, interaction.user.id, amount_change)
                color = discord.Color.green()
                emoji = "🎉"
            else:
                self.bot.db.remove_tokens(interaction.guild.id, interaction.user.id, abs(amount_change))
                color = discord.Color.red()
                emoji = "💸"
            
            new_balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            
            embed = discord.Embed(
                title=f"{emoji} Gambling Result",
                description=(
                    f"**{result_msg}**\n\n"
                    f"**Previous Balance:** {EconomyUtils.format_balance(balance)}\n"
                    f"**New Balance:** {EconomyUtils.format_balance(new_balance)}\n"
                    f"**Change:** {'+' if amount_change > 0 else ''}{EconomyUtils.format_balance(amount_change)}"
                ),
                color=color,
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "gamble", True)
            
        except Exception as e:
            logger.error(f"Error in gamble command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while gambling.",
                ephemeral=True
            )
    
    @app_commands.command(name="steal", description="Attempt to steal tokens from another user")
    @app_commands.describe(user="The user to steal from")
    async def steal(self, interaction: discord.Interaction, user: discord.Member):
        """Steal tokens from another user."""
        try:
            # Check rate limiting
            if await self.bot.is_rate_limited(interaction.user.id):
                await interaction.response.send_message(
                    "⏱️ You're using commands too quickly! Please wait a moment.",
                    ephemeral=True
                )
                return
            
            if user.id == interaction.user.id:
                await interaction.response.send_message(
                    "❌ You cannot steal from yourself!",
                    ephemeral=True
                )
                return
            
            if user.bot:
                await interaction.response.send_message(
                    "❌ You cannot steal from bots!",
                    ephemeral=True
                )
                return
            
            # Update passive earnings for both users
            self.bot.db.update_passive_earning(interaction.guild.id, interaction.user.id)
            self.bot.db.update_passive_earning(interaction.guild.id, user.id)
            
            stealer_balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            target_balance = self.bot.db.get_balance(interaction.guild.id, user.id)
            
            # Calculate steal result
            success, amount_change, result_msg = EconomyUtils.calculate_steal_result(stealer_balance, target_balance)
            
            # Update balances
            if success:
                self.bot.db.remove_tokens(interaction.guild.id, user.id, amount_change)
                self.bot.db.add_tokens(interaction.guild.id, interaction.user.id, amount_change)
                color = discord.Color.green()
                emoji = "🔓"
            else:
                self.bot.db.remove_tokens(interaction.guild.id, interaction.user.id, abs(amount_change))
                color = discord.Color.red()
                emoji = "🚫"
            
            new_stealer_balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            
            embed = discord.Embed(
                title=f"{emoji} Steal Attempt",
                description=(
                    f"**Target:** {user.mention}\n"
                    f"**Result:** {result_msg}\n\n"
                    f"**Your Balance:** {EconomyUtils.format_balance(new_stealer_balance)}"
                ),
                color=color,
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Notify target if steal was successful
            if success:
                try:
                    dm_embed = discord.Embed(
                        title=f"💰 Tokens Stolen in {interaction.guild.name}",
                        description=(
                            f"{interaction.user.mention} stole {amount_change} tokens from you!\n"
                            f"Your new balance: {self.bot.db.get_balance(interaction.guild.id, user.id):,}"
                        ),
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    await user.send(embed=dm_embed)
                except discord.Forbidden:
                    pass  # User has DMs disabled
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "steal", True)
            
        except Exception as e:
            logger.error(f"Error in steal command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while attempting to steal.",
                ephemeral=True
            )
    
    @app_commands.command(name="give", description="Give tokens to another user")
    @app_commands.describe(
        user="The user to give tokens to",
        amount="Amount of tokens to give"
    )
    async def give(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Give tokens to another user."""
        try:
            if user.id == interaction.user.id:
                await interaction.response.send_message(
                    "❌ You cannot give tokens to yourself!",
                    ephemeral=True
                )
                return
            
            if user.bot:
                await interaction.response.send_message(
                    "❌ You cannot give tokens to bots!",
                    ephemeral=True
                )
                return
            
            # Update passive earnings
            self.bot.db.update_passive_earning(interaction.guild.id, interaction.user.id)
            self.bot.db.update_passive_earning(interaction.guild.id, user.id)
            
            balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            
            # Validate amount
            valid, error_msg = EconomyUtils.validate_transaction_amount(amount, balance)
            if not valid:
                await interaction.response.send_message(f"❌ {error_msg}", ephemeral=True)
                return
            
            # Transfer tokens
            self.bot.db.remove_tokens(interaction.guild.id, interaction.user.id, amount)
            self.bot.db.add_tokens(interaction.guild.id, user.id, amount)
            
            new_giver_balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            new_receiver_balance = self.bot.db.get_balance(interaction.guild.id, user.id)
            
            embed = discord.Embed(
                title="💝 Tokens Transferred",
                description=(
                    f"**From:** {interaction.user.mention}\n"
                    f"**To:** {user.mention}\n"
                    f"**Amount:** {EconomyUtils.format_balance(amount)}\n\n"
                    f"**Your new balance:** {EconomyUtils.format_balance(new_giver_balance)}\n"
                    f"**Their new balance:** {EconomyUtils.format_balance(new_receiver_balance)}"
                ),
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Notify recipient
            try:
                dm_embed = discord.Embed(
                    title=f"💰 Tokens Received in {interaction.guild.name}",
                    description=(
                        f"{interaction.user.mention} gave you {amount:,} tokens!\n"
                        f"Your new balance: {new_receiver_balance:,}"
                    ),
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "give", True)
            
        except Exception as e:
            logger.error(f"Error in give command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while transferring tokens.",
                ephemeral=True
            )
    
    @app_commands.command(name="leaderboard", description="View the server's token leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        """View economy leaderboard."""
        try:
            leaderboard = self.bot.db.get_leaderboard(interaction.guild.id, 10)
            
            if not leaderboard:
                embed = discord.Embed(
                    title="📊 Token Leaderboard",
                    description="No users with tokens found!",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            embed = discord.Embed(
                title="📊 Token Leaderboard",
                description="Top 10 richest users in the server",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            for i, (user_id, tokens) in enumerate(leaderboard, 1):
                user = interaction.guild.get_member(user_id)
                if user:
                    rank_name, rank_emoji = EconomyUtils.get_balance_rank(tokens)
                    
                    if i == 1:
                        medal = "🥇"
                    elif i == 2:
                        medal = "🥈"
                    elif i == 3:
                        medal = "🥉"
                    else:
                        medal = f"#{i}"
                    
                    embed.add_field(
                        name=f"{medal} {user.display_name}",
                        value=f"{rank_emoji} {EconomyUtils.format_balance(tokens)} tokens",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "leaderboard", True)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching the leaderboard.",
                ephemeral=True
            )
    
    @app_commands.command(name="shop", description="View or manage the server shop")
    async def shop(self, interaction: discord.Interaction):
        """View the server shop."""
        try:
            shop_items = self.bot.db.get_shop_items(interaction.guild.id)
            
            embed = discord.Embed(
                title="🛒 Server Shop",
                description=EconomyUtils.generate_shop_embed_description(shop_items),
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            if shop_items:
                embed.set_footer(text="Use /buy <item_name> to purchase items")
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "shop", True)
            
        except Exception as e:
            logger.error(f"Error in shop command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while displaying the shop.",
                ephemeral=True
            )
    
    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item="The name of the item to buy")
    async def buy(self, interaction: discord.Interaction, item: str):
        """Buy an item from the shop."""
        try:
            shop_items = self.bot.db.get_shop_items(interaction.guild.id)
            
            # Find item (case-insensitive)
            item_data = None
            actual_item_name = None
            
            for shop_item_name, data in shop_items.items():
                if shop_item_name.lower() == item.lower():
                    item_data = data
                    actual_item_name = shop_item_name
                    break
            
            if not item_data:
                await interaction.response.send_message(
                    f"❌ Item `{item}` not found in shop! Use `/shop` to see available items.",
                    ephemeral=True
                )
                return
            
            # Update passive earnings
            self.bot.db.update_passive_earning(interaction.guild.id, interaction.user.id)
            
            balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            
            if not EconomyUtils.can_afford_item(balance, item_data['price']):
                await interaction.response.send_message(
                    f"❌ You don't have enough tokens! You need {item_data['price']:,} tokens but only have {balance:,}.",
                    ephemeral=True
                )
                return
            
            # Purchase item
            self.bot.db.remove_tokens(interaction.guild.id, interaction.user.id, item_data['price'])
            new_balance = self.bot.db.get_balance(interaction.guild.id, interaction.user.id)
            
            embed = discord.Embed(
                title="✅ Purchase Successful",
                description=(
                    f"**Item:** {actual_item_name}\n"
                    f"**Price:** {EconomyUtils.format_balance(item_data['price'])}\n"
                    f"**Description:** {item_data['description']}\n\n"
                    f"**New Balance:** {EconomyUtils.format_balance(new_balance)}"
                ),
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "buy", True)
            
        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while purchasing the item.",
                ephemeral=True
            )
    
    @app_commands.command(name="sell", description="Sell an item back to the shop")
    @app_commands.describe(item="The name of the item to sell")
    async def sell(self, interaction: discord.Interaction, item: str):
        """Sell an item back to the shop (placeholder implementation)."""
        try:
            # This is a basic implementation - in a real bot you'd track user inventories
            await interaction.response.send_message(
                "🔄 Sell functionality is not yet implemented. This feature will track your purchased items and allow you to sell them back for 50% of their original price.",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error in sell command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while selling the item.",
                ephemeral=True
            )
    
    @app_commands.command(name="economy", description="View economy statistics for the server")
    async def economy(self, interaction: discord.Interaction):
        """View economy statistics."""
        try:
            leaderboard = self.bot.db.get_leaderboard(interaction.guild.id, 100)  # Get all users
            
            if not leaderboard:
                embed = discord.Embed(
                    title="📈 Economy Statistics",
                    description="No economy data available!",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            total_tokens = sum(tokens for _, tokens in leaderboard)
            total_users = len(leaderboard)
            average_tokens = total_tokens // total_users if total_users > 0 else 0
            
            richest_user_id, max_tokens = leaderboard[0] if leaderboard else (None, 0)
            richest_user = interaction.guild.get_member(richest_user_id) if richest_user_id else None
            
            embed = discord.Embed(
                title="📈 Server Economy Statistics",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="💰 Total Tokens",
                value=f"{EconomyUtils.format_balance(total_tokens)}",
                inline=True
            )
            
            embed.add_field(
                name="👥 Active Users",
                value=f"{total_users:,}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Average Balance",
                value=f"{EconomyUtils.format_balance(average_tokens)}",
                inline=True
            )
            
            if richest_user:
                embed.add_field(
                    name="👑 Richest User",
                    value=f"{richest_user.display_name}\n{EconomyUtils.format_balance(max_tokens)}",
                    inline=True
                )
            
            embed.add_field(
                name="⚙️ Economy Settings",
                value=(
                    "• Passive earning: 0.125 tokens/hour\n"
                    "• Starting balance: 100 tokens\n"
                    "• Max balance: 1,000,000 tokens"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.bot.db.log_command(interaction.guild.id, interaction.user.id, "economy", True)
            
        except Exception as e:
            logger.error(f"Error in economy command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching economy statistics.",
                ephemeral=True
            )
