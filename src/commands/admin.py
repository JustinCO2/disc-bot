from discord.ext import commands
from discord import app_commands
import discord
from typing import Optional
from utils.data import create_guild, edit_guild

async def guild_param_autocomplete(interaction: discord.Interaction, current: str):
    """Autocomplete for guild parameters."""
    fields = ["announcements", "leaderboard", "verification", "name", "role_id"]
    return [
        app_commands.Choice(name=field, value=field)
        for field in fields
        if current.lower() in field.lower()
    ]

class AdminCommands(commands.Cog):
    """Admin commands for managing guilds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def has_permissions(self, interaction: discord.Interaction) -> bool:
        allowed_roles = [1248807293018046596, 1321315696801615872, 1321315779085467701, 1321315841366687785, 1321315919401586771, 1321315967120441364, 1244616887250456577, 1244455889965023366]  # Update role IDs as needed
        # 1248807293018046596, 1321315696801615872, 1321315779085467701, 1321315841366687785, 1321315919401586771, 1321315967120441364 | leader roles, star/celest/galaxy/moon/clown/jester
        # 1244616887250456577, 1244455889965023366 | codeman, test server
        return any(role.id in allowed_roles for role in interaction.user.roles)

    @app_commands.command()
    async def create_guild(
        self,
        interaction: discord.Interaction,
        name: str,
        announce_channel: discord.TextChannel,
        leaderboard_channel: discord.TextChannel,
        verification_channel: discord.TextChannel,
        member_role: discord.Role
    ):
        if not await self.has_permissions(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            await create_guild(
                name,
                str(announce_channel.id),
                str(leaderboard_channel.id),
                str(verification_channel.id),
                str(member_role.id)
            )
            await interaction.response.send_message(f"Successfully created guild: {name}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command()
    @app_commands.autocomplete(param=guild_param_autocomplete)
    async def edit_guild(
        self,
        interaction: discord.Interaction,
        name: str,
        param: str,
        new_channel: Optional[discord.TextChannel] = None,
        new_role: Optional[discord.Role] = None
    ):
        """Edit guild parameters."""
        if not await self.has_permissions(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            if param in ["announcements", "leaderboard", "verification"]:
                if not new_channel:
                    raise ValueError("Channel parameter requires a new channel")
                await edit_guild(name, param, str(new_channel.id))
            elif param == "role_id":
                if not new_role:
                    raise ValueError("Role parameter requires a new role")
                await edit_guild(name, param, str(new_role.id))
            else:
                raise ValueError(f"Invalid parameter: {param}")
                
            await interaction.response.send_message(f"Successfully updated {param} for guild: {name}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    """Registers the cog with the bot."""
    await bot.add_cog(AdminCommands(bot))
