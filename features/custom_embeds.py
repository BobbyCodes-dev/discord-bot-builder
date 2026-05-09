FEATURE_ID = "custom_embeds"
FEATURE_NAME = "Custom Embeds"
CATEGORY = "Utility"
DESCRIPTION = "Interactive embed builder with preview, fields, colors, images"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class CustomEmbedsCog(commands.Cog):
    """Interactive embed creation tool."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="embed", description="Create a custom embed")
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx, title: str, description: str, color: str = "blue", image_url: str = None):
        colors = {
            "red": discord.Color.red(), "blue": discord.Color.blue(),
            "green": discord.Color.green(), "gold": discord.Color.gold(),
            "purple": discord.Color.purple(), "orange": discord.Color.orange(),
            "teal": discord.Color.teal(), "pink": 0xFF69B4, "black": 0x000000,
            "white": 0xFFFFFF, "grey": discord.Color.light_gray(),
        }

        try:
            embed_color = colors.get(color.lower(), discord.Color.blue())
            if color.startswith("#"):
                embed_color = int(color.lstrip("#"), 16)
            elif color.startswith("0x"):
                embed_color = int(color, 16)
        except (ValueError, AttributeError):
            embed_color = discord.Color.blue()

        embed = discord.Embed(title=title, description=description, color=embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        if image_url:
            embed.set_image(url=image_url)
        embed.set_footer(text=f"Embed by {ctx.author.display_name}")

        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.hybrid_command(name="embedfields", description="Create a detailed embed with fields")
    @commands.has_permissions(manage_messages=True)
    async def embedfields(self, ctx):
        """Interactive embed builder with fields."""
        await ctx.send("Let's build an embed! What's the **title**? (type 'skip' to skip)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            title_msg = await self.bot.wait_for("message", timeout=120, check=check)
            title = None if title_msg.content.lower() == "skip" else title_msg.content
        except asyncio.TimeoutError:
            await ctx.send("Timed out.")
            return

        await ctx.send("What's the **description**?")
        try:
            desc_msg = await self.bot.wait_for("message", timeout=120, check=check)
            description = desc_msg.content
        except asyncio.TimeoutError:
            await ctx.send("Timed out.")
            return

        await ctx.send("What **color**? (red, blue, green, gold, purple, orange, teal, pink, or hex like #ff0000)")

        colors_map = {
            "red": discord.Color.red(), "blue": discord.Color.blue(),
            "green": discord.Color.green(), "gold": discord.Color.gold(),
            "purple": discord.Color.purple(), "orange": discord.Color.orange(),
            "teal": discord.Color.teal(), "pink": 0xFF69B4,
        }

        try:
            color_msg = await self.bot.wait_for("message", timeout=60, check=check)
            color_str = color_msg.content.lower()
            if color_str.startswith("#"):
                embed_color = int(color_str.lstrip("#"), 16)
            else:
                embed_color = colors_map.get(color_str, discord.Color.blue())
        except (asyncio.TimeoutError, ValueError):
            embed_color = discord.Color.blue()

        embed = discord.Embed(title=title, description=description[:4000], color=embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        await ctx.send("Add **fields**? Format: `name | value` (one per message). Send `done` when finished.")

        while True:
            try:
                field_msg = await self.bot.wait_for("message", timeout=60, check=check)
                if field_msg.content.lower() == "done":
                    break
                parts = field_msg.content.split("|", 1)
                if len(parts) == 2:
                    embed.add_field(name=parts[0].strip()[:256], value=parts[1].strip()[:1024], inline=False)
                    await ctx.send(f"Added field: **{parts[0].strip()}**")
                else:
                    await ctx.send("Format: `name | value`")
                if len(embed.fields) >= 25:
                    await ctx.send("Max 25 fields reached.")
                    break
            except asyncio.TimeoutError:
                break

        await ctx.send("**Footer** text? (type 'skip' to skip)")
        try:
            footer_msg = await self.bot.wait_for("message", timeout=30, check=check)
            if footer_msg.content.lower() != "skip":
                embed.set_footer(text=footer_msg.content[:2048])
        except asyncio.TimeoutError:
            pass

        await ctx.send("**Image URL**? (type 'skip' to skip)")
        try:
            img_msg = await self.bot.wait_for("message", timeout=30, check=check)
            if img_msg.content.lower() != "skip" and img_msg.content.startswith("http"):
                embed.set_image(url=img_msg.content)
        except asyncio.TimeoutError:
            pass

        # Preview
        await ctx.send("**Preview:**", embed=embed)
        await ctx.send("Send this? (yes/no)")
        try:
            confirm = await self.bot.wait_for("message", timeout=30, check=check)
            if confirm.content.lower() == "yes":
                await ctx.send(embed=embed)
            else:
                await ctx.send("Cancelled.")
        except asyncio.TimeoutError:
            await ctx.send("Cancelled.")

async def setup(bot):
    await bot.add_cog(CustomEmbedsCog(bot))
'''
