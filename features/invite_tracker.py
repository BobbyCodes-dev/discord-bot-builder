FEATURE_ID = "invite_tracker"
FEATURE_NAME = "Invite Tracker"
CATEGORY = "Utility"
DESCRIPTION = "Track who invited whom with invite leaderboard"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class InviteTrackerCog(commands.Cog):
    """Invite tracking system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/invites.json")
        self._invites = {}
        self._invite_data = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(self.data_file.read_text())
            self._invites = data.get("invites", {})
            self._invite_data = data.get("data", {})
        except Exception:
            self._invites = {}
            self._invite_data = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps({
            "invites": self._invites,
            "data": self._invite_data,
        }, indent=2))

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self._invites[str(guild.id)] = {}
            try:
                invites = await guild.invites()
                for inv in invites:
                    self._invites[str(guild.id)][inv.code] = inv.uses
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        gid = str(guild.id)

        try:
            current_invites = await guild.invites()
        except discord.Forbidden:
            return

        old_invites = self._invites.get(gid, {})

        # Find the invite whose uses increased
        for inv in current_invites:
            if inv.code in old_invites and inv.uses > old_invites[inv.code]:
                # Store who invited who
                self._invite_data.setdefault(gid, {})
                self._invite_data[gid].setdefault(str(inv.inviter.id) if inv.inviter else "unknown", {"count": 0, "invited": []})
                key = str(inv.inviter.id) if inv.inviter else "unknown"
                self._invite_data[gid][key]["count"] += 1
                self._invite_data[gid][key]["invited"].append(str(member.id))
                self._save()

                if inv.inviter:
                    try:
                        await inv.inviter.send(f"📨 {member} joined **{guild.name}** using your invite!")
                    except discord.Forbidden:
                        pass
                break

        # Update cache
        self._invites[gid] = {}
        for inv in current_invites:
            self._invites[gid][inv.code] = inv.uses

    @commands.hybrid_command(name="invites", description="Check your invite stats")
    async def invites(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        gid = str(ctx.guild.id)
        data = self._invite_data.get(gid, {}).get(str(member.id), {"count": 0, "invited": []})

        embed = discord.Embed(title=f"📨 Invites: {member.display_name}", description=f"**{data['count']}** people invited", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="invlb", description="Invite leaderboard")
    async def invlb(self, ctx):
        gid = str(ctx.guild.id)
        data = self._invite_data.get(gid, {})

        if not data:
            await ctx.send("No invite data yet.", delete_after=10)
            return

        sorted_users = sorted(data.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
        lines = [f"**#{i}** <@{uid}> — {info['count']} invites" for i, (uid, info) in enumerate(sorted_users, 1)]

        embed = discord.Embed(title=f"🏆 {ctx.guild.name} Invite Leaderboard", description="\n".join(lines), color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InviteTrackerCog(bot))
'''
