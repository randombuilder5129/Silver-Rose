"""Configuration settings for the Discord bot."""

# Bot configuration
BOT_PREFIX = "!"
BOT_DESCRIPTION = "Comprehensive Discord bot with moderation, economy, and community features"

# Command rate limiting (seconds)
COMMAND_COOLDOWN = 5

# Warning system
WARNING_DURATION_DAYS = 7
AUTO_KICK_WARNING_COUNT = 3

# Economy system
PASSIVE_EARNING_RATE = 0.125  # tokens per hour
INITIAL_BALANCE = 100
MAX_BALANCE = 1000000

# Anti-spam settings
MAX_MESSAGES_PER_MINUTE = 10
SPAM_TIMEOUT_DURATION = 300  # 5 minutes

# Raid detection
RAID_JOIN_THRESHOLD = 10  # users joining within timeframe
RAID_TIMEFRAME = 60  # seconds

# Giveaway settings
MIN_GIVEAWAY_DURATION = 60  # 1 minute
MAX_GIVEAWAY_DURATION = 604800  # 1 week

# Birthday system
BIRTHDAY_ANNOUNCEMENT_HOUR = 9  # 9 AM

# Question of the day
QOTD_DEFAULT_TIME = "09:00"

# Logging
LOG_RETENTION_DAYS = 30

# Shop items (default)
DEFAULT_SHOP_ITEMS = {
    "VIP Role": {"price": 1000, "type": "role", "description": "Get a special VIP role"},
    "Custom Color": {"price": 500, "type": "color", "description": "Get a custom color role"},
    "Server Boost": {"price": 2000, "type": "boost", "description": "Boost the server for a month"}
}
