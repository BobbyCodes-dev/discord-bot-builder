FEATURE_ID = "server_info"
FEATURE_NAME = "Server Info"
CATEGORY = "Utility"
DESCRIPTION = "Detailed server information with stats, emojis, boosts, features"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class ServerInfoCog(commands.Cog):
    """Detailed server information."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="serverinfo", aliases=["si"], description="Show server info")
    async def serverinfo(self, ctx):
        g = ctx.guild
        embed = discord.Embed(title=g.name, description=f"**ID:** {g.id}\n**Owner:** <@{g.owner_id}>\n**Created:** {discord.utils.format_dt(g.created_at, 'D')} ({discord.utils.format_dt(g.created_at, 'R')})", color=discord.Color.blue())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)

        # Stats
        total_members = g.member_count
        humans = len([m for m in g.members if not m.bot]) if hasattr(g, 'members') else "?"
        bots = len([m for m in g.members if m.bot]) if hasattr(g, 'members') else "?"

        embed.add_field(name="Members", value=f"**{total_members}** total\n{humans} humans, {bots} bots", inline=True)
        embed.add_field(name="Channels", value=f"**{len(g.text_channels)}** text\n**{len(g.voice_channels)}** voice\n{len(g.categories)} categories", inline=True)
        embed.add_field(name="Roles", value=str(len(g.roles)), inline=True)
        embed.add_field(name="Boost", value=f"Level **{g.premium_tier}** ({g.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="Emojis", value=f"**{len(g.emojis)}** / {g.emoji_limit * 2}" if g.emoji_limit else str(len(g.emojis)), inline=True)
        embed.add_field(name="Stickers", value=f"**{len(g.stickers)}** / {g.sticker_limit}" if g.sticker_limit else str(len(g.stickers)), inline=True)

        # Features
        if g.features:
            features = ", ".join(f.replace("_", " ").title() for f in g.features[:10])
            embed.add_field(name="Features", value=features, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfoCog(bot))
'''
