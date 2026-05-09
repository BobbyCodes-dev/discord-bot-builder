FEATURE_ID = "autoroles"
FEATURE_NAME = "Autoroles"
CATEGORY = "Moderation"
DESCRIPTION = "Automatically assign roles to new members on join"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class AutorolesCog(commands.Cog):
    """Automatically assign roles to new members."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/autoroles.json")
        self._autoroles = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._autoroles = json.loads(self.data_file.read_text())
        except Exception:
            self._autoroles = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._autoroles, indent=2))

    @commands.hybrid_command(name="autorole", description="Manage auto-assign roles")
    @commands.has_permissions(manage_roles=True)
    async def autorole(self, ctx, action: str, role: discord.Role = None):
        gid = str(ctx.guild.id)

        if action.lower() == "add":
            if not role:
                await ctx.send("Usage: `/autorole add <role>`", delete_after=20)
                return
            self._autoroles.setdefault(gid, [])
            if role.id in self._autoroles[gid]:
                await ctx.send(f"{role.mention} is already an autorole.")
            else:
                self._autoroles[gid].append(role.id)
                self._save()
                await ctx.send(f"✅ {role.mention} will be assigned to new members.")

        elif action.lower() == "remove":
            if not role:
                await ctx.send("Usage: `/autorole remove <role>`", delete_after=20)
                return
            if gid in self._autoroles and role.id in self._autoroles[gid]:
                self._autoroles[gid].remove(role.id)
                if not self._autoroles[gid]:
                    del self._autoroles[gid]
                self._save()
                await ctx.send(f"Removed {role.mention} from autoroles.")

        elif action.lower() == "list":
            roles = self._autoroles.get(gid, [])
            if not roles:
                await ctx.send("No autoroles configured.")
                return
            mentions = ", ".join(f"<@&{r}>" for r in roles)
            await ctx.send(f"**Autoroles:** {mentions}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        gid = str(member.guild.id)
        role_ids = self._autoroles.get(gid, [])
        for rid in role_ids:
            role = member.guild.get_role(rid)
            if role and not role.managed:
                try:
                    await member.add_roles(role, reason="Autorole")
                except (discord.Forbidden, discord.HTTPException):
                    pass

async def setup(bot):
    await bot.add_cog(AutorolesCog(bot))
'''
