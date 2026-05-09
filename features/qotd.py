FEATURE_ID = "qotd"
FEATURE_NAME = "Question of the Day"
CATEGORY = "Fun"
DESCRIPTION = "Automated daily QOTD in configured channels"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class QotdCog(commands.Cog):
    """Question of the Day system."""

    DEFAULT_QUESTIONS = [
        "What's one skill you'd love to master?",
        "If you could live anywhere in the world, where would it be?",
        "What's the best book or movie you've experienced recently?",
        "What's a hobby you've always wanted to try?",
        "What's your favorite way to relax after a long day?",
        "If you could have dinner with any person (living or historical), who?",
        "What's the most useful piece of advice you've ever received?",
        "What's one thing that always makes you smile?",
        "What's your favorite season and why?",
        "If you could only eat one cuisine for the rest of your life, which?",
    ]

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/qotd.json")
        self._config = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            data = json.loads(self.data_file.read_text())
            self._config = data.get("config", {})
            self._questions = data.get("questions", self.DEFAULT_QUESTIONS)
        except Exception:
            self._config = {}
            self._questions = self.DEFAULT_QUESTIONS

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps({"config": self._config, "questions": self._questions}, indent=2))

    @commands.hybrid_command(name="qotd", description="QOTD settings")
    @commands.has_permissions(manage_channels=True)
    async def qotd(self, ctx, action: str, *, arg: str = None):
        gid = str(ctx.guild.id)

        if action.lower() == "set" and arg:
            # Parse channel and optional time
            parts = arg.split()
            channel_id = parts[0].strip("<#>")
            channel = ctx.guild.get_channel(int(channel_id))
            if not channel:
                await ctx.send("Channel not found.", delete_after=10)
                return

            hour = 9
            minute = 0
            if len(parts) >= 2:
                try:
                    time_parts = parts[1].split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                except ValueError:
                    pass

            self._config[gid] = {
                "channel_id": channel.id,
                "hour": min(max(hour, 0), 23),
                "minute": min(max(minute, 0), 59),
                "enabled": True,
                "last_sent": None,
            }
            self._save()
            await ctx.send(f"QOTD set! Posts daily at **{hour:02d}:{minute:02d}** in {channel.mention}")

        elif action.lower() == "disable":
            if gid in self._config:
                self._config[gid]["enabled"] = False
                self._save()
                await ctx.send("QOTD disabled.")

        elif action.lower() == "enable":
            if gid in self._config:
                self._config[gid]["enabled"] = True
                self._save()
                await ctx.send("QOTD enabled.")

        elif action.lower() == "now":
            channel_id = self._config.get(gid, {}).get("channel_id")
            channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel
            question = random.choice(self._questions)
            embed = discord.Embed(title="📋 Question of the Day", description=f"**{question}**", color=discord.Color.purple())
            embed.set_footer(text="Share your thoughts below!")
            await channel.send(embed=embed)
            await ctx.send("QOTD sent!")

        elif action.lower() == "add" and arg:
            self._questions.append(arg)
            self._save()
            await ctx.send(f"Added QOTD question: {arg}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self._qotd_loop())

    async def _qotd_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = discord.utils.utcnow()
                today_str = now.strftime("%Y-%m-%d")

                for gid, cfg in self._config.items():
                    if not cfg.get("enabled"):
                        continue
                    if cfg.get("last_sent") == today_str:
                        continue
                    if now.hour == cfg["hour"] and now.minute >= cfg["minute"]:
                        guild = self.bot.get_guild(int(gid))
                        if guild:
                            channel = guild.get_channel(cfg["channel_id"])
                            if channel:
                                question = random.choice(self._questions)
                                embed = discord.Embed(title="📋 Question of the Day", description=f"**{question}**", color=discord.Color.purple())
                                embed.set_footer(text="Share your thoughts below!")
                                await channel.send(embed=embed)
                                cfg["last_sent"] = today_str
                                self._save()

                await asyncio.sleep(60)
            except Exception:
                await asyncio.sleep(120)

async def setup(bot):
    await bot.add_cog(QotdCog(bot))
'''
