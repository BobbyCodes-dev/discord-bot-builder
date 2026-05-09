FEATURE_ID = "lockdown"
FEATURE_NAME = "Server Lockdown"
CATEGORY = "Moderation"
DESCRIPTION = "Lock/unlock channels — prevent messages during emergencies"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class LockdownCog(commands.Cog):
    """Channel/server lockdown system."""

    def __init__(self, bot):
        self.bot = bot
        self._locked_channels = {}  # guild_id: {channel_id: old_overwrites}

    @commands.hybrid_command(name="lockdown", description="Lock a channel or the entire server")
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, target: str = "channel"):
        if target.lower() == "channel":
            await self._lock_channel(ctx.channel, ctx.guild)
            await ctx.send(f"🔒 {ctx.channel.mention} has been locked.")

        elif target.lower() == "all" or target.lower() == "server":
            locked = []
            for ch in ctx.guild.text_channels:
                await self._lock_channel(ch, ctx.guild)
                locked.append(ch.mention)
            await ctx.send(f"🔒 Server locked! Locked {len(locked)} channels.")

    @commands.hybrid_command(name="unlock", description="Unlock a channel or server")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, target: str = "channel"):
        if target.lower() == "channel":
            await self._unlock_channel(ctx.channel, ctx.guild)
            await ctx.send(f"🔓 {ctx.channel.mention} has been unlocked.")

        elif target.lower() in ("all", "server"):
            gid = str(ctx.guild.id)
            unlocked = 0
            for ch_id in list(self._locked_channels.get(gid, {}).keys()):
                ch = ctx.guild.get_channel(ch_id)
                if ch:
                    await self._unlock_channel(ch, ctx.guild)
                    unlocked += 1
            await ctx.send(f"🔓 Server unlocked! Unlocked {unlocked} channels.")

    async def _lock_channel(self, channel, guild):
        gid = str(guild.id)
        self._locked_channels.setdefault(gid, {})

        if channel.id not in self._locked_channels[gid]:
            old_overwrites = {}
            for target, overwrite in channel.overwrites.items():
                old_overwrites[str(target.id)] = {
                    "send_messages": overwrite.send_messages,
                    "create_public_threads": overwrite.create_public_threads,
                    "create_private_threads": overwrite.create_private_threads,
                }
            self._locked_channels[gid][channel.id] = old_overwrites

        overwrite = channel.overwrites_for(guild.default_role)
        overwrite.send_messages = False
        overwrite.create_public_threads = False
        overwrite.create_private_threads = False
        await channel.set_permissions(guild.default_role, overwrite=overwrite)

    async def _unlock_channel(self, channel, guild):
        gid = str(guild.id)

        if gid in self._locked_channels and channel.id in self._locked_channels[gid]:
            old = self._locked_channels[gid].pop(channel.id)
            overwrite = channel.overwrites_for(guild.default_role)
            overwrite.send_messages = old.get("send_messages", None)
            overwrite.create_public_threads = old.get("create_public_threads", None)
            overwrite.create_private_threads = old.get("create_private_threads", None)
            await channel.set_permissions(guild.default_role, overwrite=overwrite)

async def setup(bot):
    await bot.add_cog(LockdownCog(bot))
'''
