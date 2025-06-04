const { EmbedBuilder } = require('discord.js');

class CountingGame {
    constructor(bot) {
        this.bot = bot;
    }

    async processMessage(message) {
        const countingData = this.bot.db.getCountingData(message.guild.id);
        
        // Check if this is the counting channel
        if (!countingData.channel || message.channel.id !== countingData.channel) {
            return;
        }

        const content = message.content.trim();
        const expectedNumber = countingData.number;
        const messageNumber = parseInt(content);

        // Check if message is a valid number
        if (isNaN(messageNumber)) {
            await this.handleInvalidMessage(message, 'not a number');
            return;
        }

        // Check if it's the correct number
        if (messageNumber !== expectedNumber) {
            await this.handleWrongNumber(message, messageNumber, expectedNumber);
            return;
        }

        // Check if same user posted twice in a row
        if (countingData.lastUser === message.author.id) {
            await this.handleSameUser(message, messageNumber);
            return;
        }

        // Valid count!
        await this.handleCorrectCount(message, messageNumber);
    }

    async handleCorrectCount(message, number) {
        try {
            // Update counting data
            const newCountingData = {
                channel: message.channel.id,
                number: number + 1,
                lastUser: message.author.id
            };
            
            this.bot.db.updateCounting(message.guild.id, newCountingData);

            // Award tokens for correct counting
            const tokens = Math.floor(number / 10) + 1; // 1 token + bonus every 10 numbers
            this.bot.db.addTokens(message.guild.id, message.author.id, tokens);

            // Add reaction to show success
            await message.react('✅');

            // Special milestones
            if (number % 100 === 0) {
                await this.celebrateMilestone(message, number);
            }

            // Log the successful count
            await this.logCount(message.guild, message.author, number, 'success');

        } catch (error) {
            console.error('Error handling correct count:', error);
        }
    }

    async handleWrongNumber(message, givenNumber, expectedNumber) {
        try {
            await message.react('❌');
            
            // Remove tokens as penalty
            const penalty = 25;
            const removed = this.bot.db.removeTokens(message.guild.id, message.author.id, penalty);
            
            // Reset counting to 1
            const newCountingData = {
                channel: message.channel.id,
                number: 1,
                lastUser: null
            };
            
            this.bot.db.updateCounting(message.guild.id, newCountingData);

            // Send failure message
            const embed = new EmbedBuilder()
                .setTitle('💥 Counting Failed!')
                .setColor('#e74c3c')
                .setDescription(`${message.author} broke the count!`)
                .addFields(
                    { name: 'Expected', value: expectedNumber.toString(), inline: true },
                    { name: 'Given', value: givenNumber.toString(), inline: true },
                    { name: 'Penalty', value: removed ? `${penalty} tokens removed` : 'No tokens to remove', inline: true }
                )
                .setFooter({ text: 'Count has been reset to 1' })
                .setTimestamp();

            await message.channel.send({ embeds: [embed] });

            // Log the failed count
            await this.logCount(message.guild, message.author, givenNumber, 'wrong_number', expectedNumber);

        } catch (error) {
            console.error('Error handling wrong number:', error);
        }
    }

    async handleSameUser(message, number) {
        try {
            await message.react('🚫');
            
            // Remove tokens as penalty
            const penalty = 25;
            const removed = this.bot.db.removeTokens(message.guild.id, message.author.id, penalty);
            
            // Reset counting to 1
            const newCountingData = {
                channel: message.channel.id,
                number: 1,
                lastUser: null
            };
            
            this.bot.db.updateCounting(message.guild.id, newCountingData);

            // Send failure message
            const embed = new EmbedBuilder()
                .setTitle('🚫 Counting Failed!')
                .setColor('#e74c3c')
                .setDescription(`${message.author} counted twice in a row!`)
                .addFields(
                    { name: 'Number', value: number.toString(), inline: true },
                    { name: 'Penalty', value: removed ? `${penalty} tokens removed` : 'No tokens to remove', inline: true }
                )
                .setFooter({ text: 'Count has been reset to 1. Wait for someone else to count!' })
                .setTimestamp();

            await message.channel.send({ embeds: [embed] });

            // Log the failed count
            await this.logCount(message.guild, message.author, number, 'same_user');

        } catch (error) {
            console.error('Error handling same user:', error);
        }
    }

