const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');

class PetSystem {
    constructor(bot) {
        this.bot = bot;
        this.petTypes = ['Dog', 'Cat', 'Bird', 'Fish', 'Hamster', 'Dragon', 'Phoenix', 'Unicorn'];
        this.lifeStages = ['baby', 'child', 'teen', 'adult', 'elder'];
        this.petEmojis = {
            'Dog': '🐕',
            'Cat': '🐱', 
            'Bird': '🐦',
            'Fish': '🐠',
            'Hamster': '🐹',
            'Dragon': '🐉',
            'Phoenix': '🔥',
            'Unicorn': '🦄'
        };
    }

    async processMessage(message) {
        if (message.author.bot) return;
        
        const userPets = this.bot.db.getUserPets(message.guild.id, message.author.id);
        
        // Give small experience to active pets
        for (const pet of userPets) {
            if (pet.health > 0) {
                await this.addExperience(message.guild.id, pet.id, 1);
            }
        }
    }

    async processLifecycle() {
        console.log('Processing pet lifecycle...');
        
        for (const guild of this.bot.guilds.cache.values()) {
            const pets = this.bot.db.getGuildData(guild.id, 'pets') || {};
            
            for (const [petId, pet] of Object.entries(pets)) {
                await this.updatePetStats(guild.id, petId);
            }
        }
    }

    async updatePetStats(guildId, petId) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return;

        const now = new Date();
        const lastFed = new Date(pet.lastFed);
        const lastPlayed = new Date(pet.lastPlayed);
        
        const hoursSinceFed = (now - lastFed) / (1000 * 60 * 60);
        const hoursSincePlayed = (now - lastPlayed) / (1000 * 60 * 60);

        let updates = {};

        // Decrease hunger over time
        if (hoursSinceFed > 1) {
            const hungerDecrease = Math.floor(hoursSinceFed * 2);
            updates.hunger = Math.max(0, pet.hunger - hungerDecrease);
        }

        // Decrease happiness if not played with
        if (hoursSincePlayed > 2) {
            const happinessDecrease = Math.floor(hoursSincePlayed);
            updates.happiness = Math.max(0, pet.happiness - happinessDecrease);
        }

        // Decrease energy over time
        const energyDecrease = Math.floor(hoursSinceFed * 0.5);
        updates.energy = Math.max(0, pet.energy - energyDecrease);

        // Health affected by hunger and happiness
        if (pet.hunger < 20 || pet.happiness < 20) {
            updates.health = Math.max(0, pet.health - 5);
        } else if (pet.hunger > 80 && pet.happiness > 80) {
            updates.health = Math.min(100, pet.health + 2);
        }

        // Age progression
        const ageInHours = (now - new Date(pet.created)) / (1000 * 60 * 60);
        const newAge = Math.floor(ageInHours / 24); // Age in days
        
        if (newAge !== pet.age) {
            updates.age = newAge;
            const newStage = this.calculateLifeStage(newAge);
            if (newStage !== pet.stage) {
                updates.stage = newStage;
                await this.handleStageTransition(guildId, petId, newStage);
            }
        }

        // Update pet if there are changes
        if (Object.keys(updates).length > 0) {
            this.bot.db.updatePet(guildId, petId, updates);
        }

