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
        self.detection_window = 5
        self.threshold = 3
        self.whitelist = {123456789}
        self.recovering = False

    async def setup_hook(self):
        print(f'Анти-нюк активен | {self.user}')
        await self.wait_until_ready()
        for guild in self.guilds:
            await self.save_snapshot(guild)

    async def save_snapshot(self, guild):
        if guild.id in self.channel_snapshot:
            return
        channels = []
        for channel in guild.channels:
            try:
                overwrites = {}
                for target, overwrite in channel.overwrites.items():
                    overwrites[str(target.id)] = {
                        'allow': overwrite.pair()[0].value,
                        'deny': overwrite.pair()[1].value
                    }
                channels.append({
                    'name': channel.name,
                    'position': channel.position,
                    'category_id': channel.category_id,
                    'type': str(channel.type)
                })
                print(f'  Сохранён: {channel.name}')
            except Exception as e:
                print(f'  Ошибка сохранения {channel.name}: {e}')
        
        self.channel_snapshot[guild.id] = channels
        print(f'Слепок: {guild.name} — {len(channels)} каналов')

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
        
        print(f'Удалён канал: {channel.name} ({len(self.deleted_timestamps[guild.id])}/{self.threshold})')

        if len(self.deleted_timestamps[guild.id]) >= self.threshold:
            print('ТРИГГЕР АНТИ-НЮК')
            self.recovering = True
            self.deleted_timestamps[guild.id].clear()

            try:
                # БАН
                async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                    if entry.user and entry.user.id not in self.whitelist:
                        try:
                            await guild.ban(entry.user, reason='Анти-нюк: удаление каналов')
                            print(f'Забанен: {entry.user}')
                        except Exception as e:
                            print(f'Ошибка бана: {e}')
                        break

                # ВОССТАНОВЛЕНИЕ
                if guild.id not in self.channel_snapshot:
                    print('НЕТ СЛЕПКА, сохраняю заново')
                    await self.save_snapshot(guild)

                current_names = {ch.name for ch in guild.channels}
                snapshot = self.channel_snapshot.get(guild.id, [])
                
                print(f'Текущих каналов: {len(current_names)}, в слепке: {len(snapshot)}')
                
                restored = 0
                for saved in snapshot:
                    if saved['name'] not in current_names:
                        try:
                            category = None
                            if saved['category_id']:
                                category = guild.get_channel(saved['category_id'])
                            
                            new_channel = await guild.create_text_channel(
                                name=saved['name'],
                                category=category,
                                position=saved['position']
                            )
                            restored += 1
                            print(f'  Восстановлен: {saved["name"]}')
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f'  Ошибка восстановления {saved["name"]}: {e}')

                print(f'Итого восстановлено: {restored}')

            except Exception as e:
                print(f'Критическая ошибка: {e}')
            finally:
                self.recovering = False

    async def on_guild_join(self, guild):
        print(f'Добавлен на сервер: {guild.name}')
        await asyncio.sleep(2)
        await self.save_snapshot(guild)

    async def on_guild_role_delete(self, role):
        guild = role.guild
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
                if entry.user and entry.user.id not in self.whitelist:
                    try:
                        await guild.ban(entry.user, reason='Анти-нюк: удаление ролей')
                    except Exception:
                        pass
        except Exception:
            pass

    async def on_member_ban(self, guild, user):
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                if entry.user and entry.user.id not in self.whitelist:
                    try:
                        await guild.ban(entry.user, reason='Анти-нюк: бан участников')
                        await guild.unban(user)
                    except Exception:
                        pass
        except Exception:
            pass

bot = AntiNuke()
bot.run(os.environ['DISCORD_TOKEN'])
