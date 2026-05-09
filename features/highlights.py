FEATURE_ID = "highlights"
FEATURE_NAME = "Highlights Notifier"
CATEGORY = "Utility"
DESCRIPTION = "Get DM'd when your tracked keywords are mentioned"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class HighlightsCog(commands.Cog):
    """Keyword highlight notifications system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/highlights.json")
        self._highlights = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._highlights = json.loads(self.data_file.read_text())
        except Exception:
            self._highlights = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._highlights, indent=2))

    @commands.hybrid_command(name="highlight", description="Manage your keyword highlights")
    async def highlight(self, ctx, action: str = "list", *, word: str = None):
        uid = str(ctx.author.id)
        self._highlights.setdefault(uid, [])

        if action.lower() == "add" and word:
            word_lower = word.lower().strip()
            if word_lower in self._highlights[uid]:
                await ctx.send(f"`{word}` is already in your highlights.")
            elif len(self._highlights[uid]) >= 15:
                await ctx.send("Maximum 15 highlights. Remove some first.")
            else:
                self._highlights[uid].append(word_lower)
                self._save()
                await ctx.send(f"✅ Added highlight: **{word}**")

        elif action.lower() == "remove" and word:
            word_lower = word.lower().strip()
            if word_lower in self._highlights[uid]:
                self._highlights[uid].remove(word_lower)
                self._save()
                await ctx.send(f"🗑️ Removed highlight: **{word}**")
            else:
                await ctx.send(f"`{word}` not in your highlights.")

        elif action.lower() == "list":
            words = self._highlights.get(uid, [])
            if not words:
                await ctx.send("You have no highlights set. Add with `/highlight add <word>`", delete_after=15)
                return
            await ctx.send(f"**Your highlights:** {', '.join(f'`{w}`' for w in words)}")

        elif action.lower() == "clear":
            count = len(self._highlights[uid])
            self._highlights[uid] = []
            self._save()
            await ctx.send(f"🗑️ Cleared {count} highlights.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        content_lower = message.content.lower()
        if not content_lower:
            return

        notified = set()

        for uid, words in self._highlights.items():
            if str(message.author.id) == uid:
                continue  # Don't notify for your own messages
            if uid in notified:
                continue

            for word in words:
                if word in content_lower:
                    user = self.bot.get_user(int(uid))
                    if user:
                        try:
                            embed = discord.Embed(
                                title="🔔 Highlight Matched!",
                                description=f"**Word:** `{word}`\n**Server:** {message.guild.name}\n**Channel:** #{message.channel.name}\n**By:** {message.author.display_name}\n\n{message.content[:500]}",
                                color=discord.Color.gold(),
                                timestamp=message.created_at,
                            )
                            embed.add_field(name="Jump", value=f"[Go to message]({message.jump_url})")
                            await user.send(embed=embed)
                            notified.add(uid)
                        except discord.Forbidden:
                            pass
                    break

async def setup(bot):
    await bot.add_cog(HighlightsCog(bot))
'''
