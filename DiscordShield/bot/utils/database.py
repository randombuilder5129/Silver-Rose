import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    """In-memory database for bot data storage."""
    
    def __init__(self):
        # Guild configurations
        self.guild_configs: Dict[int, Dict[str, Any]] = {}
        
        # Warnings system
        self.warnings: Dict[int, Dict[int, List[Dict]]] = {}
        
        # Economy system
        self.economy: Dict[int, Dict[int, Dict[str, Any]]] = {}
        
        # Scheduled announcements
        self.scheduled_announcements: Dict[str, Dict[str, Any]] = {}
        
        # Locked channels
        self.locked_channels: Dict[int, Dict[str, Any]] = {}
        
        # Reminders
        self.reminders: Dict[int, List[Dict[str, Any]]] = {}
        
        # Polls
        self.polls: Dict[int, Dict[str, Any]] = {}
        
        # Suggestions
        self.suggestions: Dict[int, List[Dict[str, Any]]] = {}
        
        # Reaction roles
        self.reaction_roles: Dict[int, Dict[int, Dict[str, int]]] = {}
        
        # Birthdays
        self.birthdays: Dict[int, Dict[int, Dict[str, Any]]] = {}
        
        # Tickets
        self.tickets: Dict[int, Dict[int, Dict[str, Any]]] = {}
        
        # Giveaways
        self.giveaways: Dict[int, Dict[str, Any]] = {}
        
        # Shop items
        self.shop_items: Dict[int, Dict[str, Dict[str, Any]]] = {}
        
        # Command logs
        self.command_logs: Dict[int, List[Dict[str, Any]]] = {}
        
        # Word filters
        self.word_filters: Dict[int, List[str]] = {}
        
    def init_guild(self, guild_id: int):
        """Initialize data structures for a new guild."""
        if guild_id not in self.guild_configs:
            self.guild_configs[guild_id] = {
                'log_channel': None,
                'welcome_channel': None,
                'birthday_channel': None,
                'qotd_channel': None,
                'suggestion_channel': None,
                'boost_role': None,
                'qotd_hour': 9,
                'auto_role': None,
                'prefix': '!'
            }
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        
        if guild_id not in self.economy:
            self.economy[guild_id] = {}
        
        if guild_id not in self.reaction_roles:
            self.reaction_roles[guild_id] = {}
        
        if guild_id not in self.birthdays:
            self.birthdays[guild_id] = {}
        
        if guild_id not in self.tickets:
            self.tickets[guild_id] = {}
        
        if guild_id not in self.shop_items:
            self.shop_items[guild_id] = {}
        
        if guild_id not in self.command_logs:
            self.command_logs[guild_id] = []
        
        if guild_id not in self.word_filters:
            self.word_filters[guild_id] = []
    
    # Guild Configuration Methods
    def get_guild_config(self, guild_id: int, key: str) -> Any:
        """Get guild configuration value."""
        self.init_guild(guild_id)
        return self.guild_configs[guild_id].get(key)
    
    def set_guild_config(self, guild_id: int, key: str, value: Any):
        """Set guild configuration value."""
        self.init_guild(guild_id)
        self.guild_configs[guild_id][key] = value
    
    # Warning System Methods
    def add_warning(self, guild_id: int, user_id: int, reason: str, moderator_id: int) -> str:
        """Add a warning to a user."""
        self.init_guild(guild_id)
        
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []
        
        warning_id = f"{guild_id}-{user_id}-{len(self.warnings[guild_id][user_id])}"
        warning = {
            'id': warning_id,
            'reason': reason,
            'moderator': moderator_id,
            'timestamp': datetime.utcnow()
        }
        
        self.warnings[guild_id][user_id].append(warning)
        return warning_id
    
    def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        """Get all active warnings for a user."""
        self.init_guild(guild_id)
        
        if user_id not in self.warnings[guild_id]:
            return []
        
        # Filter out expired warnings (older than 7 days)
        current_time = datetime.utcnow()
        active_warnings = []
        
        for warning in self.warnings[guild_id][user_id]:
            if (current_time - warning['timestamp']).days < 7:
                active_warnings.append(warning)
        
        self.warnings[guild_id][user_id] = active_warnings
        return active_warnings
    
    def remove_warning(self, guild_id: int, user_id: int, warning_id: str) -> bool:
        """Remove a specific warning."""
        self.init_guild(guild_id)
        
        if user_id not in self.warnings[guild_id]:
            return False
        
        warnings = self.warnings[guild_id][user_id]
        for i, warning in enumerate(warnings):
            if warning['id'] == warning_id:
                warnings.pop(i)
                return True
        
        return False
    
    # Economy System Methods
    def get_balance(self, guild_id: int, user_id: int) -> int:
        """Get user's token balance."""
        self.init_guild(guild_id)
        
        if user_id not in self.economy[guild_id]:
            self.economy[guild_id][user_id] = {
                'tokens': 100,  # Starting balance
                'last_passive': datetime.utcnow()
            }
        
        return self.economy[guild_id][user_id]['tokens']
    
    def set_balance(self, guild_id: int, user_id: int, amount: int):
        """Set user's token balance."""
        self.init_guild(guild_id)
        
        if user_id not in self.economy[guild_id]:
            self.economy[guild_id][user_id] = {
                'tokens': amount,
                'last_passive': datetime.utcnow()
            }
        else:
            self.economy[guild_id][user_id]['tokens'] = amount
    
    def add_tokens(self, guild_id: int, user_id: int, amount: int):
        """Add tokens to user's balance."""
        current_balance = self.get_balance(guild_id, user_id)
        new_balance = min(current_balance + amount, 1000000)  # Max balance cap
        self.set_balance(guild_id, user_id, new_balance)
    
    def remove_tokens(self, guild_id: int, user_id: int, amount: int) -> bool:
        """Remove tokens from user's balance."""
        current_balance = self.get_balance(guild_id, user_id)
        if current_balance >= amount:
            self.set_balance(guild_id, user_id, current_balance - amount)
            return True
        return False
    
    def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[tuple]:
        """Get economy leaderboard."""
        self.init_guild(guild_id)
        
        leaderboard = []
        for user_id, data in self.economy[guild_id].items():
            leaderboard.append((user_id, data['tokens']))
        
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        return leaderboard[:limit]
    
    def update_passive_earning(self, guild_id: int, user_id: int):
        """Update passive earnings for a user."""
        self.init_guild(guild_id)
        
        if user_id not in self.economy[guild_id]:
            self.economy[guild_id][user_id] = {
                'tokens': 100,
                'last_passive': datetime.utcnow()
            }
            return
        
        user_data = self.economy[guild_id][user_id]
        current_time = datetime.utcnow()
        last_passive = user_data['last_passive']
        
        # Calculate hours passed
        hours_passed = (current_time - last_passive).total_seconds() / 3600
        
        if hours_passed >= 1:
            # Earn 0.125 tokens per hour
            tokens_earned = int(hours_passed * 0.125)
            if tokens_earned > 0:
                self.add_tokens(guild_id, user_id, tokens_earned)
                user_data['last_passive'] = current_time
    
    # Logging Methods
    def log_command(self, guild_id: int, user_id: int, command: str, success: bool):
        """Log command usage."""
        self.init_guild(guild_id)
        
        log_entry = {
            'user_id': user_id,
            'command': command,
            'success': success,
            'timestamp': datetime.utcnow()
        }
        
        self.command_logs[guild_id].append(log_entry)
        
        # Keep only last 1000 logs per guild
        if len(self.command_logs[guild_id]) > 1000:
            self.command_logs[guild_id] = self.command_logs[guild_id][-1000:]
    
    # Shop Methods
    def add_shop_item(self, guild_id: int, name: str, price: int, item_type: str, description: str):
        """Add item to shop."""
        self.init_guild(guild_id)
        self.shop_items[guild_id][name] = {
            'price': price,
            'type': item_type,
            'description': description
        }
    
    def get_shop_items(self, guild_id: int) -> Dict[str, Dict[str, Any]]:
        """Get all shop items for a guild."""
        self.init_guild(guild_id)
        return self.shop_items[guild_id]
    
    def remove_shop_item(self, guild_id: int, name: str) -> bool:
        """Remove item from shop."""
        self.init_guild(guild_id)
        if name in self.shop_items[guild_id]:
            del self.shop_items[guild_id][name]
            return True
        return False
