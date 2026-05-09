FEATURE_ID = "templates"
FEATURE_NAME = "Server Templates"
CATEGORY = "Utility"
DESCRIPTION = "Export/import server structure (roles, channels, categories)"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class TemplatesCog(commands.Cog):
    """Server template export/import."""

    def __init__(self, bot):
        self.bot = bot
        self.template_dir = Path("data/templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def _serialize_guild(self, guild):
        data = {
            "name": guild.name,
            "roles": [],
            "categories": [],
            "channels": [],
            "emojis": [],
            "timestamp": discord.utils.utcnow().isoformat(),
        }

        # Roles (skip @everyone and managed)
        for role in reversed(guild.roles):
            if role.is_default() or role.managed:
                continue
            data["roles"].append({
                "name": role.name,
                "color": role.color.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "permissions": role.permissions.value,
            })

        # Categories
        for cat in guild.categories:
            cat_data = {"name": cat.name, "channels": []}
            for ch in cat.channels:
                ch_data = {
                    "name": ch.name,
                    "type": "text" if isinstance(ch, discord.TextChannel) else "voice",
                }
                if isinstance(ch, discord.TextChannel):
                    ch_data.update({"topic": ch.topic or "", "nsfw": ch.nsfw})
                cat_data["channels"].append(ch_data)
            data["categories"].append(cat_data)

        # Uncategorized channels
        uncategorized = [ch for ch in guild.channels if ch.category is None and not isinstance(ch, discord.CategoryChannel)]
        if uncategorized:
            uncat = {"name": "Uncategorized", "channels": []}
            for ch in uncategorized:
                ch_data = {"name": ch.name, "type": "text" if isinstance(ch, discord.TextChannel) else "voice"}
                if isinstance(ch, discord.TextChannel):
                    ch_data.update({"topic": ch.topic or "", "nsfw": ch.nsfw})
                uncat["channels"].append(ch_data)
            data["categories"].append(uncat)

        # Emojis
        for emoji in guild.emojis:
            data["emojis"].append({"name": emoji.name, "url": str(emoji.url), "animated": emoji.animated})

        return data

    @commands.hybrid_command(name="template", description="Export/import server templates")
    @commands.has_permissions(administrator=True)
    async def template(self, ctx, action: str, *, name: str = None):
        if action.lower() == "export":
            data = self._serialize_guild(ctx.guild)
            filename = f"{ctx.guild.name}_{discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.template_dir / filename
            filepath.write_text(json.dumps(data, indent=2))

            await ctx.send(f"📦 Template exported as `{filename}`\n**{len(data['roles'])}** roles, **{len(data['categories'])}** categories")

        elif action.lower() == "import" and name:
            templates = sorted(self.template_dir.glob("*.json"), reverse=True)
            matching = [t for t in templates if name.lower() in t.name.lower()]
            if not matching:
                await ctx.send(f"No template matching `{name}` found. Templates: {', '.join(t.name for t in templates[:5])}", delete_after=30)
                return

            filepath = matching[0]
            data = json.loads(filepath.read_text())

            await ctx.send(f"⚠️ This will create roles and channels from **{data['name']}**. Proceed? (yes/no)")

            try:
                msg = await self.bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                if msg.content.lower() != "yes":
                    await ctx.send("Cancelled.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("Timed out.")
                return

            await ctx.send("Importing...")

            # Create roles
            for role_data in data["roles"]:
                try:
                    await ctx.guild.create_role(
                        name=role_data["name"],
                        color=discord.Color(role_data["color"]),
                        hoist=role_data["hoist"],
                        mentionable=role_data["mentionable"],
                        permissions=discord.Permissions(role_data["permissions"]),
                    )
                except Exception:
                    pass

            # Create categories and channels
            for cat_data in data["categories"]:
                try:
                    cat = await ctx.guild.create_category(cat_data["name"])
                    for ch_data in cat_data["channels"]:
                        try:
                            if ch_data["type"] == "text":
                                await ctx.guild.create_text_channel(
                                    ch_data["name"], category=cat,
                                    topic=ch_data.get("topic", ""),
                                    nsfw=ch_data.get("nsfw", False),
                                )
                            else:
                                await ctx.guild.create_voice_channel(ch_data["name"], category=cat)
                        except Exception:
                            pass
                except Exception:
                    pass

            await ctx.send("✅ Template imported! Roles and channels created.")

        elif action.lower() == "list":
            templates = sorted(self.template_dir.glob("*.json"), reverse=True)
            if not templates:
                await ctx.send("No templates saved.")
                return
            lines = [f"**{t.name}** ({t.stat().st_size:,} bytes)" for t in templates[:10]]
            await ctx.send("\n".join(lines))

async def setup(bot):
    await bot.add_cog(TemplatesCog(bot))
'''
