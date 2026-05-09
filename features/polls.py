FEATURE_ID = "polls"
FEATURE_NAME = "Polls"
CATEGORY = "Fun"
DESCRIPTION = "Create polls with reactions, multiple options, and timed results"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class PollsCog(commands.Cog):
    """Interactive poll system."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="poll", description="Create a poll")
    @commands.has_permissions(manage_messages=True)
    async def poll(self, ctx, question: str, *options: str):
        if len(options) < 2:
            options = ("✅ Yes", "❌ No")
        if len(options) > 10:
            await ctx.send("Maximum 10 options.", delete_after=10)
            return

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        embed = discord.Embed(title=f"📊 Poll: {question}", color=discord.Color.blue())
        embed.description = "\n".join(f"{number_emojis[i]} {o}" for i, o in enumerate(options))
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        embed.timestamp = discord.utils.utcnow()

        msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await msg.add_reaction(number_emojis[i])
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(PollsCog(bot))
'''
