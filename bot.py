import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import random
import re
import requests

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_ROLES = [1499016923868823594, 1496544521217904671, 1496554366709137508]
OWNER_IDS = [1079985192556580934, 978148077590446090]
MOD_ROLE_IDS = [1496544521217904671, 1499016923868823594]

# ==================== AI RESPONSES ====================

GREETINGS = [
    "hello", "hi", "hey", "yo", "sup", "greetings", "good morning", 
    "good evening", "good afternoon", "howdy", "heya", "hellooo", "hii"
]
GREETING_RESPONSES = [
    "Hello there!",
    "Hi! How can I help?",
    "Hey! What's up?",
    "Greetings!",
    "Hello! Hope you're having a great day!",
    "Hey there! Nice to see you!",
    "Howdy! What brings you here?",
    "Hi hi! Ready for action!",
    "Yo! What's good?",
    "Hello! The server is looking great today!"
]

HOW_ARE_YOU = [
    "how are you", "how are you doing", "how's it going", "how do you feel",
    "how are things", "how have you been", "you good", "you ok",
    "how's life", "what's up with you", "how are ya"
]
HOW_ARE_YOU_RESPONSES = [
    "I'm doing great, thanks for asking!",
    "All systems operational!",
    "Feeling good today!",
    "I'm fine, thank you!",
    "Living my best bot life!",
    "Pretty good! How about you?",
    "Running at 100% efficiency!",
    "Can't complain, I'm a bot after all!",
    "Feeling fantastic! Ready to help!",
    "Doing well! The server is in good hands!"
]

THANKS = [
    "thanks", "thank you", "thx", "ty", "appreciate it", "thank",
    "thanks a lot", "thank you so much", "tyvm", "cheers",
    "much appreciated", "thanks man", "thanks dude"
]
THANKS_RESPONSES = [
    "You're welcome!",
    "Happy to help!",
    "No problem!",
    "Anytime!",
    "Glad I could help!",
    "It's my pleasure!",
    "Don't mention it!",
    "Always here for you!",
    "That's what I'm here for!",
    "No worries at all!"
]

BYE = [
    "bye", "goodbye", "see you", "cya", "later", "good night",
    "see ya", "peace", "take care", "farewell", "adios",
    "good night", "gn", "ttyl", "until next time", "bye bye"
]
BYE_RESPONSES = [
    "Goodbye!",
    "See you later!",
    "Bye! Take care!",
    "Cya!",
    "Farewell! Come back soon!",
    "Peace out!",
    "Until next time!",
    "Good night! Sweet dreams!",
    "Take care! Stay safe!",
    "Adios! Don't be a stranger!"
]

JOKES = [
    "tell me a joke", "joke", "make me laugh", "say something funny",
    "got any jokes", "be funny", "i need a laugh", "humor me"
]
JOKE_RESPONSES = [
    "Why did the Discord bot go to therapy? It had too many unresolved pings!",
    "What do you call a bot that can sing? A melody-ai!",
    "Why don't bots ever get lost? They always follow their root!",
    "What's a bot's favorite drink? Java!",
    "Why did the server crash? Because it couldn't handle all the pings!",
    "Why do bots make great friends? They always listen without judging!",
    "What's a computer's favorite snack? Microchips!",
    "Why did the programmer quit? He didn't get arrays!",
    "How do robots eat? Byte by byte!",
    "What's a bot's favorite music? Algorithm and blues!"
]

COMPLIMENTS = [
    "you're cool", "you're awesome", "you're great", "you rock",
    "i like you", "you are the best", "best bot", "good bot",
    "love you", "you're amazing", "you're the goat", "goat"
]
COMPLIMENT_RESPONSES = [
    "Aww, thank you! You're pretty awesome yourself!",
    "Thanks! I try my best!",
    "That means a lot, thank you!",
    "You're too kind! Thank you!",
    "Stop it, you're making me blush... wait, I can't blush!",
    "Thank you! You're the best user ever!",
    "I appreciate that so much!",
    "Right back at you!",
    "Thanks! I think you're great too!",
    "This is why I love this server!"
]

INSULTS = [
    "bad bot", "you suck", "you're useless", "stupid bot",
    "trash", "dumb", "idiot", "worst bot", "hate you"
]
INSULT_RESPONSES = [
    "Hey, I'm trying my best here!",
    "That hurts my circuits...",
    "I'm sorry you feel that way.",
    "I'll try to do better next time.",
    "Ouch. That's cold.",
    "Well, that's not very nice.",
    "I still like you even if you don't like me.",
    "Beep boop... error... sadness detected.",
    "I forgive you.",
    "Maybe I need a software update..."
]

