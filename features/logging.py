FEATURE_ID = "logging"
FEATURE_NAME = "Server Logging"
CATEGORY = "Utility"
DESCRIPTION = "Log message edits, deletes, member updates, and channel changes"
ENV_VARS = ["LOG_CHANNEL_ID"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class LoggingCog(commands.Cog):
    """Server event logging."""

    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.getenv("LOG_CHANNEL_ID", "0"))

    async def _log(self, guild, title, description, color=discord.Color.dark_grey()):
        if not self.log_channel_id:
            return
        ch = guild.get_channel(self.log_channel_id)
        if ch:
            embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
            await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.content:
            return
        desc = f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Content:** {message.content[:1000]}"
        await self._log(message.guild, "📤 Message Deleted", desc, discord.Color.red())

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        desc = f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n**Before:** {before.content[:500]}\n**After:** {after.content[:500]}"
        await self._log(before.guild, "📝 Message Edited", desc, discord.Color.yellow())

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            desc = f"**User:** {after.mention}\n**Before:** {before.nick or 'None'}\n**After:** {after.nick or 'None'}"
            await self._log(after.guild, "🏷️ Nickname Changed", desc, discord.Color.purple())
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            parts = []
            if added:
                parts.append(f"**Added:** {', '.join(r.mention for r in added)}")
            if removed:
                parts.append(f"**Removed:** {', '.join(r.mention for r in removed)}")
            if parts:
                desc = f"**User:** {after.mention}\n" + "\n".join(parts)
                await self._log(after.guild, "👤 Roles Updated", desc, discord.Color.blue())

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        desc = f"**Channel:** {channel.mention} ({channel.id})\n**Type:** {str(channel.type)}"
        await self._log(channel.guild, "➕ Channel Created", desc, discord.Color.green())

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        desc = f"**Channel:** #{channel.name} ({channel.id})\n**Type:** {str(channel.type)}"
        await self._log(channel.guild, "➖ Channel Deleted", desc, discord.Color.red())

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))
'''
