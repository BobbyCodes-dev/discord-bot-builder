FEATURE_ID = "leveling"
FEATURE_NAME = "Leveling System"
CATEGORY = "Fun"
DESCRIPTION = "XP system with rank cards, leaderboard, and level-up announcements"
ENV_VARS = ["LEVELING_COOLDOWN", "LEVELING_XP_MIN", "LEVELING_XP_MAX"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class LevelingCog(commands.Cog):
    """XP-based leveling system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/leveling.json")
        self.cooldown = int(os.getenv("LEVELING_COOLDOWN", "60"))
        self.xp_min = int(os.getenv("LEVELING_XP_MIN", "15"))
        self.xp_max = int(os.getenv("LEVELING_XP_MAX", "25"))
        self._last_xp = {}

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            return json.loads(self.data_file.read_text())
        except Exception:
            return {}

    def _save(self, data):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(data, indent=2))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        now = time.time()
        uid = str(message.author.id)
        gid = str(message.guild.id)

        if uid in self._last_xp and now - self._last_xp[uid] < self.cooldown:
            return
        self._last_xp[uid] = now

        data = self._load()
        data.setdefault(gid, {})
        data[gid].setdefault(uid, {"xp": 0, "level": 0, "msgs": 0})

        gained = random.randint(self.xp_min, self.xp_max)
        data[gid][uid]["xp"] += gained
        data[gid][uid]["msgs"] += 1

        new_lvl = int(data[gid][uid]["xp"] ** 0.4)
        if new_lvl > data[gid][uid]["level"]:
            data[gid][uid]["level"] = new_lvl
            await message.channel.send(f"🎉 {message.author.mention} reached **Level {new_lvl}**!")

        self._save(data)

    @commands.hybrid_command(name="rank", description="Check your level")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = self._load()
        gid = str(ctx.guild.id)
        stats = data.get(gid, {}).get(str(member.id), {"xp": 0, "level": 0, "msgs": 0})
        embed = discord.Embed(title=f"Rank: {member.display_name}", color=member.color)
        embed.add_field(name="Level", value=str(stats["level"]), inline=True)
        embed.add_field(name="XP", value=str(stats["xp"]), inline=True)
        embed.add_field(name="Messages", value=str(stats["msgs"]), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top"], description="Server XP leaderboard")
    async def leaderboard(self, ctx):
        data = self._load()
        gid = str(ctx.guild.id)
        guild_data = data.get(gid, {})
        top = sorted(guild_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

        lines = []
        for i, (uid, stats) in enumerate(top, 1):
            lines.append(f"**#{i}** <@{uid}> — Level {stats['level']} ({stats['xp']} XP)")

        embed = discord.Embed(title=f"🏆 {ctx.guild.name} Leaderboard", description="\n".join(lines) or "No data yet.", color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelingCog(bot))
'''
