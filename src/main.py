import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import asyncio
from utils.data import validate_guilds_structure

load_dotenv()

with open('config/config.json', 'r') as config_file:
    config = json.load(config_file)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
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

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    try:
        print("Validating guild data...")
        validate_guilds_structure()
        print("Guild data validation complete.")
    except Exception as e:
        print(f"Validation error: {e}")

    try:
        await bot.tree.sync()
        print("All commands synced successfully.")
        for command in bot.tree.get_commands():
            print(f"Registered command: {command.name}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

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

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Bot encountered an error during runtime: {e}")