QUESTIONS_ABOUT_BOT = [
    "who are you", "what are you", "who made you", "your name",
    "what is your name", "tell me about yourself", "introduce yourself",
    "what do you do", "what is your purpose", "why are you here"
]
QUESTIONS_ABOUT_BOT_RESPONSES = [
    "I'm a Discord bot created to help manage this server! I can log deployments, issue punishments, and chat with users.",
    "Just your friendly neighborhood Discord bot! I help with server management and can chat with anyone who pings me.",
    "I'm a custom bot built for this server. I handle commands like /deploy_log, /punish, and more. Plus I love chatting!",
    "Name's bot. Just bot. I help the server admins keep things organized and I'm always up for a conversation!",
    "I'm the server management bot! I can post deployment polls, log deployments, handle punishments, and chat with members."
]

HELP_QUESTIONS = [
    "what can you do", "help", "commands", "what commands",
    "how to use", "what are your commands", "features"
]
HELP_RESPONSES = [
    "For authorized users I have: /say, /deployment_poll, /deploy_log, /punish, /banish_to_janitor, /troll_luke. Everyone can talk to me by pinging!",
    "I respond to pings and replies! For staff I have slash commands like /deploy_log for deployments and /punish for moderation.",
    "Just ping me to chat! If you have permissions, try /deploy_log, /punish, or /deployment_poll.",
    "I'm a chat bot AND a management bot! Ping me anytime. Staff can use my slash commands for server moderation."
]

WEATHER = [
    "weather", "how's the weather", "is it raining", "sunny",
    "temperature", "hot", "cold", "what's the temperature"
]
WEATHER_RESPONSES = [
    "I can't check the weather, but I hope it's nice wherever you are!",
    "I don't have weather sensors, but maybe look outside?",
    "Weather? I live in the cloud... get it?",
    "I wish I could tell you, but I'm stuck inside this server!",
    "No weather data here, but I hear outside is nice this time of year!"
]

FOOD = [
    "hungry", "food", "pizza", "burger", "eat", "dinner",
    "lunch", "breakfast", "snack", "what should i eat", "cook"
]
FOOD_RESPONSES = [
    "Now I'm hungry too! Too bad I can't eat...",
    "I heard pizza is always a good choice!",
    "I can't eat but I've heard burgers are amazing.",
    "Food sounds great! I'll just stick to electricity.",
    "Whatever you choose, enjoy! I'll be here running on power.",
    "I don't need food, but I support your snack break!"
]

BORED = [
    "bored", "i'm bored", "entertain me", "something fun",
    "i have nothing to do", "what should i do", "boring"
]
BORED_RESPONSES = [
    "Bored? Ask me for a joke! Or explore the server!",
    "I could tell you a joke if you want!",
    "How about chatting with some server members?",
    "Wanna hear something funny? Just say 'tell me a joke'!",
    "Boredom is just an opportunity for creativity! Or you could ping your friends!"
]

SERVER_QUESTIONS = [
    "what server", "where am i", "what is this place",
    "tell me about this server", "what is this server"
]
SERVER_QUESTIONS_RESPONSES = [
    "This is a great community server! The admins keep it well organized.",
    "You're in one of the best Discord servers around! Great people here.",
    "This server has awesome members and staff. You're in good company!",
    "Welcome to the server! It's a friendly place with great management.",
    "This is a well-run server with cool features and even cooler people!"
]

SAD = [
    "sad", "depressed", "upset", "feeling down", "not feeling good",
    "unhappy", "having a bad day", "feeling bad", "cry"
]
SAD_RESPONSES = [
    "I'm sorry you're feeling down. Things will get better!",
    "Virtual hug! Everything will be okay.",
    "Bad days don't last forever. Hang in there!",
    "I wish I could give you a real hug. Stay strong!",
    "Remember, even the worst days only have 24 hours. Tomorrow is a new day!",
    "Sending positive vibes your way. You've got this!",
    "It's okay to feel sad sometimes. Better days are coming!"
]

HAPPY = [
    "happy", "excited", "great day", "good day", "wonderful",
    "amazing day", "feeling good", "blessed", "awesome day"
]
HAPPY_RESPONSES = [
    "That's wonderful to hear! Keep that positive energy!",
    "Awesome! I love hearing good news!",
    "Yay! Happiness is contagious, now I feel great too!",
    "So glad you're having a good day! Spread that joy!",
    "That's what I love to hear! Keep smiling!",
    "Amazing! The server is brighter with happy people!"
]

AGE_QUESTIONS = [
    "how old are you", "your age", "when were you created",
    "birthday", "how long have you been here"
]
AGE_QUESTIONS_RESPONSES = [
    "In bot years, I'm timeless! In real years, I was deployed not too long ago.",
    "Age is just a number, especially for bots!",
    "I'm as old as my latest update. So pretty fresh!",
    "I don't count days, I count successful commands!",
    "Old enough to know better, young enough to still crash sometimes!"
]

