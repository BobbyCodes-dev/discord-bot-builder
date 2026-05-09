FEATURE_ID = "server_stats"
FEATURE_NAME = "Server Stats"
CATEGORY = "Utility"
DESCRIPTION = "Server statistics: member growth, voice activity, message counts, channel stats"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class ServerStatsCog(commands.Cog):
    """Server-level statistics tracking."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/server_stats.json")
        self._stats = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._stats = json.loads(self.data_file.read_text())
        except Exception:
            self._stats = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._stats, indent=2))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        gid = str(message.guild.id)
        cid = str(message.channel.id)
        today = discord.utils.utcnow().strftime("%Y-%m-%d")

        self._stats.setdefault(gid, {"messages": {}, "channels": {}, "voice": {}, "joins": {}, "leaves": {}})
        self._stats[gid]["messages"].setdefault(today, 0)
        self._stats[gid]["messages"][today] += 1
        self._stats[gid]["channels"].setdefault(cid, 0)
        self._stats[gid]["channels"][cid] += 1

        # Save every 50 messages
        if self._stats[gid]["messages"][today] % 50 == 0:
            self._save()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        gid = str(member.guild.id)
        today = discord.utils.utcnow().strftime("%Y-%m-%d")
        self._stats.setdefault(gid, {"messages": {}, "channels": {}, "voice": {}, "joins": {}, "leaves": {}})
        self._stats[gid]["joins"].setdefault(today, 0)
        self._stats[gid]["joins"][today] += 1
        self._save()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        gid = str(member.guild.id)
        today = discord.utils.utcnow().strftime("%Y-%m-%d")
        self._stats.setdefault(gid, {"messages": {}, "channels": {}, "voice": {}, "joins": {}, "leaves": {}})
        self._stats[gid]["leaves"].setdefault(today, 0)
        self._stats[gid]["leaves"][today] += 1
        self._save()

    @commands.hybrid_command(name="stats", description="Server statistics")
    async def stats(self, ctx, days: int = 7):
        gid = str(ctx.guild.id)
        guild_stats = self._stats.get(gid, {})

        if not guild_stats:
            await ctx.send("No stats collected yet.", delete_after=10)
            return

        now = discord.utils.utcnow()
        date_range = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

        total_msgs = sum(guild_stats.get("messages", {}).get(d, 0) for d in date_range)
        total_joins = sum(guild_stats.get("joins", {}).get(d, 0) for d in date_range)
        total_leaves = sum(guild_stats.get("leaves", {}).get(d, 0) for d in date_range)

        embed = discord.Embed(title=f"📊 {ctx.guild.name} Stats", description=f"Last {days} days", color=discord.Color.blue())
        embed.add_field(name="Messages", value=f"{total_msgs:,}", inline=True)
        embed.add_field(name="Joins", value=f"{total_joins:,}", inline=True)
        embed.add_field(name="Leaves", value=f"{total_leaves:,}", inline=True)
        embed.add_field(name="Members Now", value=f"{ctx.guild.member_count:,}", inline=True)
        embed.add_field(name="Channels", value=str(len(ctx.guild.channels)), inline=True)

        # Top channels
        channel_stats = guild_stats.get("channels", {})
        if channel_stats:
            top_ch = sorted(channel_stats.items(), key=lambda x: x[1], reverse=True)[:3]
            top_lines = [f"<#{cid}>: {count:,} msgs" for cid, count in top_ch]
            embed.add_field(name="Top Channels", value="\n".join(top_lines), inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerStatsCog(bot))
'''
