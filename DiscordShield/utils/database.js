class Database {
    constructor() {
        this.data = new Map();
        this.initializeStructure();
    }

    initializeStructure() {
        // Initialize default data structure
        this.defaultGuildData = {
            config: {
                logChannel: null,
                economyEnabled: true,
                countingChannel: null,
                countingNumber: 1,
                antiSpam: true,
                wordFilter: [],
                shopItems: {}
            },
            economy: {},
            warnings: {},
            pets: {},
            invites: {},
            messages: [],
            commands: [],
            counting: {
                channel: null,
                number: 1,
                lastUser: null
            },
            shop: {
                items: {
                    'VIP Role': { price: 1000, type: 'role', description: 'Get VIP status' },
                    'Custom Color': { price: 500, type: 'cosmetic', description: 'Choose your role color' },
                    'Pet Food': { price: 50, type: 'pet', description: 'Feed your pet' },
                    'Pet Toy': { price: 75, type: 'pet', description: 'Play with your pet' },
                    'Pet House': { price: 200, type: 'pet', description: 'Upgrade your pet\'s home' },
                    'Pet Clothes': { price: 150, type: 'pet', description: 'Dress up your pet' }
                }
            }
        };
    }

    getGuildData(guildId, key = null) {
        if (!this.data.has(guildId)) {
            this.data.set(guildId, JSON.parse(JSON.stringify(this.defaultGuildData)));
        }
        
        const guildData = this.data.get(guildId);
        return key ? this.getNestedValue(guildData, key) : guildData;
    }

    setGuildData(guildId, key, value) {
        if (!this.data.has(guildId)) {
            this.data.set(guildId, JSON.parse(JSON.stringify(this.defaultGuildData)));
        }
        
        const guildData = this.data.get(guildId);
        this.setNestedValue(guildData, key, value);
        this.data.set(guildId, guildData);
    }

    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => current && current[key], obj);
    }

    setNestedValue(obj, path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            if (!current[key]) current[key] = {};
            return current[key];
        }, obj);
        target[lastKey] = value;
    }

    // Economy functions
    getBalance(guildId, userId) {
        const economy = this.getGuildData(guildId, 'economy') || {};
        return economy[userId]?.balance || 0;
    }

    setBalance(guildId, userId, amount) {
        const economy = this.getGuildData(guildId, 'economy') || {};
        if (!economy[userId]) {
            economy[userId] = { balance: 0, lastActivity: new Date().toISOString() };
        }
        economy[userId].balance = Math.max(0, amount);
        this.setGuildData(guildId, 'economy', economy);
    }

    addTokens(guildId, userId, amount) {
        const currentBalance = this.getBalance(guildId, userId);
        this.setBalance(guildId, userId, currentBalance + amount);
    }

    removeTokens(guildId, userId, amount) {
        const currentBalance = this.getBalance(guildId, userId);
        if (currentBalance >= amount) {
            this.setBalance(guildId, userId, currentBalance - amount);
            return true;
        }
        return false;
    }

    updatePassiveEarning(guildId, userId) {
        const economy = this.getGuildData(guildId, 'economy') || {};
        if (!economy[userId]) {
            economy[userId] = { balance: 0 };
        }
        economy[userId].lastActivity = new Date().toISOString();
        this.setGuildData(guildId, 'economy', economy);
    }

    getLeaderboard(guildId, limit = 10) {
        const economy = this.getGuildData(guildId, 'economy') || {};
        return Object.entries(economy)
            .sort(([,a], [,b]) => (b.balance || 0) - (a.balance || 0))
            .slice(0, limit)
            .map(([userId, data]) => [userId, data.balance || 0]);
    }

    // Warning system
    addWarning(guildId, userId, reason, moderatorId) {
        const warnings = this.getGuildData(guildId, 'warnings') || {};
        if (!warnings[userId]) warnings[userId] = [];
        
        const warningId = Date.now().toString();
        const warning = {
            id: warningId,
            reason,
            moderatorId,
            timestamp: new Date().toISOString()
        };
        
        warnings[userId].push(warning);
        this.setGuildData(guildId, 'warnings', warnings);
        return warningId;
    }

    getWarnings(guildId, userId) {
        const warnings = this.getGuildData(guildId, 'warnings') || {};
        return warnings[userId] || [];
    }

    removeWarning(guildId, userId, warningId) {
        const warnings = this.getGuildData(guildId, 'warnings') || {};
        if (!warnings[userId]) return false;
        
        const index = warnings[userId].findIndex(w => w.id === warningId);
        if (index !== -1) {
            warnings[userId].splice(index, 1);
            this.setGuildData(guildId, 'warnings', warnings);
            return true;
        }
        return false;
    }

    // Pet system
    createPet(guildId, userId, petType) {
        const pets = this.getGuildData(guildId, 'pets') || {};
        const petId = `${userId}_${Date.now()}`;
        
        pets[petId] = {
            id: petId,
            ownerId: userId,
            type: petType,
            name: `${petType} Pet`,
            level: 1,
            experience: 0,
            happiness: 100,
            hunger: 100,
            energy: 100,
            health: 100,
            age: 0,
            stage: 'baby',
            items: [],
            lastFed: new Date().toISOString(),
            lastPlayed: new Date().toISOString(),
            created: new Date().toISOString()
        };
        
        this.setGuildData(guildId, 'pets', pets);
        return petId;
    }

    getPet(guildId, petId) {
        const pets = this.getGuildData(guildId, 'pets') || {};
        return pets[petId];
    }

    getUserPets(guildId, userId) {
        const pets = this.getGuildData(guildId, 'pets') || {};
        return Object.values(pets).filter(pet => pet.ownerId === userId);
    }

    updatePet(guildId, petId, updates) {
        const pets = this.getGuildData(guildId, 'pets') || {};
        if (pets[petId]) {
            Object.assign(pets[petId], updates);
            this.setGuildData(guildId, 'pets', pets);
        }
    }

    // Shop system
    addShopItem(guildId, name, price, type, description) {
        const shop = this.getGuildData(guildId, 'shop') || { items: {} };
        shop.items[name] = { price, type, description };
        this.setGuildData(guildId, 'shop', shop);
    }

    getShopItems(guildId) {
        const shop = this.getGuildData(guildId, 'shop') || { items: {} };
        return shop.items;
    }

    removeShopItem(guildId, name) {
        const shop = this.getGuildData(guildId, 'shop') || { items: {} };
        if (shop.items[name]) {
            delete shop.items[name];
            this.setGuildData(guildId, 'shop', shop);
            return true;
        }
        return false;
    }

    // Invite tracking
    setInvites(guildId, invites) {
        this.setGuildData(guildId, 'invites', invites);
    }

    getInvites(guildId) {
        return this.getGuildData(guildId, 'invites') || {};
    }

    addInvite(guildId, userId) {
        const invites = this.getGuildData(guildId, 'invites') || {};
        if (!invites[userId]) invites[userId] = 0;
        invites[userId]++;
        this.setGuildData(guildId, 'invites', invites);
    }

    // Message logging
    logMessage(guildId, messageData) {
        const messages = this.getGuildData(guildId, 'messages') || [];
        messages.push({
            ...messageData,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 10000 messages per guild
        if (messages.length > 10000) {
            messages.splice(0, messages.length - 10000);
        }
        
        this.setGuildData(guildId, 'messages', messages);
    }

    getMessages(guildId, limit = 100) {
        const messages = this.getGuildData(guildId, 'messages') || [];
        return messages.slice(-limit);
    }

    // Command logging
    logCommand(guildId, userId, command, success, details = '') {
        const commands = this.getGuildData(guildId, 'commands') || [];
        commands.push({
            userId,
            command,
            success,
            details,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 5000 command logs per guild
        if (commands.length > 5000) {
            commands.splice(0, commands.length - 5000);
        }
        
        this.setGuildData(guildId, 'commands', commands);
    }

    getCommandLogs(guildId, limit = 100) {
        const commands = this.getGuildData(guildId, 'commands') || [];
        return commands.slice(-limit);
    }

    // Counting game
    getCountingData(guildId) {
        return this.getGuildData(guildId, 'counting') || { channel: null, number: 1, lastUser: null };
    }

    updateCounting(guildId, data) {
        this.setGuildData(guildId, 'counting', data);
    }

    // Configuration
    setConfig(guildId, key, value) {
        this.setGuildData(guildId, `config.${key}`, value);
    }

    getConfig(guildId, key) {
        return this.getGuildData(guildId, `config.${key}`);
    }
}

module.exports = Database;