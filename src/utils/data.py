from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_bot"]

GUILD_TEMPLATE = {
    "channels": {
        "announcements": None,
        "leaderboard": None,
        "verification": None
    },
    "role_id": None,
    "members": {}
}

MEMBER_TEMPLATE = {
    "damages": {
        "rvd": 0,
        "aod": 0,
        "la": 0
    },
    "last_donation": None
}

def parse_damage_input(damage_str):
    """
    Parses damage input string and returns the value in raw numbers (float).
    Accepts inputs in formats like "8.88b", "8880M", or raw numbers.
    """
    damage_str = damage_str.lower().strip()
    if damage_str.endswith('b'):
        return float(damage_str[:-1]) * 1e9
    if damage_str.endswith('B'):
        return float(damage_str[:-1]) * 1e9    
    if damage_str.endswith('M'):
        return float(damage_str[:-1]) * 1e6    
    elif damage_str.endswith('m'):
        return float(damage_str[:-1]) * 1e6
    else:
        return float(damage_str)

async def create_guild(name: str, announce_id: str, leaderboard_id: str, verif_id: str, role_id: str):
    """Create a new guild using the template."""
    new_guild = GUILD_TEMPLATE.copy()
    new_guild["channels"]["announcements"] = announce_id
    new_guild["channels"]["leaderboard"] = leaderboard_id
    new_guild["channels"]["verification"] = verif_id
    new_guild["role_id"] = role_id

    existing_guild = await db.guilds.find_one({"_id": name})
    if existing_guild:
        raise ValueError(f"Guild {name} already exists")

    new_guild["_id"] = name
    await db.guilds.insert_one(new_guild)

async def edit_guild(name: str, param: str, new_value: str):
    """Edit an existing guild."""
    if param in ["announcements", "leaderboard", "verification"]:
        update_field = f"channels.{param}"
    elif param == "role_id":
        update_field = "role_id"
    else:
        raise ValueError(f"Invalid parameter: {param}")

    result = await db.guilds.update_one({"_id": name}, {"$set": {update_field: new_value}})
    if result.matched_count == 0:
        raise ValueError(f"Guild {name} not found")

async def add_member(name: str, guild: str, rvd: Optional[int] = 0, aod: Optional[int] = 0, la: Optional[int] = 0):
    """Add a new member to a guild."""
    new_member = MEMBER_TEMPLATE.copy()
    new_member["damages"]["rvd"] = rvd
    new_member["damages"]["aod"] = aod
    new_member["damages"]["la"] = la

    result = await db.guilds.update_one(
        {"_id": guild, f"members.{name}": {"$exists": False}},
        {"$set": {f"members.{name}": new_member}}
    )
    if result.matched_count == 0:
        raise ValueError(f"Guild {guild} not found or member {name} already exists")

async def edit_member(name: str, boss: str, new_damage: int):
    """Edit member data."""
    if boss in ["rvd", "aod", "la"]:
        update_field = f"members.{name}.damages.{boss}"
    elif boss == "last_donation":
        update_field = f"members.{name}.last_donation"
    else:
        raise ValueError(f"Invalid parameter: {boss}")

    result = await db.guilds.update_one(
        {f"members.{name}": {"$exists": True}},
        {"$set": {update_field: new_damage}}
    )
    if result.matched_count == 0:
        raise ValueError(f"Member {name} not found in any guild")

async def submit_dmg(member: str, boss: str, damage: str, attachment: str):
    """Submit a damage update request."""
    try:
        # Find the guild associated with the member
        guild_name = await find_guild_by_member(member)
        if not guild_name:
            raise ValueError(f"Member {member} not found in any guild")

        # Fetch guild data from the database
        guild = await db.guilds.find_one({"_id": guild_name})
        if not guild or "channels" not in guild or "verification" not in guild["channels"]:
            raise ValueError(f"Verification channel not configured for guild {guild_name}")

        verification_channel_id = guild["channels"]["verification"]

        # Parse and format damage
        parsed_damage = parse_damage_input(damage)
        formatted_damage = f"{parsed_damage / 1e9:.2f}B"

        # Return the response dictionary
        return {
            "verification_channel_id": verification_channel_id,
            "content": f"Damage Update Request:\nMember: {member}\nBoss: {boss}\nDamage: {formatted_damage}",
            "attachment": attachment
        }

    except Exception as e:
        logger.error(f"Error in submit_dmg: {e}")
        raise

async def submit_relics(member: str, attachment: str):
    """Submit a relic update request."""
    guild_name = await find_guild_by_member(member)
    if not guild_name:
        raise ValueError(f"Member {member} not found in any guild")

    guild = await db.guilds.find_one({"_id": guild_name})
    verification_channel_id = guild["channels"]["verification"]

    return {
        "verification_channel_id": verification_channel_id,
        "content": f"Relic Donation Request:\nMember: {member}",
        "attachment": attachment
    }

async def find_guild_by_member(member: str) -> Optional[str]:
    """Find the guild a member belongs to."""
    guild = await db.guilds.find_one({f"members.{member}": {"$exists": True}})
    return guild["_id"] if guild else None

async def find_guild_by_channel(channel_id: int) -> Optional[str]:
    """Find the guild associated with a verification channel."""
    guild = await db.guilds.find_one({"channels.verification": str(channel_id)})
    return guild["_id"] if guild else None

async def update_member_data(guild_name: str, member: str, field: str, value: any):
    """Update a member's data field after approval."""
    if field == "damages":
        boss, damage = value
        update_field = f"members.{member}.damages.{boss}"
    elif field == "last_donation":
        update_field = f"members.{member}.last_donation"
    else:
        raise ValueError(f"Invalid field: {field}")

    result = await db.guilds.update_one(
        {"_id": guild_name},
        {"$set": {update_field: damage if field == "damages" else value}}
    )
    if result.matched_count == 0:
        raise ValueError(f"Guild {guild_name} or member {member} not found")
