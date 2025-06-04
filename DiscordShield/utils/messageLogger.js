const { EmbedBuilder } = require('discord.js');

class MessageLogger {
    constructor(bot) {
        this.bot = bot;
    }

    async logMessage(message) {
        try {
            const messageData = {
                messageId: message.id,
                userId: message.author.id,
                username: message.author.username,
                channelId: message.channel.id,
                channelName: message.channel.name,
                content: message.content,
                attachments: message.attachments.map(att => ({
                    name: att.name,
                    url: att.url,
                    size: att.size
                })),
                embeds: message.embeds.length,
                mentions: {
                    users: message.mentions.users.map(user => user.id),
                    roles: message.mentions.roles.map(role => role.id),
                    channels: message.mentions.channels.map(channel => channel.id)
                }
            };

            // Store in database
            this.bot.db.logMessage(message.guild.id, messageData);

            // Send to log channel if configured
            await this.sendToLogChannel(message.guild, 'message', messageData);

        } catch (error) {
            console.error('Error logging message:', error);
        }
    }

    async logCommand(interaction) {
        try {
            const commandData = {
                commandId: interaction.id,
                userId: interaction.user.id,
                username: interaction.user.username,
                command: interaction.commandName,
                options: interaction.options.data.map(option => ({
                    name: option.name,
                    value: option.value,
                    type: option.type
                })),
                channelId: interaction.channel.id,
                channelName: interaction.channel.name,
                guildId: interaction.guild.id
            };

            // Store in database
            this.bot.db.logCommand(
                interaction.guild.id,
                interaction.user.id,
                interaction.commandName,
                true,
                JSON.stringify(commandData)
            );

            // Send to log channel
            await this.sendCommandToLogChannel(interaction.guild, commandData);

        } catch (error) {
            console.error('Error logging command:', error);
        }
    }

    async logCommandResult(interaction, success, error = null) {
        try {
            const resultData = {
                commandId: interaction.id,
                success,
                error: error ? error.message : null,
                executionTime: Date.now() - interaction.createdTimestamp
            };

            // Update command log with result
            this.bot.db.logCommand(
                interaction.guild.id,
                interaction.user.id,
                interaction.commandName,
                success,
                JSON.stringify(resultData)
            );

            // Send result to log channel
            await this.sendCommandResultToLogChannel(interaction.guild, resultData, interaction);

        } catch (error) {
            console.error('Error logging command result:', error);
        }
    }

    async sendToLogChannel(guild, type, data) {
        const logChannelId = this.bot.db.getConfig(guild.id, 'logChannel');
        if (!logChannelId) return;

        const logChannel = guild.channels.cache.get(logChannelId);
        if (!logChannel) return;

        try {
            let embed;

            switch (type) {
                case 'message':
                    embed = new EmbedBuilder()
                        .setTitle('📝 Message Logged')
                        .setColor('#3498db')
                        .addFields(
                            { name: 'User', value: `<@${data.userId}> (${data.username})`, inline: true },
                            { name: 'Channel', value: `<#${data.channelId}>`, inline: true },
                            { name: 'Message ID', value: data.messageId, inline: true },
                            { name: 'Content', value: data.content || '*No content*', inline: false }
                        )
                        .setTimestamp();

                    if (data.attachments.length > 0) {
                        embed.addFields({
                            name: 'Attachments',
                            value: data.attachments.map(att => `${att.name} (${(att.size / 1024).toFixed(1)}KB)`).join('\n'),
                            inline: false
                        });
                    }

                    if (data.mentions.users.length > 0) {
                        embed.addFields({
                            name: 'User Mentions',
                            value: data.mentions.users.map(id => `<@${id}>`).join(', '),
                            inline: false
                        });
                    }
                    break;
            }

            if (embed) {
                await logChannel.send({ embeds: [embed] });
            }
        } catch (error) {
            console.error('Error sending to log channel:', error);
        }
    }

