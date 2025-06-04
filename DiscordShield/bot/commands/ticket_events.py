import discord
from discord.ext import commands
from datetime import datetime

class TicketEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Only care about lock emoji
        if str(payload.emoji) != "🔒":
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        # Only act in "ticket-" channels
        if not channel.name.startswith("ticket-"):
            return

        # Get ticket info from database (update as needed for your DB structure)
        user_tickets = self.bot.db.tickets[guild.id]
        for user_id, tickets in user_tickets.items():
            for ticket in tickets:
                if ticket['channel_id'] == channel.id and not ticket.get('closed', False):
                    # Mark ticket as closed
                    ticket['closed'] = True
                    ticket['closed_at'] = datetime.utcnow()

                    # Remove everyone's permission to send messages except mods (optional)
                    overwrite = discord.PermissionOverwrite(send_messages=False)
                    await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    await channel.send("🔒 This ticket has been closed. Thank you!")

                    # Log the closure
                    self.bot.db.log_command(guild.id, payload.user_id, "ticket_close", True)

                    # Optionally delete or archive the channel:
                    # await channel.delete()
                    
                    return

def setup(bot):
    bot.add_cog(TicketEvents(bot))
