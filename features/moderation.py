FEATURE_ID = "moderation"
FEATURE_NAME = "Moderation"
CATEGORY = "Moderation"
DESCRIPTION = "Kick, ban, unban, mute, warn, purge commands"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class ModerationCog(commands.Cog):
    """Kick, ban, unban, mute, warn, purge commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick a member")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member}.", delete_after=10)

    @commands.hybrid_command(name="ban", description="Ban a member")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        await member.ban(reason=reason, delete_message_days=1)
        await ctx.send(f"Banned {member}.", delete_after=10)

    @commands.hybrid_command(name="unban", description="Unban a user by name")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user_name: str):
        bans = [entry async for entry in ctx.guild.bans()]
        for entry in bans:
            if entry.user.name.lower() == user_name.lower() or f"{entry.user.name}#{entry.user.discriminator}".lower() == user_name.lower():
                await ctx.guild.unban(entry.user)
                await ctx.send(f"Unbanned {entry.user}.", delete_after=10)
                return
        await ctx.send("User not found in ban list.", delete_after=10)

    @commands.hybrid_command(name="mute", description="Timeout a member")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, minutes: int = 10, *, reason: str = "No reason"):
        dur = timedelta(minutes=minutes)
        await member.timeout(dur, reason=reason)
        await ctx.send(f"Muted {member} for {minutes} minutes.", delete_after=10)

    @commands.hybrid_command(name="unmute", description="Remove timeout from a member")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        await member.timeout(None)
        await ctx.send(f"Unmuted {member}.", delete_after=10)

    @commands.hybrid_command(name="warn", description="Warn a member via DM")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        embed = discord.Embed(title=f"Warning from {ctx.guild.name}", description=reason, color=discord.Color.orange())
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass
        await ctx.send(f"Warned {member}.", delete_after=10)

    @commands.hybrid_command(name="purge", aliases=["clean", "clear"], description="Delete messages")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        deleted = await ctx.channel.purge(limit=min(amount + 1, 200))
        await ctx.send(f"Deleted {len(deleted)-1} messages.", delete_after=5)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
'''
