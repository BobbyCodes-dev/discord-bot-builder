FEATURE_ID = "temp_voice"
FEATURE_NAME = "Temporary Voice Channels"
CATEGORY = "Utility"
DESCRIPTION = "Auto-create temporary voice channels that delete when empty"
ENV_VARS = ["TEMP_VOICE_CATEGORY_ID"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class TempVoiceCog(commands.Cog):
    """Temporary voice channel system."""

    def __init__(self, bot):
        self.bot = bot
        self.category_id = int(os.getenv("TEMP_VOICE_CATEGORY_ID", "0"))
        self._temp_channels = []

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and not before.channel:
            # User joined a channel
            if after.channel.id == self.category_id or (self.category_id and after.channel.category_id == self.category_id):
                return  # Don't create temp channel from another temp channel
            await self._handle_join(member, after.channel)

        if before.channel and not after.channel:
            # User left a channel
            await self._handle_leave(before.channel)

        # Handle channel switch
        if before.channel and after.channel and before.channel != after.channel:
            await self._handle_leave(before.channel)

    async def _handle_join(self, member, channel):
        # If user joins the trigger channel, create a new temp channel
        if self.category_id and channel.id == self.category_id:
            guild = member.guild
            cat = guild.get_channel(self.category_id)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True),
                member: discord.PermissionOverwrite(manage_channels=True, connect=True, mute_members=True, deafen_members=True, move_members=True),
            }

            try:
                new_ch = await guild.create_voice_channel(
                    name=f"🎤 {member.display_name}",
                    category=cat,
                    overwrites=overwrites,
                )
                await member.move_to(new_ch)
                self._temp_channels.append(new_ch.id)
            except Exception:
                pass

    async def _handle_leave(self, channel):
        if channel.id not in self._temp_channels:
            return
        # Only delete if empty
        if len(channel.members) == 0:
            try:
                await channel.delete()
                self._temp_channels.remove(channel.id)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(TempVoiceCog(bot))
'''
