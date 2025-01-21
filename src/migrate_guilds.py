import json
from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection setup
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_bot"]

async def migrate_guilds():
    """Migrate guilds from the JSON file to MongoDB."""
    try:
        # Load guilds from JSON file
        with open('data/guilds.json', 'r') as file:
            guilds = json.load(file)

        # Iterate over each guild in the JSON data
        for guild_name, guild_data in guilds.items():
            # Add _id field to match the guild's name in MongoDB
            guild_data["_id"] = guild_name

            # Insert the guild data into MongoDB
            await db.guilds.insert_one(guild_data)
            print(f"Migrated guild: {guild_name}")

    except Exception as e:
        print(f"Error migrating guilds: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_guilds())