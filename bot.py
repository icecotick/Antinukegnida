import discord
from discord.ext import commands
import os
from collections import defaultdict
import time
import asyncio

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Отслеживание удалений
channel_deletions = defaultdict(list)
NUKE_THRESHOLD = 2  # Количество каналов
TIME_WINDOW = 2  # В секундах

# ID владельца сервера (опционально, для уведомлений)
OWNER_ID = 123456789  # Замени на свой Discord ID

@bot.event
async def on_ready():
    print(f'✅ {bot.user} запущен на Render!')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="за нюкерами 👀"
    ))

@bot.event
async def on_guild_channel_delete(channel):
    """Отслеживает удаление каналов и банит нарушителей"""
    try:
        # Получаем аудит лога
        guild = channel.guild
        
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            # Проверяем, совпадает ли канал и время
            if entry.target.id == channel.id:
                deleter = entry.user
                
                # Игнорируем действия самого бота
                if deleter.id == bot.user.id:
                    return
                
                current_time = time.time()
                
                # Добавляем запись об удалении
                channel_deletions[deleter.id].append(current_time)
                
                # Удаляем старые записи (старше временного окна)
                channel_deletions[deleter.id] = [
                    t for t in channel_deletions[deleter.id] 
                    if current_time - t <= TIME_WINDOW
                ]
                
                # Проверяем количество удалений в окне
                if len(channel_deletions[deleter.id]) >= NUKE_THRESHOLD:
                    await handle_nuke(guild, deleter)
                
                break
    
    except discord.Forbidden:
        print(f"❌ Недостаточно прав в {guild.name}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def handle_nuke(guild, user):
    """Обрабатывает обнаруженный нюк"""
    try:
        # Баним нарушителя
        await guild.ban(
            user,
            reason="Анти-нюк: удаление нескольких каналов за 2 секунды",
            delete_message_days=1
        )
        
        print(f"🚨 Забанен {user} ({user.id}) на сервере {guild.name}")
        
        # Отправляем уведомление в первый доступный текстовый канал
        for channel in guild.text_channels:
            try:
                embed = discord.Embed(
                    title="🚨 Обнаружен нюк!",
                    description=f"Пользователь **{user}** (`{user.id}`) был забанен за попытку нюка.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Причина", value="Удаление каналов с высокой скоростью")
                embed.add_field(name="Сервер", value=guild.name)
                embed.set_footer(text="Анти-Нюк система")
                
                await channel.send(embed=embed)
                break
            except:
                continue
        
        # Уведомление владельцу в ЛС (опционально)
        if OWNER_ID != 123456789:  # Если ID изменен
            try:
                owner = await bot.fetch_user(OWNER_ID)
                if owner:
                    await owner.send(
                        f"🚨 Нюк на сервере **{guild.name}**!\n"
                        f"Нарушитель: {user} ({user.id})\n"
                        f"Действие: Забанен"
                    )
            except:
                pass
    
    except discord.Forbidden:
        print(f"❌ Нет прав на бан в {guild.name}")
        # Пытаемся кикнуть если нельзя забанить
        try:
            await guild.kick(user, reason="Анти-нюк: попытка нюка")
        except:
            pass
    except Exception as e:
        print(f"❌ Ошибка при бане: {e}")

# Очистка старых записей каждые 5 минут
async def cleanup_old_entries():
    await bot.wait_until_ready()
    while not bot.is_closed():
        current_time = time.time()
        for user_id in list(channel_deletions.keys()):
            channel_deletions[user_id] = [
                t for t in channel_deletions[user_id] 
                if current_time - t <= TIME_WINDOW
            ]
            if not channel_deletions[user_id]:
                del channel_deletions[user_id]
        await asyncio.sleep(300)  # 5 минут

@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    """Проверка статуса анти-нюк системы"""
    embed = discord.Embed(
        title="🛡️ Анти-Нюк Статус",
        color=discord.Color.green()
    )
    embed.add_field(name="Порог срабатывания", value=f"{NUKE_THRESHOLD} каналов")
    embed.add_field(name="Временное окно", value=f"{TIME_WINDOW} сек")
    embed.add_field(name="Отслеживаемых пользователей", value=len(channel_deletions))
    await ctx.send(embed=embed)

# Запуск бота
if __name__ == "__main__":
    # Запускаем очистку в фоне
    bot.loop.create_task(cleanup_old_entries())
    
    # Получаем токен из переменных окружения Render
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ Токен не найден! Установи переменную DISCORD_TOKEN в Render")
    else:
        bot.run(TOKEN)
