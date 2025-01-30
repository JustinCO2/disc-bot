import discord
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import os
from utils.leaderboard_chrome import create_damage_board

logger = logging.getLogger('discord')

# MongoDB connection setup
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_bot"]

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = {}

    async def load_message_ids(self):
        """Load saved message IDs from MongoDB."""
        records = await db.leaderboard_messages.find().to_list(None)
        self.messages = {record["_id"]: record["message_id"] for record in records}

    async def save_message_id(self, guild_name: str, message_id: str):
        """Save a message ID to MongoDB."""
        await db.leaderboard_messages.update_one(
            {"_id": guild_name},
            {"$set": {"message_id": message_id}},
            upsert=True
        )

    # --------------------------------------------------------------------------
    # The old method to format damage text, kept in case you still need it for 
    # something else. If purely unused, you can remove or leave it as is.
    # --------------------------------------------------------------------------
    def format_damage(self, damage: int) -> str:
        if damage >= 1:
            return f"{damage / 1_000_000_000:.2f}B"
        return str(damage)

    async def load_guilds(self) -> dict:
        """Load all guilds from MongoDB."""
        guilds = {}
        async for guild in db.guilds.find():
            guilds[guild["_id"]] = guild
        return guilds

    async def initialize_leaderboards(self):
        logger.info("Initializing leaderboards...")
        await self.load_message_ids()
        guilds = await self.load_guilds()

        for guild_name, guild_data in guilds.items():
            try:
                channel_id = int(guild_data["channels"]["leaderboard"])
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    logger.error(f"Channel {channel_id} not found for guild {guild_name}")
                    continue

                if guild_name in self.messages:
                    try:
                        # Attempt to fetch the existing leaderboard message
                        await channel.fetch_message(int(self.messages[guild_name]))
                        logger.info(f"Found existing leaderboard for {guild_name}")
                        continue
                    except (discord.NotFound, discord.HTTPException):
                        logger.info(f"Stored message for {guild_name} not found, creating new one")

                # ---------------- NEW IMAGE GENERATION ----------------
                # Create the damage board image (and HTML if needed).
                screenshot_path, html_path = create_damage_board(guild_name, guild_data)
                
                # Send the generated image in a new message.
                file = discord.File(screenshot_path, filename=os.path.basename(screenshot_path))
                message = await channel.send(file=file)
                
                # Store the new message ID for future edits
                self.messages[guild_name] = str(message.id)
                await self.save_message_id(guild_name, str(message.id))

                logger.info(f"Created leaderboard image for {guild_name} in channel {channel_id}")

            except Exception as e:
                logger.error(f"Error creating leaderboard for {guild_name}: {e}")

    async def update_guild_leaderboard(self, guild_name: str, guild_data: dict):
        try:
            channel_id = int(guild_data["channels"]["leaderboard"])
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found for guild {guild_name}")
                return

            # ---------------- NEW IMAGE GENERATION ----------------
            # Create the damage board image (and HTML if needed).
            screenshot_path, html_path = create_damage_board(guild_name, guild_data)

            # Comment out the text-based content code:
            """
            content = self.format_leaderboard(guild_name, guild_data)
            """

            message = None
            if guild_name in self.messages:
                try:
                    message = await channel.fetch_message(int(self.messages[guild_name]))
                except (discord.NotFound, discord.HTTPException):
                    logger.info(f"Stored message for {guild_name} not found, creating new one")
                    message = None

            # Prepare the new file to send
            file = discord.File(screenshot_path, filename=os.path.basename(screenshot_path))

            if message:
                # Edit the existing message by removing text and updating attachment
                await message.edit(content="", attachments=[file])
                logger.info(f"Updated existing leaderboard image for {guild_name}")
            else:
                # Send a new message if none exists
                message = await channel.send(file=file)
                self.messages[guild_name] = str(message.id)
                await self.save_message_id(guild_name, str(message.id))
                logger.info(f"Created new leaderboard image for {guild_name}")

        except Exception as e:
            logger.error(f"Error updating leaderboard for {guild_name}: {e}")

'''
    @tasks.loop(minutes=1)
    async def update_leaderboards(self):
        logger.info("Running scheduled leaderboard update...")
        guilds = await self.load_guilds()
        for guild_name, guild_data in guilds.items():
            await self.update_guild_leaderboard(guild_name, guild_data)
            

    @update_leaderboards.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        await self.initialize_leaderboards()
'''

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
