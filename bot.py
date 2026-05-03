import discord
from discord.ext import commands
import asyncio
import os
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

class AntiNuke(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.deleted_channels = defaultdict(list)
        self.window_time = 25
        self.threshold = 3
        self.whitelist = {123456789}  # Твой ID

    async def setup_hook(self):
        print(f'Анти-нюк активен | {self.user}')

    async def on_guild_channel_delete(self, channel):
        if not channel.guild:
            return
        guild = channel.guild
        now = asyncio.get_running_loop().time()
        
        # Сохраняем инфу о канале ДО его удаления
        channel_info = {
            'name': channel.name,
            'position': channel.position,
            'category': channel.category,
            'overwrites': channel.overwrites,
            'type': channel.type
        }
        
        self.deleted_channels[guild.id].append({
            'time': now,
            'info': channel_info
        })
        
        # Чистим старые записи за пределами окна
        self.deleted_channels[guild.id] = [
            c for c in self.deleted_channels[guild.id] 
            if now - c['time'] <= self.window_time
        ]
        
        if len(self.deleted_channels[guild.id]) >= self.threshold:
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                    if entry.user.id not in self.whitelist:
                        try:
                            await guild.ban(entry.user, reason='Анти-нюк: массовое удаление каналов')
                        except Exception:
                            pass
                        
                        # Восстанавливаем ВСЕ удалённые каналы
                        for deleted in self.deleted_channels[guild.id]:
                            info = deleted['info']
                            try:
                                if info['category']:
                                    await guild.create_text_channel(
                                        name=info['name'],
                                        position=info['position'],
                                        category=info['category'],
                                        overwrites=info['overwrites']
                                    )
                                else:
                                    await guild.create_text_channel(
                                        name=info['name'],
                                        position=info['position'],
                                        overwrites=info['overwrites']
                                    )
                            except Exception:
                                pass
                        
                        self.deleted_channels[guild.id].clear()
            except Exception:
                pass

    async def on_guild_role_delete(self, role):
        guild = role.guild
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
                if entry.user.id not in self.whitelist:
                    try:
                        await guild.ban(entry.user, reason='Анти-нюк: удаление ролей')
                    except Exception:
                        pass
        except Exception:
            pass

    async def on_member_ban(self, guild, user):
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                if entry.user.id not in self.whitelist:
                    try:
                        await guild.ban(entry.user, reason='Анти-нюк: бан участников')
                        await guild.unban(user)
                    except Exception:
                        pass
        except Exception:
            pass

bot = AntiNuke()
bot.run(os.environ['DISCORD_TOKEN'])
