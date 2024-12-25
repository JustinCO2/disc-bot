from discord.ext import commands
from discord import app_commands
import discord
from typing import Optional
from utils.data import add_member, edit_member

class OfficerCommands(commands.Cog):
    """Officer commands for managing members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_officer(self, interaction: discord.Interaction) -> bool:
        allowed_roles = [
            1248807669117227059,  # leader
            1248807293018046596,  # officer
            1243099655223513098,  # mod
            1244616887250456577   # codeman
        ]
        return any(role.id in allowed_roles for role in interaction.user.roles)

    @app_commands.command()
    async def add_member(
        self,
        interaction: discord.Interaction,
        name: str,
        guild: str,
        rvd: Optional[int] = 0,
        aod: Optional[int] = 0,
        la: Optional[int] = 0
    ):
        if not self.is_officer(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            await add_member(name, guild, rvd, aod, la)
            await interaction.response.send_message(f"Successfully added {name} to {guild}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command()
    async def edit_member(
        self,
        interaction: discord.Interaction,
        name: str,
        param: str,
        new_value: str
    ):
        if not self.is_officer(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            if param in ["rvd", "aod", "la"]:
                new_value = int(new_value)

            await edit_member(name, param, new_value)
            await interaction.response.send_message(f"Successfully updated {param} for member: {name}")
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(OfficerCommands(bot))
