from discord.ext import commands
from discord import app_commands
import discord
from typing import Optional
from utils.data import create_guild, edit_guild

class AdminCommands(commands.Cog):
    """Admin commands for managing guilds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def has_permissions(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        if any(role.id == 1244616887250456577 for role in interaction.user.roles):
            return True

        print(f"Permission denied for user {interaction.user.display_name} ({interaction.user.id}).")
        return False


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
