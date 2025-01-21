from discord.ext import commands
from discord import app_commands
import discord
from typing import Optional
from commands.member import boss_autocomplete
from utils.data import add_member, edit_member, parse_damage_input
from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection setup
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_bot"]

class OfficerCommands(commands.Cog):
    """Officer commands for managing members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_officer(self, interaction: discord.Interaction) -> bool:
        allowed_roles = [
            1248807293018046596, 1321315696801615872, 1321315779085467701,
            1321315841366687785, 1321315919401586771, 1321315967120441364,
            1248807669117227059, 1321313038804193351, 1321313793938030662,
            1321314217734701126, 1321314303332192316, 1321314466062794852,
            1244616887250456577, 1244455889965023366, 1140634765297451113,
            1217354048416645150
        ]  # Update role IDs as needed
        return any(role.id in allowed_roles for role in interaction.user.roles)

    async def guild_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete guild names."""
        guilds = await db.guilds.find().to_list(None)
        return [
            app_commands.Choice(name=guild["_id"], value=guild["_id"])
            for guild in guilds if current.lower() in guild["_id"].lower()
        ]

    async def member_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete member names."""
        guilds = await db.guilds.find().to_list(None)
        members = [
            member for guild in guilds for member in guild.get("members", {}).keys()
        ]
        return [
            app_commands.Choice(name=member, value=member)
            for member in members if current.lower() in member.lower()
        ]

    member_group = app_commands.Group(name="member", description="Member management commands")

    @member_group.command(name="add")
    @app_commands.autocomplete(guild=guild_autocomplete)
    async def member_add(
        self,
        interaction: discord.Interaction,
        name: str,
        guild: str,
        rvd: Optional[int] = 0,
        aod: Optional[int] = 0,
        la: Optional[int] = 0
    ):
        """Add a member to a guild."""
        if not self.is_officer(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            await add_member(name, guild, rvd, aod, la)
            await interaction.response.send_message(f"Successfully added {name} to {guild}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @member_group.command(name="edit")
    @app_commands.autocomplete(name=member_autocomplete, boss=boss_autocomplete)
    async def member_edit(
        self,
        interaction: discord.Interaction,
        name: str,
        boss: str,
        new_damage: str
    ):
        """Edit a member's damage for a boss."""
        if not self.is_officer(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            if boss in ["rvd", "aod", "la"]:
                new_damage = parse_damage_input(new_damage)

            await edit_member(name, boss, new_damage)
            await interaction.response.send_message(f"Successfully updated {boss} for member: {name}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @member_group.command(name="delete")
    @app_commands.autocomplete(member_name=member_autocomplete)
    async def delete_member(
        self,
        interaction: discord.Interaction,
        guild_name: str,
        member_name: str
    ):
        """Delete a member from the guild."""
        if not await self.has_permissions(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            guild = await db.guilds.find_one({"_id": guild_name})
            if not guild:
                raise ValueError(f"Guild {guild_name} does not exist")

            members = guild.get("members", {})
            if member_name not in members:
                raise ValueError(f"Member {member_name} not found in guild {guild_name}")

            # Remove the member
            await db.guilds.update_one(
                {"_id": guild_name},
                {"$unset": {f"members.{member_name}": ""}}
            )

            await interaction.response.send_message(f"Successfully removed member: {member_name} from guild: {guild_name}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    """Set up the OfficerCommands cog."""
    await bot.add_cog(OfficerCommands(bot))
