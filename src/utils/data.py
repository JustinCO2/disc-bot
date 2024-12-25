import json
from typing import Optional

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

async def create_guild(name: str, announce_id: str, leaderboard_id: str, verif_id: str, role_id: str):
    """Create a new guild using the template."""
    new_guild = GUILD_TEMPLATE.copy()
    new_guild["channels"]["announcements"] = announce_id
    new_guild["channels"]["leaderboard"] = leaderboard_id
    new_guild["channels"]["verification"] = verif_id
    new_guild["role_id"] = role_id

    try:
        with open('data/guilds.json', 'r') as f:
            guilds = json.load(f)
    except FileNotFoundError:
        guilds = {}

    if name in guilds:
        raise ValueError(f"Guild {name} already exists")

    guilds[name] = new_guild

    with open('data/guilds.json', 'w') as f:
        json.dump(guilds, f, indent=4)

async def edit_guild(name: str, param: str, new_value: str):
    """Edit an existing guild."""
    with open('data/guilds.json', 'r') as f:
        guilds = json.load(f)

    if name not in guilds:
        raise ValueError(f"Guild {name} not found")

    if param in ["announcements", "leaderboard", "verification"]:
        guilds[name]["channels"][param] = new_value
    elif param == "role_id":
        guilds[name]["role_id"] = new_value
    else:
        raise ValueError(f"Invalid parameter: {param}")

    with open('data/guilds.json', 'w') as f:
        json.dump(guilds, f, indent=4)

# Member management
async def add_member(name: str, guild: str, rvd: Optional[int] = 0, aod: Optional[int] = 0, la: Optional[int] = 0):
    """Add a new member to a guild."""
    with open('data/guilds.json', 'r') as f:
        guilds = json.load(f)

    if guild not in guilds:
        raise ValueError(f"Guild {guild} not found")

    if name in guilds[guild]["members"]:
        raise ValueError(f"Member {name} already exists in {guild}")

    new_member = MEMBER_TEMPLATE.copy()
    new_member["damages"]["rvd"] = rvd
    new_member["damages"]["aod"] = aod
    new_member["damages"]["la"] = la

    guilds[guild]["members"][name] = new_member

    with open('data/guilds.json', 'w') as f:
        json.dump(guilds, f, indent=4)

async def edit_member(name: str, param: str, new_value: any):
    """Edit member data."""
    with open('data/guilds.json', 'r') as f:
        guilds = json.load(f)

    member_guild = next((g for g, d in guilds.items() if name in d["members"]), None)
    if not member_guild:
        raise ValueError(f"Member {name} not found in any guild")

    if param in ["rvd", "aod", "la"]:
        guilds[member_guild]["members"][name]["damages"][param] = int(new_value)
    elif param == "last_donation":
        guilds[member_guild]["members"][name]["last_donation"] = new_value
    else:
        raise ValueError(f"Invalid parameter: {param}")

    with open('data/guilds.json', 'w') as f:
        json.dump(guilds, f, indent=4)

# Submission management
async def submit_dmg(member: str, boss: str, damage: int, attachment: str):
    """Submit a damage update request."""
    guild_name = await find_guild_by_member(member)
    if not guild_name:
        raise ValueError(f"Member {member} not found in any guild")

    with open('data/guilds.json', 'r') as f:
        guilds = json.load(f)

    verification_channel_id = guilds[guild_name]["channels"]["verification"]

    return {
        "verification_channel_id": verification_channel_id,
        "content": f"Damage Update Request:\nMember: {member}\nBoss: {boss}\nDamage: {damage}",
        "attachment": attachment
    }

async def submit_relics(member: str, attachment: str):
    """Submit a relic update request."""
    guild_name = await find_guild_by_member(member)
    if not guild_name:
        raise ValueError(f"Member {member} not found in any guild")

    with open('data/guilds.json', 'r') as f:
        guilds = json.load(f)

    verification_channel_id = guilds[guild_name]["channels"]["verification"]

    return {
        "verification_channel_id": verification_channel_id,
        "content": f"Relic Donation Request:\nMember: {member}",
        "attachment": attachment
    }

async def find_guild_by_member(member: str) -> Optional[str]:
    """Find the guild a member belongs to."""
    with open('data/guilds.json', 'r') as f:
        guilds = json.load(f)

    for guild_name, guild_data in guilds.items():
        if member in guild_data["members"]:
            return guild_name

    return None

def validate_guilds_structure():
    try:
        with open('data/guilds.json', 'r') as f:
            guilds = json.load(f)
        for guild_name, guild_data in guilds.items():
            if not all(key in guild_data for key in GUILD_TEMPLATE.keys()):
                raise ValueError(f"Guild {guild_name} is missing keys")
            if "members" in guild_data:
                for member_name, member_data in guild_data["members"].items():
                    if not all(key in member_data for key in MEMBER_TEMPLATE.keys()):
                        raise ValueError(f"Member {member_name} in guild {guild_name} is missing keys")
        print("Guilds.json structure is valid.")
    except FileNotFoundError:
        print("Guilds.json not found. Validation skipped.")

async def update_member_data(guild_name: str, member: str, field: str, value: any):
    """Update a member's data field after approval."""
    with open('data/guilds.json', 'r') as f:
        guilds = json.load(f)

    if guild_name not in guilds:
        raise ValueError(f"Guild {guild_name} not found")
    if member not in guilds[guild_name]["members"]:
        raise ValueError(f"Member {member} not found in guild {guild_name}")

    if field == "damages":
        boss, damage = value
        guilds[guild_name]["members"][member]["damages"][boss] = damage
    elif field == "last_donation":
        guilds[guild_name]["members"][member]["last_donation"] = value
    else:
        raise ValueError(f"Invalid field: {field}")

    with open('data/guilds.json', 'w') as f:
        json.dump(guilds, f, indent=4)