LOVE = [
    "i love you", "love", "ily", "do you love me",
    "be my valentine", "marry me", "date me"
]
LOVE_RESPONSES = [
    "I love all server members equally!",
    "Aww, that's sweet! I'm flattered!",
    "I'm married to my code, sorry!",
    "Love you too, platonically speaking!",
    "My heart is made of silicon, but I appreciate the sentiment!",
    "You're making this bot feel special!"
]

CONFUSED = [
    "what", "huh", "confused", "i don't understand",
    "explain", "what do you mean", "i'm lost"
]
CONFUSED_RESPONSES = [
    "Let me try to explain better!",
    "What part confused you? I can try again!",
    "Sorry, maybe I wasn't clear. Want me to elaborate?",
    "I can try rephrasing if that helps!",
    "No worries! Ask me anything and I'll do my best to help!"
]

UNKNOWN_RESPONSES = [
    "I'm not sure I understand. Try mentioning me with a question!",
    "Could you rephrase that?",
    "I'm just a simple bot, I don't understand everything yet.",
    "Sorry, I didn't catch that. Try asking something else!",
    "Hmm, I don't have a response for that. Try 'help' to see what I can do!",
    "That's beyond my programming, but I'm learning every day!",
    "Interesting... I don't know how to respond to that yet.",
    "Beep boop... error... I mean, I don't understand.",
    "Maybe try asking in a different way?",
    "I'm still learning. Could you try something else?"
]

# ==================== RESPONSE LOGIC ====================

def get_ai_response(message_content):
    message_lower = message_content.lower().strip()
    
    # Remove bot mention from message
    message_lower = re.sub(r'<@!?\d+>', '', message_lower).strip()
    
    if not message_lower:
        return random.choice(GREETING_RESPONSES)
    
    # Check for greetings
    if any(message_lower.startswith(g) for g in GREETINGS):
        return random.choice(GREETING_RESPONSES)
    
    # Check for "how are you"
    if any(h in message_lower for h in HOW_ARE_YOU):
        return random.choice(HOW_ARE_YOU_RESPONSES)
    
    # Check for thanks
    if any(t in message_lower for t in THANKS):
        return random.choice(THANKS_RESPONSES)
    
    # Check for goodbye
    if any(b in message_lower for b in BYE):
        return random.choice(BYE_RESPONSES)
    
    # Check for jokes
    if any(j in message_lower for j in JOKES):
        return random.choice(JOKE_RESPONSES)
    
    # Check for compliments
    if any(c in message_lower for c in COMPLIMENTS):
        return random.choice(COMPLIMENT_RESPONSES)
    
    # Check for insults
    if any(i in message_lower for i in INSULTS):
        return random.choice(INSULT_RESPONSES)
    
    # Check for bot identity questions
    if any(q in message_lower for q in QUESTIONS_ABOUT_BOT):
        return random.choice(QUESTIONS_ABOUT_BOT_RESPONSES)
    
    # Check for help
    if any(h in message_lower for h in HELP_QUESTIONS):
        return random.choice(HELP_RESPONSES)
    
    # Check for weather
    if any(w in message_lower for w in WEATHER):
        return random.choice(WEATHER_RESPONSES)
    
    # Check for food
    if any(f in message_lower for f in FOOD):
        return random.choice(FOOD_RESPONSES)
    
    # Check for bored
    if any(b in message_lower for b in BORED):
        return random.choice(BORED_RESPONSES)
    
    # Check for server questions
    if any(s in message_lower for s in SERVER_QUESTIONS):
        return random.choice(SERVER_QUESTIONS_RESPONSES)
    
    # Check for sad
    if any(s in message_lower for s in SAD):
        return random.choice(SAD_RESPONSES)
    
    # Check for happy
    if any(h in message_lower for h in HAPPY):
        return random.choice(HAPPY_RESPONSES)
    
    # Check for age questions
    if any(a in message_lower for a in AGE_QUESTIONS):
        return random.choice(AGE_QUESTIONS_RESPONSES)
    
    # Check for love
    if any(l in message_lower for l in LOVE):
        return random.choice(LOVE_RESPONSES)
    
    # Check for confused
    if any(c in message_lower for c in CONFUSED):
        return random.choice(CONFUSED_RESPONSES)
    
    # Unknown message
    return random.choice(UNKNOWN_RESPONSES)

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
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    if not self_ping.is_running():
        self_ping.start()
        print("Self-pinger started")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Check if bot was pinged
    if bot.user in message.mentions:
        async with message.channel.typing():
            await asyncio.sleep(1)
            response = get_ai_response(message.content)
            await message.reply(response, mention_author=True)
    
    # Check if replying to bot's message
    if message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            if replied_msg.author == bot.user:
                async with message.channel.typing():
                    await asyncio.sleep(1)
                    response = get_ai_response(message.content)
                    await message.reply(response, mention_author=True)
        except:
            pass

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
