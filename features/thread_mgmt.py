FEATURE_ID = "thread_mgmt"
FEATURE_NAME = "Thread Management"
CATEGORY = "Utility"
DESCRIPTION = "Auto-create threads, archive, lock threads"
ENV_VARS = ["AUTO_THREAD_CHANNELS"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class ThreadManagementCog(commands.Cog):
    """Thread auto-creation and management."""

    def __init__(self, bot):
        self.bot = bot
        channel_ids = os.getenv("AUTO_THREAD_CHANNELS", "")
        self.auto_thread_channels = [int(c.strip()) for c in channel_ids.split(",") if c.strip().isdigit()]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if message.channel.id not in self.auto_thread_channels:
            return
        if message.type != discord.MessageType.default:
            return

        # Auto-create thread from message
        try:
            title = message.content[:100].strip() or f"Thread by {message.author.display_name}"
            await message.create_thread(name=title)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.hybrid_command(name="thread", description="Manage threads")
    @commands.has_permissions(manage_threads=True)
    async def thread(self, ctx, action: str, channel: discord.TextChannel = None):
        if action.lower() == "archive":
            target = channel or ctx.channel
            if isinstance(target, discord.Thread):
                await target.edit(archived=True)
                await ctx.send(f"📦 Archived thread: {target.mention}")
            else:
                # Archive all inactive threads in channel
                count = 0
                for thread in target.threads:
                    if not thread.archived:
                        await thread.edit(archived=True)
                        count += 1
                await ctx.send(f"📦 Archived {count} threads in {target.mention}")

        elif action.lower() == "unarchive":
            target = channel or ctx.channel
            if isinstance(target, discord.Thread):
                await target.edit(archived=False)
                await ctx.send(f"📂 Unarchived: {target.mention}")
            else:
                await ctx.send("Channel is not a thread.", delete_after=10)

        elif action.lower() == "lock":
            target = channel or ctx.channel
            if isinstance(target, discord.Thread):
                await target.edit(locked=True)
                await ctx.send(f"🔒 Locked thread: {target.mention}")
            else:
                await ctx.send("Channel is not a thread.", delete_after=10)

        elif action.lower() == "unlock":
            target = channel or ctx.channel
            if isinstance(target, discord.Thread):
                await target.edit(locked=False)
                await ctx.send(f"🔓 Unlocked thread: {target.mention}")
            else:
                await ctx.send("Channel is not a thread.", delete_after=10)

        elif action.lower() == "list":
            target = channel or ctx.channel
            if not isinstance(target, discord.TextChannel):
                await ctx.send("Not a text channel.", delete_after=10)
                return
            threads = target.threads
            if not threads:
                await ctx.send(f"No threads in {target.mention}.")
                return

            lines = [f"{'🔒' if t.locked else '📄'} {'📦' if t.archived else '📂'} {t.mention} — `{t.name}`" for t in threads[:20]]
            embed = discord.Embed(title=f"Threads in #{target.name}", description="\n".join(lines), color=discord.Color.blue())
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ThreadManagementCog(bot))
'''
