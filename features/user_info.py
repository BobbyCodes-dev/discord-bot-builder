FEATURE_ID = "user_info"
FEATURE_NAME = "User Info"
CATEGORY = "Utility"
DESCRIPTION = "Detailed user information: roles, join date, permissions, badges"
ENV_VARS = []
DEPENDENCIES = []

BLOCK_CODE = r'''
class UserInfoCog(commands.Cog):
    """Detailed user information command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois"], description="Show user info")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(title=f"{member}", color=member.color if member.color.value else discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)

        # Basic info
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)

        # Dates
        if member.joined_at:
            embed.add_field(name="Joined Server", value=f"{discord.utils.format_dt(member.joined_at, 'D')}\n{discord.utils.format_dt(member.joined_at, 'R')}", inline=True)
        embed.add_field(name="Account Created", value=f"{discord.utils.format_dt(member.created_at, 'D')}\n{discord.utils.format_dt(member.created_at, 'R')}", inline=True)

        # Roles
        roles = [r.mention for r in reversed(member.roles) if not r.is_default()]
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles[:20]) or "None", inline=False)

        # Permissions
        if member.guild_permissions.administrator:
            embed.add_field(name="Key Perms", value="Administrator", inline=True)
        else:
            perms = []
            if member.guild_permissions.manage_messages:
                perms.append("Manage Msgs")
            if member.guild_permissions.kick_members:
                perms.append("Kick")
            if member.guild_permissions.ban_members:
                perms.append("Ban")
            if member.guild_permissions.manage_channels:
                perms.append("Manage Channels")
            if member.guild_permissions.manage_roles:
                perms.append("Manage Roles")
            if perms:
                embed.add_field(name="Key Perms", value=", ".join(perms), inline=True)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserInfoCog(bot))
'''
