FEATURE_ID = "reaction_roles"
FEATURE_NAME = "Reaction Roles"
CATEGORY = "Utility"
DESCRIPTION = "Assign/remove roles based on message reactions"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class ReactionRolesCog(commands.Cog):
    """Reaction-based role assignment."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path("data/reaction_roles.json")
        self._mappings = {}
        self._load()

    def _load(self):
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._mappings = json.loads(self.data_file.read_text())
        except Exception:
            self._mappings = {}

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self._mappings, indent=2))

    @commands.hybrid_command(name="reactionrole", aliases=["rr"], description="Create a reaction role")
    @commands.has_permissions(manage_roles=True)
    async def reactionrole(self, ctx, message_id: str, emoji: str, role: discord.Role):
        try:
            msg = await ctx.channel.fetch_message(int(message_id))
        except (discord.NotFound, ValueError):
            await ctx.send("Message not found. Make sure the message is in this channel.", delete_after=10)
            return

        await msg.add_reaction(emoji)

        key = f"{ctx.guild.id}:{message_id}:{emoji}"
        self._mappings[key] = {"role_id": role.id, "channel_id": ctx.channel.id}
        self._save()

        await ctx.send(f"✅ Reaction role set: {emoji} → {role.mention} on [message]({msg.jump_url})", delete_after=10)

    @commands.hybrid_command(name="rrlist", description="List reaction roles in this server")
    @commands.has_permissions(manage_roles=True)
    async def rrlist(self, ctx):
        server_entries = {k: v for k, v in self._mappings.items() if k.startswith(f"{ctx.guild.id}:")}
        if not server_entries:
            await ctx.send("No reaction roles configured.", delete_after=10)
            return
        lines = [f"**{k.split(':')[2]}** → <@&{v['role_id']}> (msg: {k.split(':')[1]})" for k, v in server_entries.items()]
        embed = discord.Embed(title="Reaction Roles", description="\n".join(lines), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self._handle_reaction(payload, add=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self._handle_reaction(payload, add=False)

    async def _handle_reaction(self, payload, add):
        if payload.member and payload.member.bot:
            return

        emoji_str = str(payload.emoji)
        key = f"{payload.guild_id}:{payload.message_id}:{emoji_str}"

        if key not in self._mappings:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except Exception:
                return

        role = guild.get_role(self._mappings[key]["role_id"])
        if not role:
            return

        try:
            if add:
                await member.add_roles(role)
            else:
                await member.remove_roles(role)
        except (discord.Forbidden, discord.HTTPException):
            pass

async def setup(bot):
    await bot.add_cog(ReactionRolesCog(bot))
'''
