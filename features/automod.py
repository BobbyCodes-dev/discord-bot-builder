FEATURE_ID = "automod"
FEATURE_NAME = "Auto-Moderation"
CATEGORY = "Moderation"
DESCRIPTION = "Word filter, anti-spam, link blocking, invite filtering"
ENV_VARS = ["BAD_WORDS", "ANTI_SPAM_MAX", "ANTI_SPAM_SECS", "BLOCK_LINKS", "BLOCK_INVITES", "AUTOMOD_IGNORE_CHANNELS"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class AutoModCog(commands.Cog):
    """Automatic moderation tools."""

    def __init__(self, bot):
        self.bot = bot
        self.bad_words = [w.strip().lower() for w in os.getenv("BAD_WORDS", "").split(",") if w.strip()]
        self.anti_spam_max = int(os.getenv("ANTI_SPAM_MAX", "5"))
        self.anti_spam_secs = int(os.getenv("ANTI_SPAM_SECS", "10"))
        self.block_links = os.getenv("BLOCK_LINKS", "false").lower() == "true"
        self.block_invites = os.getenv("BLOCK_INVITES", "false").lower() == "true"
        self.ignore_channels = [int(c.strip()) for c in os.getenv("AUTOMOD_IGNORE_CHANNELS", "").split(",") if c.strip().isdigit()]
        self._msg_buffer = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if message.author.guild_permissions.manage_messages:
            return
        if message.channel.id in self.ignore_channels:
            return

        content_lower = message.content.lower()

        # Word filter
        if self.bad_words and any(w in content_lower for w in self.bad_words):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Watch your language!", delete_after=5)
            return

        # Link blocking
        if self.block_links and ("http://" in content_lower or "https://" in content_lower):
            if not message.author.guild_permissions.manage_messages:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Links are not allowed.", delete_after=5)
                return

        # Invite blocking
        if self.block_invites and ("discord.gg/" in content_lower or "discord.com/invite/" in content_lower):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Invite links are not allowed.", delete_after=5)
            return

        # Anti-spam
        now = discord.utils.utcnow().timestamp()
        uid = message.author.id
        self._msg_buffer.setdefault(uid, [])
        self._msg_buffer[uid] = [t for t in self._msg_buffer[uid] if now - t < self.anti_spam_secs]
        self._msg_buffer[uid].append(now)
        if len(self._msg_buffer[uid]) > self.anti_spam_max:
            await message.channel.send(f"{message.author.mention} Slow down! You're sending messages too fast.", delete_after=5)

async def setup(bot):
    await bot.add_cog(AutoModCog(bot))
'''
