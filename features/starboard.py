FEATURE_ID = "starboard"
FEATURE_NAME = "Starboard"
CATEGORY = "Fun"
DESCRIPTION = "Starboard that reposts messages to a channel when they hit a reaction threshold"
ENV_VARS = ["STARBOARD_CHANNEL", "STAR_TRIGGER", "STAR_EMOJI"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class StarboardCog(commands.Cog):
    """Starboard that highlights popular messages."""

    def __init__(self, bot):
        self.bot = bot
        self.starboard_channel = int(os.getenv("STARBOARD_CHANNEL", "0"))
        self.star_trigger = int(os.getenv("STAR_TRIGGER", "3"))
        self.star_emoji = os.getenv("STAR_EMOJI", "⭐")
        self._starred = set()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self.starboard_channel:
            return
        if str(payload.emoji) != self.star_emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return

        if message.author.bot:
            return
        if message.channel_id == self.starboard_channel:
            return

        # Get reaction count for the star emoji
        for reaction in message.reactions:
            if str(reaction.emoji) == self.star_emoji:
                if reaction.count < self.star_trigger:
                    return
                if message.id in self._starred:
                    return
                self._starred.add(message.id)

                sb = self.bot.get_channel(self.starboard_channel)
                if not sb:
                    return

                embed = discord.Embed(description=message.content or "*[no text / attachment]*", color=discord.Color.gold(), timestamp=message.created_at)
                embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
                embed.add_field(name="Original", value=f"[Jump to message]({message.jump_url})", inline=True)
                embed.add_field(name=self.star_emoji, value=str(reaction.count), inline=True)
                embed.set_footer(text=f"#{message.channel.name}")
                if message.attachments:
                    embed.set_image(url=message.attachments[0].url)
                await sb.send(embed=embed)
                return

async def setup(bot):
    await bot.add_cog(StarboardCog(bot))
'''
