FEATURE_ID = "nuke"
FEATURE_NAME = "Nuke Channel"
CATEGORY = "Moderation"
DESCRIPTION = "Clone and delete a channel — 'nuke' it clean"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class NukeCog(commands.Cog):
    """Channel nuke (clone + delete)."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="nuke", description="Nuke a channel (clone and delete)")
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx, channel: discord.TextChannel = None):
        target = channel or ctx.channel

        if channel and channel != ctx.channel:
            confirm_msg = await ctx.send(f"⚠️ Are you sure you want to nuke {target.mention}? This will delete ALL messages. Reply `yes` within 30 seconds.")
            try:
                response = await self.bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                if response.content.lower() != "yes":
                    await ctx.send("Cancelled.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("Timed out.")
                return

        # Clone the channel
        new_ch = await target.clone(reason=f"Nuked by {ctx.author}")
        # Move to same position
        await new_ch.edit(position=target.position)

        # Delete original
        await target.delete(reason=f"Nuked by {ctx.author}")

        # Send nuke message in new channel
        embed = discord.Embed(
            title="💥 Channel Nuked",
            description=f"This channel was nuked by {ctx.author.mention}.\n\n*Sometimes a fresh start is needed.*",
            color=discord.Color.dark_red(),
        )
        await new_ch.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NukeCog(bot))
'''
