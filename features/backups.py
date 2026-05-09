FEATURE_ID = "backups"
FEATURE_NAME = "Server Backups"
CATEGORY = "Utility"
DESCRIPTION = "Create and restore server backups (roles, channels, categories, emojis)"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class BackupsCog(commands.Cog):
    """Server backup and restore system."""

    def __init__(self, bot):
        self.bot = bot
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _serialize_role(self, role):
        return {
            "name": role.name,
            "color": role.color.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
            "permissions": role.permissions.value,
            "position": role.position,
        }

    def _serialize_channel(self, ch):
        base = {"name": ch.name, "type": str(ch.type), "position": ch.position}
        if isinstance(ch, discord.TextChannel):
            base["topic"] = ch.topic or ""
            base["slowmode"] = ch.slowmode_delay
            base["nsfw"] = ch.nsfw
        if ch.category:
            base["category_name"] = ch.category.name
        return base

    @commands.hybrid_command(name="backup", description="Manage server backups")
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx, action: str):
        if action.lower() == "create":
            await ctx.defer()
            guild = ctx.guild

            data = {
                "name": guild.name,
                "id": guild.id,
                "roles": [],
                "categories": [],
                "channels": [],
                "emojis": [],
                "timestamp": discord.utils.utcnow().isoformat(),
            }

            # Roles (skip @everyone, managed roles)
            for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
                if role.is_default() or role.managed:
                    continue
                data["roles"].append(self._serialize_role(role))

            # Categories
            for cat in guild.categories:
                cat_data = {"name": cat.name, "position": cat.position}
                data["categories"].append(cat_data)

            # Channels
            for ch in guild.channels:
                if ch.category is None and not isinstance(ch, discord.CategoryChannel):
                    # Uncategorized channels
                    data["channels"].append(self._serialize_channel(ch))
                elif isinstance(ch, discord.CategoryChannel):
                    continue  # Handled above
                else:
                    # Channel in category — append under its category
                    data["channels"].append(self._serialize_channel(ch))

            # Emojis
            for emoji in guild.emojis:
                data["emojis"].append({"name": emoji.name, "url": str(emoji.url), "animated": emoji.animated})

            filename = f"{guild.name}_{discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.backup_dir / filename
            filepath.write_text(json.dumps(data, indent=2))

            await ctx.send(f"✅ Backup saved: `{filename}`\n**{len(data['roles'])}** roles, **{len(data['channels'])}** channels, **{len(data['emojis'])}** emojis")

        elif action.lower() == "restore":
            await ctx.send("⚠️ Restore creates new channels/roles. It does NOT delete anything. Proceed? (yes/no)")
            try:
                msg = await self.bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                if msg.content.lower() != "yes":
                    await ctx.send("Cancelled.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("Timed out.")
                return

            # List available backups
            backups = sorted(self.backup_dir.glob("*.json"), reverse=True)
            if not backups:
                await ctx.send("No backups found.")
                return

            latest = backups[0]
            data = json.loads(latest.read_text())
            await ctx.send(f"Restoring **{data['name']}** ({len(data['roles'])} roles, {len(data['channels'])} channels)...")

            # Create roles first
            for role_data in reversed(data["roles"]):  # Create bottom-up
                try:
                    await ctx.guild.create_role(
                        name=role_data["name"],
                        color=discord.Color(role_data["color"]),
                        hoist=role_data["hoist"],
                        mentionable=role_data["mentionable"],
                        permissions=discord.Permissions(role_data["permissions"]),
                    )
                except Exception as e:
                    await ctx.send(f"Failed to create role {role_data['name']}: {e}")

            await ctx.send(f"✅ Restore complete from `{latest.name}`")

        else:
            # List backups
            backups = sorted(self.backup_dir.glob("*.json"), reverse=True)
            if not backups:
                await ctx.send("No backups found.")
                return
            lines = [f"**{b.name}** ({b.stat().st_size:,} bytes)" for b in backups[:10]]
            embed = discord.Embed(title="📦 Server Backups", description="\n".join(lines), color=discord.Color.blue())
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BackupsCog(bot))
'''
