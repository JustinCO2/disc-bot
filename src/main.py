import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Load MongoDB URL and Discord Token
MONGO_URL = os.getenv("MONGO_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
print(f"DISCORD_TOKEN (first 5 chars): {DISCORD_TOKEN[:5] if DISCORD_TOKEN else 'Not Found'}")

# MongoDB connection setup
client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_bot"]

# Discord bot intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.messages = True
intents.guilds = True

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await load_extensions(self)

bot = Bot()

# Replace with your numeric Guild ID
guild_id = 1140429772531449886
# Wrap the integer in a discord.Object for guild-specific sync
guild_obj = discord.Object(id=guild_id)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Cleared and synced {len(synced)} command(s).")
        for command in bot.tree.get_commands():
            print(f"Registered command: {command.name}")
    except Exception as e:
        print(f"Failed to clear and sync commands: {e}")

@bot.command()
async def list_commands(ctx):
    """List all registered slash commands."""
    commands_ = await bot.tree.fetch_commands()
    for cmd in commands_:
        await ctx.send(f"Command: {cmd.name}, Description: {cmd.description}")

async def load_extensions(bot):
    extensions = ["commands.admin", "commands.member", "commands.officer", "commands.leaderboard"]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension: {ext}")
        except Exception as e:
            print(f"Error loading extension {ext}: {e}")
    print(f"Current commands: {bot.tree.get_commands()}")

async def test_mongo():
    try:
        await db.command("ping")
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

asyncio.run(test_mongo())

if __name__ == "__main__":
    try:
        print("Discord.py version:", discord.__version__)
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Bot encountered an error during runtime: {e}")
