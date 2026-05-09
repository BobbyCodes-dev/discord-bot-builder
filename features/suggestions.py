FEATURE_ID = "suggestions"
FEATURE_NAME = "Suggestions"
CATEGORY = "Utility"
DESCRIPTION = "User suggestion box with upvote/downvote and staff approve/deny"
ENV_VARS = ["SUGGESTIONS_CHANNEL_ID"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class SuggestionsCog(commands.Cog):
    """Suggestion box system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/suggestions.json")
        self.suggestions_channel_id = int(os.getenv("SUGGESTIONS_CHANNEL_ID", "0"))
        self._suggestions = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._suggestions = json.loads(self.data_file.read_text())
        except Exception:
            self._suggestions = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._suggestions, indent=2))

    @commands.hybrid_command(name="suggest", description="Submit a suggestion")
    async def suggest(self, ctx, *, idea: str):
        channel = ctx.guild.get_channel(self.suggestions_channel_id) if self.suggestions_channel_id else ctx.channel
        if channel is None:
            await ctx.send("Suggestions channel not configured.", delete_after=10)
            return

        embed = discord.Embed(title="💡 New Suggestion", description=idea[:4000], color=discord.Color.blue(), timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Suggestion ID: #{max(int(k) for k in self._suggestions.keys()) + 1 if self._suggestions else 1}")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        sid = str(msg.id)
        self._suggestions[sid] = {
            "user_id": ctx.author.id,
            "channel_id": msg.channel.id,
            "idea": idea,
            "status": "pending",
            "message_id": msg.id,
        }
        self._save()

        if channel != ctx.channel:
            await ctx.send(f"Suggestion submitted! Check {channel.mention}.", delete_after=10)
        else:
            await ctx.message.delete()

    @commands.hybrid_command(name="suggestions", description="Manage suggestions")
    @commands.has_permissions(manage_messages=True)
    async def manage_suggestions(self, ctx, action: str, message_id: str = None, *, reason: str = ""):
        if action.lower() == "list":
            items = [(sid, s) for sid, s in self._suggestions.items() if s["status"] == "pending"]
            if not items:
                await ctx.send("No pending suggestions.", delete_after=10)
                return
            lines = [f"**[{sid}](<https://discord.com/channels/{ctx.guild.id}/{s['channel_id']}/{s['message_id']}>)** — {s['idea'][:80]} by <@{s['user_id']}>" for sid, s in items[:10]]
            await ctx.send("\n".join(lines))

        elif action.lower() in ("approve", "deny") and message_id:
            sid = message_id
            if sid not in self._suggestions:
                await ctx.send("Suggestion not found.", delete_after=10)
                return

            suggestion = self._suggestions[sid]
            channel = self.bot.get_channel(suggestion["channel_id"])
            if not channel:
                await ctx.send("Original channel not found.", delete_after=10)
                return

            try:
                msg = await channel.fetch_message(suggestion["message_id"])
            except Exception:
                await ctx.send("Original message not found.", delete_after=10)
                return

            if action.lower() == "approve":
                new_embed = msg.embeds[0]
                new_embed.color = discord.Color.green()
                new_embed.title = "✅ Suggestion Approved"
                if reason:
                    new_embed.add_field(name="Staff Note", value=reason)
                await msg.edit(embed=new_embed)
                self._suggestions[sid]["status"] = "approved"
                self._save()
                await ctx.send("Suggestion approved!")
            else:
                new_embed = msg.embeds[0]
                new_embed.color = discord.Color.red()
                new_embed.title = "❌ Suggestion Denied"
                if reason:
                    new_embed.add_field(name="Staff Note", value=reason)
                await msg.edit(embed=new_embed)
                self._suggestions[sid]["status"] = "denied"
                self._save()
                await ctx.send("Suggestion denied!")

async def setup(bot):
    await bot.add_cog(SuggestionsCog(bot))
'''
