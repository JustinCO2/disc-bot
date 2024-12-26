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
intents.message_content = True
intents.members = True
intents.reactions = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    leaderboard_cog = bot.get_cog('LeaderboardCog')
    #if leaderboard_cog:
    #    await leaderboard_cog.initialize_leaderboards()
    print(f"Slash commands synced. Bot ready.")

async def load_extensions():
    try:
        await bot.load_extension("commands.admin")
        await bot.load_extension("commands.member")
        await bot.load_extension("commands.officer")
        await bot.load_extension("commands.leaderboard")
        print("Command extensions loaded successfully.")
    except Exception as e:
        print(f"Error loading extensions: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)
    @commands.command(name="init_leaderboard")
    @commands.is_owner()
    async def init_leaderboard(self, ctx):
        await ctx.send("Leaderboard initialization attempted")

if __name__ == "__main__":
    asyncio.run(main())