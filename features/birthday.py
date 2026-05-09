FEATURE_ID = "birthday"
FEATURE_NAME = "Birthday System"
CATEGORY = "Fun"
DESCRIPTION = "Set birthdays, get automatic announcements, birthday list"
ENV_VARS = ["BIRTHDAY_CHANNEL_ID"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class BirthdayCog(commands.Cog):
    """Birthday tracking and announcements."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/birthdays.json")
        self.birthday_channel_id = int(os.getenv("BIRTHDAY_CHANNEL_ID", "0"))
        self._birthdays = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._birthdays = json.loads(self.data_file.read_text())
        except Exception:
            self._birthdays = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._birthdays, indent=2))

    @commands.hybrid_command(name="birthday", description="Set your birthday")
    async def birthday(self, ctx, date: str):
        """Set birthday in MM-DD format."""
        try:
            datetime.strptime(date, "%m-%d")
        except ValueError:
            await ctx.send("Invalid format. Use MM-DD (e.g., 03-15 for March 15)", delete_after=10)
            return

        uid = str(ctx.author.id)
        self._birthdays[uid] = {"date": date, "username": str(ctx.author)}
        self._save()
        await ctx.send(f"🎂 Birthday set to **{date}**! I'll announce it on that day.")

    @commands.hybrid_command(name="birthdays", description="List upcoming birthdays")
    async def birthdays_list(self, ctx):
        if not self._birthdays:
            await ctx.send("No birthdays registered yet.", delete_after=10)
            return

        today = discord.utils.utcnow()
        upcoming = []
        for uid, data in self._birthdays.items():
            month, day = map(int, data["date"].split("-"))
            bday_this_year = today.replace(month=month, day=day)
            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)
            days_left = (bday_this_year - today).days % 365
            upcoming.append((days_left, data["username"], data["date"]))

        upcoming.sort()
        lines = [f"**{username}** — {date} ({days}d away)" if days > 0 else f"**{username}** — {date} (🎉 TODAY!)" for days, username, date in upcoming[:20]]

        embed = discord.Embed(title="🎂 Birthdays", description="\n".join(lines), color=discord.Color.pink())
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self._birthday_loop())

    async def _birthday_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = discord.utils.utcnow()
                today_str = now.strftime("%m-%d")

                for uid, data in self._birthdays.items():
                    if data["date"] == today_str:
                        channel = self.bot.get_channel(self.birthday_channel_id)
                        if channel:
                            embed = discord.Embed(
                                title="🎂 Happy Birthday!",
                                description=f"Everyone wish <@{uid}> a happy birthday! 🎉🎊",
                                color=discord.Color.gold(),
                            )
                            await channel.send(embed=embed)
                        user = self.bot.get_user(int(uid))
                        if user:
                            try:
                                await user.send(f"🎂 Happy Birthday! Hope you have an amazing day!")
                            except discord.Forbidden:
                                pass

                # Check once per hour
                await asyncio.sleep(3600)
            except Exception:
                await asyncio.sleep(3600)

async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))
'''
