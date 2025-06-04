import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any
import logging

logger = logging.getLogger(__name__)

class Scheduler:
    """Task scheduler for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def schedule_announcement(
        self, 
        guild_id: int, 
        channel_id: int, 
        message: str, 
        scheduled_time: datetime, 
        repeat: str = "once"
    ) -> str:
        """
        Schedule an announcement.
        Returns task ID.
        """
        task_id = f"announcement_{guild_id}_{int(scheduled_time.timestamp())}"
        
        self.scheduled_tasks[task_id] = {
            'type': 'announcement',
            'guild_id': guild_id,
            'channel_id': channel_id,
            'message': message,
            'scheduled_time': scheduled_time,
            'repeat': repeat,
            'created_at': datetime.utcnow()
        }
        
        # Schedule the task
        delay = (scheduled_time - datetime.utcnow()).total_seconds()
        if delay > 0:
            task = asyncio.create_task(self._execute_announcement(task_id, delay))
            self.running_tasks[task_id] = task
        
        return task_id
    
    async def _execute_announcement(self, task_id: str, delay: float):
        """Execute a scheduled announcement."""
        try:
            await asyncio.sleep(delay)
            
            if task_id not in self.scheduled_tasks:
                return
            
            task_data = self.scheduled_tasks[task_id]
            guild = self.bot.get_guild(task_data['guild_id'])
            
            if guild:
                channel = guild.get_channel(task_data['channel_id'])
                if channel:
                    await channel.send(task_data['message'])
                    
                    # Handle repeat
                    if task_data['repeat'] == "daily":
                        # Schedule next day
                        next_time = task_data['scheduled_time'] + timedelta(days=1)
                        task_data['scheduled_time'] = next_time
                        delay = (next_time - datetime.utcnow()).total_seconds()
                        if delay > 0:
                            new_task = asyncio.create_task(self._execute_announcement(task_id, delay))
                            self.running_tasks[task_id] = new_task
                    elif task_data['repeat'] == "weekly":
                        # Schedule next week
                        next_time = task_data['scheduled_time'] + timedelta(weeks=1)
                        task_data['scheduled_time'] = next_time
                        delay = (next_time - datetime.utcnow()).total_seconds()
                        if delay > 0:
                            new_task = asyncio.create_task(self._execute_announcement(task_id, delay))
                            self.running_tasks[task_id] = new_task
                    else:
                        # One-time announcement - remove task
                        self.cancel_task(task_id)
        
        except Exception as e:
            logger.error(f"Error executing announcement {task_id}: {e}")
    
    async def schedule_reminder(
        self, 
        user_id: int, 
        channel_id: int, 
        message: str, 
        reminder_time: datetime
    ) -> str:
        """
        Schedule a reminder.
        Returns task ID.
        """
        task_id = f"reminder_{user_id}_{int(reminder_time.timestamp())}"
        
        self.scheduled_tasks[task_id] = {
            'type': 'reminder',
            'user_id': user_id,
            'channel_id': channel_id,
            'message': message,
            'reminder_time': reminder_time,
            'created_at': datetime.utcnow()
        }
        
        # Schedule the task
        delay = (reminder_time - datetime.utcnow()).total_seconds()
        if delay > 0:
            task = asyncio.create_task(self._execute_reminder(task_id, delay))
            self.running_tasks[task_id] = task
        
        return task_id
    
    async def _execute_reminder(self, task_id: str, delay: float):
        """Execute a scheduled reminder."""
        try:
            await asyncio.sleep(delay)
            
            if task_id not in self.scheduled_tasks:
                return
            
            task_data = self.scheduled_tasks[task_id]
            channel = self.bot.get_channel(task_data['channel_id'])
            
            if channel:
                user = self.bot.get_user(task_data['user_id'])
                if user:
                    embed = discord.Embed(
                        title="⏰ Reminder",
                        description=task_data['message'],
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_footer(text=f"Reminder for {user.display_name}")
                    
                    await channel.send(f"{user.mention}", embed=embed)
            
            # Remove completed reminder
            self.cancel_task(task_id)
        
        except Exception as e:
            logger.error(f"Error executing reminder {task_id}: {e}")
    
    async def schedule_giveaway_end(
        self, 
        guild_id: int, 
        channel_id: int, 
        message_id: int, 
        end_time: datetime,
        winners: int,
        prize: str
    ) -> str:
        """
        Schedule giveaway end.
        Returns task ID.
        """
        task_id = f"giveaway_{guild_id}_{message_id}"
        
        self.scheduled_tasks[task_id] = {
            'type': 'giveaway',
            'guild_id': guild_id,
            'channel_id': channel_id,
            'message_id': message_id,
            'end_time': end_time,
            'winners': winners,
            'prize': prize,
            'created_at': datetime.utcnow()
        }
        
        # Schedule the task
        delay = (end_time - datetime.utcnow()).total_seconds()
        if delay > 0:
            task = asyncio.create_task(self._execute_giveaway_end(task_id, delay))
            self.running_tasks[task_id] = task
        
        return task_id
    
    async def _execute_giveaway_end(self, task_id: str, delay: float):
        """Execute giveaway end."""
        try:
            await asyncio.sleep(delay)
            
            if task_id not in self.scheduled_tasks:
                return
            
            task_data = self.scheduled_tasks[task_id]
            guild = self.bot.get_guild(task_data['guild_id'])
            
            if guild:
                channel = guild.get_channel(task_data['channel_id'])
                if channel:
                    try:
                        message = await channel.fetch_message(task_data['message_id'])
                        
                        # Get users who reacted with 🎉
                        reaction = None
                        for r in message.reactions:
                            if str(r.emoji) == "🎉":
                                reaction = r
                                break
                        
                        if reaction and reaction.count > 1:  # Exclude bot's reaction
                            users = []
                            async for user in reaction.users():
                                if not user.bot:
                                    users.append(user)
                            
                            if users:
                                import random
                                winners_count = min(task_data['winners'], len(users))
                                winners = random.sample(users, winners_count)
                                
                                winner_mentions = [winner.mention for winner in winners]
                                
                                embed = discord.Embed(
                                    title="🎉 Giveaway Ended!",
                                    description=f"**Prize:** {task_data['prize']}\n**Winner(s):** {', '.join(winner_mentions)}",
                                    color=discord.Color.gold(),
                                    timestamp=datetime.utcnow()
                                )
                                
                                await channel.send(embed=embed)
                            else:
                                embed = discord.Embed(
                                    title="🎉 Giveaway Ended!",
                                    description=f"**Prize:** {task_data['prize']}\nNo valid participants!",
                                    color=discord.Color.red(),
                                    timestamp=datetime.utcnow()
                                )
                                await channel.send(embed=embed)
                        else:
                            embed = discord.Embed(
                                title="🎉 Giveaway Ended!",
                                description=f"**Prize:** {task_data['prize']}\nNo participants!",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow()
                            )
                            await channel.send(embed=embed)
                    
                    except discord.NotFound:
                        logger.warning(f"Giveaway message not found: {task_data['message_id']}")
            
            # Remove completed giveaway
            self.cancel_task(task_id)
        
        except Exception as e:
            logger.error(f"Error executing giveaway end {task_id}: {e}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            return True
        
        return False
    
    def get_scheduled_tasks(self, guild_id: int = None) -> List[Dict[str, Any]]:
        """Get all scheduled tasks, optionally filtered by guild."""
        tasks = []
        
        for task_id, task_data in self.scheduled_tasks.items():
            if guild_id is None or task_data.get('guild_id') == guild_id:
                task_data['id'] = task_id
                tasks.append(task_data)
        
        return tasks
