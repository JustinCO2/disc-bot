import discord
from discord.ext import commands, tasks
import json
from typing import Dict
import logging

logger = logging.getLogger('discord')

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = {}
        self.update_leaderboards.start()

    def format_damage(self, damage: int) -> str:
        if damage >= 1_000_000: return f"{damage/1_000_000:.1f}M"
        return str(damage)

    def format_leaderboard(self, guild_name: str, guild_data: Dict) -> str:
        widths = {
            'idx': 2,
            'member': 12,
            'rvd': 8,
            'aod': 8,
            'la': 8
        }
        
        output = ["```"]
        
        # Header
        header = (f"{guild_name} Damage Leaderboard\n\n"
                 f"{'#':<{widths['idx']}} | "
                 f"{'Member':<{widths['member']}} | "
                 f"{'RVD':<{widths['rvd']}} | "
                 f"{'AOD':<{widths['aod']}} | "
                 f"{'LA':<{widths['la']}}")
        output.append(header)
        
        # Separator
        separator = '-' * (sum(widths.values()) + 12)
        output.append(separator)
        
        # Sort members by total damage
        sorted_members = sorted(
            guild_data["members"].items(),
            key=lambda x: sum(x[1]["damages"].values()),
            reverse=True
        )
        
        # Member rows
        for idx, (member, data) in enumerate(sorted_members, 1):
            damages = data["damages"]
            row = (f"{idx:<{widths['idx']}} | "
                  f"{member[:12]:<{widths['member']}} | "
                  f"{self.format_damage(damages['rvd']):<{widths['rvd']}} | "
                  f"{self.format_damage(damages['aod']):<{widths['aod']}} | "
                  f"{self.format_damage(damages['la']):<{widths['la']}}")
            output.append(row)
            
        output.append("```")
        return '\n'.join(output)

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

                content = self.format_leaderboard(guild_name, guild_data)
                message = await channel.send(content)
                self.messages[guild_name] = message.id
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
            
            if guild_name not in self.messages:
                message = await channel.send(content)
                self.messages[guild_name] = message.id
                logger.info(f"Created new leaderboard for {guild_name}")
                return

            try:
                message = await channel.fetch_message(self.messages[guild_name])
                await message.edit(content=content)
                logger.info(f"Updated leaderboard for {guild_name}")
            except discord.NotFound:
                message = await channel.send(content)
                self.messages[guild_name] = message.id
                logger.info(f"Recreated leaderboard for {guild_name}")
                
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