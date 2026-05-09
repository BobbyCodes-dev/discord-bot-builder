FEATURE_ID = "reminders"
FEATURE_NAME = "Reminders"
CATEGORY = "Utility"
DESCRIPTION = "Set time-based reminders that DM you when triggered"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class RemindersCog(commands.Cog):
    """Time-based reminder system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/reminders.json")
        self._reminders = []
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._reminders = json.loads(self.data_file.read_text())
        except Exception:
            self._reminders = []

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._reminders, indent=2))

    def _parse_time(self, time_str):
        """Parse '10m', '2h', '1d', '30s' into seconds."""
        time_str = time_str.lower().strip()
        if time_str.endswith("s"):
            return int(time_str[:-1])
        elif time_str.endswith("m"):
            return int(time_str[:-1]) * 60
        elif time_str.endswith("h"):
            return int(time_str[:-1]) * 3600
        elif time_str.endswith("d"):
            return int(time_str[:-1]) * 86400
        return None

    @commands.hybrid_command(name="remind", description="Set a reminder")
    async def remind(self, ctx, time: str, *, message: str = "Reminder!"):
        seconds = self._parse_time(time)
        if seconds is None or seconds < 1 or seconds > 2592000:
            await ctx.send("Invalid time. Use: 30s, 10m, 2h, 1d (max 30 days)", delete_after=10)
            return

        trigger_time = (discord.utils.utcnow() + timedelta(seconds=seconds)).isoformat()

        reminder = {
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "message": message,
            "trigger_at": trigger_time,
        }
        self._reminders.append(reminder)
        self._save()

        await ctx.send(f"⏰ Reminder set! I'll DM you {discord.utils.format_dt(datetime.fromisoformat(trigger_time), 'R')}: **{message[:100]}**", delete_after=30)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self._reminder_loop())

    async def _reminder_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = discord.utils.utcnow()
                to_remove = []

                for i, rem in enumerate(self._reminders):
                    trigger_at = datetime.fromisoformat(rem["trigger_at"])
                    if now >= trigger_at:
                        user = self.bot.get_user(rem["user_id"])
                        if user:
                            try:
                                embed = discord.Embed(title="⏰ Reminder", description=rem["message"], color=discord.Color.gold())
                                embed.set_footer(text=f"Set {discord.utils.format_dt(trigger_at, 'R')}")
                                await user.send(embed=embed)
                            except discord.Forbidden:
                                pass
                        to_remove.append(i)

                if to_remove:
                    self._reminders = [r for i, r in enumerate(self._reminders) if i not in to_remove]
                    self._save()

                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception:
                await asyncio.sleep(30)

    @commands.hybrid_command(name="reminders", description="List your active reminders")
    async def list_reminders(self, ctx):
        user_reminders = [r for r in self._reminders if r["user_id"] == ctx.author.id]
        if not user_reminders:
            await ctx.send("You have no active reminders.", delete_after=10)
            return

        lines = [f"**{r['message'][:80]}** — {discord.utils.format_dt(datetime.fromisoformat(r['trigger_at']), 'R')}" for r in user_reminders]
        embed = discord.Embed(title="⏰ Your Reminders", description="\n".join(lines), color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
'''
