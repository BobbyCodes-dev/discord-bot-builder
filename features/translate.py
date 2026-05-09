FEATURE_ID = "translate"
FEATURE_NAME = "Translator"
CATEGORY = "Utility"
DESCRIPTION = "Translate text between languages using Google Translate"
ENV_VARS = []
DEPENDENCIES = ["deep-translator"]

BLOCK_CODE = r'''
class TranslateCog(commands.Cog):
    """Text translation using Google Translate."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="translate", description="Translate text")
    async def translate(self, ctx, target_lang: str, *, text: str):
        await ctx.defer()
        try:
            from deep_translator import GoogleTranslator
        except ImportError:
            await ctx.send("Install deep-translator: `pip install deep-translator`", delete_after=15)
            return

        try:
            result = GoogleTranslator(source='auto', target=target_lang.lower()).translate(text)

            embed = discord.Embed(title="🌐 Translation", color=discord.Color.blue())
            embed.add_field(name="From (auto-detect)", value=text[:1024], inline=False)
            embed.add_field(name=f"To ({target_lang})", value=result[:1024] if result else "Translation failed", inline=False)
            embed.set_footer(text="Powered by Google Translate — quality may vary")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Translation failed: {e}\nMake sure you used a valid language code (e.g., `es`, `fr`, `ja`).", delete_after=20)

    @commands.hybrid_command(name="langcodes", description="Show common language codes")
    async def langcodes(self, ctx):
        codes = {
            "ar": "Arabic", "zh": "Chinese", "nl": "Dutch", "en": "English",
            "fr": "French", "de": "German", "hi": "Hindi", "it": "Italian",
            "ja": "Japanese", "ko": "Korean", "pl": "Polish", "pt": "Portuguese",
            "ru": "Russian", "es": "Spanish", "sv": "Swedish", "th": "Thai",
            "tr": "Turkish", "uk": "Ukrainian", "vi": "Vietnamese",
        }
        lines = [f"`{code}` — {name}" for code, name in sorted(codes.items())]
        embed = discord.Embed(title="Common Language Codes", description="\n".join(lines), color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TranslateCog(bot))
'''
