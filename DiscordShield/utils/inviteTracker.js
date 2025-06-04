const { EmbedBuilder } = require('discord.js');

class InviteTracker {
    constructor(bot) {
        this.bot = bot;
        this.inviteCache = new Map();
    }

    async cacheInvites() {
        for (const guild of this.bot.guilds.cache.values()) {
            try {
                const invites = await guild.invites.fetch();
                const inviteMap = new Map();
                
                invites.forEach(invite => {
                    inviteMap.set(invite.code, {
                        uses: invite.uses,
                        inviterId: invite.inviter?.id,
                        channelId: invite.channel?.id,
                        createdAt: invite.createdAt,
                        maxUses: invite.maxUses,
                        expiresAt: invite.expiresAt
                    });
                });
                
                this.inviteCache.set(guild.id, inviteMap);
            } catch (error) {
                console.error(`Error caching invites for guild ${guild.id}:`, error);
            }
        }
    }

    async handleInviteCreate(invite) {
        const guildInvites = this.inviteCache.get(invite.guild.id) || new Map();
        
        guildInvites.set(invite.code, {
            uses: invite.uses,
            inviterId: invite.inviter?.id,
            channelId: invite.channel?.id,
            createdAt: invite.createdAt,
            maxUses: invite.maxUses,
            expiresAt: invite.expiresAt
        });
        
        this.inviteCache.set(invite.guild.id, guildInvites);
        
        // Log invite creation
        await this.logInviteAction(invite.guild, 'create', invite);
    }

    async handleInviteDelete(invite) {
        const guildInvites = this.inviteCache.get(invite.guild.id) || new Map();
        guildInvites.delete(invite.code);
        this.inviteCache.set(invite.guild.id, guildInvites);
        
        // Log invite deletion
        await this.logInviteAction(invite.guild, 'delete', invite);
    }

    async handleMemberJoin(member) {
        try {
            const guild = member.guild;
            const cachedInvites = this.inviteCache.get(guild.id) || new Map();
            const currentInvites = await guild.invites.fetch();
            
            let usedInvite = null;
            let inviter = null;
            
            // Find which invite was used
            for (const [code, currentInvite] of currentInvites) {
                const cachedInvite = cachedInvites.get(code);
                
                if (cachedInvite && currentInvite.uses > cachedInvite.uses) {
                    usedInvite = currentInvite;
                    inviter = currentInvite.inviter;
                    break;
                }
            }
            
            if (usedInvite && inviter) {
                // Update invite count in database
                this.bot.db.addInvite(guild.id, inviter.id);
                
                // Award tokens to inviter
                this.bot.db.addTokens(guild.id, inviter.id, 10);
                
                // Log the invite use
                await this.logMemberJoin(guild, member, inviter, usedInvite);
                
                // Send welcome message with invite credit
                await this.sendWelcomeMessage(guild, member, inviter);
            } else {
                // Member joined via unknown method (possibly vanity URL)
                await this.logMemberJoin(guild, member, null, null);
            }
            
            // Update invite cache
            this.updateInviteCache(guild.id, currentInvites);
            
        } catch (error) {
            console.error('Error handling member join:', error);
        }
    }

    updateInviteCache(guildId, currentInvites) {
        const inviteMap = new Map();
        
        currentInvites.forEach(invite => {
            inviteMap.set(invite.code, {
                uses: invite.uses,
                inviterId: invite.inviter?.id,
                channelId: invite.channel?.id,
                createdAt: invite.createdAt,
                maxUses: invite.maxUses,
                expiresAt: invite.expiresAt
            });
        });
        
        this.inviteCache.set(guildId, inviteMap);
    }

    async logInviteAction(guild, action, invite) {
        const logChannelId = this.bot.db.getConfig(guild.id, 'logChannel');
        if (!logChannelId) return;

        const logChannel = guild.channels.cache.get(logChannelId);
        if (!logChannel) return;

        try {
            const embed = new EmbedBuilder()
                .setTitle(`🔗 Invite ${action === 'create' ? 'Created' : 'Deleted'}`)
                .setColor(action === 'create' ? '#27ae60' : '#e74c3c')
                .addFields(
                    { name: 'Invite Code', value: invite.code, inline: true },
                    { name: 'Channel', value: `<#${invite.channel?.id}>`, inline: true },
                    { name: 'Created By', value: `<@${invite.inviter?.id}>`, inline: true }
                )
                .setTimestamp();

            if (action === 'create') {
                embed.addFields(
                    { name: 'Max Uses', value: invite.maxUses?.toString() || 'Unlimited', inline: true },
                    { name: 'Expires At', value: invite.expiresAt ? `<t:${Math.floor(invite.expiresAt.getTime() / 1000)}:F>` : 'Never', inline: true }
                );
            }

            await logChannel.send({ embeds: [embed] });
        } catch (error) {
            console.error('Error logging invite action:', error);
        }
    }

