from discord.ext import commands
from discord import app_commands
import discord
import logging
from typing import Optional
from utils.data import (
    submit_dmg,
    submit_relics,
    update_member_data,
    find_guild_by_member,
    find_guild_by_channel,
    parse_damage_input
)
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

# MongoDB connection setup
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_bot"]

def format_damage(damage) -> str:
    if isinstance(damage, tuple):
        damage = damage[0]  

    if not isinstance(damage, (int, float)):
        raise TypeError(f"Invalid damage type: {type(damage)} expected int or float")

    if damage >= 1:
        return f"{damage / 1_000_000_000:.2f}B"
    return str(damage)


async def member_autocomplete(interaction: discord.Interaction, current: str):
    """Provide autocomplete for members."""
    print(f"Autocomplete triggered. Input: '{current}'")
    try:
        # Fetch members from MongoDB
        guilds = await db.guilds.find().to_list(None)
        members = [
            member for guild in guilds
            for member in guild.get("members", {}).keys()
        ]
        return [
            app_commands.Choice(name=member, value=member)
            for member in members if current.lower() in member.lower()
        ]
    except Exception as e:
        print(f"Error in member_autocomplete: {e}")
        return []

async def boss_autocomplete(interaction: discord.Interaction, current: str):
    bosses = ["la", "rvd", "aod"]
    return [
        app_commands.Choice(name=boss, value=boss)
        for boss in bosses if current.lower() in boss.lower()
    ]

class MemberCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pending_updates = {}
        logger.info("MemberCommands cog initialized")

    @app_commands.guilds(discord.Object(id=1140429772531449886))
    @app_commands.command(name="submit_dmg", description="Submit damage image for verification")
    @app_commands.autocomplete(member=member_autocomplete, boss=boss_autocomplete)
    async def submit_dmg_command(
        self,
        interaction: discord.Interaction,
        member: str,
        boss: str,
        damage: str,
        attachment: discord.Attachment
    ):
        logger.info(f"submit_dmg invoked by {interaction.user.display_name}")
        try:
            # Parse damage input
            parsed_damage = parse_damage_input(damage)

            # Use the submit_dmg utility to prepare the submission
            submission = await submit_dmg(member, boss, parsed_damage, attachment.url)

            # Get the verification channel
            verification_channel = interaction.guild.get_channel(
                int(submission["verification_channel_id"])
            )
            if not verification_channel:
                logger.warning("Verification channel not found")
                await interaction.response.send_message(
                    "Verification channel not found.", ephemeral=True
                )
                return

            # Create and send embed
            embed = discord.Embed(
                title="Damage Submission",
                description=f"**Member:** {member}\n**Boss:** {boss}\n**Damage:** {parsed_damage / 1e9:.2f}B",
                color=discord.Color.blue()
            )
            embed.set_image(url=attachment.url)
            embed.set_footer(text=f"Submitted by {interaction.user.display_name}")

            message = await verification_channel.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            # Store pending update
            guild_name = await find_guild_by_member(member)
            self.pending_updates[message.id] = {
                'type': 'damage',
                'guild': guild_name,
                'member': member,
                'field': 'damages',
                'value': (boss, parsed_damage)
            }

            logger.info(f"Damage submission created with message ID: {message.id}")
            await interaction.response.send_message(
                "Damage update submitted for verification!", ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error in submit_dmg: {e}", exc_info=True)
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reactions to verification messages."""
        if payload.user_id == self.bot.user.id:
            return

        # Check if this message is pending verification
        update_info = self.pending_updates.get(payload.message_id)
        if not update_info:
            return

        # Get the message
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # Process the reaction
        if str(payload.emoji) == "✅":
            try:
                # Extract information
                guild_name = update_info['guild']
                member = update_info['member']
                field = update_info['field']
                value = update_info['value']

                # Use update_member_data utility to process the update
                await update_member_data(guild_name, member, field, value)
                logger.info(f"Update approved for {member} in {guild_name}")

                # Delete the verification message
                await message.delete()
                # Remove from pending updates
                del self.pending_updates[payload.message_id]

                new_val = format_damage(value)

                await channel.send(
                f"Successfully updated damage for: {member} to: {new_val}"
            )

            except Exception as e:
                logger.error(f"Error processing verification: {e}", exc_info=True)
                await channel.send(
                    f"Error processing verification: {e}", delete_after=10
                )

        elif str(payload.emoji) == "❌":
            try:
                await message.delete()
                del self.pending_updates[payload.message_id]
                logger.info(f"Submission rejected for {update_info['member']}")
            except Exception as e:
                logger.error(f"Error processing rejection: {e}", exc_info=True)

async def setup(bot: commands.Bot):
    logger.info("Setting up MemberCommands cog")
    await bot.add_cog(MemberCommands(bot))
    logger.info("MemberCommands cog setup complete")
