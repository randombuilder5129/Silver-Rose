import random
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EconomyUtils:
    """Utility functions for the economy system."""
    
    @staticmethod
    def calculate_gamble_result(bet_amount: int, balance: int) -> Tuple[bool, int, str]:
        """
        Calculate gambling result.
        Returns: (won, amount_change, result_message)
        """
        # Ensure bet is valid
        if bet_amount <= 0 or bet_amount > balance:
            return False, 0, "Invalid bet amount"
        
        # 45% chance to win (slightly house-favored)
        won = random.random() < 0.45
        
        if won:
            # Win 50% to 100% of bet amount
            multiplier = random.uniform(0.5, 1.0)
            winnings = int(bet_amount * multiplier)
            return True, winnings, f"You won {winnings} tokens!"
        else:
            return False, -bet_amount, f"You lost {bet_amount} tokens!"
    
    @staticmethod
    def calculate_steal_result(stealer_balance: int, target_balance: int) -> Tuple[bool, int, str]:
        """
        Calculate stealing result.
        Returns: (success, amount_stolen, result_message)
        """
        # Must have at least 10 tokens to attempt stealing
        if stealer_balance < 10:
            return False, 0, "You need at least 10 tokens to attempt stealing!"
        
        # Target must have tokens to steal
        if target_balance <= 0:
            return False, 0, "Target has no tokens to steal!"
        
        # 30% chance of success
        success = random.random() < 0.3
        
        if success:
            # Steal 1-10% of target's balance, minimum 1, maximum 100
            steal_percentage = random.uniform(0.01, 0.1)
            amount_stolen = max(1, min(100, int(target_balance * steal_percentage)))
            return True, amount_stolen, f"Successfully stole {amount_stolen} tokens!"
        else:
            # Failed attempt - lose 5-20 tokens as penalty
            penalty = random.randint(5, min(20, stealer_balance))
            return False, -penalty, f"Steal attempt failed! Lost {penalty} tokens as penalty."
    
    @staticmethod
    def format_balance(amount: int) -> str:
        """Format balance with commas for readability."""
        return f"{amount:,}"
    
    @staticmethod
    def validate_transaction_amount(amount: int, balance: int, max_amount: int = 1000000) -> Tuple[bool, str]:
        """
        Validate a transaction amount.
        Returns: (valid, error_message)
        """
        if amount <= 0:
            return False, "Amount must be positive!"
        
        if amount > balance:
            return False, "Insufficient balance!"
        
        if amount > max_amount:
            return False, f"Amount exceeds maximum limit of {max_amount:,}!"
        
        return True, ""
    
    @staticmethod
    def calculate_passive_earnings(hours_passed: float) -> int:
        """Calculate passive earnings based on hours passed."""
        # 0.125 tokens per hour
        return int(hours_passed * 0.125)
    
    @staticmethod
    def get_balance_rank(balance: int) -> Tuple[str, str]:
        """
        Get rank and emoji based on balance.
        Returns: (rank_name, emoji)
        """
        if balance >= 100000:
            return "💎 Diamond", "💎"
        elif balance >= 50000:
            return "👑 Platinum", "👑"
        elif balance >= 25000:
            return "🥇 Gold", "🥇"
        elif balance >= 10000:
            return "🥈 Silver", "🥈"
        elif balance >= 5000:
            return "🥉 Bronze", "🥉"
        elif balance >= 1000:
            return "⭐ Rising", "⭐"
        else:
            return "🌱 Newbie", "🌱"
    
    @staticmethod
    def generate_shop_embed_description(items: dict) -> str:
        """Generate shop description for embed."""
        if not items:
            return "No items available in the shop."
        
        description = "**Available Items:**\n\n"
        
        for name, data in items.items():
            price = data['price']
            item_description = data['description']
            description += f"**{name}** - {price:,} tokens\n{item_description}\n\n"
        
        return description
    
    @staticmethod
    def can_afford_item(balance: int, item_price: int) -> bool:
        """Check if user can afford an item."""
        return balance >= item_price
