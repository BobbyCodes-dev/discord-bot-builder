FEATURE_ID = "counting_game"
FEATURE_NAME = "Counting Game"
CATEGORY = "Fun"
DESCRIPTION = "Users count together — wrong number resets the count"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class CountingGameCog(commands.Cog):
    """Counting game where users must count in order."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/counting.json")
        self._games = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._games = json.loads(self.data_file.read_text())
        except Exception:
            self._games = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._games, indent=2))

    @commands.hybrid_command(name="counting", description="Configure the counting game")
    @commands.has_permissions(manage_channels=True)
    async def counting(self, ctx, action: str, channel: discord.TextChannel = None):
        gid = str(ctx.guild.id)
        if action.lower() == "set":
            if not channel:
                await ctx.send("Usage: `/counting set <channel>`", delete_after=20)
                return
            self._games[gid] = {"channel_id": channel.id, "current": 1, "last_user": None}
            self._save()
            await ctx.send(f"Counting game active in {channel.mention}. Start with **1**!")

        elif action.lower() == "reset":
            if gid in self._games:
                self._games[gid]["current"] = 1
                self._games[gid]["last_user"] = None
                self._save()
                await ctx.send("Counting game reset! Start from 1.")
            else:
                await ctx.send("No counting game set up.")

        elif action.lower() == "disable":
            if gid in self._games:
                del self._games[gid]
                self._save()
                await ctx.send("Counting game disabled.")
            else:
                await ctx.send("No counting game set up.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        gid = str(message.guild.id)
        if gid not in self._games:
            return
        game = self._games[gid]
        if message.channel.id != game["channel_id"]:
            return

        # Check if message is a number
        try:
            num = int(message.content.strip())
        except ValueError:
            # Not a number — delete non-number messages in counting channel
            await message.delete()
            return

        # Check if it's the correct number and not the same user
        if num != game["current"]:
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention} broke the chain! The next number was **{game['current']}**. Counting resets to 1.", delete_after=10)
            game["current"] = 1
            game["last_user"] = None
            self._save()
            return

        if message.author.id == game.get("last_user"):
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention} can't count twice in a row! Next number is still **{game['current']}**.", delete_after=10)
            return

        # Correct!
        game["current"] += 1
        game["last_user"] = message.author.id

        if game["current"] % 100 == 0:
            await message.add_reaction("🎉")
        elif game["current"] % 50 == 0:
            await message.add_reaction("🔥")

        self._save()

async def setup(bot):
    await bot.add_cog(CountingGameCog(bot))
'''
