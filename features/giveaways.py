FEATURE_ID = "giveaways"
FEATURE_NAME = "Giveaways"
CATEGORY = "Fun"
DESCRIPTION = "Create giveaways with reaction entry, auto-pick winners, DMs"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class GiveawaysCog(commands.Cog):
    """Giveaway system with auto winner selection."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/giveaways.json")
        self._giveaways = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._giveaways = json.loads(self.data_file.read_text())
        except Exception:
            self._giveaways = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._giveaways, indent=2))

    @commands.hybrid_command(name="giveaway", description="Create/manage giveaways")
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, action: str, duration: str = None, winners: int = 1, *, prize: str = None):
        if action.lower() == "create":
            if not duration or not prize:
                await ctx.send("Usage: /giveaway create <duration> <winners> <prize>\nExample: /giveaway create 1h 1 Nitro Classic", delete_after=30)
                return

            # Parse duration: 30s, 10m, 2h, 1d
            dur_secs = 0
            dur_str = duration.lower()
            if dur_str.endswith("s"):
                dur_secs = int(dur_str[:-1])
            elif dur_str.endswith("m"):
                dur_secs = int(dur_str[:-1]) * 60
            elif dur_str.endswith("h"):
                dur_secs = int(dur_str[:-1]) * 3600
            elif dur_str.endswith("d"):
                dur_secs = int(dur_str[:-1]) * 86400
            else:
                await ctx.send("Invalid duration. Use: 30s, 10m, 2h, 1d", delete_after=10)
                return

            end_time = discord.utils.utcnow() + timedelta(seconds=dur_secs)

            embed = discord.Embed(title=f"🎉 GIVEAWAY: {prize}", description=f"React with 🎉 to enter!\n\n**Winners:** {winners}\n**Ends:** {discord.utils.format_dt(end_time, 'R')}", color=discord.Color.gold())
            embed.set_footer(text=f"Hosted by {ctx.author.display_name}")
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("🎉")
            await ctx.message.delete()

            self._giveaways[str(msg.id)] = {
                "channel_id": ctx.channel.id,
                "guild_id": ctx.guild.id,
                "prize": prize,
                "winners": winners,
                "end_time": end_time.isoformat(),
                "host_id": ctx.author.id,
                "message_id": msg.id,
            }
            self._save()

            # Schedule winner selection
            await asyncio.sleep(dur_secs)
            await self._end_giveaway(msg.id)

        elif action.lower() == "list":
            active = [v for v in self._giveaways.values() if v["guild_id"] == ctx.guild.id]
            if not active:
                await ctx.send("No active giveaways.", delete_after=10)
                return
            lines = [f"**{g['prize']}** — <t:{int(datetime.fromisoformat(g['end_time']).timestamp())}:R>" for g in active]
            await ctx.send("\n".join(lines))

    async def _end_giveaway(self, message_id):
        gid = str(message_id)
        if gid not in self._giveaways:
            return
        gw = self._giveaways.pop(gid)
        self._save()

        channel = self.bot.get_channel(gw["channel_id"])
        if not channel:
            return

        try:
            msg = await channel.fetch_message(message_id)
        except Exception:
            return

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if not reaction:
            await channel.send(f"🎉 **{gw['prize']}** — No entries!")
            return

        users = [u async for u in reaction.users() if not u.bot]
        if not users:
            await channel.send(f"🎉 **{gw['prize']}** — No valid entries!")
            return

        winner_count = min(gw["winners"], len(users))
        winners = random.sample(users, winner_count)

        winner_mentions = ", ".join(w.mention for w in winners)
        embed = discord.Embed(title=f"🎉 Giveaway Ended: {gw['prize']}", description=f"**Winner{'s' if len(winners)>1 else ''}:** {winner_mentions}\n\nCongratulations! 🎊", color=discord.Color.green())
        await channel.send(embed=embed)

        # DM winners
        for winner in winners:
            try:
                await winner.send(f"🎉 Congratulations! You won **{gw['prize']}** in the giveaway on **{channel.guild.name}**!")
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_ready(self):
        # Restore active giveaways
        for gid, gw in self._giveaways.items():
            end_time = datetime.fromisoformat(gw["end_time"])
            remaining = (end_time - discord.utils.utcnow()).total_seconds()
            if remaining > 0:
                self.bot.loop.create_task(self._schedule_end(int(gid), remaining))

    async def _schedule_end(self, message_id, seconds):
        await asyncio.sleep(max(seconds, 1))
        await self._end_giveaway(message_id)

async def setup(bot):
    await bot.add_cog(GiveawaysCog(bot))
'''
