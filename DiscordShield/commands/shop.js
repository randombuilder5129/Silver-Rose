const { SlashCommandBuilder, EmbedBuilder, PermissionFlagsBits } = require('discord.js');

class ShopCommands {
    constructor(bot) {
        this.bot = bot;
    }

    register() {
        // Shop command - view items
        const shopCommand = {
            data: new SlashCommandBuilder()
                .setName('shop')
                .setDescription('Browse the server shop'),
            async execute(interaction) {
                try {
                    const shopItems = interaction.client.db.getShopItems(interaction.guildId);
                    
                    if (Object.keys(shopItems).length === 0) {
                        await interaction.reply('The shop is currently empty. Administrators can add items using `/additem`.');
                        return;
                    }

                    const embed = new EmbedBuilder()
                        .setTitle('🛒 Server Shop')
                        .setColor('#3498db')
                        .setTimestamp();

                    const itemsByType = {};
                    Object.entries(shopItems).forEach(([name, item]) => {
                        if (!itemsByType[item.type]) {
                            itemsByType[item.type] = [];
                        }
                        itemsByType[item.type].push(`**${name}** - ${item.price} tokens\n*${item.description}*`);
                    });

                    Object.entries(itemsByType).forEach(([type, items]) => {
                        const typeEmoji = {
                            'role': '👑',
                            'cosmetic': '🎨', 
                            'pet': '🐾',
                            'utility': '🔧'
                        };
                        
                        embed.addFields({
                            name: `${typeEmoji[type] || '📦'} ${type.charAt(0).toUpperCase() + type.slice(1)} Items`,
                            value: items.join('\n\n'),
                            inline: false
                        });
                    });

                    const userBalance = interaction.client.db.getBalance(interaction.guildId, interaction.user.id);
                    embed.setFooter({ text: `Your balance: ${userBalance} tokens | Use /buy <item> to purchase` });

                    await interaction.reply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'shop', true);

                } catch (error) {
                    console.error('Error in shop command:', error);
                    await interaction.reply('An error occurred while displaying the shop.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'shop', false, error.message);
                }
            }
        };

        // Buy command
        const buyCommand = {
            data: new SlashCommandBuilder()
                .setName('buy')
                .setDescription('Buy an item from the shop')
                .addStringOption(option =>
                    option.setName('item')
                        .setDescription('Name of the item to buy')
                        .setRequired(true)),
            async execute(interaction) {
                try {
                    const itemName = interaction.options.getString('item');
                    const shopItems = interaction.client.db.getShopItems(interaction.guildId);
                    const item = shopItems[itemName];

                    if (!item) {
                        await interaction.reply(`Item "${itemName}" not found in the shop. Use \`/shop\` to see available items.`);
                        return;
                    }

                    const userBalance = interaction.client.db.getBalance(interaction.guildId, interaction.user.id);
                    
                    if (userBalance < item.price) {
                        await interaction.reply(`You don't have enough tokens! You need ${item.price} tokens but only have ${userBalance}.`);
                        return;
                    }

                    // Remove tokens
                    interaction.client.db.removeTokens(interaction.guildId, interaction.user.id, item.price);

                    const embed = new EmbedBuilder()
                        .setTitle('✅ Purchase Successful!')
                        .setColor('#27ae60')
                        .addFields(
                            { name: 'Item', value: itemName, inline: true },
                            { name: 'Price', value: `${item.price} tokens`, inline: true },
                            { name: 'Remaining Balance', value: `${userBalance - item.price} tokens`, inline: true }
                        )
                        .setDescription(item.description)
                        .setFooter({ text: `Purchased by ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL({ dynamic: true }) })
                        .setTimestamp();

                    await interaction.reply({ embeds: [embed] });

                    // Log the purchase
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'buy', true, `Bought ${itemName} for ${item.price} tokens`);

                } catch (error) {
                    console.error('Error in buy command:', error);
                    await interaction.reply('An error occurred while processing your purchase.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'buy', false, error.message);
                }
            }
        };

        // Add item command (admin only)
        const addItemCommand = {
            data: new SlashCommandBuilder()
                .setName('additem')
                .setDescription('Add an item to the shop (Admin only)')
                .addStringOption(option =>
                    option.setName('name')
                        .setDescription('Name of the item')
                        .setRequired(true))
                .addIntegerOption(option =>
                    option.setName('price')
                        .setDescription('Price in tokens')
                        .setRequired(true)
                        .setMinValue(1))
                .addStringOption(option =>
                    option.setName('type')
                        .setDescription('Type of item')
                        .setRequired(true)
                        .addChoices(
                            { name: 'Role', value: 'role' },
                            { name: 'Cosmetic', value: 'cosmetic' },
                            { name: 'Pet Item', value: 'pet' },
                            { name: 'Utility', value: 'utility' }
                        ))
                .addStringOption(option =>
                    option.setName('description')
                        .setDescription('Description of the item')
                        .setRequired(true)),
            async execute(interaction) {
                // Check permissions
                if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
                    await interaction.reply({ content: 'You need Administrator permissions to use this command.', ephemeral: true });
                    return;
                }

                try {
                    const name = interaction.options.getString('name');
                    const price = interaction.options.getInteger('price');
                    const type = interaction.options.getString('type');
                    const description = interaction.options.getString('description');

                    // Check if item already exists
                    const shopItems = interaction.client.db.getShopItems(interaction.guildId);
                    if (shopItems[name]) {
                        await interaction.reply(`An item named "${name}" already exists in the shop.`);
                        return;
                    }

                    // Add item to shop
                    interaction.client.db.addShopItem(interaction.guildId, name, price, type, description);

                    const embed = new EmbedBuilder()
                        .setTitle('✅ Item Added to Shop')
                        .setColor('#27ae60')
                        .addFields(
                            { name: 'Name', value: name, inline: true },
                            { name: 'Price', value: `${price} tokens`, inline: true },
                            { name: 'Type', value: type, inline: true },
                            { name: 'Description', value: description, inline: false }
                        )
                        .setFooter({ text: `Added by ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL({ dynamic: true }) })
                        .setTimestamp();

                    await interaction.reply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'additem', true, `Added ${name} to shop`);

                } catch (error) {
                    console.error('Error in additem command:', error);
                    await interaction.reply('An error occurred while adding the item to the shop.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'additem', false, error.message);
                }
            }
        };

        // Remove item command (admin only)
        const removeItemCommand = {
            data: new SlashCommandBuilder()
                .setName('removeitem')
                .setDescription('Remove an item from the shop (Admin only)')
                .addStringOption(option =>
                    option.setName('name')
                        .setDescription('Name of the item to remove')
                        .setRequired(true)),
            async execute(interaction) {
                // Check permissions
                if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {
                    await interaction.reply({ content: 'You need Administrator permissions to use this command.', ephemeral: true });
                    return;
                }

                try {
                    const name = interaction.options.getString('name');
                    
                    const success = interaction.client.db.removeShopItem(interaction.guildId, name);
                    
                    if (!success) {
                        await interaction.reply(`Item "${name}" not found in the shop.`);
                        return;
                    }

                    const embed = new EmbedBuilder()
                        .setTitle('🗑️ Item Removed from Shop')
                        .setColor('#e74c3c')
                        .setDescription(`Successfully removed "${name}" from the shop.`)
                        .setFooter({ text: `Removed by ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL({ dynamic: true }) })
                        .setTimestamp();

                    await interaction.reply({ embeds: [embed] });

                    // Log the command
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'removeitem', true, `Removed ${name} from shop`);

                } catch (error) {
                    console.error('Error in removeitem command:', error);
                    await interaction.reply('An error occurred while removing the item from the shop.');
                    interaction.client.db.logCommand(interaction.guildId, interaction.user.id, 'removeitem', false, error.message);
                }
            }
        };

        // Register all commands
        this.bot.commands.set('shop', shopCommand);
        this.bot.commands.set('buy', buyCommand);
        this.bot.commands.set('additem', addItemCommand);
        this.bot.commands.set('removeitem', removeItemCommand);
    }
}

module.exports = ShopCommands;