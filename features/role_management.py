FEATURE_ID = "role_management"
FEATURE_NAME = "Role Management"
CATEGORY = "Moderation"
DESCRIPTION = "Create, delete, edit, assign, and color roles"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class RoleManagementCog(commands.Cog):
    """Full role CRUD management."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="role", description="Manage server roles")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, action: str, *args):
        actions = action.lower()
        if actions == "create" and len(args) >= 1:
            name = args[0]
            color = discord.Color.default()
            if len(args) >= 2:
                try:
                    color = int(args[1].lstrip("#"), 16)
                except ValueError:
                    color = discord.Color.default()
            role = await ctx.guild.create_role(name=name, color=discord.Color(color), reason=f"Created by {ctx.author}")
            await ctx.send(f"Created role {role.mention}")

        elif actions == "delete" and len(args) >= 1:
            role = await commands.RoleConverter().convert(ctx, args[0])
            await role.delete(reason=f"Deleted by {ctx.author}")
            await ctx.send(f"Deleted role `{role.name}`")

        elif actions == "assign" and len(args) >= 2:
            member = await commands.MemberConverter().convert(ctx, args[0])
            role = await commands.RoleConverter().convert(ctx, args[1])
            if role in member.roles:
                await member.remove_roles(role, reason=f"Removed by {ctx.author}")
                await ctx.send(f"Removed {role.mention} from {member.mention}")
            else:
                await member.add_roles(role, reason=f"Assigned by {ctx.author}")
                await ctx.send(f"Assigned {role.mention} to {member.mention}")

        elif actions == "color" and len(args) >= 2:
            role = await commands.RoleConverter().convert(ctx, args[0])
            try:
                new_color = int(args[1].lstrip("#"), 16)
                await role.edit(color=discord.Color(new_color))
                await ctx.send(f"Changed color of {role.mention} to `#{new_color:06x}`")
            except ValueError:
                await ctx.send("Invalid color hex. Use #RRGGBB format.")

        elif actions == "rename" and len(args) >= 2:
            role = await commands.RoleConverter().convert(ctx, args[0])
            new_name = " ".join(args[1:])
            await role.edit(name=new_name)
            await ctx.send(f"Renamed role to `{new_name}`")

        elif actions == "hoist" and len(args) >= 1:
            role = await commands.RoleConverter().convert(ctx, args[0])
            await role.edit(hoist=not role.hoist)
            await ctx.send(f"{'Hoisted' if role.hoist else 'Unhoisted'} {role.mention}")

        elif actions == "all":
            roles = [f"{r.mention} — `{r.name}` ({len(r.members)} members)" for r in ctx.guild.roles if not r.is_default()]
            embed = discord.Embed(title=f"Roles in {ctx.guild.name}", description="\n".join(roles[:25]) or "None", color=discord.Color.blue())
            await ctx.send(embed=embed)

        else:
            await ctx.send("Usage:\n`/role create <name> [color]`\n`/role delete <role>`\n`/role assign <user> <role>`\n`/role color <role> <hex>`\n`/role rename <role> <name>`\n`/role hoist <role>`\n`/role all`", delete_after=30)

async def setup(bot):
    await bot.add_cog(RoleManagementCog(bot))
'''
