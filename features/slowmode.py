FEATURE_ID = "slowmode"
FEATURE_NAME = "Slowmode"
CATEGORY = "Moderation"
DESCRIPTION = "Set channel slowmode delay quickly"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class SlowmodeCog(commands.Cog):
    """Channel slowmode management."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="slowmode", description="Set channel slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int, channel: discord.TextChannel = None):
        target = channel or ctx.channel
        if seconds < 0 or seconds > 21600:
            await ctx.send("Slowmode must be between 0 and 21600 seconds (6 hours).", delete_after=10)
            return

        await target.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send(f"⏩ Slowmode disabled in {target.mention}.")
        else:
            mins, secs = divmod(seconds, 60)
            hrs, mins = divmod(mins, 60)
            parts = []
            if hrs:
                parts.append(f"{hrs}h")
            if mins:
                parts.append(f"{mins}m")
            if secs:
                parts.append(f"{secs}s")
            await ctx.send(f"⏱️ Slowmode set to **{' '.join(parts)}** in {target.mention}.")

    @commands.hybrid_command(name="slowmodeoff", description="Disable slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmodeoff(self, ctx, channel: discord.TextChannel = None):
        target = channel or ctx.channel
        await target.edit(slowmode_delay=0)
        await ctx.send(f"⏩ Slowmode disabled in {target.mention}.")

async def setup(bot):
    await bot.add_cog(SlowmodeCog(bot))
'''
