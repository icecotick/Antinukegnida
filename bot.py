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
        self.channel_snapshot = {}
        self.deleted_timestamps = defaultdict(list)
        self.detection_window = 3
        self.threshold = 2
        self.whitelist = {123456789}
        self.recovering = False

    async def setup_hook(self):
        print(f'Анти-нюк активен | {self.user}')
        for guild in self.guilds:
            self.save_snapshot(guild)

    def save_snapshot(self, guild):
        if guild.id in self.channel_snapshot:
            return  # Не обновляем если уже есть
        self.channel_snapshot[guild.id] = []
        for channel in guild.channels:
            self.channel_snapshot[guild.id].append({
                'name': channel.name,
                'position': channel.position,
                'category': channel.category,
                'overwrites': channel.overwrites,
                'type': str(channel.type)
            })
        print(f'Слепок сохранён: {guild.name} ({len(self.channel_snapshot[guild.id])} каналов)')

    async def on_guild_channel_delete(self, channel):
        if not channel.guild or self.recovering:
            return

        guild = channel.guild
        now = asyncio.get_running_loop().time()

        self.deleted_timestamps[guild.id] = [
            t for t in self.deleted_timestamps[guild.id]
            if now - t <= self.detection_window
        ]
        self.deleted_timestamps[guild.id].append(now)

        if len(self.deleted_timestamps[guild.id]) >= self.threshold:
            self.recovering = True
            self.deleted_timestamps[guild.id].clear()

            try:
                # БАН
                async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                    if entry.user.id not in self.whitelist:
                        try:
                            await guild.ban(entry.user, reason='Анти-нюк: удаление каналов')
                            print(f'Забанен {entry.user}')
                        except Exception as e:
                            print(f'Ошибка бана: {e}')

                # ВОССТАНОВЛЕНИЕ по изначальному слепку
                if guild.id in self.channel_snapshot:
                    current_names = {ch.name for ch in guild.channels}
                    restored = 0
                    for saved in self.channel_snapshot[guild.id]:
                        if saved['name'] not in current_names:
                            try:
                                await guild.create_text_channel(
                                    name=saved['name'],
                                    category=saved['category'],
                                    overwrites=saved['overwrites'],
                                    position=saved['position']
                                )
                                restored += 1
                                await asyncio.sleep(0.3)
                            except Exception:
                                pass
                    print(f'Восстановлено: {restored}')

            except Exception as e:
                print(f'Ошибка: {e}')
            finally:
                self.recovering = False

    async def on_guild_join(self, guild):
        self.save_snapshot(guild)

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