    async sendCommandToLogChannel(guild, commandData) {
        const logChannelId = this.bot.db.getConfig(guild.id, 'logChannel');
        if (!logChannelId) return;

        const logChannel = guild.channels.cache.get(logChannelId);
        if (!logChannel) return;

        try {
            const embed = new EmbedBuilder()
                .setTitle('⚡ Command Executed')
                .setColor('#f39c12')
                .addFields(
                    { name: 'User', value: `<@${commandData.userId}> (${commandData.username})`, inline: true },
                    { name: 'Command', value: `/${commandData.command}`, inline: true },
                    { name: 'Channel', value: `<#${commandData.channelId}>`, inline: true }
                )
                .setTimestamp();

            if (commandData.options.length > 0) {
                embed.addFields({
                    name: 'Options',
                    value: commandData.options.map(opt => `${opt.name}: ${opt.value}`).join('\n'),
                    inline: false
                });
            }

            await logChannel.send({ embeds: [embed] });
        } catch (error) {
            console.error('Error sending command to log channel:', error);
        }
    }

    async sendCommandResultToLogChannel(guild, resultData, interaction) {
        const logChannelId = this.bot.db.getConfig(guild.id, 'logChannel');
        if (!logChannelId) return;

        const logChannel = guild.channels.cache.get(logChannelId);
        if (!logChannel) return;

        try {
            const embed = new EmbedBuilder()
                .setTitle(resultData.success ? '✅ Command Successful' : '❌ Command Failed')
                .setColor(resultData.success ? '#27ae60' : '#e74c3c')
                .addFields(
                    { name: 'Command', value: `/${interaction.commandName}`, inline: true },
                    { name: 'User', value: `<@${interaction.user.id}>`, inline: true },
                    { name: 'Execution Time', value: `${resultData.executionTime}ms`, inline: true }
                )
                .setTimestamp();

            if (!resultData.success && resultData.error) {
                embed.addFields({
                    name: 'Error',
                    value: resultData.error.substring(0, 1000),
                    inline: false
                });
            }

            await logChannel.send({ embeds: [embed] });
        } catch (error) {
            console.error('Error sending command result to log channel:', error);
        }
    }

    async getMessageLogs(guildId, limit = 50) {
        return this.bot.db.getMessages(guildId, limit);
    }

    async getCommandLogs(guildId, limit = 50) {
        return this.bot.db.getCommandLogs(guildId, limit);
    }

    async searchMessages(guildId, query, limit = 20) {
        const messages = this.bot.db.getMessages(guildId, 1000);
        return messages.filter(msg => 
            msg.content.toLowerCase().includes(query.toLowerCase()) ||
            msg.username.toLowerCase().includes(query.toLowerCase())
        ).slice(0, limit);
    }

    async getUserMessageCount(guildId, userId, days = 7) {
        const messages = this.bot.db.getMessages(guildId, 10000);
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);

        return messages.filter(msg => 
            msg.userId === userId && 
            new Date(msg.timestamp) > cutoff
        ).length;
    }

    async getChannelActivity(guildId, channelId, days = 7) {
        const messages = this.bot.db.getMessages(guildId, 10000);
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - days);

        return messages.filter(msg => 
            msg.channelId === channelId && 
            new Date(msg.timestamp) > cutoff
        ).length;
    }

    async generateActivityReport(guildId) {
        const messages = this.bot.db.getMessages(guildId, 10000);
        const commands = this.bot.db.getCommandLogs(guildId, 1000);
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - 7);

        const recentMessages = messages.filter(msg => new Date(msg.timestamp) > cutoff);
        const recentCommands = commands.filter(cmd => new Date(cmd.timestamp) > cutoff);

        const userActivity = {};
        recentMessages.forEach(msg => {
            if (!userActivity[msg.userId]) {
                userActivity[msg.userId] = { messages: 0, commands: 0, username: msg.username };
            }
            userActivity[msg.userId].messages++;
        });

        recentCommands.forEach(cmd => {
            if (!userActivity[cmd.userId]) {
                userActivity[cmd.userId] = { messages: 0, commands: 0 };
            }
            userActivity[cmd.userId].commands++;
        });

        const channelActivity = {};
        recentMessages.forEach(msg => {
            if (!channelActivity[msg.channelId]) {
                channelActivity[msg.channelId] = { count: 0, name: msg.channelName };
            }
            channelActivity[msg.channelId].count++;
        });

        return {
            totalMessages: recentMessages.length,
            totalCommands: recentCommands.length,
            activeUsers: Object.keys(userActivity).length,
            topUsers: Object.entries(userActivity)
                .sort(([,a], [,b]) => (b.messages + b.commands) - (a.messages + a.commands))
                .slice(0, 5),
            topChannels: Object.entries(channelActivity)
                .sort(([,a], [,b]) => b.count - a.count)
                .slice(0, 5)
        };
    }
}

module.exports = MessageLogger;