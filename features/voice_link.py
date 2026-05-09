FEATURE_ID = "voice_link"
FEATURE_NAME = "Voice Text Linking"
CATEGORY = "Utility"
DESCRIPTION = "Auto-create text channels paired with voice channels"
ENV_VARS = ["VOICE_LINK_CATEGORY_ID"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class VoiceLinkCog(commands.Cog):
    """Auto-create text channels for voice channels."""

    def __init__(self, bot):
        self.bot = bot
        self.category_id = int(os.getenv("VOICE_LINK_CATEGORY_ID", "0"))
        self._linked_channels = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Voice channel created/joined
        if after.channel:
            cat = after.channel.category
            # Only in configured category
            if self.category_id and cat and cat.id == self.category_id:
                await self._ensure_text_channel(after.channel, member.guild)

            # If user left a channel and it's now empty, clean up
            if before.channel and before.channel != after.channel:
                await self._cleanup_if_empty(before.channel)

            return

        # Voice channel left
        if before.channel:
            await self._cleanup_if_empty(before.channel)

    async def _ensure_text_channel(self, voice_channel, guild):
        if voice_channel.id in self._linked_channels:
            return

        # Create matching text channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        text_name = f"💬-{voice_channel.name.replace(' ', '-').lower()}"
        try:
            text_ch = await guild.create_text_channel(
                name=text_name[:100],
                category=voice_channel.category,
                overwrites=overwrites,
                topic=f"Text chat for 🔊 {voice_channel.name}",
            )
            self._linked_channels[voice_channel.id] = text_ch.id
        except Exception:
            pass

    async def _cleanup_if_empty(self, voice_channel):
        if voice_channel.id not in self._linked_channels:
            return
        if len(voice_channel.members) > 0:
            return

        text_ch_id = self._linked_channels.pop(voice_channel.id, None)
        if text_ch_id:
            guild = voice_channel.guild
            text_ch = guild.get_channel(text_ch_id)
            if text_ch:
                try:
                    await text_ch.delete(reason="Voice channel emptied")
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(VoiceLinkCog(bot))
'''
