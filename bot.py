import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import json
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_ROLES = [1499016923868823594, 1496544521217904671, 1496554366709137508]
OWNER_IDS = [1079985192556580934, 978148077590446090]
MOD_ROLE_IDS = [1496544521217904671, 1499016923868823594]

# OpenRouter API - using currently working free models [citation:1][citation:8]
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Try these models in order (first one that works will be used) [citation:8]
FREE_MODELS = [
    "openrouter/auto",  # Auto-selects best free model [citation:1]
    "meta-llama/llama-3.3-70b-instruct:free",  # Reliable free model [citation:8]
    "deepseek/deepseek-r1:free",  # Good for reasoning [citation:8]
    "qwen/qwen3-next-80b-a3b-instruct:free"  # Technical tasks [citation:8]
]

conversation_history = {}

def get_ai_response(message_content, user_name, channel_id):
    if not OPENROUTER_API_KEY:
        return "API key not configured. Please set OPENROUTER_API_KEY environment variable."
    
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    
    conversation_history[channel_id].append({
        "role": "user",
        "content": f"{user_name}: {message_content}"
    })
    
    if len(conversation_history[channel_id]) > 10:
        conversation_history[channel_id] = conversation_history[channel_id][-10:]
    
    system_prompt = {
        "role": "system",
        "content": "You are a friendly Discord bot. Keep responses short and casual. You help manage a server with commands like /say, /deployment_poll, /deploy_log, /punish, /banish_to_janitor, /troll_luke."
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://discord.com",
        "X-Title": "Discord Management Bot"
    }
    
    # Try each model until one works
    for model in FREE_MODELS:
        try:
            payload = {
                "model": model,
                "messages": [system_prompt] + conversation_history[channel_id][-5:],
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            print(f"Trying model: {model}")
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                conversation_history[channel_id].append({
                    "role": "assistant",
                    "content": ai_response
                })
                print(f"Success with model: {model}")
                return ai_response
            elif response.status_code == 401:
                print(f"ERROR: Invalid API key. Make sure your key starts with 'sk-or-v1-'")
                return "API key invalid. Check if your OpenRouter key is correct."
            elif response.status_code == 402:
                print(f"ERROR: Insufficient credits. Add credits at openrouter.ai/credits")
                return "Insufficient credits. Free models still need a small credit balance on OpenRouter."
            elif response.status_code == 429:
                print(f"Rate limited with {model}, trying next...")
                continue
            else:
                print(f"Error {response.status_code} with {model}: {response.text[:200]}")
                continue
                
        except Exception as e:
            print(f"Exception with {model}: {e}")
            continue
    
    return "All AI models are currently unavailable. Please try again later."

# ==================== HTTP SERVER ====================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    
    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# ==================== PERMISSIONS ====================

def has_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.id in OWNER_IDS:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in ALLOWED_ROLES)

def has_mod_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.id in OWNER_IDS:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in MOD_ROLE_IDS) or any(role_id in user_role_ids for role_id in ALLOWED_ROLES)

# ==================== SELF PING ====================

@tasks.loop(minutes=5)
async def self_ping():
    render_url = os.getenv("RENDER_URL")
    if render_url:
        try:
            requests.get(render_url, timeout=10)
        except:
            pass

# ==================== BOT EVENTS ====================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"OpenRouter API Key set: {bool(OPENROUTER_API_KEY)}")
    if OPENROUTER_API_KEY:
        print(f"Key starts with: {OPENROUTER_API_KEY[:12]}...")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    if not self_ping.is_running():
        self_ping.start()
        print("Self-pinger started")

@bot.listen('on_message')
async def on_message_listener(message):
    if message.author == bot.user:
        return
    
    if message.author.bot:
        return
    
    should_respond = False
    
    if bot.user in message.mentions:
        should_respond = True
    
    if not should_respond and message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            if replied_msg.author == bot.user:
                should_respond = True
        except:
            pass
    
    if should_respond:
        clean_content = message.content
        for mention in message.mentions:
            if mention == bot.user:
                clean_content = clean_content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '')
        clean_content = clean_content.strip()
        
        if not clean_content:
            clean_content = "Hello"
        
        await asyncio.sleep(0.5)
        async with message.channel.typing():
            response = get_ai_response(clean_content, message.author.display_name, message.channel.id)
            if len(response) > 2000:
                response = response[:1990] + "..."
            await message.reply(response, mention_author=True)

# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="say", description="Make the bot say something with an optional image")
@app_commands.describe(
    message="The message you want the bot to say",
    image="Optional image to attach"
)
async def say(interaction: discord.Interaction, message: str, image: discord.Attachment = None):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    if image:
        if not image.content_type or not image.content_type.startswith("image/"):
            await interaction.followup.send("The attached file must be an image.", ephemeral=True)
            return
        await interaction.channel.send(content=message, file=await image.to_file())
    else:
        await interaction.channel.send(content=message)
    
    await interaction.followup.send("Message sent.", ephemeral=True)

@bot.tree.command(name="deployment_poll", description="Send a deployment poll with role ping")
async def deployment_poll(interaction: discord.Interaction):
    if not has_mod_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    role_id = 1496542870117810298
    poll_message = f"<@&{role_id}>\n# Deployment Poll\n- React if you can attend.\n- Ends in 30 minutes."
    
    poll_msg = await interaction.channel.send(poll_message)
    await poll_msg.add_reaction("\u2705")
    
    await interaction.followup.send("Deployment poll sent.", ephemeral=True)
    
    await asyncio.sleep(1800)
    
    try:
        poll_msg = await interaction.channel.fetch_message(poll_msg.id)
        reaction = discord.utils.get(poll_msg.reactions, emoji="\u2705")
        if reaction:
            users = [user async for user in reaction.users() if not user.bot]
            result = f"**Poll Results:** {len(users)} people reacted."
            await interaction.channel.send(result)
    except:
        pass

@bot.tree.command(name="banish_to_janitor", description="Give a user the janitor role")
@app_commands.describe(user="The user to banish to janitor")
async def banish_to_janitor(interaction: discord.Interaction, user: discord.Member):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    role_id = 1503036586349301770
    role = interaction.guild.get_role(role_id)
    
    if not role:
        await interaction.followup.send("The janitor role was not found. Please check the role ID.", ephemeral=True)
        return
    
    if role in user.roles:
        await interaction.followup.send(f"{user.mention} already has the janitor role.", ephemeral=True)
        return
    
    try:
        await user.add_roles(role)
        await interaction.followup.send(f"{user.mention} has been banished to janitor.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("I do not have permission to assign this role.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="troll_luke", description="Send a message to troll Luke")
async def troll_luke(interaction: discord.Interaction):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    message = "<@978148077590446090> LUKE THE CLASS D APPS ARE READ"
    image_url = "https://cdn.discordapp.com/attachments/1496718942335533136/1502958361136730192/image.png?ex=6a02ec0c&is=6a019a8c&hm=c0c2b36ed47b09d07c143b01e016a93d18d54315662155cf1399d1f21b0ca43f"
    
    await interaction.channel.send(content=message)
    await interaction.channel.send(content=image_url)
    
    await interaction.followup.send("Luke has been trolled.", ephemeral=True)

