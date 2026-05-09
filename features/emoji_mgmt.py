FEATURE_ID = "emoji_mgmt"
FEATURE_NAME = "Emoji Management"
CATEGORY = "Utility"
DESCRIPTION = "List, info, steal emojis from other servers, upload"
ENV_VARS = []
DEPENDENCIES = ["requests"]

BLOCK_CODE = r'''
class EmojiManagementCog(commands.Cog):
    """Emoji management tools."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="emoji", description="Manage emojis")
    @commands.has_permissions(manage_emojis=True)
    async def emoji(self, ctx, action: str = "list", *, target: str = None):
        if action.lower() == "list":
            emojis = ctx.guild.emojis
            if not emojis:
                await ctx.send("No custom emojis in this server.")
                return

            lines = []
            for e in sorted(emojis, key=lambda x: x.name):
                prefix = "<a:" if e.animated else "<:"
                lines.append(f"{prefix}{e.name}:{e.id}> `:{e.name}:` ({'animated' if e.animated else 'static'})")
                if len(lines) >= 20:
                    lines.append(f"... and {len(emojis) - 20} more")
                    break

            embed = discord.Embed(title=f"Emojis in {ctx.guild.name}", description="\n".join(lines), color=discord.Color.blue())
            embed.set_footer(text=f"{len(emojis)} total")
            await ctx.send(embed=embed)

        elif action.lower() == "info":
            # Find emoji from raw string like <:name:id>
            import re
            match = re.match(r'<(a?):(.+):(\d+)>', target or "")
            if match:
                animated = match.group(1) == "a"
                name = match.group(2)
                eid = int(match.group(3))
                emoji_obj = discord.utils.get(ctx.guild.emojis, id=eid)
            else:
                # Try by name
                emoji_obj = discord.utils.get(ctx.guild.emojis, name=target)

            if not emoji_obj:
                await ctx.send("Emoji not found.")
                return

            embed = discord.Embed(title=f"Emoji: :{emoji_obj.name}:", color=discord.Color.blue())
            embed.set_thumbnail(url=emoji_obj.url)
            embed.add_field(name="Name", value=emoji_obj.name, inline=True)
            embed.add_field(name="ID", value=emoji_obj.id, inline=True)
            embed.add_field(name="Animated", value="Yes" if emoji_obj.animated else "No", inline=True)
            embed.add_field(name="URL", value=f"[Link]({emoji_obj.url})", inline=True)
            await ctx.send(embed=embed)

        elif action.lower() == "steal" and target:
            # Steal an emoji from URL or raw emoji string
            import re, requests

            match = re.match(r'<(a?):(.+):(\d+)>', target)
            if not match:
                await ctx.send("Usage: `/emoji steal <raw_emoji>` (paste the emoji itself)", delete_after=30)
                return

            animated = match.group(1) == "a"
            name = match.group(2)
            eid = match.group(3)

            ext = "gif" if animated else "png"
            url = f"https://cdn.discordapp.com/emojis/{eid}.{ext}"

            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()

                emoji = await ctx.guild.create_custom_emoji(
                    name=name,
                    image=resp.content,
                    reason=f"Stolen by {ctx.author}",
                )
                await ctx.send(f"✅ Added {emoji} `:{name}:`")
            except discord.Forbidden:
                await ctx.send("I don't have permission to create emojis.")
            except discord.HTTPException as e:
                if "maximum number of emojis" in str(e).lower():
                    await ctx.send("At emoji limit!")
                elif "filesize" in str(e).lower():
                    await ctx.send("File too large (max 256KB).")
                else:
                    await ctx.send(f"Error: {e}")
            except Exception as e:
                await ctx.send(f"Failed: {e}")

async def setup(bot):
    await bot.add_cog(EmojiManagementCog(bot))
'''
