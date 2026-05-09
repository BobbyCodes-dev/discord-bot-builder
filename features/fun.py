FEATURE_ID = "fun"
FEATURE_NAME = "Fun Commands"
CATEGORY = "Fun"
DESCRIPTION = "8ball, coinflip, dice, meme, joke, and other fun commands"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class FunCog(commands.Cog):
    """Various fun commands."""

    _EIGHTBALL_RESPONSES = [
        "It is certain.", "It is decidedly so.", "Without a doubt.",
        "Yes definitely.", "You may rely on it.", "As I see it, yes.",
        "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
        "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
        "Cannot predict now.", "Concentrate and ask again.",
        "Don't count on it.", "My reply is no.", "My sources say no.",
        "Outlook not so good.", "Very doubtful.",
    ]

    _JOKES = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the developer go broke? Because he used up all his cache!",
        "What's a computer's favorite snack? Microchips!",
        "Why do Java developers wear glasses? Because they don't C#!",
        "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
    ]

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="8ball", description="Ask the magic 8ball")
    async def eightball(self, ctx, *, question: str):
        embed = discord.Embed(title=f"🎱 {question}", description=random.choice(self._EIGHTBALL_RESPONSES), color=discord.Color.purple())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="coinflip", description="Flip a coin")
    async def coinflip(self, ctx):
        result = random.choice(["Heads!", "Tails!"])
        await ctx.send(f"🪙 {result}")

    @commands.hybrid_command(name="dice", aliases=["roll"], description="Roll dice (e.g., 1d20)")
    async def dice(self, ctx, dice_str: str = "1d6"):
        try:
            num, sides = dice_str.lower().split("d")
            num, sides = int(num) if num else 1, int(sides)
            if num < 1 or num > 20 or sides < 2 or sides > 1000:
                await ctx.send("Use 1-20 dice, 2-1000 sides.", delete_after=10)
                return
            rolls = [random.randint(1, sides) for _ in range(num)]
            total = sum(rolls)
            if num == 1:
                await ctx.send(f"🎲 You rolled a **{total}** (1d{sides})")
            else:
                await ctx.send(f"🎲 You rolled: {', '.join(map(str, rolls))} = **{total}**")
        except ValueError:
            await ctx.send("Format: !dice [N]d[S], e.g., !dice 2d20", delete_after=10)

    @commands.hybrid_command(name="joke", description="Get a random programming joke")
    async def joke(self, ctx):
        await ctx.send(random.choice(self._JOKES))

    @commands.hybrid_command(name="choose", description="Bot chooses between options")
    async def choose(self, ctx, *options: str):
        if not options:
            await ctx.send("Give me some options to choose from!", delete_after=10)
            return
        await ctx.send(f"🤔 I choose: **{random.choice(options)}**")

async def setup(bot):
    await bot.add_cog(FunCog(bot))
'''
