FEATURE_ID = "scheduled_msgs"
FEATURE_NAME = "Scheduled Messages"
CATEGORY = "Utility"
DESCRIPTION = "Schedule messages to be sent at specific times"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class ScheduledMessagesCog(commands.Cog):
    """Schedule messages for future delivery."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/scheduled_msgs.json")
        self._scheduled = []
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._scheduled = json.loads(self.data_file.read_text())
        except Exception:
            self._scheduled = []

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._scheduled, indent=2))

    @commands.hybrid_command(name="schedule", description="Schedule a message")
    @commands.has_permissions(manage_messages=True)
    async def schedule(self, ctx, channel: discord.TextChannel, when: str, *, message: str):
        # Parse human-readable time
        trigger_time = None
        now = discord.utils.utcnow()

        when_lower = when.lower().strip()

        # Tomorrow at X
        if when_lower.startswith("tomorrow"):
            time_part = when_lower.replace("tomorrow", "").strip().replace("at ", "")
            try:
                hour, minute = self._parse_hour_minute(time_part)
                trigger_time = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            except (ValueError, AttributeError):
                pass

        # Next dayname
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in when_lower:
                time_part = when_lower.replace(day, "").strip().replace("at ", "")
                try:
                    hour, minute = self._parse_hour_minute(time_part)
                    target_wd = days.index(day)
                    current_wd = now.weekday()
                    days_ahead = (target_wd - current_wd) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    trigger_time = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                except (ValueError, AttributeError):
                    pass
                break

        # Plain time today
        if not trigger_time:
            for fmt in ["%I:%M%p", "%I%p", "%H:%M", "%I:%M %p"]:
                try:
                    parsed = datetime.strptime(when_lower, fmt)
                    trigger_time = now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
                    if trigger_time < now:
                        trigger_time += timedelta(days=1)
                    break
                except ValueError:
                    continue

        # Relative: in XhXm
        if not trigger_time:
            trigger_time = self._parse_relative(when_lower, now)

        if not trigger_time:
            await ctx.send("Could not parse time. Try: `tomorrow 3pm`, `next monday 9am`, `in 2h`, `14:30`", delete_after=30)
            return

        entry = {
            "channel_id": channel.id,
            "guild_id": ctx.guild.id,
            "message": message[:2000],
            "trigger_at": trigger_time.isoformat(),
            "author_id": ctx.author.id,
        }
        self._scheduled.append(entry)
        self._save()

        await ctx.send(f"📅 Scheduled message in {channel.mention} for {discord.utils.format_dt(trigger_time, 'F')}", delete_after=30)

    def _parse_hour_minute(self, time_str):
        for fmt in ["%I:%M%p", "%I%p", "%H:%M", "%I:%M %p", "%I %p"]:
            try:
                parsed = datetime.strptime(time_str.strip().upper(), fmt)
                return parsed.hour, parsed.minute
            except ValueError:
                continue
        return 9, 0  # Default 9am

    def _parse_relative(self, s, now):
        import re
        total = 0
        m = re.match(r'in\s+(\d+)\s*h', s)
        if m:
            total += int(m.group(1)) * 3600
        m = re.match(r'in\s+(\d+)\s*m', s)
        if m:
            total += int(m.group(1)) * 60
        m = re.match(r'in\s+(\d+)\s*[hH](\d+)\s*[mM]', s)
        if m:
            total = int(m.group(1)) * 3600 + int(m.group(2)) * 60
        if total:
            return now + timedelta(seconds=total)
        return None

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self._check_loop())

    async def _check_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = discord.utils.utcnow()
                to_remove = []

                for i, entry in enumerate(self._scheduled):
                    trigger = datetime.fromisoformat(entry["trigger_at"])
                    if now >= trigger:
                        guild = self.bot.get_guild(entry["guild_id"])
                        if guild:
                            channel = guild.get_channel(entry["channel_id"])
                            if channel:
                                try:
                                    await channel.send(entry["message"])
                                except Exception:
                                    pass
                        to_remove.append(i)

                if to_remove:
                    self._scheduled = [e for i, e in enumerate(self._scheduled) if i not in to_remove]
                    self._save()

                await asyncio.sleep(30)
            except Exception:
                await asyncio.sleep(60)

    @commands.hybrid_command(name="scheduled", description="List scheduled messages")
    @commands.has_permissions(manage_messages=True)
    async def list_scheduled(self, ctx):
        guild_msgs = [e for e in self._scheduled if e["guild_id"] == ctx.guild.id]
        if not guild_msgs:
            await ctx.send("No scheduled messages.", delete_after=10)
            return

        lines = [f"**{e['message'][:60]}** → <#{e['channel_id']}> {discord.utils.format_dt(datetime.fromisoformat(e['trigger_at']), 'R')}" for e in guild_msgs]
        embed = discord.Embed(title="📅 Scheduled Messages", description="\n".join(lines), color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ScheduledMessagesCog(bot))
'''
