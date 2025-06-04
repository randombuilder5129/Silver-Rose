const { SlashCommandBuilder, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');

class PetCommands {
    constructor(bot) {
        this.bot = bot;
    }

    register() {
        // Adopt pet command
        const adoptCommand = {
            data: new SlashCommandBuilder()
                .setName('adopt')
                .setDescription('Adopt a new pet')
                .addStringOption(option =>
                    option.setName('type')
                        .setDescription('Type of pet to adopt')
                        .setRequired(true)
                        .addChoices(
                            { name: 'Dog 🐕', value: 'Dog' },
                            { name: 'Cat 🐱', value: 'Cat' },
                            { name: 'Bird 🐦', value: 'Bird' },
                            { name: 'Fish 🐠', value: 'Fish' },
                            { name: 'Hamster 🐹', value: 'Hamster' },
                            { name: 'Dragon 🐉', value: 'Dragon' },
                            { name: 'Phoenix 🔥', value: 'Phoenix' },
                            { name: 'Unicorn 🦄', value: 'Unicorn' }
                        )),
            async execute(interaction) {
                try {
                    const petType = interaction.options.getString('type');
                    const adoptionCost = 100;
                    
                    const userBalance = interaction.client.db.getBalance(interaction.guildId, interaction.user.id);
                    
                    if (userBalance < adoptionCost) {
                        await interaction.reply(`You need ${adoptionCost} tokens to adopt a pet. You currently have ${userBalance} tokens.`);
                        return;
                    }

                    const result = await interaction.client.petSystem.createPet(interaction.guildId, interaction.user.id, petType);
                    
                    if (!result.success) {
                        await interaction.reply(result.error);
                        return;
                    }

                    // Remove adoption cost
                    interaction.client.db.removeTokens(interaction.guildId, interaction.user.id, adoptionCost);

                    const pet = interaction.client.db.getPet(interaction.guildId, result.petId);
                    const embed = interaction.client.petSystem.getPetStatusEmbed(pet, interaction.user);
                    
                    embed.setTitle(`🎉 Congratulations! You adopted a ${petType}!`);
                    embed.setDescription(`Welcome your new ${petType} to the family! Take good care of them.`);

                    await interaction.reply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'adopt', true, `Adopted ${petType}`);

                } catch (error) {
                    console.error('Error in adopt command:', error);
                    await interaction.reply('An error occurred while adopting your pet.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'adopt', false, error.message);
                }
            }
        };

        // Pet status command
        const petCommand = {
            data: new SlashCommandBuilder()
                .setName('pet')
                .setDescription('View your pets or interact with them')
                .addSubcommand(subcommand =>
                    subcommand
                        .setName('status')
                        .setDescription('View your pet status'))
                .addSubcommand(subcommand =>
                    subcommand
                        .setName('feed')
                        .setDescription('Feed your pet')
                        .addStringOption(option =>
                            option.setName('petname')
                                .setDescription('Name of the pet to feed')
                                .setRequired(true)))
                .addSubcommand(subcommand =>
                    subcommand
                        .setName('play')
                        .setDescription('Play with your pet')
                        .addStringOption(option =>
                            option.setName('petname')
                                .setDescription('Name of the pet to play with')
                                .setRequired(true)))
                .addSubcommand(subcommand =>
                    subcommand
                        .setName('rename')
                        .setDescription('Rename your pet')
                        .addStringOption(option =>
                            option.setName('oldname')
                                .setDescription('Current name of the pet')
                                .setRequired(true))
                        .addStringOption(option =>
                            option.setName('newname')
                                .setDescription('New name for the pet')
                                .setRequired(true))),
            async execute(interaction) {
                try {
                    const subcommand = interaction.options.getSubcommand();
                    const userPets = interaction.client.db.getUserPets(interaction.guildId, interaction.user.id);
                    const activePets = userPets.filter(pet => pet.health > 0);

                    if (subcommand === 'status') {
                        if (userPets.length === 0) {
                            await interaction.reply('You don\'t have any pets yet! Use `/adopt` to get your first pet.');
                            return;
                        }

                        const embeds = [];
                        for (const pet of userPets) {
                            const embed = interaction.client.petSystem.getPetStatusEmbed(pet, interaction.user);
                            embeds.push(embed);
                        }

                        await interaction.reply({ embeds: embeds.slice(0, 10) }); // Discord limit of 10 embeds

                    } else if (subcommand === 'feed') {
                        const petName = interaction.options.getString('petname');
                        const pet = activePets.find(p => p.name.toLowerCase() === petName.toLowerCase());
                        
                        if (!pet) {
                            await interaction.reply(`You don't have an active pet named "${petName}".`);
                            return;
                        }

                        const result = await interaction.client.petSystem.feedPet(interaction.guildId, pet.id, interaction.user.id);
                        
                        if (result.success) {
                            const embed = new EmbedBuilder()
                                .setTitle('🍖 Feeding Time!')
                                .setColor('#27ae60')
                                .setDescription(result.message)
                                .setTimestamp();

                            await interaction.reply({ embeds: [embed] });
                        } else {
                            await interaction.reply(result.error);
                        }

                    } else if (subcommand === 'play') {
                        const petName = interaction.options.getString('petname');
                        const pet = activePets.find(p => p.name.toLowerCase() === petName.toLowerCase());
                        
                        if (!pet) {
                            await interaction.reply(`You don't have an active pet named "${petName}".`);
                            return;
                        }

                        const result = await interaction.client.petSystem.playWithPet(interaction.guildId, pet.id, interaction.user.id);
                        
                        if (result.success) {
                            const embed = new EmbedBuilder()
                                .setTitle('🎾 Playtime!')
                                .setColor('#f39c12')
                                .setDescription(result.message)
                                .setTimestamp();

                            await interaction.reply({ embeds: [embed] });
                        } else {
                            await interaction.reply(result.error);
                        }

                    } else if (subcommand === 'rename') {
                        const oldName = interaction.options.getString('oldname');
                        const newName = interaction.options.getString('newname');
                        const pet = userPets.find(p => p.name.toLowerCase() === oldName.toLowerCase());
                        
                        if (!pet) {
                            await interaction.reply(`You don't have a pet named "${oldName}".`);
                            return;
                        }

                        if (newName.length > 20) {
                            await interaction.reply('Pet names cannot be longer than 20 characters.');
                            return;
                        }

                        interaction.client.db.updatePet(interaction.guildId, pet.id, { name: newName });

                        const embed = new EmbedBuilder()
                            .setTitle('✏️ Pet Renamed!')
                            .setColor('#3498db')
                            .setDescription(`Successfully renamed "${oldName}" to "${newName}"!`)
                            .setTimestamp();

                        await interaction.reply({ embeds: [embed] });
                    }

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'pet', true, subcommand);

                } catch (error) {
                    console.error('Error in pet command:', error);
                    await interaction.reply('An error occurred while processing your pet command.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'pet', false, error.message);
                }
            }
        };

        // Pet leaderboard command
        const petleaderboardCommand = {
            data: new SlashCommandBuilder()
                .setName('petleaderboard')
                .setDescription('View the top pets in the server'),
            async execute(interaction) {
                try {
                    const allPets = interaction.client.db.getGuildData(interaction.guildId, 'pets') || {};
                    const activePets = Object.values(allPets).filter(pet => pet.health > 0);
                    
                    if (activePets.length === 0) {
                        await interaction.reply('No active pets in this server yet!');
                        return;
                    }

                    // Sort by level, then by experience
                    const topPets = activePets
                        .sort((a, b) => {
                            if (a.level !== b.level) return b.level - a.level;
                            return b.experience - a.experience;
                        })
                        .slice(0, 10);

                    const embed = new EmbedBuilder()
                        .setTitle('🏆 Pet Leaderboard')
                        .setColor('#f1c40f')
                        .setTimestamp();

                    let description = '';
                    for (let i = 0; i < topPets.length; i++) {
                        const pet = topPets[i];
                        const owner = await interaction.client.users.fetch(pet.ownerId).catch(() => null);
                        const ownerName = owner ? owner.username : 'Unknown';
                        const emoji = interaction.client.petSystem.petEmojis[pet.type] || '🐾';
                        
                        description += `**${i + 1}.** ${emoji} ${pet.name} (Level ${pet.level})\n`;
                        description += `Owner: ${ownerName} | Age: ${pet.age} days | Stage: ${pet.stage}\n\n`;
                    }

                    embed.setDescription(description);

                    await interaction.reply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'petleaderboard', true);

                } catch (error) {
                    console.error('Error in petleaderboard command:', error);
                    await interaction.reply('An error occurred while displaying the pet leaderboard.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'petleaderboard', false, error.message);
                }
            }
        };

        // Buy pet item command
        const buypetitemCommand = {
            data: new SlashCommandBuilder()
                .setName('buypetitem')
                .setDescription('Buy an item for your pet')
                .addStringOption(option =>
                    option.setName('item')
                        .setDescription('Item to buy')
                        .setRequired(true)
                        .addChoices(
                            { name: 'Pet Food (50 tokens)', value: 'Pet Food' },
                            { name: 'Pet Toy (75 tokens)', value: 'Pet Toy' },
                            { name: 'Pet House (200 tokens)', value: 'Pet House' },
                            { name: 'Pet Clothes (150 tokens)', value: 'Pet Clothes' }
                        ))
                .addStringOption(option =>
                    option.setName('petname')
                        .setDescription('Name of the pet')
                        .setRequired(true)),
            async execute(interaction) {
                try {
                    const itemName = interaction.options.getString('item');
                    const petName = interaction.options.getString('petname');
                    
                    const userPets = interaction.client.db.getUserPets(interaction.guildId, interaction.user.id);
                    const activePets = userPets.filter(pet => pet.health > 0);
                    const pet = activePets.find(p => p.name.toLowerCase() === petName.toLowerCase());
                    
                    if (!pet) {
                        await interaction.reply(`You don't have an active pet named "${petName}".`);
                        return;
                    }

                    const result = await interaction.client.petSystem.buyPetItem(interaction.guildId, interaction.user.id, pet.id, itemName);
                    
                    if (result.success) {
                        const embed = new EmbedBuilder()
                            .setTitle('🛍️ Purchase Successful!')
                            .setColor('#27ae60')
                            .setDescription(result.message)
                            .setTimestamp();

                        await interaction.reply({ embeds: [embed] });
                    } else {
                        await interaction.reply(result.error);
                    }

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'buypetitem', true, `${itemName} for ${petName}`);

                } catch (error) {
                    console.error('Error in buypetitem command:', error);
                    await interaction.reply('An error occurred while buying the pet item.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'buypetitem', false, error.message);
                }
            }
        };

        // Register all commands
        this.bot.commands.set('adopt', adoptCommand);
        this.bot.commands.set('pet', petCommand);
        this.bot.commands.set('petleaderboard', petleaderboardCommand);
        this.bot.commands.set('buypetitem', buypetitemCommand);
    }
}

module.exports = PetCommands;