const { Client, GatewayIntentBits, Collection, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const { OpenAI } = require('openai');
require('dotenv').config();

// Import modules
const Database = require('./utils/database');
const MessageLogger = require('./utils/messageLogger');
const InviteTracker = require('./utils/inviteTracker');
const CountingGame = require('./utils/countingGame');
const PetSystem = require('./utils/petSystem');

// Import commands
const CoreCommands = require('./commands/core');
const ModerationCommands = require('./commands/moderation');
const EconomyCommands = require('./commands/economy');
const UtilityCommands = require('./commands/utility');
const CommunityCommands = require('./commands/community');
const AICommands = require('./commands/ai');
const ShopCommands = require('./commands/shop');
const PetCommands = require('./commands/pets');

class DiscordBot extends Client {
    constructor() {
        super({
            intents: [
                GatewayIntentBits.Guilds,
                GatewayIntentBits.GuildMessages,
                GatewayIntentBits.MessageContent,
                GatewayIntentBits.GuildMembers,
                GatewayIntentBits.GuildInvites,
                GatewayIntentBits.GuildMessageReactions
            ]
        });

        // Initialize systems
        this.db = new Database();
        this.messageLogger = new MessageLogger(this);
        this.inviteTracker = new InviteTracker(this);
        this.countingGame = new CountingGame(this);
        this.petSystem = new PetSystem(this);
        
        // Initialize OpenAI
        this.openai = new OpenAI({
            apiKey: process.env.OPENAI_API_KEY
        });

        // Collections
        this.commands = new Collection();
        this.cooldowns = new Collection();
        this.startTime = new Date();

        // Rate limiting
        this.commandUsage = new Map();
        this.messageTracking = new Map();

        this.setupCommands();
        this.setupEvents();
    }

    setupCommands() {
        // Load all command modules
        const commandModules = [
            CoreCommands,
            ModerationCommands, 
            EconomyCommands,
            UtilityCommands,
            CommunityCommands,
            AICommands,
            ShopCommands,
            PetCommands
        ];

        commandModules.forEach(CommandClass => {
            const commands = new CommandClass(this);
            commands.register();
        });
    }

    setupEvents() {
        this.once('ready', () => {
            console.log(`${this.user.tag} has connected to Discord!`);
            console.log(`Connected to ${this.guilds.cache.size} guilds`);
            
            // Initialize invite tracking
            this.inviteTracker.cacheInvites();
            
            // Start background tasks
            this.startBackgroundTasks();
        });

        // Message logging and processing
        this.on('messageCreate', async (message) => {
            if (message.author.bot) return;

            // Log all messages
            await this.messageLogger.logMessage(message);

            // Process counting game
            await this.countingGame.processMessage(message);

            // Check for spam
            await this.checkSpam(message);

            // Process passive economy
            await this.processPassiveEconomy(message);

            // Pet interaction
            await this.petSystem.processMessage(message);
        });

        // Invite tracking
        this.on('inviteCreate', (invite) => {
            this.inviteTracker.handleInviteCreate(invite);
        });

        this.on('inviteDelete', (invite) => {
            this.inviteTracker.handleInviteDelete(invite);
        });

        this.on('guildMemberAdd', (member) => {
            this.inviteTracker.handleMemberJoin(member);
        });

        // Interaction handling
        this.on('interactionCreate', async (interaction) => {
            if (!interaction.isChatInputCommand()) return;

            const command = this.commands.get(interaction.commandName);
            if (!command) return;

            // Rate limiting
            if (await this.isRateLimited(interaction.user.id)) {
                await interaction.reply({
                    content: 'You are being rate limited. Please wait before using another command.',
                    ephemeral: true
                });
                return;
            }

            try {
                // Log command usage
                await this.messageLogger.logCommand(interaction);

                await command.execute(interaction);
                
                // Log successful command
                this.db.logCommand(interaction.guildId, interaction.user.id, interaction.commandName, true);
            } catch (error) {
                console.error(`Error executing command ${interaction.commandName}:`, error);
                
                // Log failed command
                this.db.logCommand(interaction.guildId, interaction.user.id, interaction.commandName, false);

                const errorMessage = 'There was an error while executing this command!';
                if (interaction.replied || interaction.deferred) {
                    await interaction.followUp({ content: errorMessage, ephemeral: true });
                } else {
                    await interaction.reply({ content: errorMessage, ephemeral: true });
                }
            }
        });

        // Pet lifecycle events
        this.on('messageReactionAdd', async (reaction, user) => {
            if (user.bot) return;
            await this.petSystem.handleReaction(reaction, user, 'add');
        });

        this.on('messageReactionRemove', async (reaction, user) => {
            if (user.bot) return;
            await this.petSystem.handleReaction(reaction, user, 'remove');
        });
    }

    async startBackgroundTasks() {
        // Passive economy earnings
        setInterval(async () => {
            await this.processPassiveEarnings();
        }, 60000); // Every minute

        // Pet lifecycle
        setInterval(async () => {
            await this.petSystem.processLifecycle();
        }, 300000); // Every 5 minutes

        // Cleanup old data
        setInterval(async () => {
            await this.cleanupOldData();
        }, 3600000); // Every hour
    }

    async processPassiveEconomy(message) {
        const guildId = message.guild.id;
        const userId = message.author.id;
        
        // Award tokens for chatting
        const bonus = Math.floor(Math.random() * 3) + 1; // 1-3 tokens
        this.db.addTokens(guildId, userId, bonus);
        
        // Update last activity
        this.db.updatePassiveEarning(guildId, userId);
    }

    async processPassiveEarnings() {
        // Process passive earnings for all users
        for (const guild of this.guilds.cache.values()) {
            const users = this.db.getGuildData(guild.id, 'economy') || {};
            
            for (const [userId, userData] of Object.entries(users)) {
                if (userData.lastActivity) {
                    const lastActivity = new Date(userData.lastActivity);
                    const now = new Date();
                    const hoursPassed = (now - lastActivity) / (1000 * 60 * 60);
                    
                    if (hoursPassed >= 1) {
                        const earnings = Math.floor(hoursPassed * 0.125); // 0.125 tokens per hour
                        if (earnings > 0) {
                            this.db.addTokens(guild.id, userId, earnings);
                        }
                    }
                }
            }
        }
    }

    async isRateLimited(userId) {
        const now = Date.now();
        const userCooldown = this.commandUsage.get(userId);
        
        if (userCooldown && now < userCooldown) {
            return true;
        }
        
        this.commandUsage.set(userId, now + 5000); // 5 second cooldown
        return false;
    }

    async checkSpam(message) {
        const userId = message.author.id;
        const now = Date.now();
        
        if (!this.messageTracking.has(userId)) {
            this.messageTracking.set(userId, []);
        }
        
        const userMessages = this.messageTracking.get(userId);
        userMessages.push(now);
        
        // Keep only messages from last minute
        const recentMessages = userMessages.filter(time => now - time < 60000);
        this.messageTracking.set(userId, recentMessages);
        
        // If more than 10 messages in a minute, timeout user
        if (recentMessages.length > 10) {
            try {
                await message.member.timeout(5 * 60 * 1000, 'Spam detection'); // 5 minute timeout
                await message.channel.send(`${message.author} has been timed out for spamming.`);
            } catch (error) {
                console.error('Error timing out user:', error);
            }
        }
    }

    async cleanupOldData() {
        // Clean up old message logs, warnings, etc.
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        
        for (const guild of this.guilds.cache.values()) {
            // Clean old warnings
            const warnings = this.db.getGuildData(guild.id, 'warnings') || {};
            for (const [userId, userWarnings] of Object.entries(warnings)) {
                const activeWarnings = userWarnings.filter(warning => 
                    new Date(warning.timestamp) > sevenDaysAgo
                );
                if (activeWarnings.length !== userWarnings.length) {
                    this.db.setGuildData(guild.id, `warnings.${userId}`, activeWarnings);
                }
            }
        }
    }

    async deployCommands() {
        const commands = [];
        
        for (const command of this.commands.values()) {
            commands.push(command.data.toJSON());
        }

        try {
            console.log('Started refreshing application (/) commands.');
            
            for (const guild of this.guilds.cache.values()) {
                await guild.commands.set(commands);
            }
            
            console.log(`Successfully reloaded ${commands.length} application (/) commands.`);
        } catch (error) {
            console.error('Error deploying commands:', error);
        }
    }
}

// Create and start the bot
const bot = new DiscordBot();

bot.login(process.env.DISCORD_TOKEN).then(() => {
    // Deploy commands after login
    setTimeout(() => {
        bot.deployCommands();
    }, 5000);
});

// Handle process termination
process.on('SIGINT', () => {
    console.log('Bot is shutting down...');
    bot.destroy();
    process.exit(0);
});

module.exports = DiscordBot;