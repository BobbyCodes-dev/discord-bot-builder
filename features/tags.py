FEATURE_ID = "tags"
FEATURE_NAME = "Tags"
CATEGORY = "Utility"
DESCRIPTION = "Server-specific custom commands (tags)"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class TagsCog(commands.Cog):
    """Custom server tags system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/tags.json")
        self._tags = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._tags = json.loads(self.data_file.read_text())
        except Exception:
            self._tags = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._tags, indent=2))

    @commands.hybrid_command(name="tag", description="View or create tags")
    async def tag(self, ctx, name: str = None, action: str = None, *, content: str = None):
        gid = str(ctx.guild.id)
        self._tags.setdefault(gid, {})

        if name and not action:
            # View a tag
            tag = self._tags[gid].get(name.lower())
            if tag:
                await ctx.send(tag["content"])
            else:
                await ctx.send(f"Tag `{name}` not found. Create it with `/tag create {name} <content>`", delete_after=15)

        elif name and action:
            if action.lower() == "create":
                if not content:
                    await ctx.send("Usage: `/tag create <name> <content>`", delete_after=20)
                    return
                self._tags[gid][name.lower()] = {"content": content, "author": ctx.author.id, "uses": 0, "created": discord.utils.utcnow().isoformat()}
                self._save()
                await ctx.send(f"✅ Tag `{name}` created!")

            elif action.lower() == "delete":
                if name.lower() in self._tags[gid]:
                    if ctx.author.id == self._tags[gid][name.lower()]["author"] or ctx.author.guild_permissions.manage_messages:
                        del self._tags[gid][name.lower()]
                        self._save()
                        await ctx.send(f"🗑️ Deleted tag `{name}`.")
                    else:
                        await ctx.send("You can only delete your own tags.", delete_after=10)
                else:
                    await ctx.send(f"Tag `{name}` not found.", delete_after=10)

            elif action.lower() == "edit":
                if not content:
                    await ctx.send("Usage: `/tag edit <name> <new_content>`", delete_after=20)
                    return
                if name.lower() in self._tags[gid]:
                    if ctx.author.id == self._tags[gid][name.lower()]["author"] or ctx.author.guild_permissions.manage_messages:
                        self._tags[gid][name.lower()]["content"] = content
                        self._save()
                        await ctx.send(f"✏️ Tag `{name}` updated.")
                    else:
                        await ctx.send("You can only edit your own tags.", delete_after=10)
                else:
                    await ctx.send(f"Tag `{name}` not found.", delete_after=10)

        elif not name:
            # List all tags
            tags = self._tags.get(gid, {})
            if not tags:
                await ctx.send("No tags in this server. Create one with `/tag create <name> <content>`", delete_after=15)
                return

            sorted_tags = sorted(tags.items(), key=lambda x: x[1].get("uses", 0), reverse=True)
            lines = [f"**{name}** — {info['content'][:60]}" for name, info in sorted_tags[:20]]
            if len(sorted_tags) > 20:
                lines.append(f"... and {len(sorted_tags)-20} more")

            embed = discord.Embed(title=f"📋 Tags in {ctx.guild.name}", description="\n".join(lines), color=discord.Color.blue())
            embed.set_footer(text=f"{len(tags)} total — use /tag <name> to view")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TagsCog(bot))
'''
