import discord
from discord.ext import commands
import datetime
import os
from dotenv import load_dotenv
import asyncio

# Загружаем переменные окружения
load_dotenv()

# Настройки лимитов
MAX_CHANNELS_DELETED = 3  # Макс. удаленных каналов
TIME_WINDOW = 60          # В течение скольких секунд

class AntiNuke(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        # Хранилище действий: {user_id: [timestamp1, timestamp2]}
        self.deletions = {}

    async def check_suspicious_activity(self, guild, user, action_type):
        if user.id == guild.owner_id:
            return  # Игнорируем владельца сервера

        now = datetime.datetime.now()
        user_actions = self.deletions.get(user.id, [])
        
        # Очищаем старые записи
        user_actions = [t for t in user_actions if (now - t).total_seconds() < TIME_WINDOW]
        user_actions.append(now)
        self.deletions[user.id] = user_actions

        if len(user_actions) >= MAX_CHANNELS_DELETED:
            await self.punish_user(guild, user, action_type)

    async def punish_user(self, guild, user, reason):
        try:
            # Логируем перед наказанием
            print(f"Наказываем пользователя {user} за: {reason}")
            # Баним пользователя
            await user.ban(reason=f"Anti-Nuke Triggered: {reason}")
            print(f"Пользователь {user} был забанен за подозрительную активность: {reason}")
        except Exception as e:
            print(f"Не удалось наказать {user}: {e}")

    # Событие удаления канала
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        # Ищем в аудит-логе, кто удалил канал
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                if entry.target.id == channel.id:
                    await self.check_suspicious_activity(guild, entry.user, "Mass Channel Deletion")
        except Exception as e:
            print(f"Ошибка при проверке аудит-лога: {e}")

    async def on_ready(self):
        print(f'Бот {self.user} запущен и готов защищать сервер!')
        # Устанавливаем статус
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="за безопасностью сервера"
            )
        )

if __name__ == "__main__":
    bot = AntiNuke()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Ошибка: Токен не найден в переменных окружения!")
        exit(1)
    
    # Запускаем бота с обработкой ошибок
    async def main():
        try:
            await bot.start(token)
        except Exception as e:
            print(f"Ошибка при запуске бота: {e}")
    
    asyncio.run(main())
