FEATURE_ID = "afk"
FEATURE_NAME = "AFK System"
CATEGORY = "Utility"
DESCRIPTION = "Set AFK status that auto-responds when mentioned"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class AfkCog(commands.Cog):
    """AFK status system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/afk.json")
        self._afk = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._afk = json.loads(self.data_file.read_text())
        except Exception:
            self._afk = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._afk, indent=2))

    @commands.hybrid_command(name="afk", description="Set your AFK status")
    async def afk(self, ctx, *, reason: str = "AFK"):
        uid = str(ctx.author.id)
        self._afk[uid] = {
            "reason": reason,
            "since": discord.utils.utcnow().isoformat(),
            "mentions": 0,
        }
        self._save()

        try:
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}"[:32])
        except (discord.Forbidden, discord.HTTPException):
            pass

        await ctx.send(f"💤 {ctx.author.mention} is now AFK: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        uid = str(message.author.id)

        # Clear AFK if user sends a message
        if uid in self._afk:
            del self._afk[uid]
            self._save()
            try:
                await message.author.edit(nick=message.author.display_name.replace("[AFK] ", ""))
            except Exception:
                pass
            try:
                await message.channel.send(f"👋 Welcome back {message.author.mention}! You are no longer AFK.", delete_after=10)
            except Exception:
                pass

        # Check for mentions of AFK users
        for mentioned in message.mentions:
            muid = str(mentioned.id)
            if muid in self._afk and muid != uid:
                afk_data = self._afk[muid]
                afk_data["mentions"] += 1
                self._save()
                since = datetime.fromisoformat(afk_data["since"])
                await message.channel.send(f"💤 **{mentioned.display_name}** is AFK: {afk_data['reason']} — {discord.utils.format_dt(since, 'R')}", delete_after=30)

async def setup(bot):
    await bot.add_cog(AfkCog(bot))
'''
