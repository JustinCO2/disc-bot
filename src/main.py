import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

with open('config/config.json', 'r') as config_file:
    config = json.load(config_file)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

# init
bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync() 
    print(f"Slash commands synced. Bot ready as {bot.user}.")

# Load extensions
async def load_extensions():
    try:
        await bot.load_extension("commands.admin")
        await bot.load_extension("commands.member")
        await bot.load_extension("commands.officer")
        print("Command extensions loaded successfully.")
    except Exception as e:
        print(f"Error loading extensions: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
