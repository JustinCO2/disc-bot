import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# Load MongoDB URL and Discord Token
MONGO_URL = os.getenv("MONGO_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

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

# Hardcoded guild IDs for development
DEV_GUILD_ID_1 = 1140429772531449886
DEV_GUILD_ID_2 = 513561942984753154

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await load_extensions(self)
        await restrict_all_commands_to_dev_guilds(self)

bot = Bot()

async def restrict_all_commands_to_dev_guilds(bot):
    """Restrict all slash commands to the two development guilds."""
    dev_guilds = [discord.Object(id=DEV_GUILD_ID_1), discord.Object(id=DEV_GUILD_ID_2)]
    for command in bot.tree.get_commands():
        command.guilds = dev_guilds

    # Sync commands with the specified guilds
    await bot.tree.sync()
    print("All slash commands restricted to development guilds.")

@bot.event
async def on_ready():
    try:
        bot.tree.clear_commands(guild=None)  # Clear global commands
        synced = await bot.tree.sync()
        print(f"Cleared and synced {len(synced)} command(s).")
        for command in bot.tree.get_commands():
            print(f"Registered command: {command.name}")
    except Exception as e:
        print(f"Failed to clear and sync commands: {e}")

@bot.command()
async def list_commands(ctx):
    """List all registered slash commands."""
    commands = await bot.tree.fetch_commands()
    for command in commands:
        await ctx.send(f"Command: {command.name}, Description: {command.description}")

async def load_extensions(bot):
    extensions = [
        "commands.admin",
        "commands.member",
        "commands.officer",
        "commands.leaderboard"
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension: {ext}")
        except Exception as e:
            print(f"Error loading extension {ext}: {e}")

async def test_mongo():
    try:
        await db.command("ping")
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

asyncio.run(test_mongo())

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Bot encountered an error during runtime: {e}")