    async logMemberJoin(guild, member, inviter, invite) {
        const logChannelId = this.bot.db.getConfig(guild.id, 'logChannel');
        if (!logChannelId) return;

        const logChannel = guild.channels.cache.get(logChannelId);
        if (!logChannel) return;

        try {
            const embed = new EmbedBuilder()
                .setTitle('👋 Member Joined')
                .setColor('#27ae60')
                .addFields(
                    { name: 'Member', value: `${member.user.tag} (<@${member.id}>)`, inline: true },
                    { name: 'Account Created', value: `<t:${Math.floor(member.user.createdTimestamp / 1000)}:R>`, inline: true }
                )
                .setThumbnail(member.user.displayAvatarURL({ dynamic: true }))
                .setTimestamp();

            if (inviter) {
                const totalInvites = this.bot.db.getInvites(guild.id)[inviter.id] || 0;
                embed.addFields(
                    { name: 'Invited By', value: `${inviter.tag} (<@${inviter.id}>)`, inline: true },
                    { name: 'Invite Code', value: invite.code, inline: true },
                    { name: 'Total Invites', value: totalInvites.toString(), inline: true }
                );
            } else {
                embed.addFields({ name: 'Invited By', value: 'Unknown (Vanity URL or Bot)', inline: true });
            }

            await logChannel.send({ embeds: [embed] });
        } catch (error) {
            console.error('Error logging member join:', error);
        }
    }

    async sendWelcomeMessage(guild, member, inviter) {
        const welcomeChannelId = this.bot.db.getConfig(guild.id, 'welcomeChannel');
        if (!welcomeChannelId) return;

        const welcomeChannel = guild.channels.cache.get(welcomeChannelId);
        if (!welcomeChannel) return;

        try {
            const totalInvites = this.bot.db.getInvites(guild.id)[inviter.id] || 0;
            
            const embed = new EmbedBuilder()
                .setTitle(`Welcome to ${guild.name}!`)
                .setDescription(`Hello ${member}, welcome to our server!`)
                .setColor('#3498db')
                .addFields(
                    { name: 'Invited By', value: `${inviter.tag} (${totalInvites} total invites)`, inline: true },
                    { name: 'Member Count', value: guild.memberCount.toString(), inline: true }
                )
                .setThumbnail(member.user.displayAvatarURL({ dynamic: true }))
                .setTimestamp();

            await welcomeChannel.send({ embeds: [embed] });
        } catch (error) {
            console.error('Error sending welcome message:', error);
        }
    }

    getUserInvites(guildId, userId) {
        const invites = this.bot.db.getInvites(guildId);
        return invites[userId] || 0;
    }

    getTopInviters(guildId, limit = 10) {
        const invites = this.bot.db.getInvites(guildId);
        return Object.entries(invites)
            .sort(([,a], [,b]) => b - a)
            .slice(0, limit)
            .map(([userId, count]) => [userId, count]);
    }

    getTotalInvites(guildId) {
        const invites = this.bot.db.getInvites(guildId);
        return Object.values(invites).reduce((total, count) => total + count, 0);
    }

    async resetUserInvites(guildId, userId) {
        const invites = this.bot.db.getInvites(guildId);
        if (invites[userId]) {
            delete invites[userId];
            this.bot.db.setInvites(guildId, invites);
            return true;
        }
        return false;
    }

    async resetAllInvites(guildId) {
        this.bot.db.setInvites(guildId, {});
        return true;
    }

    async getInviteLeaderboard(guildId, limit = 10) {
        const topInviters = this.getTopInviters(guildId, limit);
        const leaderboard = [];

        for (const [userId, count] of topInviters) {
            try {
                const user = await this.bot.users.fetch(userId);
                leaderboard.push({
                    user: user,
                    count: count,
                    username: user.username
                });
            } catch (error) {
                // User might have left or be unavailable
                leaderboard.push({
                    user: null,
                    count: count,
                    username: `Unknown User (${userId})`
                });
            }
        }

        return leaderboard;
    }
}

module.exports = InviteTracker;