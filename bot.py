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
        self.window_time = 4    # уменьшил окно
        self.threshold = 3
        self.whitelist = {123456789}  # Твой ID
        self.recovering = False      # флаг, чтобы не ловить свои же восстановления
        self.nuke_detected = set()   # сервера, где уже был нюк

    async def setup_hook(self):
        print(f'Анти-нюк активен | {self.user}')

    async def on_guild_channel_delete(self, channel):
        if not channel.guild or self.recovering:
            return
        
        guild = channel.guild
        now = asyncio.get_running_loop().time()
        
        channel_info = {
            'name': channel.name,
            'position': channel.position,
            'category': channel.category,
            'overwrites': channel.overwrites,
            'type': str(channel.type)
        }
        
        self.deleted_channels[guild.id].append({
            'time': now,
            'info': channel_info
        })
        
        self.deleted_channels[guild.id] = [
            c for c in self.deleted_channels[guild.id] 
            if now - c['time'] <= self.window_time
        ]
        
        if len(self.deleted_channels[guild.id]) >= self.threshold and guild.id not in self.nuke_detected:
            self.nuke_detected.add(guild.id)
            
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                    if entry.user.id not in self.whitelist:
                        try:
                            await guild.ban(entry.user, reason='Анти-нюк: массовое удаление каналов')
                        except Exception:
                            pass
                        
                        self.recovering = True
                        restored = 0
                        for deleted in self.deleted_channels[guild.id]:
                            if restored >= len(self.deleted_channels[guild.id]):
                                break
                            info = deleted['info']
                            try:
                                cat = info['category']
                                await guild.create_text_channel(
                                    name=info['name'],
                                    category=cat,
                                    overwrites=info['overwrites'],
                                    position=info['position']
                                )
                                restored += 1
                                await asyncio.sleep(0.5)
                            except Exception:
                                pass
                        self.recovering = False
                        self.deleted_channels[guild.id].clear()
                        self.nuke_detected.discard(guild.id)
            except Exception:
                self.recovering = False
                self.nuke_detected.discard(guild.id)

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
bot.run(os.environ['DISCORD_TOKEN'])                                    )
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
