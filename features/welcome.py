FEATURE_ID = "welcome"
FEATURE_NAME = "Welcome & Leave Messages"
CATEGORY = "Utility"
DESCRIPTION = "Custom welcome and leave messages with configurable channels"
ENV_VARS = ["WELCOME_CHANNEL_ID", "LEAVE_CHANNEL_ID", "WELCOME_MSG", "LEAVE_MSG"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class WelcomeCog(commands.Cog):
    """Welcome and leave message system."""

    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = int(os.getenv("WELCOME_CHANNEL_ID", "0"))
        self.leave_channel_id = int(os.getenv("LEAVE_CHANNEL_ID", "0"))
        self.welcome_msg = os.getenv("WELCOME_MSG", "Welcome {user} to {server}!")
        self.leave_msg = os.getenv("LEAVE_MSG", "{user} has left the server.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.welcome_channel_id:
            ch = member.guild.get_channel(self.welcome_channel_id)
            if ch:
                embed = discord.Embed(
                    description=self.welcome_msg.format(user=member.mention, server=member.guild.name),
                    color=discord.Color.green(),
                )
                embed.set_author(name=str(member), icon_url=member.display_avatar.url)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Member #", value=str(member.guild.member_count), inline=True)
                embed.set_footer(text=f"ID: {member.id}")
                await ch.send(embed=embed)
        try:
            await member.send(f"Welcome to **{member.guild.name}**! We're glad to have you.")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if self.leave_channel_id:
            ch = member.guild.get_channel(self.leave_channel_id)
            if ch:
                embed = discord.Embed(
                    description=self.leave_msg.format(user=str(member)),
                    color=discord.Color.orange()
                )
                await ch.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
'''
