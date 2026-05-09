FEATURE_ID = "announce"
FEATURE_NAME = "Announcements"
CATEGORY = "Utility"
DESCRIPTION = "Send embed announcements to channels, with role pings"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class AnnounceCog(commands.Cog):
    """Announcement commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="announce", description="Send an announcement")
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx, channel: discord.TextChannel = None, role: discord.Role = None, *, message: str):
        target = channel or ctx.channel
        embed = discord.Embed(title="📢 Announcement", description=message, color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=ctx.guild.name)
        content = role.mention if role else ""
        await target.send(content=content, embed=embed)
        await ctx.message.delete()
        if target != ctx.channel:
            await ctx.send(f"Announcement sent to {target.mention}.", delete_after=5)

async def setup(bot):
    await bot.add_cog(AnnounceCog(bot))
'''
