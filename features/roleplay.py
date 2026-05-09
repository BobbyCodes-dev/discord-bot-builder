FEATURE_ID = "roleplay"
FEATURE_NAME = "Roleplay Actions"
CATEGORY = "Fun"
DESCRIPTION = "Fun roleplay commands: hug, slap, pat, kiss, poke, cuddle"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class RoleplayCog(commands.Cog):
    """Roleplay action commands."""

    HUG_RESPONSES = [
        "{author} gives {target} a warm hug! 🤗",
        "{author} wraps their arms around {target} in a big hug! 🫂",
        "{author} squeezes {target} tightly! 🤗",
        "{target} gets a surprise hug from {author}! 💕",
        "{author} and {target} share a wholesome hug! 🫂❤️",
    ]
    SLAP_RESPONSES = [
        "{author} slaps {target} across the face! 👋",
        "{author} delivers a legendary slap to {target}! 💢",
        "{target} gets slapped by {author} — ouch! 😱",
        "{author} backhands {target} with style! 👋💥",
    ]
    PAT_RESPONSES = [
        "{author} pats {target} on the head! 🫳",
        "{author} gives {target} gentle headpats! 🥰",
        "{target} receives headpats from {author}! 😊",
        "{author} pats {target} — good job! 👏",
    ]
    KISS_RESPONSES = [
        "{author} gives {target} a kiss! 😘",
        "{author} plants a sweet kiss on {target}! 💋",
        "{target} gets kissed by {author}! 💕",
        "{author} and {target} share a romantic moment! 😘❤️",
    ]
    POKE_RESPONSES = [
        "{author} pokes {target}! 👉",
        "{author} pokes {target} — hey, notice me! 👈",
        "{target} gets poked by {author} repeatedly! 👉😤",
        "{author} sneakily pokes {target} from behind! 👆",
    ]
    CUDDLE_RESPONSES = [
        "{author} cuddles up with {target}! 🥰",
        "{author} and {target} share a cozy cuddle! 🤗💕",
        "{target} gets wrapped in a warm cuddle by {author}! 🫂",
        "{author} snuggles close to {target}! 💤❤️",
    ]

    def __init__(self, bot):
        self.bot = bot

    def _format(self, responses, author, target):
        resp = random.choice(responses)
        return resp.format(author=author.mention, target=target.mention)

    @commands.hybrid_command(name="hug", description="Hug someone!")
    async def hug(self, ctx, member: discord.Member):
        await ctx.send(self._format(self.HUG_RESPONSES, ctx.author, member))

    @commands.hybrid_command(name="slap", description="Slap someone!")
    async def slap(self, ctx, member: discord.Member):
        await ctx.send(self._format(self.SLAP_RESPONSES, ctx.author, member))

    @commands.hybrid_command(name="pat", description="Pat someone!")
    async def pat(self, ctx, member: discord.Member):
        await ctx.send(self._format(self.PAT_RESPONSES, ctx.author, member))

    @commands.hybrid_command(name="kiss", description="Kiss someone!")
    async def kiss(self, ctx, member: discord.Member):
        await ctx.send(self._format(self.KISS_RESPONSES, ctx.author, member))

    @commands.hybrid_command(name="poke", description="Poke someone!")
    async def poke(self, ctx, member: discord.Member):
        await ctx.send(self._format(self.POKE_RESPONSES, ctx.author, member))

    @commands.hybrid_command(name="cuddle", description="Cuddle someone!")
    async def cuddle(self, ctx, member: discord.Member):
        await ctx.send(self._format(self.CUDDLE_RESPONSES, ctx.author, member))

async def setup(bot):
    await bot.add_cog(RoleplayCog(bot))
'''