@bot.tree.command(name="punish", description="Issue a punishment to a user")
@app_commands.describe(
    punishment_number="Punishment number (example: 4)",
    user="The user receiving the punishment",
    reason="Reason for the punishment",
    punishment="Type of punishment (example: Verbal Warning)",
    proof="Screenshot of the proof",
    approved_by="Who approved this punishment (mention)"
)
async def punish(
    interaction: discord.Interaction, 
    punishment_number: int,
    user: discord.Member, 
    reason: str, 
    punishment: str, 
    proof: discord.Attachment, 
    approved_by: str
):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    if not proof.content_type or not proof.content_type.startswith("image/"):
        await interaction.response.send_message("The proof must be an image file.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    issuer_roles = ""
    if interaction.user.id in OWNER_IDS:
        issuer_roles = "High Council"
    else:
        user_roles = [role.name for role in interaction.user.roles if role.id in ALLOWED_ROLES]
        if user_roles:
            issuer_roles = user_roles[0]
    
    punishment_message = f"**Punishment #{punishment_number}**\n\n"
    punishment_message += f"`User of punishment:` {user.mention}\n\n"
    punishment_message += f"`Reason of punishment:` {reason}\n\n"
    punishment_message += f"`Punishment:` {punishment}\n\n"
    punishment_message += f"`Issuer of punishment:` {interaction.user.mention} {issuer_roles}\n\n"
    
    proof_file = await proof.to_file()
    punishment_message += f"`Approved by:` {approved_by}\n\n"
    punishment_message += f"-# Filed by: {interaction.user.mention}"
    
    await interaction.channel.send(content=punishment_message, file=proof_file)
    await interaction.followup.send("Punishment issued.", ephemeral=True)

@bot.tree.command(name="deploy_log", description="Log a deployment")
@app_commands.describe(
    deployment_number="Deployment number (example: 8)",
    host="Host of the deployment",
    co_host="Co-host of the deployment (optional)",
    time="Duration of the deployment (example: around 40 mins)",
    points="Points earned (example: 2)",
    proof="Screenshot of the deployment",
    attendees="Attendees (mentions separated by space, example: @user1 @user2 @user3)"
)
async def deploy_log(
    interaction: discord.Interaction,
    deployment_number: int,
    host: discord.Member,
    time: str,
    points: str,
    proof: discord.Attachment,
    attendees: str,
    co_host: discord.Member = None
):
    if not has_mod_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    if not proof.content_type or not proof.content_type.startswith("image/"):
        await interaction.response.send_message("The proof must be an image file.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    deploy_message = f"# Deployment {deployment_number}\n\n"
    deploy_message += f"Host: {host.mention}\n"
    
    if co_host:
        deploy_message += f"Co-Host: {co_host.mention}\n"
    else:
        deploy_message += "Co-Host: <@>\n"
    
    deploy_message += f"Time: {time}\n"
    deploy_message += f"Points: {points}\n"
    deploy_message += f"Attendees: {attendees}"
    
    proof_file = await proof.to_file()
    
    await interaction.channel.send(content=deploy_message, file=proof_file)
    await interaction.followup.send("Deployment logged.", ephemeral=True)

# ==================== START BOT ====================

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
# ==================== SELF PING ====================

@tasks.loop(minutes=5)
async def self_ping():
    render_url = os.getenv("RENDER_URL")
    if render_url:
        try:
            requests.get(render_url, timeout=10)
        except:
            pass

# ==================== BOT EVENTS ====================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    if not self_ping.is_running():
        self_ping.start()
        print("Self-pinger started")

@bot.listen('on_message')
async def on_message_listener(message):
    if message.author == bot.user:
        return
    
    if message.author.bot:
        return
    
    should_respond = False
    
    if bot.user in message.mentions:
        should_respond = True
    
    if not should_respond and message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            if replied_msg.author == bot.user:
                should_respond = True
        except:
            pass
    
    if should_respond:
        # Remove bot mention from message
        clean_content = message.content
        for mention in message.mentions:
            if mention == bot.user:
                clean_content = clean_content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '')
        clean_content = clean_content.strip()
        
        if not clean_content:
            clean_content = "Hello"
        
        await asyncio.sleep(0.5)
        async with message.channel.typing():
            response = get_ai_response(clean_content, message.author.display_name, message.channel.id)
            # Split long messages
            if len(response) > 2000:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await message.reply(chunk, mention_author=True)
                    await asyncio.sleep(0.5)
            else:
                await message.reply(response, mention_author=True)

# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="say", description="Make the bot say something with an optional image")
@app_commands.describe(
    message="The message you want the bot to say",
    image="Optional image to attach"
)
async def say(interaction: discord.Interaction, message: str, image: discord.Attachment = None):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    if image:
        if not image.content_type or not image.content_type.startswith("image/"):
            await interaction.followup.send("The attached file must be an image.", ephemeral=True)
            return
        await interaction.channel.send(content=message, file=await image.to_file())
    else:
        await interaction.channel.send(content=message)
    
    await interaction.followup.send("Message sent.", ephemeral=True)

@bot.tree.command(name="deployment_poll", description="Send a deployment poll with role ping")
async def deployment_poll(interaction: discord.Interaction):
    if not has_mod_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    role_id = 1496542870117810298
    poll_message = f"<@&{role_id}>\n# Deployment Poll\n- React if you can attend.\n- Ends in 30 minutes."
    
    poll_msg = await interaction.channel.send(poll_message)
    await poll_msg.add_reaction("\u2705")
    
    await interaction.followup.send("Deployment poll sent.", ephemeral=True)
    
    await asyncio.sleep(1800)
    
    try:
        poll_msg = await interaction.channel.fetch_message(poll_msg.id)
        reaction = discord.utils.get(poll_msg.reactions, emoji="\u2705")
        if reaction:
            users = [user async for user in reaction.users() if not user.bot]
            result = f"**Poll Results:** {len(users)} people reacted."
            await interaction.channel.send(result)
    except:
        pass

@bot.tree.command(name="banish_to_janitor", description="Give a user the janitor role")
@app_commands.describe(user="The user to banish to janitor")
async def banish_to_janitor(interaction: discord.Interaction, user: discord.Member):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    role_id = 1503036586349301770
    role = interaction.guild.get_role(role_id)
    
    if not role:
        await interaction.followup.send("The janitor role was not found. Please check the role ID.", ephemeral=True)
        return
    
    if role in user.roles:
        await interaction.followup.send(f"{user.mention} already has the janitor role.", ephemeral=True)
        return
    
    try:
        await user.add_roles(role)
        await interaction.followup.send(f"{user.mention} has been banished to janitor.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("I do not have permission to assign this role.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="troll_luke", description="Send a message to troll Luke")
async def troll_luke(interaction: discord.Interaction):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    message = "<@978148077590446090> LUKE THE CLASS D APPS ARE READ"
    image_url = "https://cdn.discordapp.com/attachments/1496718942335533136/1502958361136730192/image.png?ex=6a02ec0c&is=6a019a8c&hm=c0c2b36ed47b09d07c143b01e016a93d18d54315662155cf1399d1f21b0ca43f"
    
    await interaction.channel.send(content=message)
    await interaction.channel.send(content=image_url)
    
    await interaction.followup.send("Luke has been trolled.", ephemeral=True)

@bot.tree.command(name="punish", description="Issue a punishment to a user")
@app_commands.describe(
    punishment_number="Punishment number (example: 4)",
    user="The user receiving the punishment",
    reason="Reason for the punishment",
    punishment="Type of punishment (example: Verbal Warning)",
    proof="Screenshot of the proof",
    approved_by="Who approved this punishment (mention)"
)
async def punish(
    interaction: discord.Interaction, 
    punishment_number: int,
    user: discord.Member, 
    reason: str, 
    punishment: str, 
    proof: discord.Attachment, 
    approved_by: str
):
    if not has_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    if not proof.content_type or not proof.content_type.startswith("image/"):
        await interaction.response.send_message("The proof must be an image file.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    issuer_roles = ""
    if interaction.user.id in OWNER_IDS:
        issuer_roles = "High Council"
    else:
        user_roles = [role.name for role in interaction.user.roles if role.id in ALLOWED_ROLES]
        if user_roles:
            issuer_roles = user_roles[0]
    
    punishment_message = f"**Punishment #{punishment_number}**\n\n"
    punishment_message += f"`User of punishment:` {user.mention}\n\n"
    punishment_message += f"`Reason of punishment:` {reason}\n\n"
    punishment_message += f"`Punishment:` {punishment}\n\n"
    punishment_message += f"`Issuer of punishment:` {interaction.user.mention}\n\n"
    
    proof_file = await proof.to_file()
    punishment_message += f"`Approved by:` {approved_by}\n\n"
    punishment_message += f"-# Filed by: {interaction.user.mention}"
    
    await interaction.channel.send(content=punishment_message, file=proof_file)
    await interaction.followup.send("Punishment issued.", ephemeral=True)

@bot.tree.command(name="deploy_log", description="Log a deployment")
@app_commands.describe(
    deployment_number="Deployment number (example: 8)",
    host="Host of the deployment",
    co_host="Co-host of the deployment (optional)",
    time="Duration of the deployment (example: around 40 mins)",
    points="Points earned (example: 2)",
    proof="Screenshot of the deployment",
    attendees="Attendees (mentions separated by space, example: @user1 @user2 @user3)"
)
async def deploy_log(
    interaction: discord.Interaction,
    deployment_number: int,
    host: discord.Member,
    time: str,
    points: str,
    proof: discord.Attachment,
    attendees: str,
    co_host: discord.Member = None
):
    if not has_mod_permission(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    if not proof.content_type or not proof.content_type.startswith("image/"):
        await interaction.response.send_message("The proof must be an image file.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    deploy_message = f"# Deployment {deployment_number}\n\n"
    deploy_message += f"Host: {host.mention}\n"
    
    if co_host:
        deploy_message += f"Co-Host: {co_host.mention}\n"
    else:
        deploy_message += "Co-Host: <@>\n"
    
    deploy_message += f"Time: {time}\n"
    deploy_message += f"Points: {points}\n"
    deploy_message += f"Attendees: {attendees}"
    
    proof_file = await proof.to_file()
    
    await interaction.channel.send(content=deploy_message, file=proof_file)
    await interaction.followup.send("Deployment logged.", ephemeral=True)

# ==================== START BOT ====================

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
