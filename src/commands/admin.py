from discord.ext import commands
from discord import app_commands
import discord
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection setup
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_bot"]

async def guild_param_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for guild parameters."""
    fields = ["announcements", "leaderboard", "verification", "name", "role_id"]
    return [
        app_commands.Choice(name=field, value=field)
        for field in fields if current.lower() in field.lower()
    ]

class AdminCommands(commands.Cog):
    """Admin commands for managing guilds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def has_permissions(self, interaction: discord.Interaction) -> bool:
        allowed_roles = [
            1248807293018046596, 1321315696801615872, 1321315779085467701,
            1321315841366687785, 1321315919401586771, 1321315967120441364,
            1244616887250456577, 1244455889965023366, 1217354048416645150
        ]  # Update role IDs as needed
        return any(role.id in allowed_roles for role in interaction.user.roles)

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=1140429772531449886))
    async def create_guild(
        self,
        interaction: discord.Interaction,
        name: str,
        announce_channel: discord.TextChannel,
        leaderboard_channel: discord.TextChannel,
        verification_channel: discord.TextChannel,
        member_role: discord.Role
    ):
        """Create a new guild in the database."""
        if not await self.has_permissions(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            guild = {
                "_id": name,
                "channels": {
                    "announcements": str(announce_channel.id),
                    "leaderboard": str(leaderboard_channel.id),
                    "verification": str(verification_channel.id),
                },
                "role_id": str(member_role.id),
                "members": {}
            }

            existing_guild = await db.guilds.find_one({"_id": name})
            if existing_guild:
                raise ValueError(f"Guild {name} already exists")

            await db.guilds.insert_one(guild)
            await interaction.response.send_message(f"Successfully created guild: {name}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=1140429772531449886))
    @app_commands.autocomplete(param=guild_param_autocomplete)
    async def edit_guild(
        self,
        interaction: discord.Interaction,
        name: str,
        param: str,
        new_channel: Optional[discord.TextChannel] = None,
        new_role: Optional[discord.Role] = None
    ):
        """Edit guild parameters in the database."""
        if not await self.has_permissions(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            guild = await db.guilds.find_one({"_id": name})
            if not guild:
                raise ValueError(f"Guild {name} does not exist")

            if param in ["announcements", "leaderboard", "verification"]:
                if not new_channel:
                    raise ValueError("Channel parameter requires a new channel")
                update_field = f"channels.{param}"
                await db.guilds.update_one({"_id": name}, {"$set": {update_field: str(new_channel.id)}})
            elif param == "role_id":
                if not new_role:
                    raise ValueError("Role parameter requires a new role")
                await db.guilds.update_one({"_id": name}, {"$set": {"role_id": str(new_role.id)}})
            else:
                raise ValueError(f"Invalid parameter: {param}")

            await interaction.response.send_message(f"Successfully updated {param} for guild: {name}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    """Registers the cog with the bot."""
    await bot.add_cog(AdminCommands(bot))
