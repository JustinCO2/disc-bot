import discord
from discord.ext import commands, tasks
import json
from typing import Dict
import logging
import os

logger = logging.getLogger('discord')

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = self.load_message_ids()
        self.update_leaderboards.start()

    def load_message_ids(self) -> Dict:
        """Load saved message IDs from JSON file."""
        try:
            if os.path.exists('data/leaderboard_messages.json'):
                with open('data/leaderboard_messages.json', 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading leaderboard_messages.json: {e}")
            return {}

    def save_message_ids(self):
        """Save message IDs to JSON file."""
        try:
            with open('data/leaderboard_messages.json', 'w') as f:
                json.dump(self.messages, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving leaderboard_messages.json: {e}")

    def format_damage(self, damage: int) -> str:
        if damage >= 1_000_000_000: return f"{damage/1_000_000_000:.2f}B"
        return str(damage)

    def format_leaderboard(self, guild_name: str, guild_data: Dict) -> str:
        # Column widths
        member_col_width = 7
        rvd_col_width = 5
        aod_col_width = 5
        la_col_width = 5

        # Build leaderboard string
        leaderboard = ["```"]

        # Header
        leaderboard.append(f"{guild_name} DMG Board\n")
        leaderboard.append(f"{'#':<2} │ {'Members':<{member_col_width}} │ {'RVD':>{rvd_col_width}} │ {'AOD':>{aod_col_width}} │ {'LA':>{la_col_width}}")
        leaderboard.append('─' * (2 + 3 + member_col_width + 3 + rvd_col_width + 3 + aod_col_width + 3 + la_col_width))

        # Sort members by total damage
        sorted_members = sorted(
            guild_data["members"].items(),
            key=lambda x: sum(x[1]["damages"].values()),
            reverse=True
        )

        # Rows
        for idx, (member, data) in enumerate(sorted_members, 1):
            damages = data["damages"]
            leaderboard.append(
                f"{idx:<2} │ {member[:member_col_width]:<{member_col_width}} │ "
                f"{self.format_damage(damages['rvd']):>{rvd_col_width}} │ "
                f"{self.format_damage(damages['aod']):>{aod_col_width}} │ "
                f"{self.format_damage(damages['la']):>{la_col_width}}"
            )

        leaderboard.append("```")
        return "\n".join(leaderboard)

    async def load_guilds(self) -> Dict:
        try:
            with open('data/guilds.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading guilds.json: {e}")
            return {}

    async def initialize_leaderboards(self):
        logger.info("Initializing leaderboards...")
        guilds = await self.load_guilds()
        
        for guild_name, guild_data in guilds.items():
            try:
                channel_id = int(guild_data["channels"]["leaderboard"])
                channel = self.bot.get_channel(channel_id)
                
                if not channel:
                    logger.error(f"Could not find channel {channel_id} for guild {guild_name}")
                    continue

                # Try to fetch existing message first
                if guild_name in self.messages:
                    try:
                        await channel.fetch_message(int(self.messages[guild_name]))
                        logger.info(f"Found existing leaderboard for {guild_name}")
                        continue
                    except (discord.NotFound, discord.HTTPException):
                        logger.info(f"Stored message for {guild_name} not found, creating new one")

                content = self.format_leaderboard(guild_name, guild_data)
                message = await channel.send(content)
                self.messages[guild_name] = str(message.id)
                self.save_message_ids()
                logger.info(f"Created leaderboard for {guild_name} in channel {channel_id}")
                
            except Exception as e:
                logger.error(f"Error creating leaderboard for {guild_name}: {e}")

    async def update_guild_leaderboard(self, guild_name: str, guild_data: Dict):
        try:
            channel_id = int(guild_data["channels"]["leaderboard"])
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logger.error(f"Channel {channel_id} not found for {guild_name}")
                return

            content = self.format_leaderboard(guild_name, guild_data)
            
            message = None
            if guild_name in self.messages:
                try:
                    message = await channel.fetch_message(int(self.messages[guild_name]))
                except (discord.NotFound, discord.HTTPException):
                    logger.info(f"Stored message for {guild_name} not found, creating new one")
                    message = None

            if message:
                await message.edit(content=content)
                logger.info(f"Updated existing leaderboard for {guild_name}")
            else:
                message = await channel.send(content)
                self.messages[guild_name] = str(message.id)
                self.save_message_ids()
                logger.info(f"Created new leaderboard for {guild_name}")
                
        except Exception as e:
            logger.error(f"Error updating leaderboard for {guild_name}: {e}")

    @tasks.loop(minutes=1)
    async def update_leaderboards(self):
        logger.info("Running scheduled leaderboard update")
        guilds = await self.load_guilds()
        for guild_name, guild_data in guilds.items():
            await self.update_guild_leaderboard(guild_name, guild_data)

    @update_leaderboards.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()
        await self.initialize_leaderboards()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot: return
            
        member_cog = self.bot.get_cog('MemberCommands')
        if not member_cog or reaction.message.id not in member_cog.pending_updates:
            return
            
        check_reactions = discord.utils.get(reaction.message.reactions, emoji="✅")
        if check_reactions and check_reactions.count >= 2:
            update_info = member_cog.pending_updates[reaction.message.id]
            guilds = await self.load_guilds()
            if update_info['guild'] in guilds:
                await self.update_guild_leaderboard(update_info['guild'], guilds[update_info['guild']])

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))