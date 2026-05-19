import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_ROLES = [1499016923868823594, 1496544521217904671, 1496554366709137508]
OWNER_IDS = [1079985192556580934, 978148077590446090]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_http_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

def has_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.id in OWNER_IDS:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in ALLOWED_ROLES)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

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
    if not has_permission(interaction):
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
    if not has_permission(interaction):
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

threading.Thread(target=run_http_server, daemon=True).start()
bot.run(os.getenv("DISCORD_TOKEN"))
