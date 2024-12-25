from discord.ext import commands
from discord import app_commands
import discord
from typing import Optional
from utils.data import submit_dmg, submit_relics, update_member_data

class MemberCommands(commands.Cog):
    """Member commands for submitting damage and relic requests."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()
    async def submit_dmg(
        self,
        interaction: discord.Interaction,
        member: str,
        boss: str,
        damage: int,
        attachment: discord.Attachment
    ):
        """Submit damage for verification."""
        try:
            result = await submit_dmg(member, boss, damage, attachment.url)

            verification_channel = interaction.guild.get_channel(int(result["verification_channel_id"]))
            if not verification_channel:
                await interaction.response.send_message("Verification channel not found.", ephemeral=True)
                return

            embed = discord.Embed(
                title="Damage Submission",
                description=f"**Member:** {member}\n**Boss:** {boss}\n**Damage:** {damage}",
                color=discord.Color.blue()
            )
            embed.set_image(url=attachment.url)
            embed.set_footer(text=f"Submitted by {interaction.user.display_name}")

            message = await verification_channel.send(embed=embed)
            await message.add_reaction("\u2705")  # :check:
            await message.add_reaction("\u274C")  # :x:

            await interaction.response.send_message("Damage update submitted for verification!", ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command()
    async def submit_relics(
        self,
        interaction: discord.Interaction,
        member: str,
        attachment: discord.Attachment
    ):
        """Submit relics for verification."""
        try:
            result = await submit_relics(member, attachment.url)

            verification_channel = interaction.guild.get_channel(int(result["verification_channel_id"]))
            if not verification_channel:
                await interaction.response.send_message("Verification channel not found.", ephemeral=True)
                return

            embed = discord.Embed(
                title="Relic Donation Submission",
                description=f"**Member:** {member}",
                color=discord.Color.gold()
            )
            embed.set_image(url=attachment.url)
            embed.set_footer(text=f"Submitted by {interaction.user.display_name}")

            message = await verification_channel.send(embed=embed)
            await message.add_reaction("\u2705")  # :check:
            await message.add_reaction("\u274C")  # :x:

            await interaction.response.send_message("Relic donation submitted for verification!", ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handle reactions for approval or denial."""
        if user.bot:
            return  # Ignore bot reactions

        message = reaction.message
        if not message.embeds or not message.guild:
            return  # Ignore non-embed messages or messages outside of a guild

        embed = message.embeds[0]
        if reaction.emoji == "\u2705":  # :check:
            if "Damage Submission" in embed.title:
                details = embed.description.split("\n")
                member = details[0].split(":")[1].strip()
                boss = details[1].split(":")[1].strip()
                damage = int(details[2].split(":")[1].strip())

                guild_name = "Some Guild Name"  # Replace this logic to dynamically find the guild
                await update_member_data(guild_name, member, "damages", (boss, damage))
                await message.reply(f"✅ Damage for {member} has been approved and updated.")
            elif "Relic Donation Submission" in embed.title:
                details = embed.description.split("\n")
                member = details[0].split(":")[1].strip()

                guild_name = "Some Guild Name"  # Replace this logic to dynamically find the guild
                await update_member_data(guild_name, member, "last_donation", "2024-12-01")
                await message.reply(f"✅ Relic donation for {member} has been approved and updated.")
        elif reaction.emoji == "\u274C":  # :x:
            await message.reply(f"❌ Submission has been denied.")

async def setup(bot: commands.Bot):
    """Registers the cog with the bot."""
    await bot.add_cog(MemberCommands(bot))
