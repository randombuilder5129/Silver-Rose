# Silver-Rose

📚 Bot Commands & Features
Here are all available commands organized by category:
🔧 Core Commands (4)
/announce - Schedule messages
/logset - Set logging channel
/lock - Lock channel temporarily
/lockall - Emergency server lockdown
🛡️ Moderation Commands (7)
/warn - Warn a user
/warnings - View user warnings
/removewarning - Remove specific warning
/clear - Delete messages
/slowmode - Set channel slowmode
/nick - Change user nickname
/unlock - Unlock channels
💰 Economy Commands (9)
/balance - Check token balance
/gamble - Risk tokens for rewards
/steal - Attempt to steal tokens
/give - Transfer tokens
/leaderboard - View top users
/shop - Browse shop items
/buy - Purchase items
/sell - Sell items back
/economy - Toggle economy system
🔧 Utility Commands (8)
/ping - Check bot latency
/commands - Show this list
/remindme - Set reminders
/poll - Create polls
/suggest - Make suggestions
/serverstats - Server statistics
/userinfo - User information
/serverconfig - Configure settings
👥 Community Commands (9)
/reactionroles - Set up reaction roles
/birthday - Set your birthday
/qotd - Question of the day
/ticket - Create support ticket
/giveaway - Host giveaways
/boostconfig - Configure boost rewards
🤖 Automated Features
• Anti-spam detection & timeouts
• Raid detection & auto-lockdown
• Word filtering system
• Passive economy earnings
• Birthday celebrations
• Server boost rewards
• Comprehensive logging
• Reaction role management

AI and Pet systems under development coming soon features when added will be listed bellow 

Overview for Pet system
The pet system is a virtual pet feature that allows users to adopt, care for, and interact with digital pets within your Discord server. It is similar to a “Tamagotchi” or “Neopets” mechanic and is designed to increase engagement and community fun.

Key Features
Pet Adoption

Users can adopt a pet by invoking a command (e.g., /adopt).
Each user can own up to 3 active pets at a time.
The pet type (e.g., dog, cat, dragon, etc.) is chosen or randomly assigned at adoption.
Pet Stats and Lifecycle

Pets have several stats, including:
Name (customizable)
Type (species)
Level
Experience
Happiness
Hunger
Energy
Health
Age (in days)
Stage (e.g., baby, child, adult, evolved forms)
Items (inventory or upgrades)
Pets “age” over time and can evolve to new stages.
Interacting with Pets

Feed: Users can feed their pets to restore hunger and possibly health.
Play: Users can play with their pets to increase happiness and energy.
Rename: Users can rename their pets (with name length restrictions).
Status: Users can check a detailed status page for each pet, showing all stats and possibly a visual embed.
Pet Evolution and Death

As pets age and are cared for, they may “evolve” to new stages (e.g., from baby to adult).
If a pet’s health drops to zero (from neglect), it can “die.” The owner is notified, and the pet is memorialized.
Upon evolving or dying, the system tries to DM the owner or post in a general/chat channel if DMs fail.
Pet Management

Users can only have a limited number of active pets.
Pet data is stored per guild/user in the database, including all stats and timestamps for last fed/played, etc.
Automated Events

The system includes logic for passive pet aging and stat changes (e.g., hunger decreases over time).
Periodic tasks may update pet status, check for evolution, or trigger death from neglect.
Rewards

Evolving pets and other milestones reward the user with tokens (integrated with the economy system).
Technical Integration
Commands:
/adopt, /pet status, /pet feed, /pet play, /pet rename (actual command names may vary).
Embeds:
Rich Discord embeds are used for status updates, evolution, and other notifications.
Database:
All pet data is persisted with user and guild context, allowing for cross-session continuity.
Example User Flow
Adopt a Pet:
User runs /adopt and selects a species/type.
View Status:
User runs /pet status to see their pet’s current stats.
Care:
User must feed and play with the pet regularly to maintain its health and happiness.
Evolution:
After a set age/level, the pet evolves, and the user is rewarded.
Neglect:
If ignored, the pet’s health drops. If it reaches zero, the pet “dies” and is memorialized.
Manage:
User can rename or adopt new pets (up to the limit).
Extensibility
The system is designed to allow adding new pet types, stages, stats, and interactive features.
Integration with the economy system allows for buying pet-related items or upgrades (potentially via the shop).
Summary
The pet system is a feature-rich, Discord-native virtual pet simulator that lets users adopt, care for, interact with, and evolve digital pets. It tracks a variety of stats, supports multiple pets per user, encourages regular interaction, and integrates with your server’s economy for deeper engagement.

AI Overview
The AI feature lets users chat with
The AI feature lets users chat with an advanced AI (powered by OpenAI GPT-4o) directly in Discord using the /chat command. Simply type your message, and the bot responds intelligently, offering helpful, friendly, and concise replies. There's also an /analyze command, which allows users to upload images and receive detailed AI-generated descriptions or analyses. The AI system is designed for easy, natural interactions and enhances server engagement with both text and image-based AI assistance.
