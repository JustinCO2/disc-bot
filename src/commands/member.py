from discord.ext import commands 
from discord import app_commands
import discord
import json
import logging
from typing import Optional
from utils.data import submit_dmg, submit_relics, update_member_data, find_guild_by_member, find_guild_by_channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

class MemberCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pending_updates = {}
        logger.info("MemberCommands cog initialized")
        
    async def cog_load(self):
        logger.info("MemberCommands cog loaded")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        logger.info(f"Reaction detected: {reaction.emoji} by {user}")
        if user.bot:
            return

        message = reaction.message
        if message.id not in self.pending_updates:
            return

        logger.info(f"Processing reaction for message {message.id}")
        check_reactions = discord.utils.get(message.reactions, emoji="✅")
        x_reactions = discord.utils.get(message.reactions, emoji="❌")
        
        check_count = check_reactions.count if check_reactions else 0
        x_count = x_reactions.count if x_reactions else 0
        
        logger.info(f"Reaction counts - ✅: {check_count}, ❌: {x_count}")

        if check_count >= 2:
            update_info = self.pending_updates[message.id]
            try:
                if update_info['type'] == 'damage':
                    await update_member_data(
                        update_info['guild'],
                        update_info['member'],
                        'damages',
                        update_info['data']
                    )
                else:
                    await update_member_data(
                        update_info['guild'],
                        update_info['member'],
                        'last_donation',
                        update_info['data']
                    )
                await message.delete()
                del self.pending_updates[message.id]
                logger.info(f"Update successful for message {message.id}")
            except Exception as e:
                logger.error(f"Error updating data: {e}")
                await message.channel.send(f"Error updating data: {e}")
        elif x_count >= 2:
            await message.delete()
            del self.pending_updates[message.id]
            logger.info(f"Message {message.id} rejected and deleted")

    @app_commands.command(name="submit_dmg", description="Submit damage for verification")
    async def submit_dmg(
        self,
        interaction: discord.Interaction,
        member: str,
        boss: str,
        damage: int,
        attachment: discord.Attachment
    ):
        logger.info(f"submit_dmg invoked by {interaction.user.display_name}")
        try:
            with open('data/guilds.json', 'r') as f:
                guilds = json.load(f)

            guild_name = await find_guild_by_member(member)
            if not guild_name:
                logger.warning(f"Guild not found for member: {member}")
                await interaction.response.send_message("Could not find guild for this member.", ephemeral=True)
                return

            verification_channel_id = guilds[guild_name]["channels"]["verification"]
            verification_channel = interaction.guild.get_channel(int(verification_channel_id))
            if not verification_channel:
                logger.warning(f"Verification channel not found for guild: {guild_name}")
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
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            self.pending_updates[message.id] = {
                'type': 'damage',
                'guild': guild_name,
                'member': member,
                'data': (boss, damage)
            }
            logger.info(f"Damage submission created with message ID: {message.id}")

            await interaction.response.send_message("Damage update submitted for verification!", ephemeral=True)

        except Exception as e:
            logger.error(f"Error in submit_dmg: {e}", exc_info=True)
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    # [submit_relics command implementation remains the same but with added logging]

async def setup(bot: commands.Bot):
    logger.info("Setting up MemberCommands cog")
    await bot.add_cog(MemberCommands(bot))
    logger.info("MemberCommands cog setup complete")