        // Check for pet death (health reaches 0)
        if (updates.health === 0 && pet.health > 0) {
            await this.handlePetDeath(guildId, petId);
        }
    }

    calculateLifeStage(age) {
        if (age < 3) return 'baby';
        if (age < 7) return 'child';
        if (age < 14) return 'teen';
        if (age < 30) return 'adult';
        return 'elder';
    }

    async handleStageTransition(guildId, petId, newStage) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return;

        try {
            const owner = await this.bot.users.fetch(pet.ownerId);
            const guild = this.bot.guilds.cache.get(guildId);
            
            const embed = new EmbedBuilder()
                .setTitle('🎉 Pet Evolution!')
                .setColor('#f1c40f')
                .setDescription(`${pet.name} has grown into a ${newStage}!`)
                .addFields(
                    { name: 'Pet', value: `${this.petEmojis[pet.type]} ${pet.name}`, inline: true },
                    { name: 'New Stage', value: newStage.charAt(0).toUpperCase() + newStage.slice(1), inline: true },
                    { name: 'Age', value: `${pet.age} days`, inline: true }
                )
                .setThumbnail(owner.displayAvatarURL({ dynamic: true }))
                .setTimestamp();

            // Try to send DM to owner
            try {
                await owner.send({ embeds: [embed] });
            } catch (error) {
                // If DM fails, try to find a general channel
                const channel = guild.channels.cache.find(c => c.name.includes('general') || c.name.includes('chat'));
                if (channel) {
                    await channel.send({ content: `<@${owner.id}>`, embeds: [embed] });
                }
            }

            // Award evolution bonus
            this.bot.db.addTokens(guildId, pet.ownerId, 25);

        } catch (error) {
            console.error('Error handling stage transition:', error);
        }
    }

    async handlePetDeath(guildId, petId) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return;

        try {
            const owner = await this.bot.users.fetch(pet.ownerId);
            const guild = this.bot.guilds.cache.get(guildId);
            
            const embed = new EmbedBuilder()
                .setTitle('💔 Pet Passed Away')
                .setColor('#2c2f33')
                .setDescription(`${pet.name} has passed away peacefully...`)
                .addFields(
                    { name: 'Pet', value: `${this.petEmojis[pet.type]} ${pet.name}`, inline: true },
                    { name: 'Age', value: `${pet.age} days`, inline: true },
                    { name: 'Stage', value: pet.stage.charAt(0).toUpperCase() + pet.stage.slice(1), inline: true },
                    { name: 'Memorial', value: 'Your pet will be remembered fondly. Consider adopting a new companion!', inline: false }
                )
                .setTimestamp();

            // Try to send DM to owner
            try {
                await owner.send({ embeds: [embed] });
            } catch (error) {
                // If DM fails, try to find a general channel
                const channel = guild.channels.cache.find(c => c.name.includes('general') || c.name.includes('chat'));
                if (channel) {
                    await channel.send({ content: `<@${owner.id}>`, embeds: [embed] });
                }
            }

        } catch (error) {
            console.error('Error handling pet death:', error);
        }
    }

    async createPet(guildId, userId, petType) {
        // Check if user already has maximum pets (limit to 3)
        const userPets = this.bot.db.getUserPets(guildId, userId);
        const activePets = userPets.filter(pet => pet.health > 0);
        
        if (activePets.length >= 3) {
            return { success: false, error: 'You can only have 3 active pets at a time!' };
        }

        const petId = this.bot.db.createPet(guildId, userId, petType);
        return { success: true, petId };
    }

    async feedPet(guildId, petId, userId) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return { success: false, error: 'Pet not found!' };
        if (pet.ownerId !== userId) return { success: false, error: 'This is not your pet!' };
        if (pet.health === 0) return { success: false, error: 'This pet has passed away!' };

        const now = new Date();
        const lastFed = new Date(pet.lastFed);
        const hoursSinceFed = (now - lastFed) / (1000 * 60 * 60);

        if (hoursSinceFed < 1) {
            return { success: false, error: 'Your pet is not hungry yet! Wait a bit.' };
        }

        // Check if user has pet food
        const balance = this.bot.db.getBalance(guildId, userId);
        const foodCost = 50;
        
        if (balance < foodCost) {
            return { success: false, error: `You need ${foodCost} tokens to buy pet food!` };
        }

        // Remove tokens and feed pet
        this.bot.db.removeTokens(guildId, userId, foodCost);
        
        const updates = {
            hunger: Math.min(100, pet.hunger + 30),
            health: Math.min(100, pet.health + 5),
            lastFed: now.toISOString()
        };

        this.bot.db.updatePet(guildId, petId, updates);
        await this.addExperience(guildId, petId, 5);

        return { success: true, message: `${pet.name} enjoyed the meal! +30 hunger, +5 health` };
    }

    async playWithPet(guildId, petId, userId) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return { success: false, error: 'Pet not found!' };
        if (pet.ownerId !== userId) return { success: false, error: 'This is not your pet!' };
        if (pet.health === 0) return { success: false, error: 'This pet has passed away!' };

        const now = new Date();
        const lastPlayed = new Date(pet.lastPlayed);
        const hoursSincePlayed = (now - lastPlayed) / (1000 * 60 * 60);

        if (hoursSincePlayed < 0.5) {
            return { success: false, error: 'Your pet is tired! Let them rest for a bit.' };
        }

        const updates = {
            happiness: Math.min(100, pet.happiness + 25),
            energy: Math.max(0, pet.energy - 10),
            lastPlayed: now.toISOString()
        };

        this.bot.db.updatePet(guildId, petId, updates);
        await this.addExperience(guildId, petId, 3);

        return { success: true, message: `You played with ${pet.name}! +25 happiness, -10 energy` };
    }

    async addExperience(guildId, petId, amount) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return;

        const newExp = pet.experience + amount;
        const newLevel = Math.floor(newExp / 100) + 1;
        
        const updates = { experience: newExp };
        
        if (newLevel > pet.level) {
            updates.level = newLevel;
            // Level up bonuses
            updates.health = Math.min(100, pet.health + 10);
            
            // Notify owner of level up
            await this.notifyLevelUp(guildId, petId, newLevel);
        }

        this.bot.db.updatePet(guildId, petId, updates);
    }

    async notifyLevelUp(guildId, petId, newLevel) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return;

        try {
            const owner = await this.bot.users.fetch(pet.ownerId);
            
            const embed = new EmbedBuilder()
                .setTitle('⬆️ Pet Level Up!')
                .setColor('#00ff00')
                .setDescription(`${pet.name} reached level ${newLevel}!`)
                .addFields(
                    { name: 'Pet', value: `${this.petEmojis[pet.type]} ${pet.name}`, inline: true },
                    { name: 'New Level', value: newLevel.toString(), inline: true },
                    { name: 'Bonus', value: '+10 Health', inline: true }
                )
                .setTimestamp();

            await owner.send({ embeds: [embed] });
        } catch (error) {
            console.error('Error notifying level up:', error);
        }
    }

    async handleReaction(reaction, user, action) {
        // Pet interaction through reactions
        if (reaction.emoji.name === '🍖' && action === 'add') {
            // Quick feed attempt
            const message = reaction.message;
            if (message.embeds.length > 0) {
                const embed = message.embeds[0];
                if (embed.title && embed.title.includes('Pet Status')) {
                    // Extract pet info and attempt to feed
                    // This would require parsing the embed or storing pet ID in message
                }
            }
        }
    }

    getPetStatusEmbed(pet, owner) {
        const emoji = this.petEmojis[pet.type] || '🐾';
        const stageEmoji = {
            'baby': '👶',
            'child': '🧒',
            'teen': '👦',
            'adult': '👨',
            'elder': '👴'
        };

        const healthBar = this.createStatBar(pet.health);
        const hungerBar = this.createStatBar(pet.hunger);
        const happinessBar = this.createStatBar(pet.happiness);
        const energyBar = this.createStatBar(pet.energy);

        const embed = new EmbedBuilder()
            .setTitle(`${emoji} ${pet.name} - ${stageEmoji[pet.stage]} ${pet.stage.charAt(0).toUpperCase() + pet.stage.slice(1)}`)
            .setColor(pet.health > 50 ? '#27ae60' : pet.health > 20 ? '#f39c12' : '#e74c3c')
            .addFields(
                { name: 'Health', value: healthBar, inline: true },
                { name: 'Hunger', value: hungerBar, inline: true },
                { name: 'Happiness', value: happinessBar, inline: true },
                { name: 'Energy', value: energyBar, inline: true },
                { name: 'Level', value: pet.level.toString(), inline: true },
                { name: 'Age', value: `${pet.age} days`, inline: true },
                { name: 'Experience', value: `${pet.experience}/100`, inline: true },
                { name: 'Type', value: pet.type, inline: true },
                { name: 'Items', value: pet.items.length > 0 ? pet.items.join(', ') : 'None', inline: true }
            )
            .setFooter({ text: `Owned by ${owner.username}`, iconURL: owner.displayAvatarURL({ dynamic: true }) })
            .setTimestamp();

        if (pet.health === 0) {
            embed.setDescription('💀 This pet has passed away...');
        }

        return embed;
    }

    createStatBar(value) {
        const maxBars = 10;
        const filledBars = Math.round((value / 100) * maxBars);
        const emptyBars = maxBars - filledBars;
        
        return '█'.repeat(filledBars) + '░'.repeat(emptyBars) + ` ${value}%`;
    }

    async buyPetItem(guildId, userId, petId, itemName) {
        const pet = this.bot.db.getPet(guildId, petId);
        if (!pet) return { success: false, error: 'Pet not found!' };
        if (pet.ownerId !== userId) return { success: false, error: 'This is not your pet!' };

        const shopItems = this.bot.db.getShopItems(guildId);
        const item = shopItems[itemName];
        
        if (!item || item.type !== 'pet') {
            return { success: false, error: 'Item not found in pet section!' };
        }

        const balance = this.bot.db.getBalance(guildId, userId);
        if (balance < item.price) {
            return { success: false, error: `You need ${item.price} tokens to buy this item!` };
        }

        // Remove tokens and add item to pet
        this.bot.db.removeTokens(guildId, userId, item.price);
        
        const updates = { items: [...pet.items, itemName] };
        
        // Apply item effects
        switch (itemName) {
            case 'Pet House':
                updates.happiness = Math.min(100, pet.happiness + 20);
                break;
            case 'Pet Clothes':
                updates.happiness = Math.min(100, pet.happiness + 15);
                break;
            case 'Pet Toy':
                updates.happiness = Math.min(100, pet.happiness + 10);
                break;
        }

        this.bot.db.updatePet(guildId, petId, updates);
        
        return { success: true, message: `Bought ${itemName} for ${pet.name}!` };
    }
}

module.exports = PetSystem;