    async handleInvalidMessage(message, reason) {
        try {
            await message.react('❓');
            
            // Don't reset for invalid messages, just ignore them
            const countingData = this.bot.db.getCountingData(message.guild.id);
            
            // Send a gentle reminder
            const embed = new EmbedBuilder()
                .setTitle('❓ Invalid Count')
                .setColor('#f39c12')
                .setDescription(`${message.author}, please send the next number: **${countingData.number}**`)
                .setFooter({ text: 'Only numbers are allowed in the counting channel!' })
                .setTimestamp();

            const reply = await message.channel.send({ embeds: [embed] });
            
            // Delete the reminder after 10 seconds
            setTimeout(async () => {
                try {
                    await reply.delete();
                } catch (error) {
                    // Ignore deletion errors
                }
            }, 10000);

        } catch (error) {
            console.error('Error handling invalid message:', error);
        }
    }

    async celebrateMilestone(message, number) {
        try {
            const embed = new EmbedBuilder()
                .setTitle('🎉 Milestone Reached!')
                .setColor('#f1c40f')
                .setDescription(`Congratulations! The server reached **${number}**!`)
                .addFields(
                    { name: 'Achieved By', value: message.author.toString(), inline: true },
                    { name: 'Bonus Reward', value: '50 tokens', inline: true }
                )
                .setThumbnail(message.author.displayAvatarURL({ dynamic: true }))
                .setTimestamp();

            await message.channel.send({ embeds: [embed] });

            // Award milestone bonus
            this.bot.db.addTokens(message.guild.id, message.author.id, 50);

        } catch (error) {
            console.error('Error celebrating milestone:', error);
        }
    }

    async logCount(guild, user, number, result, expectedNumber = null) {
        const logChannelId = this.bot.db.getConfig(guild.id, 'logChannel');
        if (!logChannelId) return;

        const logChannel = guild.channels.cache.get(logChannelId);
        if (!logChannel) return;

        try {
            let title, color, description;

            switch (result) {
                case 'success':
                    title = '🔢 Counting Success';
                    color = '#27ae60';
                    description = `${user} correctly counted **${number}**`;
                    break;
                case 'wrong_number':
                    title = '💥 Counting Failed - Wrong Number';
                    color = '#e74c3c';
                    description = `${user} gave **${number}** but expected **${expectedNumber}**`;
                    break;
                case 'same_user':
                    title = '🚫 Counting Failed - Same User';
                    color = '#e74c3c';
                    description = `${user} counted **${number}** but counted twice in a row`;
                    break;
                default:
                    return;
            }

            const embed = new EmbedBuilder()
                .setTitle(title)
                .setColor(color)
                .setDescription(description)
                .addFields(
                    { name: 'User', value: `${user.tag} (<@${user.id}>)`, inline: true },
                    { name: 'Channel', value: `<#${guild.channels.cache.find(c => c.id === this.bot.db.getCountingData(guild.id).channel)?.id}>`, inline: true }
                )
                .setTimestamp();

            await logChannel.send({ embeds: [embed] });
        } catch (error) {
            console.error('Error logging count:', error);
        }
    }

    async setCountingChannel(guildId, channelId) {
        const countingData = {
            channel: channelId,
            number: 1,
            lastUser: null
        };
        
        this.bot.db.updateCounting(guildId, countingData);
        return true;
    }

    async resetCounting(guildId) {
        const countingData = this.bot.db.getCountingData(guildId);
        const newCountingData = {
            channel: countingData.channel,
            number: 1,
            lastUser: null
        };
        
        this.bot.db.updateCounting(guildId, newCountingData);
        return true;
    }

    async getCountingStats(guildId) {
        const countingData = this.bot.db.getCountingData(guildId);
        const messages = this.bot.db.getMessages(guildId, 10000);
        
        // Filter counting messages
        const countingMessages = messages.filter(msg => 
            msg.channelId === countingData.channel && 
            !isNaN(parseInt(msg.content.trim()))
        );

        // Calculate user participation
        const userCounts = {};
        countingMessages.forEach(msg => {
            if (!userCounts[msg.userId]) {
                userCounts[msg.userId] = 0;
            }
            userCounts[msg.userId]++;
        });

        const topCounters = Object.entries(userCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5);

        return {
            currentNumber: countingData.number,
            channel: countingData.channel,
            lastUser: countingData.lastUser,
            totalCounts: countingMessages.length,
            topCounters: topCounters,
            highestReached: Math.max(...countingMessages.map(msg => parseInt(msg.content.trim())).filter(n => !isNaN(n)), 0)
        };
    }

    getNextNumber(guildId) {
        const countingData = this.bot.db.getCountingData(guildId);
        return countingData.number;
    }

    getCountingChannel(guildId) {
        const countingData = this.bot.db.getCountingData(guildId);
        return countingData.channel;
    }

    async disableCounting(guildId) {
        const countingData = {
            channel: null,
            number: 1,
            lastUser: null
        };
        
        this.bot.db.updateCounting(guildId, countingData);
        return true;
    }
}

module.exports = CountingGame;