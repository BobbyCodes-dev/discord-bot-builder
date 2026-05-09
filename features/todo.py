FEATURE_ID = "todo"
FEATURE_NAME = "To-Do List"
CATEGORY = "Utility"
DESCRIPTION = "Personal todo list with add, remove, list, clear"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class TodoCog(commands.Cog):
    """Personal todo list system."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/todos.json")
        self._todos = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._todos = json.loads(self.data_file.read_text())
        except Exception:
            self._todos = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._todos, indent=2))

    @commands.hybrid_command(name="todo", description="Manage your todo list")
    async def todo(self, ctx, action: str = "list", *, arg: str = None):
        uid = str(ctx.author.id)
        self._todos.setdefault(uid, [])

        if action.lower() == "add" and arg:
            self._todos[uid].append({"task": arg, "added": discord.utils.utcnow().isoformat()})
            self._save()
            await ctx.send(f"✅ Added: **{arg}** (#{len(self._todos[uid])})")

        elif action.lower() == "remove" and arg:
            try:
                idx = int(arg) - 1
                removed = self._todos[uid].pop(idx)
                self._save()
                await ctx.send(f"🗑️ Removed: **{removed['task']}**")
            except (ValueError, IndexError):
                await ctx.send(f"Invalid index. Use a number 1-{len(self._todos[uid])}.", delete_after=10)

        elif action.lower() == "list":
            items = self._todos[uid]
            if not items:
                await ctx.send("Your todo list is empty! Add tasks with `/todo add <task>`", delete_after=15)
                return

            lines = [f"**{i}. {item['task']}**" for i, item in enumerate(items, 1)]
            embed = discord.Embed(title=f"📋 {ctx.author.display_name}'s To-Do List", description="\n".join(lines), color=discord.Color.blue())
            embed.set_footer(text=f"{len(items)} tasks — /todo remove <#> to remove")
            await ctx.send(embed=embed)

        elif action.lower() == "clear":
            count = len(self._todos[uid])
            self._todos[uid] = []
            self._save()
            await ctx.send(f"🗑️ Cleared {count} tasks from your todo list.")

        elif action.lower() == "done" and arg:
            try:
                idx = int(arg) - 1
                task = self._todos[uid].pop(idx)
                self._save()
                await ctx.send(f"✅ Completed: **{task['task']}**")
            except (ValueError, IndexError):
                await ctx.send(f"Invalid index. Use a number 1-{len(self._todos[uid])}.", delete_after=10)

        else:
            await ctx.send("Usage:\n`/todo add <task>`\n`/todo remove <#>`\n`/todo list`\n`/todo clear`\n`/todo done <#>`", delete_after=20)

async def setup(bot):
    await bot.add_cog(TodoCog(bot))
'''
