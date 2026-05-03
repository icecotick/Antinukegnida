import discord
from discord.ext import commands
import asyncio
import os
from collections import defaultdict

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

whitelist = {123456789}  # Твой ID

deleted_channels = defaultdict(list)
WINDOW_TIME = 25        # окно в секундах
THRESHOLD = 4           # сколько удалений считать нюком

@bot.event
async def on_ready():
    print(f'Анти-нюк активен | {bot.user}')

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    now = asyncio.get_event_loop().time()
    
    deleted_channels[guild.id].append(now)
    deleted_channels[guild.id] = [t for t in deleted_channels[guild.id] if now - t <= WINDOW_TIME]
    
    if len(deleted_channels[guild.id]) >= THRESHOLD:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
            if entry.user.id not in whitelist:
                try: await guild.ban(entry.user, reason='Анти-нюк: массовое удаление каналов')
                except: pass
                # Восстановление последнего удалённого
                await channel.clone()
                deleted_channels[guild.id].clear()

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild
    async for entry in guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
        if entry.user.id not in whitelist:
            try: await guild.ban(entry.user, reason='Анти-нюк: удаление ролей')
            except: pass

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
        if entry.user.id not in whitelist:
            try:
                await guild.ban(entry.user, reason='Анти-нюк: бан участников')
                await guild.unban(user)
            except: pass

bot.run(os.environ['DISCORD_TOKEN'])
